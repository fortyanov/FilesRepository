from django.forms import *
from multiupload.fields import MultiFileField


class LoginForm(Form):
    login = CharField(label=u'Логин', max_length=15)
    password = CharField(label=u'Пароль', max_length=15, widget=PasswordInput)

    def clean_login(self):
        login = self.cleaned_data['login']
        if len(login) < 4:
            raise forms.ValidationError(u"Не менее 4 символов.")
        return login

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 4:
            raise forms.ValidationError(u"Не менее 4 символов.")
        return password


class RegisterForm(LoginForm):
    rep_password = CharField(label=u'Пароль', max_length=15, widget=PasswordInput)

