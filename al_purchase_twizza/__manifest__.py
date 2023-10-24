# -*- coding: utf-8 -*-
###################################################################################
#
#    @lahlou apps
#
#    Copyright (C) 2021 alahlou.com
#
###################################################################################
{
    'name': "@lahlou : Purchase Twizza",

    'summary': """
        Customisations in Purchase module for twizza.""",

    'description': """
        Customisations in Purchase module for twizza.
    """,

    'author': "Ahmed LAHLOU, @lahlou",
    'website': "https://alahlou.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full listhr
    'category': 'purchase',
    'version': '13.0.0.1',

    'depends': [
        'purchase_stock',
        'stock_account',
        'sale_purchase',
        'al_sale_twizza',
    ],

    # always loaded
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Views
        # 'views/purchase_views.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_type.xml',
        # menuitems
        'views/menuitems.xml',
    ],

    'application': True,
    'sequence': 2,
}
