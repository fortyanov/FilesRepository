from django.shortcuts import render_to_response, HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.template import RequestContext
from django.db import IntegrityError
from main.forms import LoginForm, RegisterForm
from main.models import File, Repr
from FileRepo.settings import MEDIA_ROOT
import os
import hashlib


def login(request):
    login_form_errors = {}
    if request.method == 'GET':
        login_form = LoginForm()
    elif request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            cd = login_form.cleaned_data
            user = auth.authenticate(username=cd['login'], password=cd['password'])
            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect("/repository/")
            else:
                login_form._errors["login"] = login_form.error_class([u'Ошибка при авторизации'])
        login_form_errors = {field: login_form._errors[field].as_text()[2:] for field in login_form._errors}

    return render_to_response('login.html', {'login_form_errors': login_form_errors}, context_instance=RequestContext(request))


def register(request):
    reg_form_errors = {}
    if request.method == 'GET':
        reg_form = RegisterForm()
    elif request.method == 'POST':
        reg_form = RegisterForm(request.POST)
        if reg_form.is_valid():
            cd = reg_form.cleaned_data
            if cd['password'] == cd['rep_password']:
                try:
                    user = User.objects.create(username=cd['login'])
                    user.set_password(cd['password'])
                    user.save()
                    user = auth.authenticate(username=cd['login'], password=cd['password'])
                    auth.login(request, user)
                    return HttpResponseRedirect("/repository/")
                except IntegrityError:
                    reg_form._errors['login'] = reg_form.error_class(['Невозможно создать существующего пользователя'])
            reg_form._errors['password'] = reg_form.error_class(['Пароли не совпали'])
            reg_form._errors['rep_password'] = reg_form.error_class(['Пароли не совпали'])
        reg_form_errors = {k: reg_form._errors[k].as_text()[2:] for k in reg_form._errors.keys()}

    return render_to_response('register.html', {"reg_form_errors": reg_form_errors}, context_instance=RequestContext(request))


def repository_proc(request):
    files = [(f.reprname, f.file.file.name) for f in Repr.objects.filter(user=request.user)]
    return {'files': files}


@login_required
def repository(request):
    return render_to_response('repository.html', context_instance=RequestContext(request, processors=[repository_proc]))


@login_required
def add_file(request):
    errors = []
    if request.method == 'POST':
        files = request.FILES.getlist('file')
        if files:
            for f in files:
                hash = hashlib.md5(f.read()).hexdigest()
                file_exist = File.objects.filter(hash=hash)
                if len(Repr.objects.filter(user=request.user)) < 100:
                    if file_exist:
                        r = Repr.objects.filter(file=file_exist[0])[0]
                        errors.append('Оригинал файла %s уже существует у пользователя %s, под именем %s.' %
                                      (f.name, r.user.username, r.reprname))
                        if not Repr.objects.filter(file=file_exist[0], user=request.user):
                            Repr.objects.create(reprname=f.name, user=request.user, file=file_exist[0])
                    else:
                        file = File.objects.create(hash=hash, file=f)
                        file.save()
                        Repr.objects.create(reprname=f.name, user=request.user, file=file)
                else:
                    errors.append('У пользователя может быть не более 100 файлов!')
                    break
        else:
            errors.append('Файлы для загрузки не выбраны!')

    return render_to_response('repository.html', {'errors': errors}, context_instance=RequestContext(request, processors=[repository_proc]))


@login_required
def del_file(request, filename):
    rep = Repr.objects.filter(file=File.objects.get(file=('./'+filename)))
    if len(rep) == 1:
        rep[0].file.delete()
        rep[0].delete()
        os.remove('%s%s' % (MEDIA_ROOT, filename))
    else:
        # map(lambda r: r.delete() if r.user == request.user else r, rep)
        [r.delete() for r in rep if r.user == request.user]

    return render_to_response('repository.html', context_instance=RequestContext(request, processors=[repository_proc]))


def download_file(request, filename):
    file = open('%s%s' % (MEDIA_ROOT, filename), 'rb')
    response = HttpResponse(file, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/accounts/login/")