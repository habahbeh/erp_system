#!/bin/bash
# MySQL Database Setup Script

DB_NAME="erp_system"
DB_USER="erp_user"
DB_PASS="Sygma@2025_GM"
DB_ROOT_PASS="Sygma@2025_GM"

echo "=== Setting up MySQL Database ==="

# Secure MySQL installation (set root password)
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASS}';" 2>/dev/null || echo "Root password already set"

# Create database
mysql -u root -p"${DB_ROOT_PASS}" <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "=== MySQL Database Setup Complete ==="
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Host: localhost"

# Test connection
mysql -u ${DB_USER} -p"${DB_PASS}" -e "USE ${DB_NAME}; SHOW TABLES;" 2>/dev/null && echo "✓ Database connection successful!" || echo "✗ Database connection failed"
