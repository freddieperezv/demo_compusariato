# -*- coding: utf-8 -*-
{
    'name': "Customizaciones Product Template",

    'summary': """
        Modificacion en catálogo de producto""",

    'description': """
        Oculta el campo costo que se encuentra en el catálogo de producto
        solo los podrá visualizar el rol de facturación de contabilidad o superior
    """,

    'author': 'Newmind-IT',
    'contributors': [
        'Freddie Perez',
    ],
    'website': "http://www.newmind-it.com",
    'category': 'Stock',
    'version': '1.0',
    'license':'LGPL-3',
    'depends': ['stock'],
    'data': [
        "views/product_views.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}