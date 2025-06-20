{
    'name': 'Mise à jour Achat - Vues et Workflow',
    'version': '17.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Mise à jour des vues et du workflow du module Achat',
    'description': """
Ce module met à jour les vues personnalisées et le workflow du module d'Achat.
    """,
    'author': 'Neonara',
    'website': 'https://neonara.digital',
    'depends': ['purchase', 'base', 'nn_commercial_docs', 'mail'],
    'data': [
        'data/purchase_rfq_order_email.xml',
        'data/purchase_rfq_email.xml',
        'views/purchase_order_views.xml',
        'views/purchase_rfq_views.xml',
        'views/purchase_product_search.xml',
        'reports/purchase_quotation_templates.xml',
        'reports/purchase_order_templates.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
