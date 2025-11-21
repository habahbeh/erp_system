# Quick Deployment Guide - Django ERP System

## Current Status
- ✅ Server: 138.68.146.118 (CentOS Stream 9)
- ✅ SSH Access: root / Sygma@2025_GM
- ✅ System Updated
- ✅ Python 3.9.23 installed
- 🔄 Installing: Apache, MySQL, and dependencies

## Complete the Deployment

### Step 1: Wait for Installation to Complete
```bash
ssh root@138.68.146.118
tail -f /root/deployment.log  # Monitor progress
```

### Step 2: Set Up MySQL Database
```bash
# Transfer and run MySQL setup script
scp setup_mysql.sh root@138.68.146.118:/root/
ssh root@138.68.146.118 "bash /root/setup_mysql.sh"
```

### Step 3: Transfer Project Files
```bash
cd "/Users/mohammadhabahbeh/Desktop/My File/Project/erp_system"

rsync -avz --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' \
  --exclude='.git' --exclude='staticfiles' --exclude='media' \
  -e "sshpass -p 'Sygma@2025_GM' ssh" \
  . root@138.68.146.118:/var/www/erp_system/
```

### Step 4: Update .env File
```bash
ssh root@138.68.146.118
nano /var/www/erp_system/.env
```

Change:
- DEBUG=False
- ALLOWED_HOSTS=138.68.146.118

### Step 5: Install Python Dependencies
```bash
cd /var/www/erp_system
source venv/bin/activate
pip install -r requirements.txt
```

### Step 6: Configure Apache
```bash
# Transfer Apache config
scp erp_system_apache.conf root@138.68.146.118:/etc/httpd/conf.d/

# Test configuration
httpd -t
```

### Step 7: Run Final Deployment
```bash
# Transfer and run final deployment script
scp final_deployment.sh root@138.68.146.118:/root/
ssh root@138.68.146.118 "bash /root/final_deployment.sh"
```

### Step 8: Create Superuser
```bash
ssh root@138.68.146.118
cd /var/www/erp_system
source venv/bin/activate
python manage.py createsuperuser
```

### Step 9: Access Your Site
Open in browser: http://138.68.146.118

## Troubleshooting

### Check Services
```bash
systemctl status httpd
systemctl status mysqld
```

### View Logs
```bash
tail -f /var/log/httpd/erp_system_error.log
tail -f /var/log/httpd/error_log
```

### Restart Apache
```bash
systemctl restart httpd
```

## Files Created
1. `install_dependencies.sh` - Install system packages
2. `setup_mysql.sh` - Configure MySQL database
3. `erp_system_apache.conf` - Apache configuration
4. `final_deployment.sh` - Complete deployment setup
5. `DEPLOYMENT_GUIDE.md` - Detailed documentation
6. `QUICK_DEPLOYMENT.md` - This quick guide

## Database Details
- Database: erp_system
- User: erp_user  
- Password: Sygma@2025_GM
- Host: localhost
- Charset: utf8mb4

## Support
If you encounter errors:
1. Check /var/log/httpd/erp_system_error.log
2. Verify database connection
3. Check file permissions
4. Review SELinux settings (ausearch -m avc -ts recent)
