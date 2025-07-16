from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.timezone import now, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import Ticket, TicketHistory
from .forms import CommentForm, TicketForm
from .mixins import AdminOrAgentRequiredMixin




class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    context_object_name = 'tickets'
    template_name = 'tickets/ticket_list.html'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        view = self.request.GET.get('view')
        
        if view == 'all' and user.role == 'agent':
            return Ticket.objects.all()
        if user.role == 'agent':
            return Ticket.objects.filter(Q(agent=user) | Q(status='open'))
        else:
            return Ticket.objects.filter(customer=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        view = self.request.GET.get('view')

        if view != 'all':
            if user.role == 'agent':
                context['assigned_tickets'] = Ticket.objects.filter(agent=user)
                context['unassigned_tickets'] = Ticket.objects.filter(agent__isnull=True, status='open')
            else:
                context['customer_tickets'] = Ticket.objects.filter(customer=user)

        # Chart data only for agents
        if user.role == 'agent':
            context['tickets_by_status'] = Ticket.objects.values('status').annotate(count=Count('id'))
            context['open_tickets_count'] = Ticket.objects.filter(Q(status='open') | Q(status='in_progress')).count()
            context['closed_tickets_count'] = Ticket.objects.filter(status='closed').count()

        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    context_object_name = 'ticket'
    template_name = 'tickets/ticket_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('user').order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST, request.FILES)  # ✅ Fix here
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = self.object
            comment.user = request.user
            comment.save()
        return redirect('tickets:ticket_detail', pk=self.object.pk)


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:ticket_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # pass user to form
        return kwargs
    
    def form_valid(self, form):
        ticket = form.save(commit=False)
        user = self.request.user
        ticket.customer = user

        if user.role != 'agent':
            ticket.status = 'open'
            ticket.agent = None

        ticket.save()
        return super().form_valid(form)


class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:ticket_list')

    def test_func(self):
        ticket = self.get_object()
        user = self.request.user
        if user.role == 'agent':
            return True
        return ticket.customer == user

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter agent field queryset to only users with role 'agent'
        form.fields['agent'].queryset = form.fields['agent'].queryset.filter(role='agent')
        return form

    def form_valid(self, form):
        original = self.get_object()
        ticket = form.save(commit=False)

        status_changed = ticket.status != original.status
        agent_changed = ticket.agent != original.agent
        priority_changed = ticket.priority != original.priority

        response = super().form_valid(form)

        if status_changed or agent_changed or priority_changed:
            TicketHistory.objects.create(
                ticket=self.object,
                changed_by=self.request.user,
                previous_status=original.status if status_changed else None,
                new_status=ticket.status if status_changed else None,
                previous_agent=original.agent if agent_changed else None,
                new_agent=ticket.agent if agent_changed else None,
                previous_priority=original.priority if priority_changed else None,
                new_priority=ticket.priority if priority_changed else None,
            )

        return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # pass user to form
        return kwargs


class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket
    template_name = 'tickets/ticket_confirm_delete.html'
    success_url = reverse_lazy('tickets:ticket_list')

    def test_func(self):
        # Only the customer who created the ticket can delete it
        ticket = self.get_object()
        return self.request.user == ticket.customer
    

class AdminReportView(LoginRequiredMixin, AdminOrAgentRequiredMixin, TemplateView):
    template_name = 'reports/admin_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Tickets by status
        status_qs = Ticket.objects.values('status').annotate(count=Count('id'))
        context['status_labels'] = [item['status'].capitalize() for item in status_qs]
        context['status_counts'] = [item['count'] for item in status_qs]

        # Tickets by priority
        priority_qs = Ticket.objects.values('priority').annotate(count=Count('id'))
        context['priority_labels'] = [item['priority'].capitalize() for item in priority_qs]
        context['priority_counts'] = [item['count'] for item in priority_qs]

        # Tickets by agent
        agent_qs = Ticket.objects.exclude(agent=None).values('agent__email').annotate(count=Count('id'))
        context['agent_labels'] = [item['agent__email'] for item in agent_qs]
        context['agent_counts'] = [item['count'] for item in agent_qs]

        # Activity over the last 30 days
        last_30_days = now() - timedelta(days=30)
        activity_qs = (
            Ticket.objects.filter(created_at__gte=last_30_days)
            .extra({'day': "date(created_at)"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        context['activity_days'] = [str(item['day']) for item in activity_qs]
        context['activity_counts'] = [item['count'] for item in activity_qs]

        return context


@login_required
def assign_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    if user.role == 'agent' and ticket.agent is None:
        ticket.agent = user
        ticket.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", reverse('tickets:ticket_list')))
