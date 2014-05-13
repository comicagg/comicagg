from django import forms

class ProfileForm(forms.Form):
    hide_read = forms.BooleanField(required=False)
    #  sort_by_points = forms.BooleanField(required=False)
    alert_new_comics = forms.BooleanField(required=False)
    alert_new_blog = forms.BooleanField(required=False)
    navigation_max_columns = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'2'}))
    navigation_max_per_column = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'2'}))

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    oauth2 = forms.BooleanField(widget=forms.HiddenInput(), required=False)

class EmailChangeForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'size':'35'}))

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))

class PasswordResetForm(forms.Form):
    data = forms.CharField(widget=forms.TextInput(attrs={'size':'35'}))

class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'size':'30'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'size':'50'}))
    captcha = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}))
