# -*- coding: utf-8 -*-
{
    'name': "Costing of imported products by Newmind-IT",

    'summary': """
        Entry of Imports in Odoo""",

    'description': """
        It allows to costing products that are purchased from international suppliers.
    """,

    'author': 'NewMind-IT',
    'contributors': [
        'Freddie Perez',
    ],
    'website': "http://www.newmind-it.com",
    'images': ['static/description/icon.png'],
    'category': 'Purchase',
    'version': '1.0',
    'license':'LGPL-3',
    'depends': ['stock_landed_costs'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/import.folder.type.csv',
        'report/stock_landed_report_view.xml',
        'views/tag_view.xml',
        'views/purchase_import_views.xml',
        'views/account_invoice_views.xml',
        'views/account_account_views.xml',
        'views/stock_landed_cost_views.xml',
        'views/account_payment_views.xml',
        'views/purchase_order_views.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',        
    ],
}