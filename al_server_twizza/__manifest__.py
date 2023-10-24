# -*- coding: utf-8 -*-
###################################################################################
#
#    @lahlou apps
#
#    Copyright (C) 2021 alahlou.com
#
###################################################################################
{
    'name': "@lahlou : Server Twizza",

    'summary': """
        Server utilities.
    """,

    'description': """
        Server utilities.
    """,

    'author': "Ahmed LAHLOU, @lahlou",
    'website': "https://alahlou.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full listhr
    'category': 'server',
    'version': '13.0.0.1',

    'depends': [
        'base',
    ],

    # always loaded
    'data': [
        # security
        # data
        'data/ir_cron_data.xml',
        # Views
        'views/res_config_settings.xml',
    ],

    'application': True,
    'sequence': 2,
}
