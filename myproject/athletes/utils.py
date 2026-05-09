import json
import xml.etree.ElementTree as ET
from pathlib import Path
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
import uuid

def validate_athlete(data):
    required_fields = ['name', 'sport', 'age', 'country', 'medals']
    if not all(field in data for field in required_fields):
        return False
    if not isinstance(data['name'], str) or not data['name'].strip():
        return False
    if not isinstance(data['sport'], str) or not data['sport'].strip():
        return False
    if not isinstance(data['age'], int) or not (0 <= data['age'] <= 120):
        return False
    if not isinstance(data['country'], str) or not data['country'].strip():
        return False
    medals = data['medals']
    if not isinstance(medals, dict):
        return False
    for key in ['gold', 'silver', 'bronze']:
        if key not in medals or not isinstance(medals[key], int) or medals[key] < 0:
            return False
    return True

def validate_athletes_list(data):
    if isinstance(data, list):
        return all(validate_athlete(item) for item in data)
    elif isinstance(data, dict):
        return validate_athlete(data)
    return False

def validate_json_file(content):
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return False, f"Ошибка синтаксиса JSON: {e}"
    if validate_athletes_list(data):
        return True, data
    else:
        return False, "Структура данных не соответствует схеме спортсмена"

def validate_xml_file(content):
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return False, f"Ошибка синтаксиса XML: {e}"
    
    athletes = []
    if root.tag == 'athletes':
        athlete_elements = root.findall('athlete')
        if not athlete_elements:
            return False, "Корневой тег <athletes> не содержит элементов <athlete>"
    elif root.tag == 'athlete':
        athlete_elements = [root]
    else:
        return False, "Корневой тег должен быть <athlete> или <athletes>"
    
    for elem in athlete_elements:
        try:
            athlete = {
                'name': elem.find('name').text,
                'sport': elem.find('sport').text,
                'age': int(elem.find('age').text),
                'country': elem.find('country').text,
                'medals': {
                    'gold': int(elem.find('medals').find('gold').text),
                    'silver': int(elem.find('medals').find('silver').text),
                    'bronze': int(elem.find('medals').find('bronze').text),
                }
            }
            if validate_athlete(athlete):
                athletes.append(athlete)
            else:
                return False, "Некорректные данные внутри XML"
        except (AttributeError, ValueError, TypeError):
            return False, "Неверная структура XML (отсутствуют обязательные поля)"
    
    if root.tag == 'athlete' and len(athlete_elements) == 1:
        return True, athletes[0]
    else:
        return True, athletes

def save_athlete_to_file(athlete_dict, file_format):
    timestamp = str(uuid.uuid4())[:8]
    filename = f"athlete_{timestamp}.{file_format}"
    file_path = settings.DATA_DIR / filename
    
    if file_format == 'json':
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(athlete_dict, f, ensure_ascii=False, indent=2)
    elif file_format == 'xml':
        root = ET.Element('athlete')
        ET.SubElement(root, 'name').text = athlete_dict['name']
        ET.SubElement(root, 'sport').text = athlete_dict['sport']
        ET.SubElement(root, 'age').text = str(athlete_dict['age'])
        ET.SubElement(root, 'country').text = athlete_dict['country']
        medals_elem = ET.SubElement(root, 'medals')
        ET.SubElement(medals_elem, 'gold').text = str(athlete_dict['medals']['gold'])
        ET.SubElement(medals_elem, 'silver').text = str(athlete_dict['medals']['silver'])
        ET.SubElement(medals_elem, 'bronze').text = str(athlete_dict['medals']['bronze'])
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    return file_path

def save_uploaded_file(uploaded_file: UploadedFile):
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ['.json', '.xml']:
        raise ValueError("Неподдерживаемое расширение. Ожидается .json или .xml")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = settings.DATA_DIR / safe_name
    with open(file_path, 'wb') as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)
    return file_path, ext[1:]

def get_all_athletes_from_files():
    athletes = []
    errors = []
    for file_path in settings.DATA_DIR.glob('*'):
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            valid, data = validate_json_file(content)
            if valid:
                if isinstance(data, list):
                    athletes.extend(data)
                else:
                    athletes.append(data)
            else:
                errors.append(f"Файл {file_path.name}: {data}")
        elif file_path.suffix == '.xml':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            valid, data = validate_xml_file(content)
            if valid:
                if isinstance(data, list):
                    athletes.extend(data)
                else:
                    athletes.append(data)
            else:
                errors.append(f"Файл {file_path.name}: {data}")
    return athletes, errors