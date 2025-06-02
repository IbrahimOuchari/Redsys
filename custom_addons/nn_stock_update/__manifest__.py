{
    'name': 'Stock Advanced Features',
    'version': '1.2',
    'category': 'Inventory',
    'summary': 'Ajout de fonctionnalités avancées pour le module Stock',
    'description': '''
        - Support multi-monnaie (Dinar, Euro, Dollar)
        - Numérotation en série
        - Notification de seuil critique
        - Champs de dates (création, dernier mouvement)
        - Fournisseur principal et dernier bon de commande
        - Champs supplémentaires produit
    ''',
    'author': 'Neonara',
    'depends': ['stock', 'purchase', 'product'],
    'data': [
        'views/product_template_views.xml',
        'data/ir_cron_data.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application':True,
}