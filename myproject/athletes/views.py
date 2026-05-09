from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AthleteForm, UploadFileForm
from .utils import (
    save_athlete_to_file, save_uploaded_file, validate_json_file, validate_xml_file,
    get_all_athletes_from_files
)
import os
from django.conf import settings

def index(request):
    athletes, file_errors = get_all_athletes_from_files()
    no_files = len(list(settings.DATA_DIR.glob('*'))) == 0
    context = {
        'athlete_form': AthleteForm(),
        'upload_form': UploadFileForm(),
        'athletes': athletes,
        'no_files': no_files,
        'file_errors': file_errors,
    }
    return render(request, 'athletes/index.html', context)

def add_athlete(request):
    if request.method == 'POST':
        form = AthleteForm(request.POST)
        if form.is_valid():
            athlete_data = {
                'name': form.cleaned_data['name'],
                'sport': form.cleaned_data['sport'],
                'age': form.cleaned_data['age'],
                'country': form.cleaned_data['country'],
                'medals': {
                    'gold': form.cleaned_data['gold'],
                    'silver': form.cleaned_data['silver'],
                    'bronze': form.cleaned_data['bronze'],
                }
            }
            file_format = form.cleaned_data['file_format']
            save_athlete_to_file(athlete_data, file_format)
            messages.success(request, f'Спортсмен успешно сохранён в {file_format.upper()} файл.')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('athletes:index')

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES['data_file']
            try:
                file_path, ext = save_uploaded_file(uploaded)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if ext == 'json':
                    valid, msg = validate_json_file(content)
                else:
                    valid, msg = validate_xml_file(content)
                if not valid:
                    os.remove(file_path)
                    messages.error(request, f'Файл невалиден: {msg}. Файл удалён.')
                else:
                    messages.success(request, f'Файл {uploaded.name} успешно загружен и валиден.')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Ошибка при загрузке: {e}')
        else:
            messages.error(request, 'Неверная форма загрузки.')
    return redirect('athletes:index')