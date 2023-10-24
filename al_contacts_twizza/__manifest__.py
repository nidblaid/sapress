# -*- coding: utf-8 -*-
###################################################################################
#
#    @lahlou apps
#
#    Copyright (C) 2021 alahlou.com
#
###################################################################################
{
    'name': "@lahlou : Contacts Twizza",

    'summary': """
        Customisations in Contacts module for twizza.""",

    'description': """
        Customisations in Contacts module for twizza.
    """,

    'author': "Ahmed LAHLOU, @lahlou",
    'website': "https://alahlou.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full listhr
    'category': 'contacts',
    'version': '13.0.0.1',

    'depends': [
        'contacts'
    ],

    # always loaded
    'data': [
        # Views
        'views/res_partner_views.xml',
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
