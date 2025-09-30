{
    'name': 'C10i Purchase Dashboard',
    'version': '14.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Dashboard for Purchase Orders using base dashboard cards',
    'description': """
Purchase Dashboard Module
========================
This module provides comprehensive purchase order analytics with:
- Pie chart for orders by product category
- Bar chart for vendor order counts
- Line chart for amount trends per category
- Top vendors by total amount

Uses Chart.js for interactive visualizations.
    """,
    'author': 'Your Company',
    'depends': ['purchase', 'c10i_base_dashboard', 'web'],
    'data': [
        'views/assets.xml',
        'views/purchase_dashboard.xml',
    ],
    'qweb': [
        'static/src/xml/purchase_dashboard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}