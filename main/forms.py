from .models import ClientsList
from django.forms import ModelForm, TextInput, Textarea


class ClientListForm(ModelForm):
    class Meta:
        model = ClientsList
        fields = ["client_name"]
        widgets = {"client_name": TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите наименование клиента'
        })}