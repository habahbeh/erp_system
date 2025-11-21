# Django ERP System - Deployment Guide
## Server: 138.68.146.118 (CentOS Stream 9)

---

## ✅ Completed Steps

### 1. Server Access Configured
- SSH connection established to 138.68.146.118
- Root access confirmed
- Credentials set: Sygma@2025_GM

### 2. System Updated  
- CentOS Stream 9 confirmed
- System packages updated successfully
- EPEL repository installed

### 3. Deployment Script Running
- Automated deployment script created and transferred
- Script is installing Python 3.10, Apache, MySQL, and dependencies
- Monitor progress: ssh root@138.68.146.118 then tail -f /root/deployment.log

---

## 📋 Remaining Steps (Complete these manually)

### Step 1: Wait for Script Completion
Check if the automated script has finished:
```bash
ssh root@138.68.146.118
cat /root/deployment.log
```

### Step 2: Transfer Project Files
```bash
cd "/Users/mohammadhabahbeh/Desktop/My File/Project/erp_system"

rsync -avz --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' \
  --exclude='.git' --exclude='staticfiles' \
  -e "sshpass -p 'Sygma@2025_GM' ssh -o StrictHostKeyChecking=no" \
  . root@138.68.146.118:/var/www/erp_system/
```

### Step 3: Install Python Dependencies
```bash
ssh root@138.68.146.118
cd /var/www/erp_system
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Update .env for Production
```bash
nano /var/www/erp_system/.env
```
Set DEBUG=False and update ALLOWED_HOSTS

### Step 5: Run Migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Step 6: Configure Apache
Create /etc/httpd/conf.d/erp_system.conf with proper WSGI configuration

### Step 7: Set Permissions
```bash
chown -R apache:apache /var/www/erp_system
chcon -R -t httpd_sys_content_t /var/www/erp_system
setsebool -P httpd_can_network_connect_db 1
```

### Step 8: Start Apache
```bash
systemctl start httpd
systemctl enable httpd
```

Access your site at: http://138.68.146.118
