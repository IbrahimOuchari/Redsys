{
    'name': "NeoNara Admin",
    'author': 'NeoNara',
    'category': '',
    'summary': """""",
    'license': 'AGPL-3',
    'website': 'www.neonara.digital',
    'description': "Module NeonNara ",
    'version': '17.0',

    'depends': ['base'],

    'data': [
        'views/res_partner_views.xml',
        'views/res_company.xml',
             ],

    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}