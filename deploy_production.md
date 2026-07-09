# Інструкція з промислового розгортання додатку (Nginx + Gunicorn + Systemd + PostgreSQL)

Ця інструкція описує стандартний, надійний та продуктивний спосіб запуску Flask-додатків на Linux-серверах за допомогою зв'язки **Nginx** (реверс-проксі) + **Gunicorn** (WSGI-сервер) + **Systemd** (автозапуск та контроль процесу) + **PostgreSQL** (база даних).

---

## Крок 1. Встановлення системних пакетів

Залежно від операційної системи вашого сервера, виконайте відповідні команди в терміналі.

### Варіант А. Якщо у вас Ubuntu / Debian
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev postgresql postgresql-contrib nginx git curl
```

### Варіант Б. Якщо у вас CentOS / AlmaLinux / Rocky Linux
```bash
# Підключення репозиторію EPEL для встановлення Nginx
sudo dnf install -y epel-release
sudo dnf update -y
sudo dnf install -y python3 python3-devel postgresql-server postgresql-contrib nginx git curl
# Ініціалізація бази даних PostgreSQL (тільки для CentOS/RHEL)
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

---

## Крок 2. Налаштування бази даних PostgreSQL

1. Увійдіть у консоль керування PostgreSQL:
   ```bash
   sudo -i -u postgres psql
   ```
2. Виконайте наступні команди для створення бази даних та користувача (замініть `StrongPassword123` на ваш пароль):
   ```sql
   -- Створення бази даних
   CREATE DATABASE teaching_staff_rating;

   -- Створення користувача додатку
   CREATE USER staff_rating_user WITH PASSWORD 'StrongPassword123';

   -- Налаштування параметрів сесії
   ALTER ROLE staff_rating_user SET client_encoding TO 'utf8';
   ALTER ROLE staff_rating_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE staff_rating_user SET timezone TO 'UTC';

   -- Надання прав доступу користувачу до бази даних
   GRANT ALL PRIVILEGES ON DATABASE teaching_staff_rating TO staff_rating_user;
   ```
3. *(Для PostgreSQL 15 і вище)* Надайте додаткові права на схему public:
   ```sql
   \c teaching_staff_rating
   GRANT ALL ON SCHEMA public TO staff_rating_user;
   ```
4. Вийдіть із консолі PostgreSQL:
   ```sql
   \q
   ```

---

## Крок 3. Копіювання коду та налаштування оточення

1. Клонуйте проект у каталог `/var/www/`:
   ```bash
   sudo mkdir -p /var/www/staff_rating
   sudo chown -R $USER:$USER /var/www/staff_rating
   git clone https://github.com/IdzaYar120/-teaching_staff_rating.git /var/www/staff_rating
   cd /var/www/staff_rating
   ```
2. Створіть віртуальне середовище Python:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install gunicorn
   ```
3. Створіть та налаштуйте конфігураційний файл `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Встановіть такі значення (замініть паролі на власні):
   ```ini
   SECRET_KEY=генеруйте_випадковий_довгий_рядок
   ADMIN_PASSWORD=ваш_пароль_адміністратора_для_рейтингу
   DATABASE_URL=postgresql://staff_rating_user:StrongPassword123@localhost:5432/teaching_staff_rating
   ```
4. Налаштуйте права доступу для папки сесій:
   В Ubuntu користувачем веб-сервера є `www-data`, у CentOS — `nginx`.
   ```bash
   # Для Ubuntu:
   sudo chown -R www-data:www-data /var/www/staff_rating/flask_session
   # Для CentOS:
   sudo chown -R nginx:nginx /var/www/staff_rating/flask_session
   
   sudo chmod -R 775 /var/www/staff_rating/flask_session
   ```

---

## Крок 4. Створення служби Systemd (Автозапуск)

Для того щоб додаток працював у фоновому режимі та запускався автоматично при старті сервера, створимо сервіс.

1. Створіть файл служби:
   ```bash
   sudo nano /etc/systemd/system/staff_rating.service
   ```
2. Вставте наступну конфігурацію:
   ```ini
   [Unit]
   Description=Gunicorn instance to serve Teaching Staff Rating Calculator
   After=network.target postgresql.service

   [Service]
   User=www-data
   # Примітка: для CentOS змініть User на: User=nginx
   Group=www-data
   # Примітка: для CentOS змініть Group на: Group=nginx
   WorkingDirectory=/var/www/staff_rating
   Environment="PATH=/var/www/staff_rating/venv/bin"
   ExecStart=/var/www/staff_rating/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```
3. Запустіть сервіс та додайте його в автозапуск:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start staff_rating
   sudo systemctl enable staff_rating
   ```
4. Перевірте статус сервісу (має бути зеленим `active (running)`):
   ```bash
   sudo systemctl status staff_rating
   ```

---

## Крок 5. Налаштування Nginx як реверс-проксі

Тепер налаштуємо Nginx, щоб він приймав запити на стандартному порту HTTP (80) та перенаправляв їх локально на запущений Gunicorn (порт 5000).

### Варіант А. Конфігурація для Ubuntu
1. Створіть файл конфігурації сайту:
   ```bash
   sudo nano /etc/nginx/sites-available/staff_rating
   ```
2. Вставте наступний код (замініть `IP_або_домен_сервера` на реальну IP-адресу або домен вашого сервера):
   ```nginx
   server {
       listen 80;
       server_name IP_або_домен_сервера;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. Активуйте конфігурацію:
   ```bash
   sudo ln -s /etc/nginx/sites-available/staff_rating /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   ```

### Варіант Б. Конфігурація для CentOS / AlmaLinux
1. Створіть файл конфігурації сайту:
   ```bash
   sudo nano /etc/nginx/conf.d/staff_rating.conf
   ```
2. Вставте аналогічний код конфігурації Nginx:
   ```nginx
   server {
       listen 80;
       server_name IP_або_домен_сервера;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. Перезапустіть Nginx та дозвольте йому підключення до мережі в SELinux (критично важливо для CentOS):
   ```bash
   sudo setsebool -P httpd_can_network_connect 1
   ```

---

## Крок 6. Запуск та перевірка

1. Перевірте синтаксис Nginx конфігурації:
   ```bash
   sudo nginx -t
   ```
   *Має вивести: `nginx: configuration file /etc/nginx/nginx.conf syntax is ok`.*
2. Перезапустіть Nginx:
   ```bash
   sudo systemctl restart nginx
   sudo systemctl enable nginx
   ```
3. Тепер ви можете відкрити додаток через браузер за вказаною IP-адресою чи доменом сервера.

---

## Крок 7. Налаштування HTTPS (SSL) за допомогою Certbot (Рекомендовано)

Якщо у сервера є доменне ім'я, обов'язково захистіть передачу паролів за допомогою безкоштовного сертифіката SSL.

```bash
# Для Ubuntu:
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ваші_доменні_імена

# Для CentOS/AlmaLinux (вимагає ввімкненого EPEL):
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ваші_доменні_імена
```
Certbot автоматично оновить конфігурацію Nginx, підключить сертифікат Let's Encrypt та налаштує автоматичне перенаправлення з HTTP на HTTPS.
