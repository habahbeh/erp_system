# 🚀 دليل الإطلاق (Deployment Guide)
# ERP System Production Deployment

**تاريخ:** 2025-01-18
**النسخة:** 1.0.0

---

## 📋 المتطلبات الأساسية

### متطلبات الخادم
```
- نظام التشغيل: Ubuntu 20.04 LTS أو أحدث
- Python: 3.10 أو أحدث
- MySQL: 8.0 أو أحدث
- RAM: 4GB كحد أدنى (8GB موصى به)
- المساحة: 20GB كحد أدنى
- النطاق: domain name مع SSL certificate
```

### البرامج المطلوبة
```bash
- Python 3.10+
- MySQL Server
- Nginx أو Apache
- Supervisor (لإدارة العمليات)
- Git
```

---

## 🛠️ خطوات الإعداد

### 1. تحديث النظام
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. تثبيت Python والمتطلبات
```bash
sudo apt install python3.10 python3.10-venv python3-pip -y
sudo apt install python3.10-dev -y
sudo apt install build-essential -y
```

### 3. تثبيت MySQL
```bash
sudo apt install mysql-server -y
sudo mysql_secure_installation
```

### 4. إنشاء قاعدة البيانات
```bash
sudo mysql -u root -p

# في MySQL console
CREATE DATABASE erp_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'erp_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON erp_production.* TO 'erp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. إنشاء مستخدم النظام
```bash
sudo useradd -m -s /bin/bash erp
sudo passwd erp
```

### 6. رفع الكود
```bash
# التبديل للمستخدم erp
sudo su - erp

# استنساخ المشروع
cd /home/erp
git clone <repository-url> erp_system
cd erp_system
```

### 7. إنشاء البيئة الافتراضية
```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 8. تثبيت المتطلبات
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 9. إعداد ملف البيئة
```bash
cp .env.example .env
nano .env
```

**محتوى ملف .env:**
```env
# Django Settings
SECRET_KEY=your-very-long-secret-key-here-min-50-chars
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=erp_production
DB_USER=erp_user
DB_PASSWORD=strong_password_here
DB_HOST=localhost
DB_PORT=3306

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 10. تطبيق الـ Migrations
```bash
python manage.py migrate
```

### 11. جمع الملفات الثابتة
```bash
python manage.py collectstatic --noinput
```

### 12. إنشاء مستخدم إداري
```bash
python manage.py createsuperuser
```

### 13. تحسين قاعدة البيانات
```bash
python manage.py optimize_database
```

### 14. فحص النظام
```bash
python manage.py check_system
```

---

## 🌐 إعداد Nginx

### 1. تثبيت Nginx
```bash
sudo apt install nginx -y
```

### 2. إنشاء ملف إعداد Nginx
```bash
sudo nano /etc/nginx/sites-available/erp
```

**محتوى الملف:**
```nginx
upstream erp_server {
    server unix:/home/erp/erp_system/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 50M;

    access_log /var/log/nginx/erp-access.log;
    error_log /var/log/nginx/erp-error.log;

    location /static/ {
        alias /home/erp/erp_system/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/erp/erp_system/media/;
        expires 7d;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://erp_server;
    }
}
```

### 3. تفعيل الموقع
```bash
sudo ln -s /etc/nginx/sites-available/erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔧 إعداد Gunicorn

### 1. تثبيت Gunicorn
```bash
pip install gunicorn
```

### 2. إنشاء ملف Gunicorn config
```bash
nano /home/erp/erp_system/gunicorn_config.py
```

**محتوى الملف:**
```python
bind = 'unix:/home/erp/erp_system/gunicorn.sock'
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2
errorlog = '/home/erp/erp_system/logs/gunicorn-error.log'
accesslog = '/home/erp/erp_system/logs/gunicorn-access.log'
loglevel = 'info'
```

### 3. إنشاء مجلد Logs
```bash
mkdir -p /home/erp/erp_system/logs
```

---

## 👷 إعداد Supervisor

### 1. تثبيت Supervisor
```bash
sudo apt install supervisor -y
```

### 2. إنشاء ملف Supervisor
```bash
sudo nano /etc/supervisor/conf.d/erp.conf
```

**محتوى الملف:**
```ini
[program:erp]
command=/home/erp/erp_system/venv/bin/gunicorn config.wsgi:application -c /home/erp/erp_system/gunicorn_config.py
directory=/home/erp/erp_system
user=erp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/erp/erp_system/logs/supervisor.log
```

### 3. تحديث Supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status erp
```

---

## 🔒 إعداد SSL مع Let's Encrypt

### 1. تثبيت Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. الحصول على SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. التجديد التلقائي
```bash
sudo certbot renew --dry-run
```

---

## 🔄 النسخ الاحتياطي التلقائي

### 1. إنشاء سكريبت النسخ الاحتياطي
```bash
nano /home/erp/backup.sh
```

**محتوى السكريبت:**
```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/home/erp/backups"
DB_NAME="erp_production"
DB_USER="erp_user"
DB_PASS="strong_password_here"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/erp/erp_system/media/

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 2. جعل السكريبت قابلاً للتنفيذ
```bash
chmod +x /home/erp/backup.sh
```

### 3. إضافة Cron Job
```bash
crontab -e

# Add this line (backup daily at 2 AM)
0 2 * * * /home/erp/backup.sh >> /home/erp/backup.log 2>&1
```

---

## 📊 المراقبة والصيانة

### فحص حالة النظام
```bash
# Check Nginx
sudo systemctl status nginx

# Check Supervisor
sudo supervisorctl status

# Check database
sudo systemctl status mysql

# View logs
tail -f /home/erp/erp_system/logs/gunicorn-error.log
tail -f /var/log/nginx/erp-error.log
```

### تحديث النظام
```bash
cd /home/erp/erp_system
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart erp
```

---

## 🔐 قائمة الأمان

- [ ] DEBUG = False
- [ ] SECRET_KEY آمن وطويل
- [ ] ALLOWED_HOSTS محدد
- [ ] SSL مفعّل
- [ ] Firewall مفعّل (ufw)
- [ ] SSH بمفتاح فقط (لا password)
- [ ] MySQL من localhost فقط
- [ ] نسخ احتياطية تلقائية
- [ ] مراقبة Logs
- [ ] تحديثات أمنية منتظمة

---

## 🚨 استكشاف الأخطاء

### الموقع لا يعمل
```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check Gunicorn
sudo supervisorctl status erp
sudo supervisorctl restart erp

# Check logs
tail -f /home/erp/erp_system/logs/gunicorn-error.log
```

### خطأ 502 Bad Gateway
```bash
# Check Gunicorn socket
ls -la /home/erp/erp_system/gunicorn.sock

# Restart services
sudo supervisorctl restart erp
sudo systemctl restart nginx
```

### قاعدة البيانات
```bash
# Check MySQL
sudo systemctl status mysql

# Test connection
mysql -u erp_user -p erp_production
```

---

## 📞 الدعم

**للمساعدة:**
- راجع ملفات الـ Logs
- تحقق من الإعدادات
- اتصل بالدعم الفني

---

**✅ النظام جاهز للإطلاق!**
