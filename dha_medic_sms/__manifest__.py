# -*- coding: utf-8 -*-
{
    'name': "DHA Medic SMS",

    'summary': """
        Send SMS to Customer""",

    'description': """
        Send SMS to Customer
    """,

    'author': "DHA Medic / Viet",
    'website': "http://www.dhamedic.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHAMEDIC',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','marketing_campaign'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/sms_views.xml',
        'views/sms_list_view.xml',
        'views/marketing_campaign_views.xml',
        'views/templates.xml',
    ],
}