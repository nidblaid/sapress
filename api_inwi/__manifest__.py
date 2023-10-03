# -*- coding: utf-8 -*-
{
    'name': "API INWI",

    'summary': """ """,

    'description': """
        Inwi API details
    """,

    'author': "DOOSYS",
    'website': "http://doosys.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sochepress_base', 'mail'],

    # always loaded
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/inwi_config_settings.xml',
        'views/get_demand_from_inwi.xml',
        'views/partners_inwi_destinations.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
