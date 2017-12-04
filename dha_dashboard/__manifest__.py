# -*- coding: utf-8 -*-
{
    'name': "dha_dashboard",


    'description': """
        Add Dashboard
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhacorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHA',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'dhac_double_approve_pr', 'purchase_request', 'hr_holidays'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/dashboard_views.xml',
        'views/dashboard_templates.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    # only loaded in demonstration mode
    'demo': [
    ],
}