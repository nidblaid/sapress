# -*- coding: utf-8 -*-
###################################################################################
#
#    @lahlou apps
#
#    Copyright (C) 2021 alahlou.com
#
###################################################################################
{
    'name': "@lahlou : Sale Twizza",

    'summary': """
        Customisations in sale module for twizza.""",

    'description': """
        Customisations in sale module for twizza.
    """,

    'author': "Ahmed LAHLOU, @lahlou",
    'website': "https://alahlou.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full listhr
    'category': 'sale',
    'version': '13.0.0.1',

    'depends': [
        'account',
        'sale_margin',
        'sale_stock',
        'sales_team',
        'delivery',
        # twizza addons
        'al_contacts_twizza',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # views
        'views/sale_views.xml',
        'views/crm_team_views.xml',
        'views/partner_area_views.xml',
        'views/models_views.xml',
        'views/partner_area_views.xml',
        'views/res_partner_views.xml',
        'views/menuitems.xml',
        # report
        'report/sale_report_templates.xml',
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
