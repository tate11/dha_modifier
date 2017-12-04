# -*- coding: utf-8 -*-
{
    'name': "dhac_office_modifier",

    'description': """
        1. Document submit functional
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhacorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHA',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr'],

    # always loaded
    'data': [
        'security/document_submit_security.xml',
        'security/ir.model.access.csv',
        'document_submit/document_submit_views.xml',
        'document_submit/document_submit_data.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],

    'demo': [
    ],
}