# Детальна інструкція з розгортання рейтингового калькулятора на Ubuntu
### (Apache + mod_wsgi + PostgreSQL)

Цей посібник містить вичерпні покрокові інструкції для розгортання вашого Flask-додатку на сервері Ubuntu. 
Припускається, що веб-сервер **Apache** та база даних **PostgreSQL** вже встановлені на вашому сервері.

---

## Зміст
1. [Встановлення системних бібліотек](#1-встановлення-системних-бібліотек)
2. [Налаштування бази даних PostgreSQL (яка вже є на сервері)](#2-налаштування-бази-даних-postgresql)
3. [Копіювання файлів проекту на сервер](#3-копіювання-файлів-проекту)
4. [Створення віртуального середовища Python та встановлення пакетів](#4-створення-віртуального-середовища)
5. [Створення та налаштування файлу конфігурації `.env`](#5-створення-та-налаштування-файлу-env)
6. [Налаштування прав доступу веб-сервера (вкрай важливо)](#6-налаштування-прав-доступу)
7. [Налаштування Apache та модуля mod_wsgi](#7-налаштування-apache)
8. [Активація конфігурації та запуск сайту](#8-активація-конфігурації-та-запуск)
9. [Пошук помилок та вирішення проблем (Troubleshooting)](#9-пошук-помилок-та-вирішення-проблем)
10. [Налаштування безпечного з'єднання HTTPS (SSL)](#10-налаштування-безпечного-зєднання-https-ssl)

---

## 1. Встановлення системних бібліотек

Оскільки ви будете запускати Flask через Apache за допомогою WSGI, а також працюватимете з PostgreSQL, вам знадобляться спеціальні системні пакети.

Виконайте команду у терміналі сервера:
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev libpq-dev libapache2-mod-wsgi-py3
```
*   `libapache2-mod-wsgi-py3` — це модуль Apache, який дозволяє йому запускати Python 3 додатки.
*   `libpq-dev` — системна бібліотека для PostgreSQL, необхідна для збірки та роботи Python-драйвера `psycopg2-binary`.

---

## 2. Налаштування бази даних PostgreSQL

Оскільки PostgreSQL вже встановлено на сервері, вам потрібно лише створити нову базу даних та користувача з правами доступу до неї.

### Крок 2.1. Вхід у консоль PostgreSQL
Зайдіть у термінал під системним користувачем `postgres`:
```bash
sudo -i -u postgres psql
```
*Після цього запрошення вводу в терміналі зміниться на `postgres=#`.*

### Крок 2.2. Створення бази даних та користувача
У консолі бази даних виконайте наступні SQL-запити (замініть `Vlasний_Super_Parol_99` на ваш надійний пароль):

```sql
-- 1. Створюємо базу даних для рейтингу
CREATE DATABASE teaching_staff_rating;

-- 2. Створюємо користувача, який обслуговуватиме наш додаток
CREATE USER staff_rating_user WITH PASSWORD 'Vlasний_Super_Parol_99';

-- 3. Налаштовуємо часовий пояс та кодування для цього користувача
ALTER ROLE staff_rating_user SET client_encoding TO 'utf8';
ALTER ROLE staff_rating_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE staff_rating_user SET timezone TO 'UTC';

-- 4. Надаємо користувачу всі права на нову базу даних
GRANT ALL PRIVILEGES ON DATABASE teaching_staff_rating TO staff_rating_user;
```

### Крок 2.3. Спеціальне налаштування для нових версій PostgreSQL (15 і вище)
У PostgreSQL 15+ за замовчуванням обмежено права на схему `public`. Щоб Flask міг автоматично створювати таблиці, виконайте:
```sql
-- Підключаємося до нашої бази даних
\c teaching_staff_rating

-- Надаємо права на схему public користувачу
GRANT ALL ON SCHEMA public TO staff_rating_user;
```

Вийдіть із консолі PostgreSQL:
```sql
\q
```
І поверніться до звичайного користувача Ubuntu:
```bash
exit
```

---

## 3. Копіювання файлів проекту

Зазвичай веб-сайти розміщують у каталозі `/var/www/`.

### Крок 3.1. Створення папки
Створіть папку для сайту та зробіть свого користувача її власником, щоб ви могли копіювати файли без `sudo`:
```bash
sudo mkdir -p /var/www/staff_rating
sudo chown -R $USER:$USER /var/www/staff_rating
```

### Крок 3.2. Перенесення коду
Скопіюйте ваші файли на сервер (за допомогою Git, FileZilla, SCP або rsync). Структура папки `/var/www/staff_rating` повинна мати такий вигляд:
```
/var/www/staff_rating/
├── app.py
├── data.py
├── db.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   └── ...
└── wsgi.py
```

---

## 4. Створення віртуального середовища

Для безпечної роботи та уникнення конфліктів бібліотек обов’язково використовуйте віртуальне середовище Python (`venv`).

Перейдіть у каталог проекту:
```bash
cd /var/www/staff_rating
```

Створіть віртуальне середовище з назвою `venv`:
```bash
python3 -m venv venv
```

Активуйте його:
```bash
source venv/bin/activate
```
*(у вашому рядку терміналу зліва з'явиться префікс `(venv)`)*

Оновіть `pip` та встановіть бібліотеки, зазначені у файлі `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Створення та налаштування файлу `.env`

Файл `.env` зберігає секретні ключі та паролі окремо від коду. Скопіюйте його з прикладу:

```bash
cp .env.example .env
```

Відкрийте файл на редагування за допомогою текстового редактора `nano`:
```bash
nano .env
```

Внесіть реальні налаштування. Файл повинен виглядати приблизно так:
```ini
# Секретний ключ для підпису сесій (зробіть його складним та випадковим)
SECRET_KEY=y0ur_rand0m_secret_key_string_here

# Пароль для доступу до адміністративних функцій лідерборду
ADMIN_PASSWORD=Vlasний_Super_Parol_Admina

# Рядок підключення до створеної вами бази даних PostgreSQL
DATABASE_URL=postgresql://staff_rating_user:Vlasний_Super_Parol_99@localhost:5432/teaching_staff_rating
```
*Для збереження файлу в `nano` натисніть `Ctrl+O`, потім `Enter`. Для виходу натисніть `Ctrl+X`.*

---

## 6. Налаштування прав доступу

Користувач, під яким працює веб-сервер Apache в Ubuntu, називається `www-data`. Йому потрібні права для читання вашого коду, а також повні права на запис до папки сесій `flask_session`.

### Крок 6.1. Створення папки сесій (якщо вона ще не створена)
```bash
mkdir -p /var/www/staff_rating/flask_session
```

### Крок 6.2. Зміна власника папки сесій на `www-data`
```bash
sudo chown -R www-data:www-data /var/www/staff_rating/flask_session
sudo chmod -R 775 /var/www/staff_rating/flask_session
```

### Крок 6.3. Захист файлу `.env`
Файл `.env` містить паролі до БД, тому інші користувачі сервера не повинні мати до нього доступу. Але веб-сервер Apache (`www-data`) має його читати.
Надамо права доступу групі `www-data`:
```bash
sudo chgrp www-data /var/www/staff_rating/.env
sudo chmod 640 /var/www/staff_rating/.env
```

---

## 7. Налаштування Apache

Вам потрібно створити файл конфігурації Віртуального хоста (VirtualHost) для Apache.

### Крок 7.1. Створення конфігураційного файлу сайту
Створіть файл `staff-rating.conf` у папці налаштувань Apache:
```bash
sudo nano /etc/apache2/sites-available/staff-rating.conf
```

Вставте наступний текст. 
*(Замініть `your_server_ip_or_domain` на IP вашого сервера, наприклад `192.168.1.50`, або на домен, якщо він є)*:

```apache
<VirtualHost *:80>
    ServerName your_server_ip_or_domain
    ServerAdmin webmaster@localhost

    # --- Налаштування WSGI Daemon Process ---
    # python-path: кореневий каталог вашого проекту
    # python-home: шлях до створеного віртуального середовища (venv)
    WSGIDaemonProcess staff_rating python-path=/var/www/staff_rating python-home=/var/www/staff_rating/venv user=www-data group=www-data threads=5
    WSGIProcessGroup staff_rating
    WSGIScriptAlias / /var/www/staff_rating/wsgi.py

    # Дозволи для каталогу з додатком
    <Directory /var/www/staff_rating>
        WSGIProcessGroup staff_rating
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>

    # Логування помилок та запитів
    ErrorLog ${APACHE_LOG_DIR}/staff_rating_error.log
    CustomLog ${APACHE_LOG_DIR}/staff_rating_access.log combined
</VirtualHost>
```

---

## 8. Активація конфігурації та запуск

Тепер увімкнемо наш новий сайт, вимкнемо дефолтну сторінку Apache та перезапустимо сервер.

### Крок 8.1. Увімкнення модулів та конфігурації
```bash
# Переконайтеся, що модуль mod_wsgi активовано
sudo a2enmod wsgi

# Активуємо наш новий сайт
sudo a2ensite staff-rating.conf

# Вимикаємо стандартну заглушку Apache (якщо це єдиний сайт на сервері)
sudo a2dissite 000-default.conf
```

### Крок 8.2. Перевірка синтаксису конфігурації Apache
Перед перезапуском перевіримо, чи немає помилок у файлах конфігурації:
```bash
sudo apache2ctl configtest
```
*Має вивести: `Syntax OK`.*

### Крок 8.3. Перезапуск веб-сервера
```bash
sudo systemctl restart apache2
```

---

## 9. Пошук помилок та вирішення проблем (Troubleshooting)

Якщо під час відкриття сайту у браузері ви бачите помилку **500 Internal Server Error** або **Forbidden**:

### А. Логи помилок (це найголовніший інструмент)
Майже кожна помилка Flask/Python записується в лог Apache. Перегляньте останні 50 рядків логу в реальному часі:
```bash
sudo tail -n 50 -f /var/log/apache2/staff_rating_error.log
```

### Б. Помилка: `ModuleNotFoundError: No module named 'psycopg2'` або подібні
*   **Причина**: Apache не використовує віртуальне середовище або ви забули його активувати при встановленні пакетів.
*   **Вирішення**: Переконайтеся, що в файлі `/etc/apache2/sites-available/staff-rating.conf` параметри `python-path` та `python-home` прописані абсолютно вірно і вказують саме на папку проекту та папку `venv`.

### В. Помилка: `Permission denied` для `flask_session`
*   **Причина**: Apache не може записувати файли сесій у папку `flask_session`.
*   **Вирішення**: Запустіть знову:
    ```bash
    sudo chown -R www-data:www-data /var/www/staff_rating/flask_session
    sudo chmod -R 775 /var/www/staff_rating/flask_session
    ```

### Г. Помилка: `Connection refused` при спробі підключитись до БД
*   **Причина**: База даних PostgreSQL не запущена, або не приймає підключення на локальному порту.
*   **Вирішення**: 
    1. Перевірте статус бази: `sudo systemctl status postgresql`.
    2. Перевірте правильність реквізитів підключення (`staff_rating_user` та пароль) у файлі `.env`.

---

## 10. Налаштування безпечного з'єднання HTTPS (SSL)

Для захисту персональних даних користувачів та пароля адміністратора вкрай рекомендується налаштувати шифрування з'єднання через SSL (HTTPS). Ми використаємо безкоштовні сертифікати від **Let's Encrypt** та інструмент **Certbot**.

> [!IMPORTANT]
> Для отримання безкоштовного SSL-сертифікату ваш сервер обов'язково повинен мати зареєстроване доменне ім'я (наприклад, `rating.university.edu.ua`), яке вказує на публічну IP-адресу вашого сервера. Let's Encrypt **не видає** сертифікати на «голі» IP-адреси.

### Крок 10.1. Встановлення Certbot
Встановіть Certbot та його модуль інтеграції з веб-сервером Apache:
```bash
sudo apt update
sudo apt install -y certbot python3-certbot-apache
```

### Крок 10.2. Отримання та автоматичне налаштування сертифікату
Запустіть Certbot, вказавши ваше доменне ім'я (замініть `your_domain.edu.ua` на ваше реальне доменне ім'я):
```bash
sudo certbot --apache -d your_domain.edu.ua
```

Під час виконання команди Certbot попросить вас пройти кілька кроків:
1. **Електронна пошта**: введіть пошту адміністратора (для сервісних сповіщень та нагадувань про оновлення сертифіката).
2. **Умови використання**: натисніть `A` (Agree), щоб погодитися.
3. **Розсилка новин**: натисніть `Y` (так) або `N` (ні).
4. **Перенаправлення (Redirect)**: Certbot запитає, чи потрібно автоматично перенаправляти весь HTTP трафік на HTTPS. Оберіть варіант **`2: Redirect`** (це автоматично оновить конфігурацію Apache і налаштує перенаправлення з HTTP на безпечний HTTPS).

### Крок 10.3. Перевірка автооновлення сертифікатів
Сертифікати Let's Encrypt є дійсними протягом 90 днів. Проте встановлений пакет Certbot автоматично додає системне завдання (systemd timer) для перевірки та оновлення сертифікатів двічі на добу.

Ви можете протестувати працездатність автооновлення у тестовому режимі:
```bash
sudo certbot renew --dry-run
```
*Якщо команда виконана без помилок, автооновлення налаштовано успішно.*
