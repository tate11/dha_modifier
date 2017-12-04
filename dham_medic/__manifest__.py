# -*- coding: utf-8 -*-
{
    'name': "DHAM Medic",

    'description': """
        Long description of module's purpose
    """,

    'author': "DHA Medic/ Vu / Viet",
    'website': "http://www.dhamedic.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHAMEDIC',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account', 'stock', 'hr', 'web_kanban', 'web', 'calendar', 'dha_res_partner_modifier'],

    # always loaded
    'data': [

        'security/group_access_right_medic.xml',
        'security/ir.model.access.csv',

        'data/sequence.xml',
        'data/ir_cron.xml',

        'wizard/wizard_check_customer_views.xml',
        'wizard/wizard_print_test_number.xml',
        'wizard/wizard_import_employee_company_check_view.xml',

        'views/ir_sequence.xml',
        'views/menu_item.xml',
        'views/template.xml',
        'views/run_one_time_function.xml',

        # Receive
        'dham_medic_receive/dham_medic_patient_receive_view.xml',
        # partner
        'partner/data/partner_data.xml',
        'partner/views/res_partner_views.xml',
        'partner/views/medic_company_check_views.xml',
        'partner/views/medic_contract_schedule.xml',

        # patient
        'patient/views/dha_medic_patient_view.xml',

        # product
        'product/data/product_data.xml',
        'product/views/medic_product_template_views.xml',

        # lab test
        'lab_test/data/lab_test_unit.xml',
        'lab_test/data/tests_type.xml',
        'lab_test/views/medic_test_views.xml',

        # account
        'account/views/medic_account_invoice_views.xml',

        # department
        'department/views/medic_heath_center_views.xml',

        # medical bill
        'department/data/building_type.xml',
        'department/data/out_building_center_stock.xml',
        'medical_bill/views/medic_medical_bill_views.xml',

        # product
        'product/data/product_data.xml',
        'product/views/medic_product_template_views.xml',

        # diseases
        'diseases/views/medic_diseases_views.xml',

        # appoint
        'appoint/views/medic_appoint_views.xml',

        # stock
        'stock/views/medic_stock_views.xml',

        # sale
        'sale/views/medic_sale_order.xml',

        # employee
        'employee/views/medic_hr_employee_view.xml'
    ],
    # only loaded in demonstration mode
    'qweb': ['static/src/xml/*.xml'],

    'demo': [
    ],
    'installable': True,
}