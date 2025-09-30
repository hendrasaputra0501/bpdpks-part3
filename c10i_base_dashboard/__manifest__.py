# -*- coding: utf-8 -*-
{
    'name': 'C10i Base Dashboard',
    'version': '14.0.1.0.0',
    'category': 'Tools',
    'summary': 'Base dashboard components for reusable dashboard cards',
    'description': """
Base Dashboard Module
====================
This module provides reusable dashboard components including:
- Chart Type Cards
- KPI Cards
- Generic Dashboard Framework
- Common dashboard utilities

This module serves as a foundation for other specific dashboard modules.
    """,
    'author': 'C10i Solutions',
    'website': 'https://www.c10i.com',
    'depends': ['base', 'web'],
    'data': [
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard_card.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}