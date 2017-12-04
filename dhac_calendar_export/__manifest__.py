# -*- coding: utf-8 -*-
{
    'name': "dhac_calendar_export",

    'description': """
        Add function calendar export 
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhacorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHA',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/calendar_views.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],

    'demo': [
    ],
}