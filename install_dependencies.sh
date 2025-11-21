#!/bin/bash
# Install all required packages for Django ERP deployment

set -e

echo "=== Installing Apache and Python dependencies ==="
dnf install -y httpd httpd-devel python3-devel gcc mysql-server mysql-devel python3-mod_wsgi

echo "=== Installing build tools ==="
dnf install -y gcc-c++ make git wget pkg-config

echo "=== Starting and enabling MySQL ==="
systemctl start mysqld
systemctl enable mysqld

echo "=== Creating project directory ==="
mkdir -p /var/www/erp_system

echo "=== Setting up virtual environment ==="
cd /var/www/erp_system
python3 -m venv venv

echo "=== Installation complete! ==="
echo "Python version: $(python3 --version)"
echo "Apache installed: $(httpd -v | head -1)"
echo "MySQL installed: $(mysql --version)"
echo ""
echo "Next: Transfer project files and install Python packages"
