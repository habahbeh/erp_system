# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-company Django-based ERP system primarily written in Arabic, supporting multiple modules including Core, Accounting, Assets, HR, Inventory, Purchases, Sales, and Reports.

**Key Technologies:**
- Django 5.2.5
- MySQL database
- Python 3.10
- RTL (Right-to-Left) UI for Arabic language support

## Essential Commands

### Development Server
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux

# Run development server
python manage.py runserver

# Run with specific port
python manage.py runserver 8080
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Database shell
python manage.py dbshell
```

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic

# Clear static files
python manage.py collectstatic --clear
```

### Testing & Development
```bash
# Django shell
python manage.py shell

# Django shell with IPython
python manage.py shell_plus  # requires django-extensions
```

## Architecture & Design Patterns

### Multi-Company Multi-Branch Architecture

The system is designed from the ground up for multi-tenancy:

1. **Company Isolation**: Each company has its own data space. The `Company` model (apps/core/models.py:89) is the root entity for data segregation.

2. **Branch Management**: Each company can have multiple branches (`Branch` model). Users are assigned to a specific branch but can switch between authorized branches.

3. **Middleware-Driven Context**: `CurrentBranchMiddleware` (apps/core/middleware.py:43) automatically sets `request.current_company` and `request.current_branch` for every request:
   - Superusers can switch between companies via session
   - Regular users are locked to their assigned company
   - Branch selection is persisted in session

4. **Base Models Pattern**: Two abstract base models enforce company isolation:
   - `BaseModel` (apps/core/models.py:14): For master data, includes company, audit fields (created_at, updated_at, created_by), and is_active
   - `DocumentBaseModel` (apps/core/models.py:28): For transactional documents, extends BaseModel and adds branch reference

### Module Structure

The system follows a modular Django app structure under `apps/`:

**Core Module** (`apps/core/`):
- Central models for the entire system (17 models total)
- User management with custom User model extending AbstractUser
- Company, Branch, Warehouse management
- Items (products/materials) with multi-level categories (4 levels max)
- Item variants with dynamic attributes
- Business Partners (unified Customer/Supplier model)
- Price Lists with date-based pricing
- Numbering Sequences for auto-generating document numbers
- Custom Permission system separate from Django's built-in permissions
- Currency management with exchange rates

**Accounting Module** (`apps/accounting/`):
- Structured in sub-models: account_models, fiscal_models, journal_models, voucher_models, balance_models
- Chart of Accounts with hierarchical structure
- Fiscal Year and Accounting Period management
- Journal Entries with template support
- Payment and Receipt Vouchers
- Account Balance tracking with history

**Assets Module** (`apps/assets/`):
- Comprehensive fixed assets management system
- Depreciation calculation (multiple methods)
- Asset lifecycle: acquisition, transfer, disposal, leasing
- Maintenance scheduling and tracking
- Physical count/inventory verification
- Insurance management with claims
- Approval workflow system
- Automatic journal entry generation for asset transactions

**Other Modules**:
- HR, Inventory, Purchases, Sales (currently commented out in settings.py:46-49)
- Reports module for cross-module reporting

### Numbering Sequence System

Document numbering is centralized through `NumberingSequence` model (apps/core/models.py:700):
- Auto-generates sequential numbers for all document types
- Supports yearly reset with configurable format: `PREFIX/YEAR/NUMBER`
- Configurable padding (e.g., 000001)
- Optional month inclusion
- Default sequences auto-created when a new company is created (apps/core/models.py:134)

### Accounting Integration

The system features deep accounting integration:

1. **Default Chart of Accounts**: Auto-created when a company is initialized (apps/core/models.py:333)
2. **Asset Accounting Configuration**: Links asset categories to GL accounts (apps/assets/models/accounting_config.py)
3. **Automatic Journal Entries**: Configured via `SystemSettings.auto_create_journal_entries` (apps/core/models.py:1443)
4. **Account Linking**: Items, BusinessPartners, and Assets can be linked to specific GL accounts

### Permission System

Dual permission system:
1. **Django Permissions**: Standard CRUD operations via Django's auth system
2. **Custom Permissions**: Advanced business logic permissions (apps/core/models.py:834)
   - Support for amount limits (max_amount)
   - Approval workflows
   - Organized by category (sales, purchases, inventory, accounting, hr, reports, system)
   - Permission groups for bulk assignment (apps/core/models.py:1483)

### Multi-Language Support

- Default language: Arabic (`LANGUAGE_CODE = 'ar'`)
- Supported languages: Arabic, English
- Timezone: Asia/Amman
- All models include both Arabic and English name fields where applicable

## Database Configuration

The system uses MySQL with specific configurations:

```python
# Custom MySQL setup to bypass version checks
mysql_base.DatabaseWrapper.check_database_version_supported = dummy_check
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False
```

This is handled in config/settings.py:12-21 and required due to specific MySQL version compatibility.

**Environment Variables** (defined in .env):
- SECRET_KEY: Django secret key
- DEBUG: Debug mode toggle
- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT: Database connection parameters

## Important Patterns & Conventions

### Context Processors
Two custom context processors (apps/core/context_processors.py) provide global template variables:
- `system_settings`: System name, version, company name, branch name, currency
- `companies_processor`: Available companies, current company/branch, company switching capability

### Audit Trail
`AuditLog` model (apps/core/models.py:1456) tracks all significant operations:
- CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT actions
- Stores old and new values as JSON
- Records user, company, branch, IP address, timestamp

### Custom Fields
Many models include a `custom_fields` JSONField for extensibility without schema changes.

### Signal-Based Automation
The assets module uses Django signals (apps/assets/signals.py) for:
- Automatic depreciation calculations
- Journal entry generation
- Notification triggering

## Working with the Codebase

### Adding New Companies
When creating a company, two methods should be called:
1. `company.create_default_sequences()` - Creates numbering sequences for all document types
2. `company.create_default_accounts()` - Creates the default chart of accounts

### User Access Control
Check user access using:
- `user.can_access_branch(branch)` - Branch access verification
- `user.profile.has_custom_permission(code)` - Custom permission check
- `user.profile.has_custom_permission_with_limit(code, amount)` - Permission with monetary limit

### Getting Current Context
In views, always use:
- `request.current_company` - Currently active company
- `request.current_branch` - Currently active branch

These are set by middleware and should never be None for authenticated users.

### Price Calculation
Use the helper function `get_item_price(item, variant, price_list, quantity, check_date)` from apps/core/models.py:1694 to get correct pricing with all business rules applied (date validity, quantity breaks, etc.).

### Warehouse Management
Each branch has a default warehouse. Users can also have a default warehouse. The system supports negative stock control via `SystemSettings.negative_stock_allowed`.

## Module Dependencies

```
core (foundation)
  ├── accounting (fiscal, accounts, journals, vouchers)
  ├── assets (fixed assets, linked to accounting)
  ├── inventory (stock management, linked to accounting)
  ├── sales (sales orders, invoices)
  ├── purchases (purchase orders, bills)
  ├── hr (employees, payroll)
  └── reports (cross-module reporting)
```

Currently active: core, accounting, assets, reports
Currently disabled: sales, purchases, inventory, hr

## URL Structure

- `/admin/` - Django admin
- `/` - Core module (dashboard, login, master data)
- `/accounting/` - Accounting module
- `/assets/` - Assets module
- Login/Logout handled at root level

## Development Notes

- The system expects MySQL charset utf8mb4
- Static files are in `/static/`, collected to `/staticfiles/`
- Media files (uploads) are in `/media/`
- Templates use RTL layout in `templates/base/`
- All user-facing content is in Arabic by default
- Debug toolbar is installed for development (django-debug-toolbar)
- django-extensions provides enhanced management commands
- Widget tweaks and django-select2 are used for form rendering
