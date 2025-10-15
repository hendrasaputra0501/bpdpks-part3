# -*- coding: utf-8 -*-
{
    'name': "bpdpks_bank_statement_integration_status",

    'summary': """ Module bank statement integration status """,

    'description': """
        Long description of module's purpose
    """,

    'author': "PT. Konsalten Solusi Indonesia",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'bpdpks_operation'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/bank_statement_api_status_views.xml',
        'views/account_journal_views.xml',

        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
