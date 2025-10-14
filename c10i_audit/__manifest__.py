# -*- coding: utf-8 -*-
{
    'name': "c10i_audit",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "PT. Konsalten Solusi Indonesia",
    'website': "http://www.konsaltensolsindonesia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'mail', 'portal'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        
        # data stage (status pada form audit)
        'data/audit_stage_data.xml',

        'views/audit_audit_views.xml',
        'views/document_request_views.xml',
        'views/findings_views.xml',
        'views/discuss_note_views.xml',
        'views/menu_views.xml',

        # View untuk user portal
        'views/portal_templates.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
