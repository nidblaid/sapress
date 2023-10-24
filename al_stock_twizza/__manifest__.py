# -*- coding: utf-8 -*-
###################################################################################
#
#    @lahlou apps
#
#    Copyright (C) 2021 alahlou.com
#
###################################################################################
{
    'name': "@lahlou : Stock Twizza",

    'summary': """
        Customisations in Stock module for twizza.""",

    'description': """
        Customisations in Stock module for twizza.
    """,

    'author': "Ahmed LAHLOU, @lahlou",
    'website': "https://alahlou.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full listhr
    'category': 'stock',
    #'version': '13.0.0.1',

    'depends': [
        # odoo addons
        'base',
        'stock_account',
        'sale_stock',
        # twizza addons
        'al_product_twizza',
    ],

    # always loaded
    'data': [
        # security
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        # views
        'views/stock_views.xml',
        # menus
        'views/menuitems.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': [
        # 'static/src/xml/file.xml',
    ],
    'application': True,
    'sequence': 2,
}
