{
    'name': 'Kardex',
    'version': '1.1',
    'category': 'Stock/Inventory',
    'summary': 'Inventory',
    'description': """
    Reporte Kardex
 """,
    'author': "Newmind-IT",
    'website': 'https://www.newmind-it.com/',
    'depends': [
        'base_setup',
        'account_reports',
        'account',
        'stock',
        'purchase_stock',
        'sale_stock',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizards/report_inventory_views.xml',
        'report/report_kardex_pdf.xml',
        'report/stock_warehouse_valued_report_view.xml',
            ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}

