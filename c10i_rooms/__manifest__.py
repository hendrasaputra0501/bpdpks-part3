# -*- coding: utf-8 -*-
{
    'name': "c10i_rooms",

    'summary': """
        Booking Room Management
    """,

    'description': """
        Booking Room Management
    """,

    'author': "PT Konsalten Solusi Indonesia",
    'website': "http://www.konsaltensolsindonesia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'web_gantt'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'views/room_views.xml',
        'views/room_booking_views.xml',
        'views/room_menu_views.xml',


        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
