#!/bin/bash
# Final Django ERP Deployment Steps

set -e

PROJECT_DIR="/var/www/erp_system"
VENV_DIR="${PROJECT_DIR}/venv"

echo "=== Step 1: Installing Python Dependencies ==="
cd ${PROJECT_DIR}
source ${VENV_DIR}/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Step 2: Running Database Migrations ==="
python manage.py migrate --noinput

echo "=== Step 3: Collecting Static Files ==="
python manage.py collectstatic --noinput

echo "=== Step 4: Setting File Permissions ==="
chown -R apache:apache ${PROJECT_DIR}
find ${PROJECT_DIR} -type d -exec chmod 755 {} \;
find ${PROJECT_DIR} -type f -exec chmod 644 {} \;
chmod +x ${PROJECT_DIR}/manage.py

echo "=== Step 5: Configuring SELinux ==="
chcon -R -t httpd_sys_content_t ${PROJECT_DIR}
chcon -R -t httpd_sys_rw_content_t ${PROJECT_DIR}/media
chcon -R -t httpd_sys_rw_content_t ${PROJECT_DIR}/staticfiles
setsebool -P httpd_can_network_connect_db 1
setsebool -P httpd_can_network_connect 1

echo "=== Step 6: Configuring Firewall ==="
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

echo "=== Step 7: Testing Apache Configuration ==="
httpd -t

echo "=== Step 8: Starting Services ==="
systemctl restart httpd
systemctl enable httpd
systemctl status httpd --no-pager

echo "=== Deployment Complete! ==="
echo ""
echo "Your ERP system is now accessible at: http://138.68.146.118"
echo "Apache status: $(systemctl is-active httpd)"
echo "MySQL status: $(systemctl is-active mysqld)"
echo ""
echo "To create a superuser, run:"
echo "  cd ${PROJECT_DIR}"
echo "  source venv/bin/activate"
echo "  python manage.py createsuperuser"
