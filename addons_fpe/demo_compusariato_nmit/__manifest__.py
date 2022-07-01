# -*- coding: utf-8 -*-
{
    'name': "Base Demo Compusariato",

    'summary': """
        Base configurada con todas las configuraciones necesarias""",

    'description': """
        Base configurada con todas las configuraciones necesarias
    """,

    'author': 'Newmind-IT',
    'contributors': [
        'Freddie Perez',
    ],
    'website': "http://www.newmind-it.com",
    #'images': ['static/description/icon.png'],
    'category': 'Purchase',
    'version': '1.0',
    'license':'LGPL-3',
    'depends': ['account_accountant',
                'purchase',
                'sale_management',
                'contacts',
                'board',
                'stock',
                'stock_landed_costs',
                'maintenance',
                'mrp',
                'sale_mrp',
                # 'mrp_maintenance', 
                'crm',               
                'purchase_importation_cost_nmit',
                'sale_commission',
                'bt_asset_management',
                'industry_fsm',
                'helpdesk',
                'repair',
                'l10n_ec',
                'l10n_ec_nmit',
                'l10n_ec_nmitfix',
                'l10n_ec_remission',
                'l10n_ec_check_printing_nmit',
                'l10n_ec_ats'],
    'data': [
        # Chart of Accounts
        "data/account_account_data.xml",
        # Comisiones
        "data/sale_commission.xml",
        # Partners data
        "data/res_partner_data.xml",
        # Products
        "data/product_template_data.xml",
        # Journal
        "data/account_journal_data.xml",
        # Mrp
        "data/mrp_data.xml",
        # Mantenimiento
        "data/maintenance_data.xml",        
        # Activos fijos
        "data/account_asset_data.xml",
        # Cuentas Analíticas
        "data/analytic_account.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}