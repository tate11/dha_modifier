# -*- coding: utf-8 -*-
{
    'name': "dhac_double_approve_pr",

    'description': """
        Add double approval for Purchase Request
        Sent notification to approver
        
        Create a purchase request will sent out a notification via email base on Department follower
        Request Approve to sent notification via email for Approver Lv 2
        
        Create purchase leader group, add state accept vendor, sent notification per level approval.
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhacorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHA',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase_request', 'purchase_request_to_rfq', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_request_security.xml',
        'security/purchase_order_security.xml',
        'data/data.xml',
        'views/product_category_views.xml',
        'views/purchase_request_views.xml',
        'views/purchase_order.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],

    'demo': [
    ],
}