#!/bin/bash
# Django ERP System Deployment Script for CentOS 9
# This script automates the deployment process

set -e  # Exit on any error

echo "=== Django ERP Deployment Script ==="
echo "Starting deployment at $(date)"

# Variables
DB_NAME="erp_system"
DB_USER="erp_user"
DB_PASS="Sygma@2025_GM"
DB_ROOT_PASS="Sygma@2025_GM"
PROJECT_DIR="/var/www/erp_system"
PYTHON_VERSION="3.10"

echo "Step 1: Installing EPEL Release..."
dnf install -y epel-release

echo "Step 2: Installing Python ${PYTHON_VERSION}..."
dnf install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-devel python${PYTHON_VERSION}-pip

echo "Step 3: Installing Apache and mod_wsgi..."
dnf install -y httpd httpd-devel
dnf install -y python3-mod_wsgi

echo "Step 4: Installing MySQL Server..."
dnf install -y mysql-server mysql-devel

echo "Step 5: Installing development tools..."
dnf install -y gcc gcc-c++ make git wget

echo "Step 6: Starting and enabling MySQL..."
systemctl start mysqld
systemctl enable mysqld

echo "Step 7: Securing MySQL and creating database..."
# Set root password and create database
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASS}';" 2>/dev/null || mysql -u root -p"${DB_ROOT_PASS}" -e "SELECT 1;" 2>/dev/null || echo "MySQL root password already set or needs manual configuration"

# Create database and user
mysql -u root -p"${DB_ROOT_PASS}" <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "Step 8: Creating project directory..."
mkdir -p ${PROJECT_DIR}
cd ${PROJECT_DIR}

echo "Step 9: Setting up Python virtual environment..."
python${PYTHON_VERSION} -m venv venv
source venv/bin/activate

echo "Step 10: Upgrading pip..."
pip install --upgrade pip

echo "Step 11: Installing mysqlclient dependencies..."
dnf install -y pkg-config

echo "Step 12: Project files will be transferred separately..."
echo "After transfer, run: pip install -r requirements.txt"

echo "Step 13: Configuring firewall..."
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload 2>/dev/null || echo "Firewall not running or already configured"

echo "Step 14: Creating directories for static and media files..."
mkdir -p ${PROJECT_DIR}/staticfiles
mkdir -p ${PROJECT_DIR}/media

echo "=== Initial setup completed at $(date) ==="
echo "Next steps:"
echo "1. Transfer project files to ${PROJECT_DIR}"
echo "2. Update .env file with production settings"
echo "3. Install Python dependencies: source venv/bin/activate && pip install -r requirements.txt"
echo "4. Run migrations: python manage.py migrate"
echo "5. Collect static files: python manage.py collectstatic --noinput"
echo "6. Configure Apache virtual host"
echo "7. Set permissions and SELinux policies"
echo "8. Start Apache: systemctl start httpd && systemctl enable httpd"
