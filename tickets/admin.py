from django.contrib import admin
from .models import Ticket, Comment, TicketHistory
from django.contrib import admin

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    can_delete = True
    fields = ('message','attachment', 'created_at')
    readonly_fields = ('created_at',)

    def has_change_permission(self, request, obj=None):
        return True  # Allow edits

    def has_add_permission(self, request, obj=None):
        return True  # Allow adding

    def has_delete_permission(self, request, obj=None):
        return True  # Allow deleting

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'status', 'customer', 'agent', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'customer__email', 'agent__email')
    autocomplete_fields = ('customer', 'agent')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CommentInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'status')
        }),
        ('Participants', {
            'fields': ('customer', 'agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def save_formset(self, request, form, formset, change):
        # Override to auto-assign the user to new comments
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Comment) and not instance.user_id:
                instance.user = request.user  # Set current admin user
            instance.save()
        formset.save_m2m()

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_id_display', 'user', 'created_at')
    search_fields = ('message', 'user__email', 'ticket__id')
    list_filter = ('created_at',)

    def ticket_id_display(self, obj):
        return f"#{obj.ticket.id}"
    ticket_id_display.short_description = "Ticket ID"

@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'changed_by', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('new_status', 'timestamp')