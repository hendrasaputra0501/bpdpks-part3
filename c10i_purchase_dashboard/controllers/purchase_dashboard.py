from odoo import http
from odoo.http import request
import json
from collections import defaultdict
from datetime import datetime

class PurchaseDashboardController(http.Controller):
    
    def _get_base_domain(self, filters=None):
        """Build base domain from filters"""
        domain = [('state', 'in', ('purchase', 'done'))]
        
        if not filters:
            return domain
            
        # Date filters
        if filters.get('date_start'):
            domain.append(('date_order', '>=', filters['date_start']))
        if filters.get('date_end'):
            domain.append(('date_order', '<=', filters['date_end']))
        
        # Vendor filter
        if filters.get('vendor_ids') and len(filters['vendor_ids']) > 0:
            domain.append(('partner_id', 'in', filters['vendor_ids']))
            
        return domain
    
    def _get_product_domain(self, filters=None):
        """Build product domain from filters"""
        product_domain = []
        
        # Products filter
        if filters and filters.get('product_ids') and len(filters['product_ids']) > 0:
            product_domain.append(('id', 'in', filters['product_ids']))
            
        # Category filter
        if filters and filters.get('category_ids') and len(filters['category_ids']) > 0:
            product_domain.append(('categ_id', 'in', filters['category_ids']))
            
        return product_domain

    @http.route('/purchase_dashboard/product_category_pie', type='json', auth='user')
    def get_product_category_pie_data(self, **filters):
        """Pie Chart based on Product Category"""
        base_domain = self._get_base_domain(filters)
        product_domain = self._get_product_domain(filters)
        
        # Build query with filters - include category IDs for drill-down
        query = """
            SELECT pc.name as category_name, pc.id as category_id, 
                   COUNT(DISTINCT po.id) as order_count,
                   ARRAY_AGG(DISTINCT po.id) as order_ids
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            JOIN product_product pp ON pp.id = pol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN product_category pc ON pc.id = pt.categ_id
            WHERE po.state IN ('purchase', 'done')
        """
        params = []
        
        # Add date filters
        if filters.get('date_from'):
            query += " AND po.date_order >= %s"
            params.append(filters['date_from'])
        if filters.get('date_to'):
            query += " AND po.date_order <= %s"
            params.append(filters['date_to'])
            
        # Add vendor filter
        if filters.get('vendor_ids') and len(filters['vendor_ids']) > 0:
            query += " AND po.partner_id = ANY(%s)"
            params.append(filters['vendor_ids'])
            
        # Add products filter
        if filters.get('product_ids') and len(filters['product_ids']) > 0:
            query += " AND pp.id = ANY(%s)"
            params.append(filters['product_ids'])
            
        # Add category filter
        if filters.get('category_ids') and len(filters['category_ids']) > 0:
            query += " AND pc.id = ANY(%s)"
            params.append(filters['category_ids'])
        
        query += " GROUP BY pc.name, pc.id ORDER BY order_count DESC LIMIT 10"
        
        request.env.cr.execute(query, params)
        results = request.env.cr.fetchall()
        
        dataset = []
        labels = []
        data = []
        record_ids = []
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF8C42', '#6C5CE7', '#A29BFE', '#00B894']
        
        for i, (category_name, category_id, count, order_ids) in enumerate(results):
            labels.append(category_name)
            data.append(count)
            record_ids.append({
                'category_id': category_id,
                'category_name': category_name,
                'order_ids': order_ids,
                'order_count': count
            })
            dataset.append({
                'label': category_name,
                'value': count,
                'color': colors[i % len(colors)],
                'category_id': category_id,
                'order_ids': order_ids
            })
        
        return {
            'dataset': dataset,
            'labels': labels,
            'data': data,
            'record_ids': record_ids,
            'colors': colors[:len(results)],
            'options': {
                'title': 'Purchase Orders by Product Category',
                'canvas_id': 'product_category_pie_chart',
                'type': 'pie'
            },
            'style': {
                'backgroundColor': colors[:len(results)]
            }
        }

    @http.route('/purchase_dashboard/vendor_orders_bar', type='json', auth='user')
    def get_vendor_orders_bar_data(self, **filters):
        """Bar Chart based on Vendor Orders Count"""
        query = """
            SELECT rp.name as vendor_name, rp.id as vendor_id, 
                   COUNT(po.id) as order_count,
                   ARRAY_AGG(po.id) as order_ids
            FROM purchase_order po
            JOIN res_partner rp ON rp.id = po.partner_id
            WHERE po.state IN ('purchase', 'done')
        """
        params = []
        
        # Add date filters
        if filters.get('date_start'):
            query += " AND po.date_order >= %s"
            params.append(filters['date_start'])
        if filters.get('date_end'):
            query += " AND po.date_order <= %s"
            params.append(filters['date_end'])
            
        # Add vendor filter
        if filters.get('vendor_ids') and len(filters['vendor_ids']) > 0:
            query += " AND po.partner_id = ANY(%s)"
            params.append(filters['vendor_ids'])
        
        # Add products filter via order lines
        if filters.get('product_ids') and len(filters['product_ids']) > 0:
            query += """ AND EXISTS (
                SELECT 1 FROM purchase_order_line pol2 
                WHERE pol2.order_id = po.id
                AND pol2.product_id = ANY(%s)
            )"""
            params.append(filters['product_ids'])
            
        # Add category filter via order lines
        if filters.get('category_ids') and len(filters['category_ids']) > 0:
            query += """ AND EXISTS (
                SELECT 1 FROM purchase_order_line pol3
                JOIN product_product pp3 ON pp3.id = pol3.product_id
                JOIN product_template pt3 ON pt3.id = pp3.product_tmpl_id
                WHERE pol3.order_id = po.id
                AND pt3.categ_id = ANY(%s)
            )"""
            params.append(filters['category_ids'])
        
        query += " GROUP BY rp.name, rp.id ORDER BY order_count DESC LIMIT 10"
        
        request.env.cr.execute(query, params)
        results = request.env.cr.fetchall()
        
        labels = []
        data = []
        record_ids = []
        
        for vendor_name, vendor_id, order_count, order_ids in results:
            labels.append(vendor_name)
            data.append(order_count)
            record_ids.append({
                'vendor_id': vendor_id,
                'vendor_name': vendor_name,
                'order_ids': order_ids,
                'order_count': order_count
            })
        
        return {
            'dataset': results,
            'labels': labels,
            'data': data,
            'record_ids': record_ids,
            'options': {
                'title': 'Purchase Orders Count by Vendor',
                'canvas_id': 'vendor_orders_bar_chart',
                'type': 'bar'
            },
            'style': {
                'backgroundColor': '#36A2EB',
                'borderColor': '#1E88E5',
                'borderWidth': 1
            }
        }

    @http.route('/purchase_dashboard/amount_per_category_line', type='json', auth='user')
    def get_amount_per_category_line_data(self, **filters):
        """Line chart based on Amount per Product Category over time"""
        query = """
            SELECT 
                pc.name as category_name,
                DATE_TRUNC('month', po.date_order) as order_month,
                SUM(po.amount_total) as total_amount
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            JOIN product_product pp ON pp.id = pol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN product_category pc ON pc.id = pt.categ_id
            WHERE po.state IN ('purchase', 'done')
        """
        params = []
        
        # Add date filters (default to last 6 months if not provided)
        if filters.get('date_start'):
            query += " AND po.date_order >= %s"
            params.append(filters['date_start'])
        else:
            query += " AND po.date_order >= NOW() - INTERVAL '6 months'"
            
        if filters.get('date_end'):
            query += " AND po.date_order <= %s"
            params.append(filters['date_end'])
            
        # Add vendor filter
        if filters.get('vendor_ids') and len(filters['vendor_ids']) > 0:
            query += " AND po.partner_id = ANY(%s)"
            params.append(filters['vendor_ids'])
            
        # Add products filter
        if filters.get('product_ids') and len(filters['product_ids']) > 0:
            query += " AND pp.id = ANY(%s)"
            params.append(filters['product_ids'])
            
        # Add category filter
        if filters.get('category_ids') and len(filters['category_ids']) > 0:
            query += " AND pc.id = ANY(%s)"
            params.append(filters['category_ids'])
        
        query += " GROUP BY pc.name, DATE_TRUNC('month', po.date_order) ORDER BY order_month, pc.name"
        
        request.env.cr.execute(query, params)
        results = request.env.cr.fetchall()
        
        # Organize data by category
        categories = {}
        months = set()
        
        for category, month, amount in results:
            if category not in categories:
                categories[category] = {}
            month_str = month.strftime('%Y-%m')
            categories[category][month_str] = float(amount)
            months.add(month_str)
        
        months = sorted(list(months))
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
        datasets = []
        
        for i, (category, data_points) in enumerate(categories.items()):
            dataset_data = [data_points.get(month, 0) for month in months]
            datasets.append({
                'label': category,
                'data': dataset_data,
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)],
                'fill': False
            })
        
        return {
            'datasets': datasets,
            'labels': months,
            'options': {
                'title': 'Purchase Amount per Category',
                'canvas_id': 'amount_per_category_line_chart',
                'type': 'line'
            },
            'style': {
                'tension': 0.1
            }
        }

    @http.route('/purchase_dashboard/top_vendors', type='json', auth='user')
    def get_top_vendors_data(self, **filters):
        """Top Vendor by Amount"""
        query = """
            SELECT 
                rp.name as vendor_name,
                rp.id as vendor_id,
                COUNT(po.id) as order_count,
                SUM(po.amount_total) as total_amount,
                AVG(po.amount_total) as avg_amount,
                ARRAY_AGG(po.id) as order_ids
            FROM purchase_order po
            JOIN res_partner rp ON rp.id = po.partner_id
            WHERE po.state IN ('purchase', 'done')
        """
        params = []
        
        # Add date filters
        if filters.get('date_start'):
            query += " AND po.date_order >= %s"
            params.append(filters['date_start'])
        if filters.get('date_end'):
            query += " AND po.date_order <= %s"
            params.append(filters['date_end'])
            
        # Add products filter via order lines
        if filters.get('product_ids') and len(filters['product_ids']) > 0:
            query += """ AND EXISTS (
                SELECT 1 FROM purchase_order_line pol2 
                WHERE pol2.order_id = po.id
                AND pol2.product_id = ANY(%s)
            )"""
            params.append(filters['product_ids'])
            
        # Add category filter via order lines
        if filters.get('category_ids') and len(filters['category_ids']) > 0:
            query += """ AND EXISTS (
                SELECT 1 FROM purchase_order_line pol3
                JOIN product_product pp3 ON pp3.id = pol3.product_id
                JOIN product_template pt3 ON pt3.id = pp3.product_tmpl_id
                WHERE pol3.order_id = po.id
                AND pt3.categ_id = ANY(%s)
            )"""
            params.append(filters['category_ids'])
        
        query += " GROUP BY rp.name, rp.id ORDER BY total_amount DESC LIMIT 5"
        
        request.env.cr.execute(query, params)
        results = request.env.cr.fetchall()
        
        dataset = []
        record_ids = []
        for vendor_name, vendor_id, order_count, total_amount, avg_amount, order_ids in results:
            dataset.append({
                'vendor_name': vendor_name,
                'order_count': order_count,
                'total_amount': float(total_amount),
                'avg_amount': float(avg_amount)
            })
            record_ids.append({
                'vendor_id': vendor_id,
                'vendor_name': vendor_name,
                'order_ids': order_ids,
                'order_count': order_count,
                'total_amount': float(total_amount)
            })
        
        labels = [item['vendor_name'] for item in dataset]
        data = [item['total_amount'] for item in dataset]
        
        return {
            'dataset': dataset,
            'record_ids': record_ids,
            'labels': labels,
            'data': data,
            'options': {
                'title': 'Top 5 Vendors by Total Amount',
                'canvas_id': 'top_vendors_chart',
                'type': 'bar'
            },
            'style': {
                'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
                'borderColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
                'borderWidth': 1
            }
        }

    @http.route('/purchase_dashboard/chart_drill_down', type='json', auth='user')
    def chart_drill_down(self, chart_type=None, record_data=None, **kwargs):
        """Handle chart drill-down actions to show detailed data"""
        if not chart_type or not record_data:
            return {'error': 'Missing chart_type or record_data'}
        
        # Get purchase orders based on the clicked chart data
        domain = [('state', 'in', ('purchase', 'done'))]
        
        if 'order_ids' in record_data and record_data['order_ids']:
            domain.append(('id', 'in', record_data['order_ids']))
        
        # Fetch purchase orders
        purchase_orders = request.env['purchase.order'].search(domain, limit=100)
        
        # Prepare data for display
        orders_data = []
        for order in purchase_orders:
            orders_data.append({
                'id': order.id,
                'name': order.name,
                'partner_name': order.partner_id.name,
                'date_order': order.date_order.strftime('%Y-%m-%d') if order.date_order else '',
                'amount_total': order.amount_total,
                'state': order.state,
                'currency': order.currency_id.symbol,
                'order_lines_count': len(order.order_line),
            })
        
        return {
            'success': True,
            'chart_type': chart_type,
            'record_data': record_data,
            'orders': orders_data,
            'orders_count': len(orders_data),
            'title': self._get_drill_down_title(chart_type, record_data)
        }
    
    def _get_drill_down_title(self, chart_type, record_data):
        """Generate title for drill-down popup based on chart type"""
        if chart_type == 'product_category_pie':
            return f"Purchase Orders for Category: {record_data.get('category_name', 'Unknown')}"
        elif chart_type == 'vendor_orders_bar':
            return f"Purchase Orders for Vendor: {record_data.get('vendor_name', 'Unknown')}"
        elif chart_type == 'top_vendors':
            return f"Purchase Orders for Top Vendor: {record_data.get('vendor_name', 'Unknown')}"
        else:
            return "Purchase Orders Details"

    @http.route('/purchase_dashboard/rfq_counts', type='json', auth='user')
    def get_rfq_counts(self, **filter):
        """Get purchase order counts by status"""
        # Get filter values
        date_from = filter.get('date_from')
        date_to = filter.get('date_to')
        vendor_ids = filter.get('vendor_ids', [])
        category_ids = filter.get('category_ids', [])

        # Build domain
        domain = [('state','in',['draft','sent','to approve'])]
        # if date_from:
        #     domain.append(('date_order', '>=', date_from))
        # if date_to:
        #     domain.append(('date_order', '<=', date_to))
        if vendor_ids:
            domain.append(('partner_id', 'in', vendor_ids))

        rfq = request.env['purchase.order'].search(domain)

        return {
                'count': len(rfq.ids),
                'order_ids': rfq.ids if rfq else [],
                'title': 'RFQ',
                'subtitle': 'Draft, Sent, To Approve'
        }

    @http.route('/purchase_dashboard/order_counts', type='json', auth='user')
    def get_order_counts(self, **filter):
        """Get purchase order counts by status"""
        # Get filter values
        date_from = filter.get('date_from')
        date_to = filter.get('date_to')
        vendor_ids = filter.get('vendor_ids', [])
        category_ids = filter.get('category_ids', [])

        # Build domain
        domain = [('state','=','purchase')]
        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            domain.append(('date_order', '<=', date_to))
        if vendor_ids:
            domain.append(('partner_id', 'in', vendor_ids))

        purchase_orders = request.env['purchase.order'].search(domain)
        return {
                'count': len(purchase_orders), 
                'order_ids': purchase_orders.ids if purchase_orders else [],
                'title': 'Purchase Orders',
                'subtitle': 'Purchase Order, Done'
        }

    @http.route('/purchase_dashboard/pending_orders_list', type='json', auth='user')
    def get_pending_orders_list(self, **filters):
        """Get pending purchase orders list for ListCard"""
        # Build domain for pending orders
        domain = [('state', '=', 'purchase'),('invoice_status', '=', 'to invoice')]
        
        # Add date filters
        # if filters.get('date_from'):
        #     domain.append(('date_order', '>=', filters['date_from']))
        # if filters.get('date_to'):
        #     domain.append(('date_order', '<=', filters['date_to']))
            
        # Add vendor filter
        if filters.get('vendor_ids') and len(filters['vendor_ids']) > 0:
            domain.append(('partner_id', 'in', filters['vendor_ids']))
        
        # Fetch pending orders
        purchase_orders = request.env['purchase.order'].search(domain, 
                                            order='date_order desc', 
                                            limit=50)
        
        # Prepare data for ListCard
        orders_data = []
        for order in purchase_orders:
            orders_data.append({
                'id': order.id,
                'name': order.name,
                'partner_name': order.partner_id.name,
                'date_order': order.date_order.strftime('%Y-%m-%d') if order.date_order else '',
                'amount_total': f"{order.amount_total:,.2f}",
                'state': order.state.title(),
                'state_color': self._getStateColor(order.state),
                'currency_symbol': order.currency_id.symbol,
                'lines_count': len(order.order_line),
            })
        
        # Define columns for the list
        columns = [
            {'field': 'name', 'title': 'Reference', 'type': 'text'},
            {'field': 'partner_name', 'title': 'Vendor', 'type': 'text'},
            {'field': 'date_order', 'title': 'Order Date', 'type': 'date'},
            {'field': 'amount_total', 'title': 'Total', 'type': 'currency', 'align': 'right'},
            {'field': 'state', 'title': 'Status', 'type': 'badge', 'align': 'center'},
        ]
        
        return {
            'data': orders_data,
            'columns': columns,
            'total_count': len(orders_data)
        }
    
    @http.route('/purchase_dashboard/vendor_hierarchy_list', type='json', auth='user')
    def get_vendor_hierarchy_list(self, **filters):
        """Get vendor hierarchy list with their purchase orders"""
        # Build domain
        domain = [('state', 'in', ['purchase', 'done'])]
        
        # Add date filters
        if filters.get('date_from'):
            domain.append(('date_order', '>=', filters['date_from']))
        if filters.get('date_to'):
            domain.append(('date_order', '<=', filters['date_to']))
        
        # Fetch orders and group by vendor
        purchase_orders = request.env['purchase.order'].search(domain, order='partner_id, date_order desc')
        
        # Group orders by vendor
        vendors_data = {}
        for order in purchase_orders:
            vendor_id = order.partner_id.id
            if vendor_id not in vendors_data:
                vendors_data[vendor_id] = {
                    'id': f'vendor_{vendor_id}',
                    'name': order.partner_id.name,
                    'partner_name': f"{len([o for o in purchase_orders if o.partner_id.id == vendor_id])} orders",
                    'date_order': '',
                    'amount_total': f"{sum(o.amount_total for o in purchase_orders if o.partner_id.id == vendor_id):,.2f}",
                    'state': 'Vendor',
                    'state_color': 'info',
                    'currency_symbol': order.currency_id.symbol,
                    'children': [],
                    'level': 0,
                }
            
            # Add order as child
            vendors_data[vendor_id]['children'].append({
                'id': order.id,
                'name': order.name,
                'partner_name': order.partner_id.name,
                'date_order': order.date_order.strftime('%Y-%m-%d') if order.date_order else '',
                'amount_total': f"{order.amount_total:,.2f}",
                'state': order.state.title(),
                'state_color': self._getStateColor(order.state),
                'currency_symbol': order.currency_id.symbol,
                'level': 1,
            })
        
        # Define columns
        columns = [
            {'field': 'name', 'title': 'Reference/Vendor', 'type': 'text'},
            {'field': 'partner_name', 'title': 'Details', 'type': 'text'},
            {'field': 'date_order', 'title': 'Date', 'type': 'date'},
            {'field': 'amount_total', 'title': 'Amount', 'type': 'currency', 'align': 'right'},
            {'field': 'state', 'title': 'Status', 'type': 'badge', 'align': 'center'},
        ]
        
        return {
            'data': list(vendors_data.values()),
            'columns': columns,
            'is_hierarchy': True,
            'total_count': len(vendors_data)
        }
    
    @http.route('/purchase_dashboard/purchase_amount_kpi', type='json', auth='user')
    def get_purchase_amount_kpi(self, **filters):
        """KPI data for Purchase Order Amount vs Target"""
        base_domain = self._get_base_domain(filters)
        
        # Get total purchase order amount
        orders = request.env['purchase.order'].search(base_domain)
        total_amount = sum(orders.mapped('amount_total'))
        
        # Get current company currency
        currency = request.env.user.company_id.currency_id
        currency_symbol = currency.symbol or currency.name
        
        # For demo purposes, set target based on current date
        # In a real scenario, this should come from company settings or budget
        from datetime import datetime
        current_month = datetime.now().month
        target_amount = 100000 * current_month  # Example: increasing target by month
        
        # Format amounts for display
        formatted_actual = f"{currency_symbol} {total_amount:,.2f}"
        formatted_target = f"{currency_symbol} {target_amount:,.2f}"
        
        return {
            'actual_value': total_amount,
            'actual_label': formatted_actual,
            'target': target_amount,
            'target_label': formatted_target,
            'currency_symbol': currency_symbol
        }
    
    @http.route('/purchase_dashboard/vendor_mapping', type='json', auth='user')
    def get_vendor_mapping_data(self, **filters):
        """Map data for Vendor Locations"""
        # Get purchase orders with vendor location data
        vendors = request.env['res.partner'].search([])
        
        vendor_locations = []
        for vendor in vendors:
            # Skip vendors without location data
            if not vendor.partner_latitude or not vendor.partner_longitude:
                continue
                
            # Count orders for this vendor
            order_count = 10
            total_amount = 10000000
            
            # Get currency symbol
            currency = request.env.user.company_id.currency_id
            currency_symbol = currency.symbol or currency.name
            
            vendor_locations.append({
                'id': vendor.id,
                'name': vendor.name,
                'latitude': float(vendor.partner_latitude),
                'longitude': float(vendor.partner_longitude),
                'city': vendor.city or '',
                'country': vendor.country_id.name if vendor.country_id else '',
                'email': vendor.email or '',
                'phone': vendor.phone or '',
            })
        
        # grouped_locations = defaultdict(list)
        # for vendor_loc in vendor_locations:
        #     key = (vendor_loc['latitude'], vendor_loc['longitude'])
        #     if key not in grouped_locations:
        #         grouped_locations[key] = {
        #             'latitude': vendor_loc['latitude'],
        #             'longitude': vendor_loc['longitude'],
        #             'vendors': [],
        #             'count': 0
        #         }
        #     grouped_locations[key]['vendors'].append(vendor_loc)
        #     grouped_locations[key]['count'] += 1

        return {
            'locations': list(vendor_locations),
            # 'locations': list(grouped_locations.values()),
            'total_vendors': len(vendor_locations),
        }
    
    def _getStateColor(self, state):
        """Get color class for purchase order state"""
        state_colors = {
            'draft': 'secondary',
            'sent': 'info',
            'to approve': 'warning',
            'purchase': 'primary',
            'done': 'success',
            'cancel': 'danger'
        }
        return state_colors.get(state, 'secondary')
