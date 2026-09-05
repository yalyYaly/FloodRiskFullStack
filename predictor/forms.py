from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Name")
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("first_name", "username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Username or email")
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier", "").strip()
        password = cleaned_data.get("password")
        if not identifier or not password:
            return cleaned_data

        username = identifier
        user = User.objects.filter(email__iexact=identifier).first()
        if user:
            username = user.get_username()

        self.user_cache = authenticate(
            self.request,
            username=username,
            password=password,
        )
        if self.user_cache is None:
            raise forms.ValidationError("Enter a valid username/email and password.")
        if not self.user_cache.is_active:
            raise forms.ValidationError("This account is inactive.")
        return cleaned_data

    def get_user(self):
        return self.user_cache