{
    'name': 'C10i Legal Cases',
    'version': '14.1',
    'category': 'Application',
    'summary': 'Legal Cases for BPDP',
    'description': """
Legal Cases for BPDP
    """,
    'author': 'Konsalten',
    'depends': ['base','mail','portal'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/legal_case_jenis_view.xml',
        'views/legal_case_classification_view.xml',
        'views/legal_case_type_view.xml',
        'views/legal_case_view.xml',

        # 'views/purchase_dashboard.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}