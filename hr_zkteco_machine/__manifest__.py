# -*- coding: utf-8 -*-
{
    'name': "Biometric Machine[Zkteco] ",

    'summary': """
       Employee Attendance, Fingerprint Machine Integration""",

    'description': """
Biometric Machine Integration
=============================

This application enables you to integrate the fingerprint machine at you organization with Odoo.
Downloads the logs of each employee from the fingerprint machine with their details.
    """,

    'author': "OnGood, Pravitha V",
    'website': "https://www.odoo.com/",
    'category': 'Human Resources Custom',
    'version': '0.1',

    'depends': ['base_setup', 'hr', 'hr_attendance',],
    'images': ['static/description/images/main_screenshot.png'],
    'external_dependencies': {
        'python': ['zklib'],
    },

    'data': [
        # 'security/ir.model.access.csv',
        'views/biometric_machine_view.xml',
        'report/daily_attendance_view.xml',
        'schedule.xml',
        'wizard/schedule_wizard.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
    
}
