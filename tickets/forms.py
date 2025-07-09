# tickets/forms.py

from django import forms
from .models import Comment, Ticket

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Write a reply...'})
        }


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'status', 'agent']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # If user is not agent, remove status and agent fields from the form
        if user and user.role != 'agent':
            self.fields.pop('status')
            self.fields.pop('agent')
            self.fields.pop('priority')