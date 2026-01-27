import os
import csv
import io
import re
import threading
import json  # ВАЖЛИВО!
from datetime import datetime  # ВАЖЛИВО!
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, stream_with_context
from data import get_indicator_choices, get_indicator_details

# Імпорти для Word (ВАЖЛИВО!)
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

app = Flask(__name__)
app.secret_key = 'd5aeb79aff27c1cbc690473e25c5b70dbcc959da288a0f67'

LEADERBOARD_FILE = 'leaderboard.csv'
ALLOWED_EXTENSIONS = {'csv'}
leaderboard_lock = threading.Lock()
ADMIN_PASSWORD = "admin" 

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
                for i, row in enumerate(reader):
                    try:
                        if len(row) >= 2: 
                            name = row[0].strip()
                            position = row[1].strip() if len(row) > 2 else "Не вказано"
                            score_str = row[2] if len(row) > 2 else row[1]
                            score = float(score_str.replace(',', '.'))
                            if name:
                                if name not in leaderboard_data or score > leaderboard_data[name]['score']:
                                    leaderboard_data[name] = {'score': score, 'position': position}
                    except Exception: pass
    except FileNotFoundError: pass
    return leaderboard_data

def save_leaderboard(leaderboard_data):
    try:
        with leaderboard_lock:
            with open(LEADERBOARD_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['ПІБ', 'Посада', 'Загальний бал'])
                for name, data in sorted(leaderboard_data.items()):
                    score_str = "{:.2f}".format(data.get('score', 0)).replace('.', ',')
                    writer.writerow([name, data.get('position', 'Не вказано'), score_str])
    except Exception as e: print(f"Error saving: {e}")

def parse_input_data_string(input_str, expected_type):
    parsed_values = {}
    input_str = input_str.strip()
    if expected_type == 'boolean': 
        parsed_values['boolean_value'] = (input_str.lower() == 'так')
        return parsed_values
    elif expected_type == 'fixed' or input_str == '-': return {}
    
    n_match = re.search(r'n=(\d+([.,]\d+)?)', input_str, re.IGNORECASE)
    s_match = re.search(r'S=(\d+([.,]\d+)?)', input_str, re.IGNORECASE)
    k_match = re.search(r'k=(\d+([.,]\d+)?)', input_str, re.IGNORECASE)
    
    try:
        if n_match: parsed_values['n_value'] = float(n_match.group(1).replace(',', '.'))
        if s_match: parsed_values['s_value'] = float(s_match.group(1).replace(',', '.'))
        if k_match: parsed_values['k_value'] = float(k_match.group(1).replace(',', '.'))
    except ValueError: pass
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
    flash('Персональні дані збережено.', 'success')
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_entry():
    indicator_id = request.form.get('indicator_id')
    if not indicator_id: return redirect(url_for('index'))
    
    indicator_details = get_indicator_details(indicator_id)
    if not indicator_details: return redirect(url_for('index'))
    
    indicator_type = indicator_details['type']
    base_coeff = indicator_details['coeff']
    score = 0
    input_values = {}
    comment = request.form.get('comment', '').strip()
    
    try:
        if indicator_type == 'fixed': score = base_coeff
        elif indicator_type == 'boolean': 
            boolean_value = request.form.get('boolean_value') == 'yes'
            input_values['boolean_value'] = boolean_value
            score = base_coeff if boolean_value else 0
        
        if 'n' in indicator_details['inputs']: 
            n = float(request.form.get('n_value').replace(',', '.'))
            input_values['n_value'] = n
            if indicator_type == 'n_value': score = n * base_coeff
        
        if 's' in indicator_details['inputs']: 
            s = float(request.form.get('s_value').replace(',', '.'))
            input_values['s_value'] = s
            if indicator_type == 's_value': score = s * base_coeff
        
        if 'k' in indicator_details['inputs']: 
            k = float(request.form.get('k_value').replace(',', '.'))
            input_values['k_value'] = k
        
        if indicator_type == 'k_s_value':
            score = input_values['k_value'] * input_values['s_value'] * base_coeff
            
    except Exception as e: 
        flash(f"Помилка розрахунку: {e}", 'error')
        return redirect(url_for('index'))
    
    entries = session.get('entries', [])
    new_entry = { 
        'id': indicator_id, 
        'name': indicator_details['name'], 
        'coeff': base_coeff, 
        'score': score, 
        'block': indicator_details['block'], 
        'type': indicator_type, 
        'comment': comment, 
        **input_values 
    }
    entries.append(new_entry)
    session['entries'] = entries
    session.modified = True
    flash(f"Додано: {score:.2f} балів", 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:entry_index>', methods=['POST'])
def delete_entry(entry_index):
    entries = session.get('entries', [])
    if 0 <= entry_index < len(entries): 
        entries.pop(entry_index)
        session['entries'] = entries
        session.modified = True
    return redirect(url_for('index'))

@app.route('/edit/<int:entry_index>', methods=['GET'])
def edit_entry(entry_index):
    entries = session.get('entries', [])
    if 0 <= entry_index < len(entries):
        return render_template('edit_entry.html', entry=entries[entry_index], entry_index=entry_index)
    return redirect(url_for('index'))

@app.route('/update/<int:entry_index>', methods=['POST'])
def update_entry(entry_index):
    entries = session.get('entries', [])
    if not (0 <= entry_index < len(entries)): return redirect(url_for('index'))
    
    entry_to_update = entries[entry_index]
    indicator_details = get_indicator_details(entry_to_update['id'])
    
    base_coeff = indicator_details['coeff']
    score = 0
    input_values = {}
    comment = request.form.get('comment', '').strip()
    
    try:
        # Спрощена логіка оновлення (копія з add_entry)
        if indicator_details['type'] == 'fixed': score = base_coeff
        elif indicator_details['type'] == 'boolean': 
            boolean_value = request.form.get('boolean_value') == 'yes'
            input_values['boolean_value'] = boolean_value
            score = base_coeff if boolean_value else 0
        
        if 'n' in indicator_details['inputs']: 
            n = float(request.form.get('n_value').replace(',', '.'))
            input_values['n_value'] = n
            if indicator_details['type'] == 'n_value': score = n * base_coeff
        
        if 's' in indicator_details['inputs']: 
            s = float(request.form.get('s_value').replace(',', '.'))
            input_values['s_value'] = s
            if indicator_details['type'] == 's_value': score = s * base_coeff
        
        if 'k' in indicator_details['inputs']: 
            k = float(request.form.get('k_value').replace(',', '.'))
            input_values['k_value'] = k
        
        if indicator_details['type'] == 'k_s_value':
            score = input_values['k_value'] * input_values['s_value'] * base_coeff
            
    except Exception as e:
        flash(f"Помилка оновлення: {e}", 'error')
        return redirect(url_for('index'))

    entries[entry_index].update({
        'score': score, 
        'comment': comment, 
        **input_values
    })
    session['entries'] = entries
    session.modified = True
    return redirect(url_for('index'))

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files: return redirect(url_for('index'))
    file = request.files['csv_file']
    if file.filename == '' or not allowed_file(file.filename): return redirect(url_for('index'))
    
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        csv_reader = csv.reader(stream, delimiter=';')
        
        parsed_entries = []
        personal_info = {}
        header_found = False
        
        # Спрощений парсер для відновлення
        for row in csv_reader:
            if not row: continue
            if "ПІБ:" in row[0]: personal_info['full_name'] = row[1]
            if "Посада:" in row[0]: personal_info['position'] = row[1]
            if "Блок" in row[0] and "Показник" in row[2]: header_found = True; continue
            
            if header_found and len(row) >= 6:
                if "Підсумки" in row[2]: break
                try:
                    entry_id = row[1].strip()
                    if not entry_id: continue
                    details = get_indicator_details(entry_id)
                    if not details: continue
                    
                    score = float(row[5].replace(',', '.'))
                    comment = row[6] if len(row) > 6 else ""
                    
                    parsed_inputs = parse_input_data_string(row[3], details['type'])
                    
                    parsed_entries.append({
                        'id': entry_id, 'name': details['name'], 'coeff': details['coeff'],
                        'score': score, 'block': details['block'], 'type': details['type'],
                        'comment': comment, **parsed_inputs
                    })
                except: pass
        
        session['entries'] = parsed_entries
        session.update(personal_info)
        session.modified = True
        flash(f"Завантажено {len(parsed_entries)} записів.", 'success')
    except Exception as e:
        flash(f"Помилка CSV: {e}", 'error')
        
    return redirect(url_for('index'))

@app.route('/table')
def show_table():
    entries = session.get('entries', [])
    full_name = session.get('full_name')
    position = session.get('position')
    
    total = sum(e['score'] for e in entries)
    
    if full_name and position:
        leaderboard = load_leaderboard()
        if full_name not in leaderboard or total > leaderboard[full_name]['score']:
            leaderboard[full_name] = {'score': total, 'position': position}
            save_leaderboard(leaderboard)
            
            # --- ЗБЕРЕЖЕННЯ JSON ДЛЯ WORD (ОСЬ ЦЬОГО НЕ ВИСТАЧАЛО) ---
            try:
                safe_name = "".join([c for c in full_name if c.isalnum() or c in ' .-_']).strip()
                with open(f"details_{safe_name}.json", 'w', encoding='utf-8') as f:
                    json.dump(entries, f, ensure_ascii=False, indent=4)
            except Exception as e: print(f"JSON save error: {e}")
            # ---------------------------------------------------------

    # Повертаємо змінні для шаблону results_table.html
    # Переконайтеся, що змінні тут співпадають з тими, що очікує шаблон
    total_block1 = sum(e['score'] for e in entries if e.get('block') == 1)
    total_block2 = sum(e['score'] for e in entries if e.get('block') == 2)
    
    return render_template('results_table.html', 
                           entries=entries, 
                           grand_total=total, 
                           total_block1=total_block1,
                           total_block2=total_block2,
                           personal_info={'full_name': full_name, 'position': position})

@app.route('/clear')
def clear_entries(): 
    session.clear()
    return redirect(url_for('index'))

@app.route('/leaderboard')
def show_leaderboard():
    leaderboard = load_leaderboard()
    
    # Фільтрація
    all_pos = sorted(list(set(d.get('position', '') for d in leaderboard.values()) - {''}))
    filter_pos = request.args.get('position_filter')
    
    lb_list = []
    for name, data in leaderboard.items():
        if filter_pos and data.get('position') != filter_pos: continue
        lb_list.append({'name': name, 'score': data.get('score', 0), 'position': data.get('position')})
    
    lb_list.sort(key=lambda x: x['score'], reverse=True)
    return render_template('leaderboard.html', leaderboard=lb_list, available_positions=all_pos, current_filter=filter_pos)

@app.route('/delete_leaderboard_entry', methods=['POST'])
def delete_leaderboard_entry():
    name = request.form.get('name')
    password = request.form.get('admin_password')
    
    if password != ADMIN_PASSWORD:
        flash('Невірний пароль!', 'error')
        return redirect(url_for('show_leaderboard'))
        
    lb = load_leaderboard()
    if name in lb:
        del lb[name]
        save_leaderboard(lb)
        flash(f'Користувача {name} видалено.', 'success')
    return redirect(url_for('show_leaderboard'))

@app.route('/download_report_docx/<name>')
def download_report_docx(name):
    safe_name = "".join([c for c in name if c.isalnum() or c in ' .-_']).strip()
    filename = f"details_{safe_name}.json"
    
    if not os.path.exists(filename):
        flash("Детальний звіт не знайдено.", 'error')
        return redirect(url_for('show_leaderboard'))
        
    with open(filename, 'r', encoding='utf-8') as f:
        entries = json.load(f)
        
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    p = doc.add_paragraph('УНІВЕРСИТЕТ ЕКОНОМІКИ І ПІДПРИЄМНИЦТВА')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph('ДОДАТОК Б')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    p = doc.add_paragraph('Індивідуальні дані,')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold = True
    p = doc.add_paragraph('що відображають результати діяльності науково-педагогічного працівника')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f'\nПІБ викладача: {name}')
    doc.add_paragraph(f'Дата: {datetime.now().strftime("%d.%m.%Y")}\n')
    
    table = doc.add_table(rows=1, cols=6)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = 'Блок'; hdr[1].text = '№'; hdr[2].text = 'Показник'
    hdr[3].text = 'Дані'; hdr[4].text = 'Бал'; hdr[5].text = 'Коментар'
    
    total = 0
    def sort_key(e):
        try: return (e['block'], float(e['id'].split('.')[-1]))
        except: return (0, 0)
        
    for e in sorted(entries, key=sort_key):
        cells = table.add_row().cells
        cells[0].text = str(e['block'])
        cells[1].text = str(e['id'])
        cells[2].text = str(e['name'])
        
        parts = []
        if 'n_value' in e: parts.append(f"n={e['n_value']}")
        if 's_value' in e: parts.append(f"S={e['s_value']}")
        if 'k_value' in e: parts.append(f"k={e['k_value']}")
        if e.get('boolean_value'): parts.append("Так")
        cells[3].text = ", ".join(parts)
        
        cells[4].text = "{:.2f}".format(e['score'])
        cells[5].text = e.get('comment', '')
        total += e['score']
        
    doc.add_paragraph(f'\nЗагальний рейтинг: {total:.2f}').runs[0].bold = True
    
    doc.add_paragraph('\n' + '-'*60 + '\n')
    p = doc.add_paragraph('Індивідуальні дані, що відображають результати моєї науково-педагогічної діяльності внесені мною особисто та є достовірними.')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    doc.add_paragraph('\n\n')
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.allow_autofit = True
    sig_table.rows[0].cells[0].text = f"Викладач _______________ {name}"
    sig_table.rows[0].cells[1].text = "Завідувач кафедри _______________"
    
    f_out = io.BytesIO()
    doc.save(f_out)
    f_out.seek(0)
    
    return Response(f_out, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    headers={'Content-Disposition': f'attachment; filename=Report_{safe_name}.docx'})
    
# --- ОНОВЛЕНИЙ ROUTE CSV ЗАВАНТАЖЕННЯ ---
@app.route('/download/csv')
def download_csv():
    # Цей маршрут залишається таким же, як був у вас в app.py
    # Скопіюйте його зі старого файлу або залиште як є, якщо він працював.
    # Я додав його сюди для повноти.
    entries = session.get('entries', [])
    personal_info = { 
        'full_name': session.get('full_name', 'N/A'), 
        'institution_type': session.get('institution_type', 'N/A'), 
        'department': session.get('department', 'N/A'), 
        'position': session.get('position', 'N/A') 
    }
    total_block1 = sum(e['score'] for e in entries if e.get('block') == 1)
    total_block2 = sum(e['score'] for e in entries if e.get('block') == 2)
    grand_total = total_block1 + total_block2

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

    for entry in entries:
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
    return Response(
        u'\ufeff'.encode('utf-8') + output.getvalue().encode('utf-8'), 
        mimetype="text/csv; charset=utf-8", 
        headers={"Content-Disposition": "attachment;filename=rating_results.csv"}
    )

if __name__ == '__main__':
    if not os.path.exists(LEADERBOARD_FILE): save_leaderboard({})
    app.run(host='0.0.0.0', port=5000)