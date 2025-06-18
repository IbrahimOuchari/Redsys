{
    'name': "NeoNara Admin",
    'author': 'NeoNara',
    'category': '',
    'summary': """""",
    'license': 'AGPL-3',
    'website': 'www.neonara.digital',
    'description': "Module NeonNara ",
    'version': '17.0',

    'depends': ['base', 'muk_web_theme'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/res_company.xml',
        'views/company_bank.xml',
             ],

    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}