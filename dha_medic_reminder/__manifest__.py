# -*- coding: utf-8 -*-
{
    'name': "DHA Medic Reminder",

    'summary': """
        Send Email Reminder""",

    'description': """
        Send Email Reminder at 7:00AM about Pending task, Approval, ... 
    """,

    'author': "DHA Medic / Viet",
    'website': "http://www.dhamedic.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHAMEDIC',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','dhac_double_approve_pr','purchase_request','mail','contacts'],

    # always loaded
    'data': [
        'data/cron.xml',
        'data/email_template.xml',
        'security/mail_group.xml',
        # 'security/ir.model.access.csv',
        'views/email_reminder_view.xml'
    ],
}