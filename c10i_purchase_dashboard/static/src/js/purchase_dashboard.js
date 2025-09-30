odoo.define('c10i_purchase_dashboard.PurchaseDashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var DashboardCard = require('c10i_base_dashboard.DashboardCard');
    var ChartCard = DashboardCard.ChartCard;
    var StatusCard = DashboardCard.StatusCard;
    var ListCard = DashboardCard.ListCard;
    var KpiCard = DashboardCard.KpiCard;
    var MapCard = DashboardCard.MapCard;
    var core = require('web.core');
    var datepicker = require('web.datepicker');
    var field_utils = require('web.field_utils');
    var RelationalFields = require('web.relational_fields');
    var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
    var WarningDialog = require('web.CrashManager').WarningDialog;
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    // M2M Filter Widget for Purchase Dashboard
    var PurchaseM2MFilters = Widget.extend(StandaloneFieldManagerMixin, {
        init: function (parent, fields) {
            this._super.apply(this, arguments);
            StandaloneFieldManagerMixin.init.call(this);
            this.fields = fields;
            this.widgets = {};
        },
        
        willStart: function () {
            var self = this;
            var defs = [this._super.apply(this, arguments)];
            _.each(this.fields, function (field, fieldName) {
                defs.push(self._makeM2MWidget(field, fieldName));
            });
            return Promise.all(defs);
        },
        
        start: function () {
            var self = this;
            var $content = $(QWeb.render("purchase_m2mWidgetTable", {fields: this.fields}));
            self.$el.append($content);
            _.each(this.fields, function (field, fieldName) {
                self.widgets[fieldName].appendTo($content.find('#'+fieldName+'_field'));
            });
            return this._super.apply(this, arguments);
        },

        _confirmChange: function () {
            var self = this;
            var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
            var data = {};
            _.each(this.fields, function (filter, fieldName) {
                data[fieldName] = self.widgets[fieldName].value.res_ids;
            });
            this.trigger_up('value_changed', data);
            return result;
        },
        
        _makeM2MWidget: function (fieldInfo, fieldName) {
            var self = this;
            var options = {};
            options[fieldName] = {
                options: {
                    no_create_edit: true,
                    no_create: true,
                }
            };
            
            var fieldType = fieldInfo.fieldType || 'many2many';
            var widgetClass = fieldType === 'many2one' ? 
                RelationalFields.FieldMany2One : RelationalFields.FieldMany2ManyTags;
            
            return this.model.makeRecord(fieldInfo.modelName, [{
                fields: [{
                    name: 'id',
                    type: 'integer',
                }, {
                    name: 'display_name',
                    type: 'char',
                }],
                name: fieldName,
                relation: fieldInfo.modelName,
                type: fieldType,
                value: fieldInfo.value,
            }], options).then(function (recordID) {
                self.widgets[fieldName] = new widgetClass(self,
                    fieldName,
                    self.model.get(recordID),
                    {mode: 'edit'}
                );
                self._registerWidget(recordID, fieldName, self.widgets[fieldName]);
            });
        },
    });

    var PurchaseDashboard = AbstractAction.extend({
        template: 'c10i_purchase_dashboard.Dashboard',
        events: {
            'click .js_date_filter': '_onDateFilterClick',
            'click .js_foldable_trigger': '_onFoldableClick',
            'click .separator-header': '_onSeparatorClick',
        },
        
        custom_events: {
            'value_changed': function(ev) {
                var self = this;
                self.filter_options.vendor_ids = ev.data.vendor_ids || this.filter_options.vendor_ids;
                self.filter_options.product_ids = ev.data.product_ids || this.filter_options.product_ids;
                self.filter_options.category_ids = ev.data.category_ids || this.filter_options.category_ids;
                return self._loadAllCharts();
            },
        },
        
        init: function(parent, action) {
            this._super(parent, action);
            this.dashboardCards = [];
            this.filter_options = {
                date_filter: 'this_month',
                date_from: null,
                date_to: null,
                vendor_ids: [],
                product_ids: [],
                category_ids: [],
            };
            this.M2MFilters = {};
        },
        
        start: function () {
            var self = this;
            return this._super().then(function () {
                self._initializeSeparators();
                return self._setupFilters().then(function() {
                    return self._loadAllCharts();
                });
            });
        },

        _initializeSeparators: function() {
            // Initialize all separators in expanded state
            this.$('.separator-toggle').removeClass('collapsed');
            this.$('.dashboard-section').removeClass('collapsed collapsing');
        },

        _setupFilters: function() {
            var self = this;
            
            // Setup date filters with default values
            this._setDefaultDateRange();
            this._setupDatePickers();
            
            // Setup vendor filter (Many2Many)
            var vendorDef = this._setupVendorFilter();
            
            // Setup category filter (Many2Many) 
            var categoryDef = this._setupCategoryFilter();
            
            // Setup product filter (Many2Many)
            var productDef = this._setupProductFilter();
            
            return Promise.all([vendorDef, categoryDef, productDef]);
        },

        _setDefaultDateRange: function() {
            var today = moment();
            var dateFrom = today.clone().startOf('month');
            var dateTo = today.clone().endOf('month');

            this.filter_options.date_from = dateFrom.format('YYYY-MM-DD');
            this.filter_options.date_to = dateTo.format('YYYY-MM-DD');
        },

        _setupDatePickers: function() {
            var self = this;
            var $datetimepickers = this.$('.js_account_reports_datetimepicker');
            var options = {
                locale : moment.locale(),
                format : 'L',
                icons: {
                    date: "fa fa-calendar",
                },
            };
            
            $datetimepickers.each(function () {
                var name = $(this).find('input').attr('name');
                var dt = new datepicker.DateWidget(options);
                dt.replace($(this)).then(function () {
                    dt.$el.find('input').attr('name', name);
                    if (name === 'date_from') {
                        dt.setValue(moment(self.filter_options.date_from));
                    } else if (name === 'date_to') {
                        dt.setValue(moment(self.filter_options.date_to));
                    }
                });
            });
        },

        _setupVendorFilter: function() {
            var self = this;
            if (!this.M2MFilters.vendor) {
                var fields = {
                    'vendor_ids': {
                        label: _t('Vendors'),
                        modelName: 'res.partner',
                        value: this.filter_options.vendor_ids,
                        fieldType: 'many2many'
                    }
                };
                this.M2MFilters.vendor = new PurchaseM2MFilters(this, fields);
                return this.M2MFilters.vendor.appendTo(this.$('.js_vendor_m2m'));
            }
            return Promise.resolve();
        },

        _setupCategoryFilter: function() {
            var self = this;
            if (!this.M2MFilters.category) {
                var fields = {
                    'category_ids': {
                        label: _t('Product Categories'),
                        modelName: 'product.category',
                        value: this.filter_options.category_ids,
                        fieldType: 'many2many'
                    }
                };
                this.M2MFilters.category = new PurchaseM2MFilters(this, fields);
                return this.M2MFilters.category.appendTo(this.$('.js_category_m2m'));
            }
            return Promise.resolve();
        },

        _setupProductFilter: function() {
            var self = this;
            if (!this.M2MFilters.product) {
                var fields = {
                    'product_ids': {
                        label: _t('Products'),
                        modelName: 'product.product',
                        value: this.filter_options.product_ids,
                        fieldType: 'many2many'
                    }
                };
                this.M2MFilters.product = new PurchaseM2MFilters(this, fields);
                return this.M2MFilters.product.appendTo(this.$('.js_products_m2m'));
            }
            return Promise.resolve();
        },

        _onDateFilterClick: function(event) {
            var self = this;
            var filter = $(event.currentTarget).data('filter');
            this.filter_options.date_filter = filter;
            
            // Remove selected class from all buttons and add to current
            this.$('.js_date_filter').removeClass('selected btn-primary').addClass('btn-outline-secondary');
            $(event.currentTarget).removeClass('btn-outline-secondary').addClass('selected btn-primary');
            
            // Update period display
            this.$('.period-display').text($(event.currentTarget).text());
            
            var error = false;
            if (filter === 'custom') {
                // Show custom date range inputs
                this.$('.custom-date-range').show();
                var date_from = this.$('input[name="date_from"]');
                var date_to = this.$('input[name="date_to"]');
                if (date_from.length > 0) {
                    error = date_from.val() === "" || date_to.val() === "";
                    if (!error) {
                        this.filter_options.date_from = field_utils.parse.date(date_from.val());
                        this.filter_options.date_to = field_utils.parse.date(date_to.val());
                    }
                }
            } else {
                // Hide custom date range inputs
                this.$('.custom-date-range').hide();
                // Calculate date range based on filter
                this._calculateDateRange(filter);
            }
            
            if (error) {
                new WarningDialog(this, {
                    title: _t("Odoo Warning"),
                }, {
                    message: _t("Date cannot be empty")
                }).open();
            } else {
                this._loadAllCharts();
            }
        },

        _onDateInputChange: function(event) {
            var self = this;
            var date_from = this.$('input[name="date_from"]');
            var date_to = this.$('input[name="date_to"]');
            var error = date_from === "" || date_to === "";
            if (error) {
                new WarningDialog(this, {
                    title: _t("Odoo Warning"),
                }, {
                    message: _t("Date cannot be empty")
                }).open();
            } else {
                this.filter_options.date_from = field_utils.parse.date(date_from);
                this.filter_options.date_to = field_utils.parse.date(date_to);
                this._loadAllCharts();
            }
        },

        _calculateDateRange: function(filter) {
            var today = moment();
            var dateFrom, dateTo;
            
            switch(filter) {
                case 'today':
                    dateFrom = dateTo = today;
                    break;
                case 'this_week':
                    dateFrom = today.clone().startOf('week');
                    dateTo = today.clone().endOf('week');
                    break;
                case 'this_month':
                    dateFrom = today.clone().startOf('month');
                    dateTo = today.clone().endOf('month');
                    break;
                case 'this_quarter':
                    dateFrom = today.clone().startOf('quarter');
                    dateTo = today.clone().endOf('quarter');
                    break;
                case 'this_year':
                    dateFrom = today.clone().startOf('year');
                    dateTo = today.clone().endOf('year');
                    break;
                case 'last_month':
                    dateFrom = today.clone().subtract(1, 'month').startOf('month');
                    dateTo = today.clone().subtract(1, 'month').endOf('month');
                    break;
                case 'last_6_months':
                default:
                    // dateFrom = today.clone().subtract(6, 'months');
                    // dateTo = today;
                    dateFrom = today.clone().startOf('month');
                    dateTo = today.clone().endOf('month');
                    break;
            }
            
            this.filter_options.date_from = dateFrom.format('YYYY-MM-DD');
            this.filter_options.date_to = dateTo.format('YYYY-MM-DD');
        },

        _onFoldableClick: function(event) {
            event.preventDefault();
            $(event.currentTarget).toggleClass('o_closed_menu o_open_menu');
            this.$('.o_foldable_menu[data-filter="'+$(event.currentTarget).data('filter')+'"]').toggle();
        },

        _onSeparatorClick: function(event) {
            event.preventDefault();
            var $header = $(event.currentTarget);
            var $toggle = $header.find('.separator-toggle');
            var sectionName = $header.closest('.dashboard-separator').data('section');
            var $sections = this.$('.dashboard-section[data-section="' + sectionName + '"]');
            
            // Toggle the collapsed state
            var isCollapsed = $toggle.hasClass('collapsed');
            
            if (isCollapsed) {
                // Expand
                $toggle.removeClass('collapsed');
                $sections.removeClass('collapsed');
                $sections.slideDown();
                $sections.removeClass('collapsing');
                
                // Animate expansion
                // $sections.each(function() {
                //     var $section = $(this);
                //     $section.css({
                //         'max-height': 'none',
                //         'opacity': '1',
                //         'margin': '',
                //         'padding': ''
                //     });
                // });
            } else {
                // Collapse
                $toggle.addClass('collapsed');
                $sections.slideUp();
                $sections.addClass('collapsing');
                
                // Animate collapse
                // setTimeout(function() {
                //     $sections.addClass('collapsed');
                // }, 10);
            }
        },

        _getFilterParams: function() {
            return {
                date_from: this.filter_options.date_from,
                date_to: this.filter_options.date_to,
                vendor_ids: this.filter_options.vendor_ids,
                product_ids: this.filter_options.product_ids,
                category_ids: this.filter_options.category_ids,
            };
        },

        _loadAllCharts: function() {
            var self = this;
            // Destroy existing charts
            _.each(this.dashboardCards, function(chartCard) {
                if (chartCard) {
                    chartCard.destroy();
                }
            });
            this.dashboardCards = [];
            
            // Get current filter parameters
            var filterParams = this._getFilterParams();
            console.log("Loading charts with filters:", this.filter_options);
            
            // Reload all charts and status cards with current filters
            return Promise.all([
                self._createRfqCount(filterParams),
                self._createOrderCount(filterParams),
                self._createPurchaseAmountKPI(filterParams),
                self._createVendorMapping(filterParams),
                self._createPendingOrdersList(filterParams),
                self._createVendorHierarchyList(filterParams),
                self._createProductCategoryPieChart(filterParams),
                self._createVendorOrdersBarChart(filterParams),
                self._createAmountPerCategoryLineChart(filterParams),
                self._createTopVendorsChart(filterParams)
            ]);
        },
        
        _createProductCategoryPieChart: function() {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/product_category_pie',
                params: this.filter_options
            }).then(function (result) {
                var chartOptions = {
                    title: result.options.title,
                    canvas_id: 'product_category_pie_chart',
                    onChartClick: function(dataIndex, chartData, options) {
                        self._onChartClick('product_category_pie', dataIndex, result);
                    },
                    data: {
                        type: 'pie',
                        chartData: {
                            labels: result.labels,
                            datasets: [{
                                data: result.data,
                                backgroundColor: result.colors,
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: result.options.title
                                },
                                legend: {
                                    position: 'bottom'
                                },
                                tooltip: {
                                    callbacks: {
                                        afterLabel: function(context) {
                                            return 'Click to view details';
                                        }
                                    }
                                }
                            }
                        }
                    }
                };
                
                var chartCard = new ChartCard(self, chartOptions);
                self.dashboardCards.push(chartCard);
                return chartCard.appendTo(self.$('#chart_container_1'));
            });
        },
        
        _createVendorOrdersBarChart: function() {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/vendor_orders_bar',
                params: this.filter_options
            }).then(function (result) {
                var chartOptions = {
                    title: result.options.title,
                    canvas_id: 'vendor_orders_bar_chart',
                    onChartClick: function(dataIndex, chartData, options) {
                        self._onChartClick('vendor_orders_bar', dataIndex, result);
                    },
                    data: {
                        type: 'bar',
                        chartData: {
                            labels: result.labels,
                            datasets: [{
                                label: 'Order Count',
                                data: result.data,
                                backgroundColor: result.style.backgroundColor,
                                borderColor: result.style.borderColor,
                                borderWidth: result.style.borderWidth
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: result.options.title
                                },
                                tooltip: {
                                    callbacks: {
                                        afterLabel: function(context) {
                                            return 'Click to view details';
                                        }
                                    }
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    }
                };
                
                var chartCard = new ChartCard(self, chartOptions);
                self.dashboardCards.push(chartCard);
                return chartCard.appendTo(self.$('#chart_container_2'));
            });
        },
        
        _createAmountPerCategoryLineChart: function() {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/amount_per_category_line',
                params: this.filter_options
            }).then(function (result) {
                var chartOptions = {
                    title: result.options.title,
                    canvas_id: 'amount_per_category_line_chart',
                    data: {
                        type: 'line',
                        chartData: {
                            labels: result.labels,
                            datasets: result.datasets
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: result.options.title
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    }
                };
                
                var chartCard = new ChartCard(self, chartOptions);
                self.dashboardCards.push(chartCard);
                return chartCard.appendTo(self.$('#chart_container_3'));
            });
        },
        
        _createTopVendorsChart: function() {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/top_vendors',
                params: this.filter_options
            }).then(function (result) {
                var chartOptions = {
                    title: result.options.title,
                    canvas_id: 'top_vendors_chart',
                    onChartClick: function(dataIndex, chartData, options) {
                        self._onChartClick('top_vendors', dataIndex, result);
                    },
                    data: {
                        type: 'bar',
                        chartData: {
                            labels: result.labels,
                            datasets: [{
                                label: 'Total Amount',
                                data: result.data,
                                backgroundColor: result.style.backgroundColor,
                                borderColor: result.style.borderColor,
                                borderWidth: result.style.borderWidth
                            }]
                        },
                        options: {
                            indexAxis: 'y',
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: result.options.title
                                },
                                tooltip: {
                                    callbacks: {
                                        afterLabel: function(context) {
                                            return 'Click to view details';
                                        }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    beginAtZero: true
                                }
                            }
                        }
                    }
                };
                
                var chartCard = new ChartCard(self, chartOptions);
                self.dashboardCards.push(chartCard);
                return chartCard.appendTo(self.$('#chart_container_4'));
            });
        },

        _createRfqCount: function(filterParams) {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/rfq_counts',
                params: filterParams || {}
            }).then(function(result) {
                // Create RFQ Status Card
                var rfqCard = new StatusCard(self, {
                    title: result.title,
                    subtitle: result.subtitle,
                    count: result.count,
                    order_ids: result.order_ids,
                    icon: 'fa-file-text',
                    onClick: function() {
                        self._openStatusRecords(result.order_ids);
                    }
                });
                
                self.dashboardCards.push(rfqCard);
                
                return rfqCard.appendTo(self.$('#status_card_rfq'));
            });
        },

        _createOrderCount: function(filterParams) {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/order_counts',
                params: filterParams || {}
            }).then(function(result) {
                // Create Order Status Card
                var rfqCard = new StatusCard(self, {
                    title: result.title,
                    subtitle: result.subtitle,
                    count: result.count,
                    order_ids: result.order_ids,
                    icon: 'fa-shopping-cart',
                    color: '#33ed3cff',
                    onClick: function() {
                        self._openStatusRecords(result.order_ids);
                    }
                });
                
                self.dashboardCards.push(rfqCard);
                
                return rfqCard.appendTo(self.$('#status_card_purchase'));
            });
        },

        _createPurchaseAmountKPI: function(filterParams) {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/purchase_amount_kpi',
                params: filterParams || {}
            }).then(function(result) {
                // Create KPI Card for Purchase Amount vs Target
                var kpiCard = new KpiCard(self, {
                    title: 'Purchase Amount',
                    header: 'Total Purchase Orders',
                    // footer: 'vs Monthly Target',
                    actualValue: result.actual_value,
                    actualLabel: result.actual_label,
                    target: true,
                    // targetValue: result.target,
                    targetValue: 1000000000,
                    targetLabel: 'Rp 1,000,000,000',
                    percentage: true,
                    percentageValue: Math.round(( result.actual_value / 1000000000 ) * 100),
                    trend: true,
                    trendValue: 'up',
                    headerColor: 'success',
                    icon: 'fa-dollar-sign',
                    onClick: function(clickData) {
                        self.do_action({
                            name: 'Purchase Orders',
                            type: 'ir.actions.act_window',
                            res_model: 'purchase.order',
                            domain: [
                                ('date_order', '>=', filterParams.date_from),
                                ('date_order', '<=', filterParams.date_to),
                                ('state', 'in', ['purchase', 'done'])
                            ],
                            view_mode: 'tree,form',
                            views: [[false, 'list'], [false, 'form']],
                            target: 'current'
                        });
                    }
                });
                
                self.dashboardCards.push(kpiCard);
                
                return kpiCard.appendTo(self.$('#kpi_card_container'));
            });
        },

        _createPendingOrdersList: function(filterParams) {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/pending_orders_list',
                params: filterParams || {}
            }).then(function(result) {
                var listCard = new ListCard(self, {
                    title: 'Pending Purchase Orders',
                    data: result.data,
                    columns: result.columns,
                    is_hierarchy: false,
                    page_size: 15,
                    onItemClick: function(item, $element) {
                        if (item.id && !item.id.toString().startsWith('vendor_')) {
                            self._openPurchaseOrder(item.id);
                        }
                    }
                });
                
                self.dashboardCards.push(listCard);
                return listCard.appendTo(self.$('#list_container_1'));
            });
        },

        _createVendorMapping: function(filterParams) {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/vendor_mapping',
                params: filterParams || {}
            }).then(function(result) {
                // Check if we have vendor location data
                if (!result.locations || result.locations.length === 0) {
                    // Create a placeholder card with message
                    var $placeholder = $('<div class="alert alert-info">' +
                        '<i class="fa fa-info-circle"></i> ' +
                        'No vendor location data available. Please ensure vendors have latitude and longitude coordinates.' +
                        '</div>');
                    self.$('#map_container_1').html($placeholder);
                    return Promise.resolve();
                }

                var mapCard = new MapCard(self, {
                    title: 'Vendor Locations',
                    headerColor: 'info',
                    icon: 'fa-map-marker-alt',
                    defaultCenter: [-6.2088, 106.8456],
                    defaultZoom: 6,
                    mapData: result.locations,
                    
                    // Marker Info
                    latitudeFieldName: 'latitude',
                    longitudeFieldName: 'longitude',
                    clusterHotSpotMode: true, //optional : to create a heatmap for a clustered data

                    // List Panel Item Info
                    panelTitle: 'Vendors at Locations',
                    panelItemFieldName: 'name',
                    panelItemFields: ['city'],

                    onItemClick: function(vendor) {
                        self.do_action({
                            name: 'Vendor Details',
                            type: 'ir.actions.act_window',
                            res_model: 'res.partner',
                            res_id: vendor.id,
                            view_mode: 'form',
                            views: [[false, 'form']],
                            target: 'current'
                        });
                    }
                });

                // Pass the data to the map card
                // mapCard.mapData = result;
                
                self.dashboardCards.push(mapCard);
                return mapCard.appendTo(self.$('#map_container_1'));
            }).catch(function(error) {
                console.error('Error creating vendor mapping:', error);
                var $error = $('<div class="alert alert-danger">' +
                    '<i class="fa fa-exclamation-triangle"></i> ' +
                    'Failed to load vendor mapping data.' +
                    '</div>');
                self.$('#map_container_1').html($error);
            });
        },

        _createVendorHierarchyList: function(filterParams) {
            var self = this;
            return this._rpc({
                route: '/purchase_dashboard/vendor_hierarchy_list',
                params: filterParams || {}
            }).then(function(result) {
                var listCard = new ListCard(self, {
                    title: 'Orders by Vendor (Hierarchical)',
                    data: result.data,
                    columns: result.columns,
                    is_hierarchy: result.is_hierarchy,
                    page_size: 10,
                    onItemClick: function(item, $element) {
                        if (item.id && !item.id.toString().startsWith('vendor_')) {
                            self._openPurchaseOrder(item.id);
                        }
                    }
                });
                
                self.dashboardCards.push(listCard);
                return listCard.appendTo(self.$('#list_container_2'));
            });
        },

        _onChartClick: function(chartType, dataIndex, chartResult) {
            var self = this;
            var recordData = null;
            
            // Get the record data based on chart type and clicked index
            if (chartResult.record_ids && chartResult.record_ids[dataIndex]) {
                recordData = chartResult.record_ids[dataIndex];
            }
            
            if (!recordData) {
                console.warn('No record data found for clicked chart element');
                return;
            }
            
            // Call drill-down route
            this._rpc({
                route: '/purchase_dashboard/chart_drill_down',
                params: {
                    chart_type: chartType,
                    record_data: recordData
                }
            }).then(function (result) {
                if (result.success) {
                    self._showDrillDownDialog(result);
                } else {
                    console.error('Drill-down failed:', result.error);
                }
            });
        },

        _showDrillDownDialog: function(drillDownData) {
            var self = this;
            var $content = $(QWeb.render('purchase_dashboard.DrillDownDialog', {
                title: drillDownData.title,
                orders: drillDownData.orders,
                orders_count: drillDownData.orders_count,
            }));
            
            // Add click handlers for order links
            $content.find('.order-link').click(function(e) {
                e.preventDefault();
                var orderId = $(this).data('order-id');
                self._openPurchaseOrder(orderId);
            });
            
            var Dialog = require('web.Dialog');
            var dialog = new Dialog(self, {
                title: drillDownData.title,
                size: 'large',
                $content: $content,
                buttons: [{
                    text: 'Close',
                    close: true,
                    classes: 'btn-secondary'
                }]
            });
            
            dialog.open();
        },

        _openPurchaseOrder: function(orderId) {
            this.do_action({
                name: 'Purchase Order',
                type: 'ir.actions.act_window',
                res_model: 'purchase.order',
                res_id: orderId,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current'
            });
        },

        _openStatusRecords: function(orderIds) {
            if (!orderIds || orderIds.length === 0) {
                return;
            }
            this.do_action({
                name: 'Purchase Orders',
                type: 'ir.actions.act_window',
                res_model: 'purchase.order',
                domain: [['id', 'in', orderIds]],
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        destroy: function () {
            // Destroy all chart cards
            _.each(this.dashboardCards, function(chartCard) {
                if (chartCard) {
                    chartCard.destroy();
                }
            });
            this.dashboardCards = [];
            
            // Destroy M2M filters
            _.each(this.M2MFilters, function(filter) {
                if (filter) {
                    filter.destroy();
                }
            });
            this.M2MFilters = {};
            
            this._super();
        }
    });
    
    core.action_registry.add('purchase_dashboard', PurchaseDashboard);
    
    return PurchaseDashboard;
});