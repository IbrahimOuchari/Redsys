{
    'name': 'Custom Invoice Report',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Customizations for Odoo 17 invoice reports',
    'description': """
Custom Invoice Report Module
============================
This module customizes the invoice reports in Odoo 17:
- Displays product_id in PDF reports
- Adds payment method options to invoices
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['account', 'sale', 'product', 'base'],
    'data': [
        'views/product_form_view.xml',
        'views/account_move_form.xml',
        'reports/account_invoice_report_templates.xml',
        'reports/sale_order_report.xml',
        # 'reports/custom_invoice_templates.xml',
        'reports/sale_quotation_report.xml',
        'views/res_company_form.xml',
    ],



    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
