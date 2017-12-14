# -*- coding: utf-8 -*-
{
    'name': "DHA Medic GIS",

    'summary': """
        Show position customer""",

    'description': """
        Show position customer
    """,

    'author': "DHA Medic / Viet",
    'website': "http://www.dhamedic.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHAMEDIC',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','web','dha_medic_modifier'],

    # always loaded
    'data': [
        'data/partner_type_data.xml',
        # 'security/ir.model.access.csv',
        'views/templates.xml',
        'views/res_partner.xml',
    ],
}