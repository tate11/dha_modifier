# -*- coding: utf-8 -*-
{
    'name': "dham_doctor_interface",

    'summary': """
        Doctor interface""",

    'description': """
        Doctor interface
    """,

    'author': "DHA Medic / Viet",
    'website': "http://www.dhamedic.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHAMEDIC',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','dha_medic_modifier'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/medic_medical_bill_views.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
}