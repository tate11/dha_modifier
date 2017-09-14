# -*- coding: utf-8 -*-
{
    'name': "dha_helpdesk_project",

    'description': """
        Routing helpdesk to project
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhamedic.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'helpdesk'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/fetch_mail_server_views.xml',
        'views/helpdesk_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}