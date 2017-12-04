# -*- coding: utf-8 -*-
{
    'name': "dha_medic_sale_report",

    'description': """
        DHA Medic Report
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhamedic.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHAMEDIC',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'report', 'sale'],

    # always loaded
    'data': [
        'views/views.xml',
        'report/external_layout.xml',
        'report/sale_report_templates.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],

    'demo': [
    ],
}