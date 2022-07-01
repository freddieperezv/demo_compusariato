{
    'name': "localization by Newmind-IT",
    'summary': """
        Newmind-IT customization for odoo EC
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
        'external_dependencies': {
       'python': ['xmlsig', 'pyopenSSL', 'suds-jurko', 'num2words',
            'xades',  'grpcio',  'cryptography==3.3.2', 'six==1.16.0'
        ],
    },
    'depends': [
        'l10n_ec', 'account_edi'
    ],
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'wizard/batch_move_edi_web_service_view.xml',
        'data/l10n_latam.document.type.csv',
        'data/account_report.xml',
        'data/account_tax_group_data.xml',
        'data/cron.xml',
        'data/account_edi_data.xml',
        'data/out_invoice.xml',
        'data/out_refund.xml',
        'data/liq_purchase.xml',
        'data/res_currency_data.xml',
        'data/account_wh.xml',
        'data/tax_support.xml',
        'data/tax_support_mapping.xml',   
        'data/res_partner_data.xml',        
        'reports/account_move.xml',
        'reports/account_wh.xml',
        'data/electronic_documents.xml',
        'views/account_wh_view.xml',
        'views/res_config_settings_view.xml',
        'views/res_company.xml',
        'views/res_currency_view.xml',
        'views/templates.xml',
        'views/account_move.xml',  
        'views/account_stating_sequence.xml',
        'views/tax_support.xml',
        'views/tax_support_mapping.xml',
        'views/accoount_tag.xml',
        'views/report_payment_receipt_templates.xml'
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
