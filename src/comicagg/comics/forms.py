"""Forms used in the comics app"""
from django import forms

class RequestForm(forms.Form):
    url = forms.URLField(widget=forms.TextInput(attrs={'size':50}))
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':3, 'cols':40}))
