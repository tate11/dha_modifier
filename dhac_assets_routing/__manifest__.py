# -*- coding: utf-8 -*-
{
    'name': "dhac_assets_routing",

    'description': """
        Add routing functional for Assets
            - From Purchase Request -> RFQ -> PO -> Invoice -> Create Asset
    """,

    'author': "DHA / Vu",
    'website': "http://www.dhacorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'DHA',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'asset', 'account_asset', 'report'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/asset_security.xml',
        'views/asset_seq.xml',
        'views/asset_asset_views.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],

    'demo': [
    ],
}
