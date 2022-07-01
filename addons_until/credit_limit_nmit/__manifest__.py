{
    'name': 'Customer Credit Limit',
    'author': 'NewMind-IT',
    'category': 'Accounting',
    'version': '1.0',
    'description': """Customer Credit Limit, Credit Limit With Warning and Blocking, Customer Credit Limit With Warning and Blocking""",
    'summary': """Customer Credit Limit""",
    'depends': ['account', 'sale'],
    'license': 'LGPL-3',
    'data': [
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/res_config_settings.xml',
    ]
}
