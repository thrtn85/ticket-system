# tickets/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Comment, Ticket
from users.models import CustomUser


ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt']

def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f'Unsupported file extension. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}')


class CommentForm(forms.ModelForm):
    attachment = forms.FileField(required=False, validators=[validate_file_extension])

    class Meta:
        model = Comment
        fields = ['message','attachment']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Write a reply...'})
        }


class TicketForm(forms.ModelForm):
    attachment = forms.FileField(required=False, validators=[validate_file_extension])

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'status', 'agent', 'attachment']

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
        else:
            # Show only agents in the agent field
            self.fields['agent'].queryset = CustomUser.objects.filter(role='agent')