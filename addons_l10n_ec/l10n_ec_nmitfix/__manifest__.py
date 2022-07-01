{
    'name': "fix localization by Newmind-IT",
    'summary': """
        long fix  for the items has this module
        """,
    'description': """
        long description for the items has this module
    """,
    'author': "Newmind-IT",
    'website': "http://www.newmind-it.com",
    'images': ['static/description/icon.png'],
    'license':'AGPL-3',
    'category': 'account',
    'version': '15.0.1',
    'depends': [
        'l10n_ec', 'account_edi',
        'l10n_ec_nmit'
    ],
    'auto_install': True,
    'data': [
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}