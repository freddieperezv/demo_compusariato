# -*- coding:utf-8 -*-

{
    'name': 'ATS Ecuador',
    'version': '1.0',
    'depends': [
        'l10n_ec_nmit',
        'l10n_latam_invoice_document',
    ],
    'author': 'NewMind-IT',
    'contributors': [
        'itobetter@gmail.com',
        'Freddie Perez',
    ],
    'category': 'Account',
    'website':'www.newmind-it.com',
    'images': ['static/description/icon.png'],
    'summary':'Generación del XML',
    'license':'LGPL-3',
    'description': """
        Módulo para la generación del xml del ATS
     """,
     'data':[
         'security/ir.model.access.csv',
         'data/pay_resident.xml',
         'data/type_foreign_tax_regime.xml',
         'data/country_payment_regime.xml',
         'data/tax_haven_country.xml',
         'data/account_ats.xml',
         'wizard/account_ats_view.xml',
         'views/partner_view.xml',
         'views/pay_resident_view.xml',
         'views/type_foreign_tax_regime_view.xml',
         'views/country_payment_regime_view.xml',
         'views/tax_haven_country_view.xml',
         'views/res_partner_menu_config.xml',
     ],

}