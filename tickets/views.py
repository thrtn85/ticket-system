from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from .models import Ticket, Comment
from .forms import CommentForm, TicketForm
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect


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
            context['open_tickets_count'] = Ticket.objects.filter(status='open').count()
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
        form = CommentForm(request.POST)
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
        return super().form_valid(form)
    
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
    

@login_required
def assign_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    if user.role == 'agent' and ticket.agent is None:
        ticket.agent = user
        ticket.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", reverse('tickets:ticket_list')))