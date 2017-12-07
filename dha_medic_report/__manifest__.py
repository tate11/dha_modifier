# -*- coding: utf-8 -*-
{
    'name': "dha_medic_report",

    'description': """
        DHA Medic Report
    """,

    'author': "DHA Medic/ Vu",
    'website': "http://www.dhamedic.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHAMEDIC',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'dha_medic_modifier', 'report'],

    # always loaded
    'data': [
        
        'views/medic_test_views.xml',
        'views/medic_partner_company_check.xml',
        'report/invoice_receipt_voucher.xml',
        'report/lab_test_report.xml',
        'report/medic_medical_bill_report.xml',
        'report/dha_medic_report.xml',
        'report/medic_medical_check_list.xml',
        'report/dham_check_list.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],

    'demo': [
    ],
}