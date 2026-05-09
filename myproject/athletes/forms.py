from django import forms

class AthleteForm(forms.Form):
    name = forms.CharField(max_length=100, label='Имя')
    sport = forms.CharField(max_length=100, label='Вид спорта')
    age = forms.IntegerField(min_value=0, max_value=120, label='Возраст')
    country = forms.CharField(max_length=100, label='Страна')
    gold = forms.IntegerField(min_value=0, label='Золото')
    silver = forms.IntegerField(min_value=0, label='Серебро')
    bronze = forms.IntegerField(min_value=0, label='Бронза')
    file_format = forms.ChoiceField(choices=[('json', 'JSON'), ('xml', 'XML')], label='Формат файла')

class UploadFileForm(forms.Form):
    data_file = forms.FileField(label='Файл (JSON/XML)')