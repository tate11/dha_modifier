# -*- coding: utf-8 -*-
{
    'name': "dhac_follower_leaves",

    'description': """
        Add employee manager as follower when create a leave request.
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhacorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHA',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_holidays'],

    # always loaded
    'data': [
    ],
    # only loaded in demonstration mode
    'qweb': [],

    'demo': [
    ],
}