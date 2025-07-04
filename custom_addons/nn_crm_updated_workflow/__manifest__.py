{
    'name': 'Mise à jour CRM - Vues et Workflow',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Mise à jour des vues et du workflow du module CRM',
    'description': """
Ce module met à jour les vues personnalisées et le workflow du module CRM.
    """,
    'author': 'Neonara',
    'website': 'https://neonara.digital',
    'depends': ['crm','purchase','nn_purchase_updated_workflow'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/taux_dd_menu.xml',
        'views/sale_quotations_line.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
