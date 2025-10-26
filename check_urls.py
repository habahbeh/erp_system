#!/usr/bin/env python3
"""Script to check and find URL mismatches in assets templates"""

import os
import re
from collections import defaultdict

# Read all URL names from urls.py
def get_url_names():
    url_names = set()
    with open('apps/assets/urls.py', 'r') as f:
        for line in f:
            match = re.search(r"name='([^']+)'", line)
            if match:
                url_names.add(match.group(1))
    return url_names

# Read all URL references from templates
def get_template_urls():
    template_urls = defaultdict(list)
    templates_dir = 'apps/assets/templates/'

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    matches = re.findall(r"{% url 'assets:([^']+)'", content)
                    for match in matches:
                        template_urls[match].append(filepath)

    return template_urls

# Find possible matches
def find_possible_match(wrong_name, correct_names):
    # Common mapping patterns
    mappings = {
        'attachment_create': 'upload_attachment',
        'attachment_delete': 'delete_attachment',
        'attachment_list': 'asset_list',  # No separate attachment list
        'attachment_update': 'upload_attachment',
        'approval_dashboard': 'dashboard',
        'count_detail': 'count_detail',  # This should exist
        'depreciation_history': 'depreciation_list',
        'depreciation_reverse': 'depreciation_detail',
        'insurance_alerts': 'notifications_dashboard',
        'insurance_claim_create': 'claim_create',
        'insurance_claim_detail': 'claim_detail',
        'insurance_claim_list': 'claim_list',
        'insurance_claim_update': 'claim_update',
        'insurance_company_detail': 'insurance_company_list',  # No detail view
        'lease_payment_create': 'payment_create',
        'lease_payment_delete': 'payment_list',
        'lease_payment_post': 'post_transaction',
        'lease_payment_update': 'payment_list',
        'lease_terminate': 'terminate_lease',
        'maintenance_alerts': 'notifications_dashboard',
        'maintenance_type_detail': 'maintenance_type_list',
        'physical_count_adjustment_detail': 'adjustment_detail',
        'physical_count_adjustment_list': 'adjustment_list',
        'physical_count_create': 'count_create',
        'physical_count_cycle_create': 'cycle_create',
        'physical_count_cycle_detail': 'cycle_detail',
        'physical_count_cycle_list': 'cycle_list',
        'physical_count_cycle_update': 'cycle_update',
        'physical_count_detail': 'count_detail',
        'physical_count_list': 'count_list',
        'physical_count_update': 'count_update',
        'reports_list': 'reports',
        'transaction_dispose': 'dispose_asset',
        'transaction_revalue': 'revalue_asset',
        'transaction_sell': 'sell_asset',
        'transfer_approve': 'approve_transfer',
        'valuation_approve': 'asset_detail',  # Or depreciation related
        'valuation_create': 'asset_create',
        'valuation_detail': 'asset_detail',
        'valuation_list': 'asset_list',
        'valuation_update': 'asset_update',
        'workflow_request_approve': 'approve_request',
        'workflow_request_create': 'request_list',
        'workflow_request_detail': 'request_detail',
        'workflow_request_list': 'request_list',
        'workflow_request_reject': 'reject_request',
    }

    return mappings.get(wrong_name, None)

# Main
url_names = get_url_names()
template_urls = get_template_urls()

print("=" * 80)
print("URL MISMATCH REPORT")
print("=" * 80)

mismatches = []
for template_url, files in sorted(template_urls.items()):
    if template_url not in url_names:
        suggested = find_possible_match(template_url, url_names)
        mismatches.append((template_url, suggested, files))

if mismatches:
    print(f"\nFound {len(mismatches)} URL mismatches:\n")
    for wrong, correct, files in mismatches:
        print(f"❌ '{wrong}' -> ✅ '{correct}'")
        for f in files[:3]:  # Show first 3 files
            print(f"   📄 {f}")
        if len(files) > 3:
            print(f"   ... and {len(files) - 3} more files")
        print()
else:
    print("\n✅ No URL mismatches found!")

print("=" * 80)
