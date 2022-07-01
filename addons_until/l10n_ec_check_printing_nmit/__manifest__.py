# -*- coding: utf-8 -*-
{
    'name': 'Impresion de Cheques para Ecuador',
    'version': '10.0.0.1.0',
    'author': 'NewMind-IT',
    'category': 'Accounting',
    'complexity': 'normal',
    'website':'www.newmind-it.com',
    'images': ['static/description/icon.png'],    
    'license': 'AGPL-3',
    'data': [
        'views/report_check_pacifico.xml',
        'views/reports.xml',
        'views/account_view.xml',
        'views/report_template_matriz.xml',
        'views/reports_matriz.xml',
        'wizard/wizard_payment.xml',
    ],
    'depends': [

        'base',
        'account_accountant',
        'account_check_printing',
        'account_batch_payment',        
    ]
}
