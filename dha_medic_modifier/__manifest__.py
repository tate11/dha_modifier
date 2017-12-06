# -*- coding: utf-8 -*-
{
    'name': "dha_medic_modifier",

    'description': """
        Long description of module's purpose
    """,

    'author': "DHA Medic/ Vu",
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
        'data/partner_data.xml',
        'data/product_data.xml',
        'data/sequence.xml',
        'data/tests_type.xml',
        'data/ir_cron.xml',
        'data/lab_test_unit.xml',
        'data/out_building_center_stock.xml',
        'data/building_type.xml',
        'data/treatement_classify.xml',

        'wizard/wizard_check_customer_views.xml',
        'wizard/wizard_print_test_number.xml',
        'wizard/wizard_import_employee_company_check_view.xml',

        'dham_lab_image_test/dham_image_test_view.xml',
        'views/menu_item.xml',
        'views/template.xml',
        'views/medic_package.xml',
        'views/medic_medicine_order_views.xml',
        'views/res_partner_views.xml',
        'views/medic_test_views.xml',
        'views/medic_account_invoice_views.xml',
        'views/medic_heath_center_views.xml',
        'views/medic_medical_bill_views.xml',
        'views/medic_product_template_views.xml',
        'views/medic_diseases_views.xml',
        'views/medic_appoint_views.xml',
        'views/medic_company_check_views.xml',
        'views/medic_stock_views.xml',
        'views/medic_sale_order.xml',
        'views/medic_hr_employee_view.xml',
        'views/medic_contract_schedule.xml',
        'patient/views/dham_patient.xml',
        'views/run_one_time_function.xml',
    ],
    # only loaded in demonstration mode
    'qweb': ['static/src/xml/*.xml'],

    'demo': [
    ],
    'installable': True,
}