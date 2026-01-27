import os
import csv
import io
import re
import threading
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, stream_with_context
from data import get_indicator_choices, get_indicator_details

# Імпорти для Word
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

app = Flask(__name__)
# У продакшені краще використовувати змінну оточення
app.secret_key = 'd5aeb79aff27c1cbc690473e25c5b70dbcc959da288a0f67'

LEADERBOARD_FILE = 'leaderboard.csv'
ALLOWED_EXTENSIONS = {'csv'}
leaderboard_lock = threading.Lock()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_leaderboard():
    leaderboard_data = {}
    try:
        with leaderboard_lock:
            with open(LEADERBOARD_FILE, 'r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                header = next(reader, None)
                expected_header = ['ПІБ', 'Посада', 'Загальний бал']
                # Перевірка заголовка (спрощена)
                if header != expected_header and header != ['ПІБ', 'Загальний бал']: 
                    pass 
                
                for i, row in enumerate(reader):
                    row_num = i + 2
                    name = ""
                    score_str = ""
                    try:
                        if len(row) == 3: 
                            name = row[0].strip()
                            position = row[1].strip() or "Не вказано"
                            score_str = row[2]
                            score = float(score_str.replace(',', '.'))
                        elif len(row) == 2: 
                            name = row[0].strip()
                            position = "Не вказано"
                            score_str = row[1]
                            score = float(score_str.replace(',', '.'))
                        elif row: 
                            continue
                        else: 
                            continue
                        
                        if name:
                            if name in leaderboard_data:
                                if score > leaderboard_data[name]['score']: 
                                    leaderboard_data[name] = {'score': score, 'position': position if len(row)==3 else leaderboard_data[name].get('position', position)}
                            else: 
                                leaderboard_data[name] = {'score': score, 'position': position}
                    except ValueError: 
                        print(f"Warning: Could not convert score '{score_str}' for '{name}'")
                    except Exception as e: 
                        print(f"Error processing row {row_num}: {e}")
    except FileNotFoundError: 
        print(f"{LEADERBOARD_FILE} not found. Will be created.")
    except Exception as e: 
        print(f"Error reading {LEADERBOARD_FILE}: {e}")
    return leaderboard_data

def save_leaderboard(leaderboard_data):
    try:
        with leaderboard_lock:
            with open(LEADERBOARD_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['ПІБ', 'Посада', 'Загальний бал'])
                for name, data in sorted(leaderboard_data.items()):
                    score = data.get('score', 0.0)
                    position = data.get('position', 'Не вказано')
                    score_str = "{:.2f}".format(score).replace('.', ',')
                    writer.writerow([name, position, score_str])
    except Exception as e: 
        print(f"Error saving {LEADERBOARD_FILE}: {e}")
        flash(f"Could not save rating update. Error: {e}", 'error')

def parse_input_data_string(input_str, expected_type):
    parsed_values = {}
    input_str = input_str.strip()
    if expected_type == 'boolean': 
        parsed_values['boolean_value'] = (input_str.lower() == 'так')
        return parsed_values
    elif expected_type == 'fixed' or input_str == '-': 
        return {}
    
    n_match = re.search(r'n=(\d+([.,]\d+)?)', input_str, re.IGNORECASE)
    s_match = re.search(r'S=(\d+([.,]\d+)?)', input_str, re.IGNORECASE)
    k_match = re.search(r'k=(\d+([.,]\d+)?)', input_str, re.IGNORECASE)
    
    try:
        if n_match: 
            n_val = float(n_match.group(1).replace(',', '.'))
            parsed_values['n_value'] = n_val if n_val >= 0 else 0
        if s_match: 
            s_val = float(s_match.group(1).replace(',', '.'))
            parsed_values['s_value'] = s_val if s_val >= 0 else 0
        if k_match: 
            k_val = float(k_match.group(1).replace(',', '.'))
            parsed_values['k_value'] = k_val if k_val >= 0 else 0
    except ValueError as e: 
        print(f"Error parsing number in '{input_str}': {e}")
    return parsed_values


@app.route('/')
def index():
    indicator_choices = get_indicator_choices()
    current_entries = session.get('entries', [])
    current_total_block1 = sum(e['score'] for e in current_entries if e.get('block') == 1)
    current_total_block2 = sum(e['score'] for e in current_entries if e.get('block') == 2)
    return render_template('index.html', indicator_choices=indicator_choices, current_entries=current_entries, current_total_block1=current_total_block1, current_total_block2=current_total_block2)

@app.route('/update_personal_data', methods=['POST'])
def update_personal_data():
    session['full_name'] = request.form.get('full_name', '').strip()
    session['institution_type'] = request.form.get('institution_type')
    session['department'] = request.form.get('department')
    session['position'] = request.form.get('position')
    session.modified = True
    
    if (session.get('full_name') and session.get('institution_type') and session.get('department') and session.get('position')): 
        flash('Персональні дані збережено.', 'success')
    else: 
        flash('Не всі персональні дані збережено.', 'warning')
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_entry():
    indicator_id = request.form.get('indicator_id')
    if not indicator_id: 
        flash('Оберіть показник.', 'error')
        return redirect(url_for('index'))
    
    indicator_details = get_indicator_details(indicator_id)
    if not indicator_details: 
        flash('Недійсний показник.', 'error')
        return redirect(url_for('index'))
    
    indicator_type = indicator_details['type']
    base_coeff = indicator_details['coeff']
    required_inputs = indicator_details['inputs']
    block_num = indicator_details['block']
    score = 0
    input_values = {}
    comment = request.form.get('comment', '').strip()
    
    try:
        if indicator_type == 'fixed': 
            score = base_coeff
        elif indicator_type == 'boolean': 
            boolean_value = request.form.get('boolean_value') == 'yes'
            input_values['boolean_value'] = boolean_value
            score = base_coeff if boolean_value else 0
        
        if 'n' in required_inputs: 
            n_value_str = request.form.get('n_value')
            n_value = float(n_value_str.replace(',', '.'))
            input_values['n_value'] = n_value
            score = n_value * base_coeff if indicator_type == 'n_value' else score
        
        if 's' in required_inputs: 
            s_value_str = request.form.get('s_value')
            s_value = float(s_value_str.replace(',', '.'))
            input_values['s_value'] = s_value
            score = s_value * base_coeff if indicator_type == 's_value' and base_coeff is not None else score
        
        if 'k' in required_inputs: 
            k_value_str = request.form.get('k_value')
            k_value = float(k_value_str.replace(',', '.'))
            input_values['k_value'] = k_value
        
        if indicator_type == 'k_s_value':
            if 'k_value' in input_values and 's_value' in input_values and base_coeff is not None: 
                score = input_values['k_value'] * input_values['s_value'] * base_coeff
            else: 
                raise ValueError("Відсутні k або S для k_s_value.")
    except Exception as e: 
        flash(f"Помилка введення/розрахунку: {e}", 'error')
        return redirect(url_for('index'))
    
    entries = session.get('entries', [])
    new_entry = { 
        'id': indicator_id, 
        'name': indicator_details['name'], 
        'coeff': base_coeff, 
        'score': score, 
        'block': block_num, 
        'type': indicator_type, 
        'comment': comment, 
        **input_values 
    }
    entries.append(new_entry)
    session['entries'] = entries
    session.modified = True
    flash(f"Показник '{indicator_details['name']}' додано. Бал: {score:.2f}", 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:entry_index>', methods=['POST'])
def delete_entry(entry_index):
    entries = session.get('entries', [])
    try:
        if 0 <= entry_index < len(entries): 
            deleted_entry = entries.pop(entry_index)
            session['entries'] = entries
            session.modified = True
            flash(f"Показник '{deleted_entry.get('name', '?')}' видалено.", 'success')
        else: 
            flash('Неправильний індекс.', 'error')
    except Exception as e: 
        print(f"Помилка видалення {entry_index}: {e}")
        flash('Помилка видалення.', 'error')
    return redirect(url_for('index'))

@app.route('/edit/<int:entry_index>', methods=['GET'])
def edit_entry(entry_index):
    entries = session.get('entries', [])
    try:
        if 0 <= entry_index < len(entries):
            entry_to_edit = entries[entry_index]
            if entry_to_edit.get('type') == 'fixed': 
                flash('Фіксовані показники не редагуються.', 'info')
                return redirect(url_for('index'))
            return render_template('edit_entry.html', entry=entry_to_edit, entry_index=entry_index)
        else: 
            flash('Запис для редагування не знайдено.', 'error')
            return redirect(url_for('index'))
    except Exception as e: 
        print(f"Помилка /edit {entry_index}: {e}")
        flash('Помилка відкриття редагування.', 'error')
        return redirect(url_for('index'))

@app.route('/update/<int:entry_index>', methods=['POST'])
def update_entry(entry_index):
    entries = session.get('entries', [])
    if not (0 <= entry_index < len(entries)): 
        flash('Запис для оновлення не знайдено.', 'error')
        return redirect(url_for('index'))
    
    entry_to_update = entries[entry_index]
    original_indicator_id = entry_to_update.get('id')
    
    if entry_to_update.get('type') == 'fixed': 
        flash('Фіксовані показники не оновлюються.', 'error')
        return redirect(url_for('index'))
    
    indicator_details = get_indicator_details(original_indicator_id)
    if not indicator_details: 
        flash(f"Не знайдено деталей для ID '{original_indicator_id}'.", 'error')
        return redirect(url_for('index'))
    
    indicator_type = indicator_details['type']
    base_coeff = indicator_details['coeff']
    new_score = 0
    updated_input_values = {}
    updated_comment = request.form.get('comment', '').strip()
    
    try:
        if 'n_value' in entry_to_update: 
            n_value_str = request.form.get('n_value')
            updated_input_values['n_value'] = float(n_value_str.replace(',', '.'))
        if 's_value' in entry_to_update: 
            s_value_str = request.form.get('s_value')
            updated_input_values['s_value'] = float(s_value_str.replace(',', '.'))
        if 'k_value' in entry_to_update: 
            k_value_str = request.form.get('k_value')
            updated_input_values['k_value'] = float(k_value_str.replace(',', '.'))
        if 'boolean_value' in entry_to_update: 
            updated_input_values['boolean_value'] = request.form.get('boolean_value') == 'yes'
        
        if indicator_type == 'boolean': 
            new_score = base_coeff if updated_input_values.get('boolean_value') else 0
        elif indicator_type == 'n_value': 
            new_score = updated_input_values.get('n_value', 0) * base_coeff
        elif indicator_type == 's_value': 
            new_score = updated_input_values.get('s_value', 0) * base_coeff if base_coeff is not None else 0
        elif indicator_type == 'k_s_value': 
            new_score = updated_input_values.get('k_value', 0) * updated_input_values.get('s_value', 0) * base_coeff if base_coeff is not None else 0
        
        entries[entry_index].update({'score': new_score, 'comment': updated_comment, **updated_input_values})
        session['entries'] = entries
        session.modified = True
        flash(f"Показник '{entry_to_update.get('name', '?')}' оновлено. Бал: {new_score:.2f}", 'success')
    except Exception as e: 
        flash(f"Помилка оновлення: {e}", 'error')
        return render_template('edit_entry.html', entry=entry_to_update, entry_index=entry_index)
    return redirect(url_for('index'))

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files: 
        flash('Файл не вибрано.', 'error')
        return redirect(url_for('index'))
    file = request.files['csv_file']
    if file.filename == '': 
        flash('Файл не вибрано.', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
            csv_reader = csv.reader(stream, delimiter=';')
            parsed_personal_info = {}
            parsed_entries = []
            table_header_found = False
            expected_table_header = ["Блок", "№ Пункту", "Показник", "Введені дані", "Коеф./База", "Отримані бали"]
            expected_table_header_with_comment = ["Блок", "№ Пункту", "Показник", "Введені дані", "Коеф./База", "Отримані бали", "Коментар"]
            line_num = 0
            header_row = -1
            
            for row in csv_reader:
                line_num += 1
                if not row: continue
                if not table_header_found:
                    if len(row) >= 2 and ':' in row[0]:
                        key = row[0].split(':')[0].strip()
                        value = row[1].strip() if len(row) > 1 else ""
                        if key == 'ПІБ': parsed_personal_info['full_name'] = value
                        elif key == 'Заклад': parsed_personal_info['institution_type'] = value
                        elif key == 'Кафедра': parsed_personal_info['department'] = value
                        elif key == 'Посада': parsed_personal_info['position'] = value
                    elif row == expected_table_header or row == expected_table_header_with_comment: 
                        table_header_found = True
                        header_row = line_num
                    continue
                
                if line_num <= header_row: continue
                
                if table_header_found:
                    if row[0].strip() == "" and "Підсумки" in row[2]: break
                    
                    if len(row) == len(expected_table_header) or len(row) == len(expected_table_header_with_comment):
                        try:
                            if len(row) == len(expected_table_header_with_comment):
                                block_str, entry_id, entry_name_csv, input_data_str, coeff_str, score_str, comment_csv = [s.strip() for s in row]
                            else:
                                block_str, entry_id, entry_name_csv, input_data_str, coeff_str, score_str = [s.strip() for s in row]
                                comment_csv = ""
                                
                            if not block_str or not entry_id or not entry_name_csv: continue
                            
                            indicator_details = get_indicator_details(entry_id)
                            if not indicator_details: 
                                print(f"Warning (row {line_num}): ID '{entry_id}' not found.")
                                continue
                            
                            entry_type = indicator_details['type']
                            base_coeff = indicator_details['coeff']
                            block_num = indicator_details['block']
                            entry_name_orig = indicator_details['name']
                            
                            parsed_inputs = parse_input_data_string(input_data_str, entry_type)
                            try: 
                                score = float(score_str.replace(',', '.')) if score_str else 0.0
                            except ValueError: 
                                score = 0.0
                            
                            entry_dict = {
                                'id': entry_id, 
                                'name': entry_name_orig, 
                                'coeff': base_coeff, 
                                'score': score, 
                                'block': block_num, 
                                'type': entry_type, 
                                'comment': comment_csv, 
                                **parsed_inputs
                            }
                            parsed_entries.append(entry_dict)
                        except Exception as e: 
                            print(f"Error parsing data row {line_num}: {e}")
            
            if not parsed_entries and not parsed_personal_info: 
                flash('Файл порожній або не розпізнано.', 'warning')
            elif not table_header_found: 
                flash('Не знайдено заголовок таблиці.', 'error')
            else:
                session.pop('entries', None)
                session.pop('full_name', None)
                session.pop('institution_type', None)
                session.pop('department', None)
                session.pop('position', None)
                
                session['entries'] = parsed_entries
                session.update(parsed_personal_info)
                session.modified = True
                flash(f'Дані завантажено з "{file.filename}". {len(parsed_entries)} показників.', 'success')
        except Exception as e: 
            print(f"Error /upload_csv: {e}")
            flash(f'Помилка обробки файлу: {e}', 'error')
    else: 
        flash('Неприпустимий тип файлу (.csv).', 'error')
    return redirect(url_for('index'))

@app.route('/table')
def show_table():
    entries = session.get('entries', [])
    personal_info = {
        'full_name': session.get('full_name'),
        'institution_type': session.get('institution_type'),
        'department': session.get('department'),
        'position': session.get('position')
    }
    total_block1 = sum(e['score'] for e in entries if e.get('block') == 1)
    total_block2 = sum(e['score'] for e in entries if e.get('block') == 2)
    grand_total = total_block1 + total_block2
    user_name = personal_info.get('full_name')
    user_position = personal_info.get('position', 'Не вказано')

    if user_name and user_position and user_position != 'Не вказано':
        try:
            leaderboard_data = load_leaderboard()
            current_score = grand_total
            existing_entry = leaderboard_data.get(user_name)

            if not existing_entry or current_score > existing_entry.get('score', -1):
                leaderboard_data[user_name] = {'score': current_score, 'position': user_position}
                save_leaderboard(leaderboard_data)
                
                # --- НОВЕ: Зберігаємо детальний звіт у JSON ---
                try:
                    safe_filename = "".join([c for c in user_name if c.isalpha() or c.isdigit() or c in ' .-_']).strip()
                    details_filename = f"details_{safe_filename}.json"
                    
                    with open(details_filename, 'w', encoding='utf-8') as f:
                        json.dump(entries, f, ensure_ascii=False, indent=4)
                    print(f"Деталі збережено для {user_name} у {details_filename}")
                except Exception as e:
                    print(f"Помилка збереження JSON деталей: {e}")
                # -----------------------------------------------

        except Exception as e:
            print(f"Error updating leaderboard for '{user_name}': {e}")
            flash("Could not update rating.", 'warning')
    elif user_name:
        flash("Result not saved to rating (position not specified).", 'info')

    def entry_sort_key(entry):
        block = entry.get('block', 0)
        item_key = entry.get('id', '')
        parts = item_key.split('.')
        key_tuple = [block]
        for part in parts:
            try:
                key_tuple.append(int(part))
            except ValueError:
                key_tuple.append(float('inf'))
                key_tuple.append(part)
        return tuple(key_tuple)
    sorted_entries = sorted(entries, key=entry_sort_key)

    return render_template(
        'results_table.html',
        entries=sorted_entries,
        total_block1=total_block1,
        total_block2=total_block2,
        grand_total=grand_total,
        personal_info=personal_info
    )

@app.route('/clear')
def clear_entries(): 
    session.pop('entries', None)
    session.pop('full_name', None)
    session.pop('institution_type', None)
    session.pop('department', None)
    session.pop('position', None)
    flash('Всі дані видалено.', 'info')
    return redirect(url_for('index'))

@app.route('/download/csv')
def download_csv():
    entries = session.get('entries', [])
    personal_info = { 
        'full_name': session.get('full_name', 'N/A'), 
        'institution_type': session.get('institution_type', 'N/A'), 
        'department': session.get('department', 'N/A'), 
        'position': session.get('position', 'N/A') 
    }
    
    if not entries and personal_info['full_name'] == 'N/A': 
        flash("Немає даних.", 'warning')
        return redirect(url_for('show_table'))
    
    total_block1 = sum(e['score'] for e in entries if e.get('block') == 1)
    total_block2 = sum(e['score'] for e in entries if e.get('block') == 2)
    grand_total = total_block1 + total_block2

    def entry_sort_key(entry):
        block = entry.get('block', 0)
        item_key = entry.get('id', '')
        parts = item_key.split('.')
        key_tuple = [block]
        for part in parts:
            try: key_tuple.append(int(part))
            except ValueError: key_tuple.append(float('inf')); key_tuple.append(part)
        return tuple(key_tuple)
    sorted_entries = sorted(entries, key=entry_sort_key)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['ПІБ:', personal_info['full_name']])
    writer.writerow(['Заклад:', personal_info['institution_type']])
    writer.writerow(['Кафедра:', personal_info['department']])
    writer.writerow(['Посада:', personal_info['position']])
    writer.writerow([])
    
    header = ["Блок", "№ Пункту", "Показник", "Введені дані", "Коеф./База", "Отримані бали", "Коментар"]
    writer.writerow(header)

    def format_input_data(entry):
        parts = []
        if entry.get('type') == 'fixed': return "-"
        if entry.get('n_value') is not None: parts.append(f"n={str(entry.get('n_value', '')).replace('.', ',')}")
        if entry.get('s_value') is not None: parts.append(f"S={str(entry.get('s_value', '')).replace('.', ',')}")
        if entry.get('k_value') is not None: parts.append(f"k={str(entry.get('k_value', '')).replace('.', ',')}")
        if 'boolean_value' in entry: parts.append("Так" if entry.get('boolean_value') else "Ні")
        return " ".join(parts) if parts else "-"

    current_block = 0
    for entry in sorted_entries:
        if entry.get('block') != current_block: current_block = entry.get('block')
        input_data_str = format_input_data(entry)
        coeff_str = str(entry.get('coeff', '')).replace('.', ',')
        score_str = "{:.2f}".format(entry.get('score', 0)).replace('.', ',')
        comment = entry.get('comment', '')
        row = [entry.get('block', ''), entry.get('id', ''), entry.get('name', ''), input_data_str, coeff_str, score_str, comment]
        writer.writerow(row)
        
    writer.writerow([])
    writer.writerow(["", "", "--- Підсумки ---", "", "", "", ""])
    writer.writerow(["", "", "Всього за Блок 1:", "", "", "{:.2f}".format(total_block1).replace('.', ','), ""])
    writer.writerow(["", "", "Всього за Блок 2:", "", "", "{:.2f}".format(total_block2).replace('.', ','), ""])
    writer.writerow(["", "", "Загальна сума балів:", "", "", "{:.2f}".format(grand_total).replace('.', ','), ""])
    
    output.seek(0)
    csv_data = output.getvalue()
    return Response(
        u'\ufeff'.encode('utf-8') + csv_data.encode('utf-8'), 
        mimetype="text/csv; charset=utf-8", 
        headers={"Content-Disposition": "attachment;filename=rating_results.csv"}
    )

@app.route('/download/html')
def download_html():
    entries = session.get('entries', [])
    personal_info = {
        'full_name': session.get('full_name'),
        'institution_type': session.get('institution_type'),
        'department': session.get('department'),
        'position': session.get('position')
    }

    if not entries and not personal_info.get('full_name'):
        flash("Немає даних для завантаження.", 'warning')
        return redirect(url_for('show_table'))

    total_block1 = sum(e['score'] for e in entries if e.get('block') == 1)
    total_block2 = sum(e['score'] for e in entries if e.get('block') == 2)
    grand_total = total_block1 + total_block2

    def entry_sort_key(entry):
        block = entry.get('block', 0)
        item_key = entry.get('id', '')
        parts = item_key.split('.')
        key_tuple = [block]
        for part in parts:
            try: key_tuple.append(int(part))
            except ValueError: key_tuple.append(float('inf')); key_tuple.append(part)
        return tuple(key_tuple)
    sorted_entries = sorted(entries, key=entry_sort_key)

    try:
        html_content = render_template(
            'printable_table.html',
            entries=sorted_entries,
            total_block1=total_block1,
            total_block2=total_block2,
            grand_total=grand_total,
            personal_info=personal_info
        )
        return Response(
            html_content.encode('utf-8'),
            mimetype="text/html",
            headers={"Content-Disposition": "attachment;filename=rating_results.html"}
        )
    except Exception as e:
        print(f"HTML Error: {e}")
        flash(f"Помилка генерації HTML: {e}", "error")
        return redirect(url_for('show_table'))

@app.route('/leaderboard')
def show_leaderboard():
    try:
        leaderboard_data = load_leaderboard()
        
        # Отримуємо всі унікальні посади для фільтра
        all_positions = set()
        for data in leaderboard_data.values():
            pos = data.get('position', 'Не вказано')
            if pos: all_positions.add(pos)
        sorted_positions = sorted(list(all_positions))

        # Перевіряємо фільтр
        filter_pos = request.args.get('position_filter')
        
        leaderboard_list = []
        for name, data in leaderboard_data.items():
            pos = data.get('position', 'Не вказано')
            score = data.get('score', 0.0)
            
            # Якщо є фільтр і посада не співпадає - пропускаємо
            if filter_pos and pos != filter_pos:
                continue
                
            leaderboard_list.append({
                'name': name,
                'score': score,
                'position': pos
            })

        sorted_leaderboard = sorted(leaderboard_list, key=lambda item: item['score'], reverse=True)
        
        return render_template(
            'leaderboard.html', 
            leaderboard=sorted_leaderboard,
            available_positions=sorted_positions,
            current_filter=filter_pos
        )
    except Exception as e:
        print(f"Error /leaderboard: {e}")
        flash(f"Не вдалося завантажити рейтинг: {e}", 'error')
        return render_template('leaderboard.html', leaderboard=[], available_positions=[])

# --- НОВА ФУНКЦІЯ: ВИДАЛЕННЯ ---
@app.route('/delete_leaderboard_entry', methods=['POST'])
def delete_leaderboard_entry():
    name_to_delete = request.form.get('name')
    if not name_to_delete:
        flash('Не вказано ім\'я для видалення.', 'error')
        return redirect(url_for('show_leaderboard'))

    try:
        leaderboard_data = load_leaderboard()
        if name_to_delete in leaderboard_data:
            del leaderboard_data[name_to_delete]
            save_leaderboard(leaderboard_data)
            flash(f"Користувача '{name_to_delete}' успішно видалено з рейтингу.", 'success')
        else:
            flash(f"Користувача '{name_to_delete}' не знайдено.", 'warning')
    except Exception as e:
        print(f"Error deleting entry: {e}")
        flash(f"Помилка при видаленні: {e}", 'error')

    return redirect(url_for('show_leaderboard'))

# --- НОВА ФУНКЦІЯ: WORD ---
@app.route('/download_report_docx/<name>')
def download_report_docx(name):
    safe_filename = "".join([c for c in name if c.isalpha() or c.isdigit() or c in ' .-_']).strip()
    details_filename = f"details_{safe_filename}.json"
    
    if not os.path.exists(details_filename):
        flash(f"Детальний звіт для '{name}' не знайдено (можливо, він був доданий до оновлення системи).", 'error')
        return redirect(url_for('show_leaderboard'))

    try:
        with open(details_filename, 'r', encoding='utf-8') as f:
            entries = json.load(f)
            
        doc = Document()
        heading = doc.add_heading(f'Рейтинговий звіт: {name}', 0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f'Дата формування: {os.path.exists(details_filename) and "Актуальний"}')
        doc.add_paragraph('------------------------------------------------------------------')

        table = doc.add_table(rows=1, cols=6)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Блок'
        hdr_cells[1].text = '№'
        hdr_cells[2].text = 'Показник'
        hdr_cells[3].text = 'Введені дані'
        hdr_cells[4].text = 'Бал'
        hdr_cells[5].text = 'Коментар'

        total_score = 0
        
        def entry_sort_key(entry):
            block = entry.get('block', 0)
            item_key = entry.get('id', '')
            parts = item_key.split('.')
            key_tuple = [block]
            for part in parts:
                try: key_tuple.append(int(part))
                except ValueError: key_tuple.append(float('inf')); key_tuple.append(part)
            return tuple(key_tuple)
            
        sorted_entries = sorted(entries, key=entry_sort_key)

        for entry in sorted_entries:
            row_cells = table.add_row().cells
            row_cells[0].text = str(entry.get('block', ''))
            row_cells[1].text = str(entry.get('id', ''))
            row_cells[2].text = str(entry.get('name', ''))
            
            parts = []
            if entry.get('n_value') is not None: parts.append(f"n={entry['n_value']}")
            if entry.get('s_value') is not None: parts.append(f"S={entry['s_value']}")
            if entry.get('k_value') is not None: parts.append(f"k={entry['k_value']}")
            if entry.get('boolean_value'): parts.append("Так")
            row_cells[3].text = ", ".join(parts) if parts else "-"
            
            score = entry.get('score', 0)
            total_score += score
            row_cells[4].text = "{:.2f}".format(score)
            row_cells[5].text = entry.get('comment', '')

        doc.add_paragraph('') 
        p = doc.add_paragraph()
        runner = p.add_run(f'ЗАГАЛЬНА СУМА БАЛІВ: {total_score:.2f}')
        runner.bold = True
        runner.font.size = Pt(14)

        f = io.BytesIO()
        doc.save(f)
        f.seek(0)
        
        return Response(
            f,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={'Content-Disposition': f'attachment; filename=rating_{safe_filename}.docx'}
        )

    except Exception as e:
        print(f"Word gen error: {e}")
        flash(f"Помилка генерації Word: {e}", 'error')
        return redirect(url_for('show_leaderboard'))

if __name__ == '__main__':
    print("Завантаження початкового лідерборду...")
    initial_data = load_leaderboard()
    if not initial_data and not os.path.exists(LEADERBOARD_FILE): 
        save_leaderboard({})
        print(f"Створено порожній файл лідерборду: {LEADERBOARD_FILE}")
    else: 
        print(f"Лідерборд завантажено. Знайдено записів: {len(initial_data)}")
    app.run(host='0.0.0.0', port=5000, debug=False)