"""Form API dealing with User Login and Registration.

Available Class:
- UserLoginForm: Deals with user login form by providing username and password fields.
- UserRegisterForm: Deals with user register form by providing username, password, and email fields.
"""
from django import forms
from django.contrib.auth import authenticate, get_user_model


class UserLoginForm(forms.Form):
    """Dealing with user login
    
    Public attributes:
    - username: CharField
    - password: CharField implementing PasswordInput to conceal what a user inputs
    """
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))

    # form.is_valid()の呼ばれた時に、その内部の処理としてcleanメソッドも呼ばれる
    def clean(self):
        """
        :param self:
        :return: None
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            user = authenticate(username=username, password=password)   # <class 'django.contrib.auth.models.User'>
        if not user:
                raise forms.ValidationError('This user does not exist.')
        if not user.check_password(password):
                raise forms.ValidationError('Incorrect password.')
        if not user.is_active:
                raise forms.ValidationError('This user is not longer active.')
        # return super(UserLoginForm, self).clean(*args, **kwargs)
        return super().clean()


User = get_user_model()


class UserRegisterForm(forms.ModelForm):
    """Dealing with user register
    
    Public attributes:
    - username: CharFiled 
    - email: EmailInput
    - email2: EmailInput for confirming user email
    - password: CharField implementing PasswordInput to conceal what a user inputs 
    """
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'enter you email address'}))
    email2 = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'confirm you email address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'put your password'}))

    class Meta:
        """Binding User Model with User Register Form
        
        Attributes:
        - model: Storing User Model 
        - fields: The list of shown fields
        """
        model = User
        fields = ['username', 'email', 'email2', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username_qs = User.objects.filter(username=username)
        if username_qs.exists():
            raise forms.ValidationError('The same username has already existed')
        return username

    def clean_email2(self):
        email = self.cleaned_data.get('email')
        email2 = self.cleaned_data.get('email2')
        if email != email2:
            raise forms.ValidationError('The email you typed does not match!!!')
        email_qs = User.objects.filter(email=email)
        if email_qs.exists():
            raise forms.ValidationError('This email has already been registered!!!')
        return email
