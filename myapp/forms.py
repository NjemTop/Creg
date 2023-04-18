from django import forms
from .models import BMInfoOnClient

class AddClientForm(forms.ModelForm):
    class Meta:
        model = BMInfoOnClient
        fields = ['client_name', 'notes']
