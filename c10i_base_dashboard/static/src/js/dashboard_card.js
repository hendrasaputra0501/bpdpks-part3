odoo.define('c10i_base_dashboard.DashboardCard', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var core = require('web.core');

    var ChartCard = Widget.extend({
        template: 'c10i_base_dashboard.ChartCard',
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
            this.chart = null;
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                if (self.options.data) {
                    self.renderChart(self.options.data);
                }
            });
        },

        renderChart: function (data) {
            var self = this;
            if (!window.Chart) {
                console.error('Chart.js is not loaded');
                return;
            }

            var canvas = this.$('canvas')[0];
            if (!canvas) {
                console.error('Canvas element not found');
                return;
            }

            var ctx = canvas.getContext('2d');
            
            // Destroy existing chart if it exists
            if (this.chart) {
                this.chart.destroy();
            }

            // Add click handling if callback is provided
            var chartOptions = data.options || {};
            if (this.options.onChartClick) {
                chartOptions.onClick = function(event, elements) {
                    if (elements.length > 0) {
                        var element = elements[0];
                        var dataIndex = element.index;
                        self.options.onChartClick(dataIndex, data, self.options);
                    }
                };
                // Make chart cursor pointer on hover
                chartOptions.onHover = function(event, elements) {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                };
            }

            this.chart = new Chart(ctx, {
                type: data.type || 'bar',
                data: data.chartData,
                options: chartOptions
            });
        },

        destroy: function () {
            if (this.chart) {
                this.chart.destroy();
            }
            this._super();
        }
    });

    // New StatusCard Widget
    var StatusCard = Widget.extend({
        template: 'c10i_base_dashboard.StatusCard',
        events: {
            'click .status-card-clickable': '_onCardClick',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.title = options.title || 'Status';
            this.count = options.count || 0;
            this.subtitle = options.subtitle || '';
            this.icon = options.icon || 'fa fa-file';
            this.status_type = options.status_type || '';
            this.color = options.color || '#3498db';
            this.onClick = options.onClick || null;
            this.data = options || {};
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                self._renderStatusCard();
            });
        },

        _renderStatusCard: function () {
            if (this.color) {
                this.$('.card').css('background-color', this.color);
                this.$('.status-icon-container').css('background-color', this.color);
            }

            // Make clickable if callback provided
            if (this.onClick) {
                this.$('.status-card-content').addClass('status-card-clickable');
            }
        },

        _onCardClick: function () {
            if (this.onClick) {
                this.onClick(this);
            }
        },

        destroy: function () {
            this._super();
        }
    });

    var ListCardItem = Widget.extend({
        template: 'c10i_base_dashboard.ListCardItem',
        events: {
            'click .list-item-action': '_onItemClick',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.item = options.item || {};
            this.columns = options.columns || [];
            this.onItemClick = options.onItemClick || null;
        },
        
        start: function () {
            return this._super();
        },

        _onItemClick: function (e) {
            e.stopPropagation();
            if (this.onItemClick) {
                this.onItemClick(this.item, this.$el);
            }
        }
    });

    // New ListCard Widget
    var ListCard = Widget.extend({
        template: 'c10i_base_dashboard.ListCard',
        events: {
            'click .hierarchy-toggle': '_onToggleHierarchy',
            'click .pager-btn': '_onPageChange',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.title = options.title || 'List';
            this.columns = options.columns || [];
            this.data = options.data || [];
            this.is_hierarchy = options.is_hierarchy || false;
            this.onItemClick = options.onItemClick || null;
            this.page_size = options.page_size || 15;
            this.current_page = 0;
            this.expanded_items = new Set();
            this.visible_items = [];
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                self._renderListCard();
            });
        },

        _renderListCard: function () {
            this._updatePaginationData();
            this._renderPager();
            this._bindEvents();
        },

        _updatePaginationData: function () {
            var visible_data = this.is_hierarchy ? this._getVisibleHierarchyData() : this.data;
            this.total_pages = Math.ceil(visible_data.length / this.page_size);
            this.current_page = Math.min(this.current_page, Math.max(0, this.total_pages - 1));
            
            var start_index = this.current_page * this.page_size;
            var end_index = start_index + this.page_size;
            this.visible_items = visible_data.slice(start_index, end_index);
            this._renderListItems();
        },

        _renderListItems: function () {
            var self = this;
            var tbody = this.$('.list-container table tbody');
            tbody.empty();

            _.each(this.visible_items, function(item, index) {
                var new_item = new ListCardItem(self, {
                    item: item,
                    columns: self.columns,
                    onItemClick: self.onItemClick
                });
                new_item.appendTo(tbody);
            });
        },

        _getVisibleHierarchyData: function () {
            var visible = [];
            var self = this;
            
            function addItemsRecursively(items, level) {
                _.each(items, function(item) {
                    var item_copy = _.extend({}, item, {level: level || 0});
                    visible.push(item_copy);
                    
                    if (item.children && item.children.length > 0 && 
                        (self.expanded_items.has(item.id) || level === 0)) {
                        addItemsRecursively(item.children, (level || 0) + 1);
                    }
                });
            }
            
            addItemsRecursively(this.data);
            return visible;
        },

        _renderPager: function () {
            var $pager = this.$('.list-pager');
            var total_data_length = this.is_hierarchy ? this._getVisibleHierarchyData().length : this.data.length;
            
            // Show pager only if total data length is greater than page_size
            if (total_data_length <= this.page_size) {
                $pager.hide();
                return;
            }
            
            $pager.show();
            $pager.find('.current-page').text(this.current_page + 1);
            $pager.find('.total-pages').text(this.total_pages);
            
            $pager.find('.pager-prev').prop('disabled', this.current_page === 0);
            $pager.find('.pager-next').prop('disabled', this.current_page === this.total_pages - 1);
        },

        _bindEvents: function () {
            // Event binding is now handled by individual ListCardItem components
        },

        _onToggleHierarchy: function (e) {
            e.stopPropagation();
            var $toggle = $(e.currentTarget);
            var item_id = $toggle.data('id');
            
            if (this.expanded_items.has(item_id)) {
                this.expanded_items.delete(item_id);
                $toggle.find('i').removeClass('fa-minus').addClass('fa-plus');
            } else {
                this.expanded_items.add(item_id);
                $toggle.find('i').removeClass('fa-plus').addClass('fa-minus');
            }
            
            this._renderListCard();
        },

        _onPageChange: function (e) {
            var action = $(e.currentTarget).data('action');
            
            if (action === 'prev' && this.current_page > 0) {
                this.current_page--;
            } else if (action === 'next' && this.current_page < this.total_pages - 1) {
                this.current_page++;
            }
            
            this._renderListCard();
        },

        _findItemById: function (id) {
            var self = this;
            
            function findRecursive(items) {
                for (var i = 0; i < items.length; i++) {
                    if (items[i].id === id) {
                        return items[i];
                    }
                    if (items[i].children) {
                        var found = findRecursive(items[i].children);
                        if (found) return found;
                    }
                }
                return null;
            }
            
            return findRecursive(this.data);
        },

        updateData: function (data) {
            this.data = data;
            this.current_page = 0;
            this.expanded_items.clear();
            this._renderListCard();
        },

        destroy: function () {
            this._super();
        }
    });

    // New KpiCard Widget
    var KpiCard = Widget.extend({
        template: 'c10i_base_dashboard.KpiCard',
        events: {
            'click .kpi-card-content': '_onKpiClick',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.title = options.title || 'KPI';
            this.header = options.header || '';
            this.footer = options.footer || '';
            this.headerColor = options.headerColor || 'primary';
            this.icon = options.icon || 'fa-chart-line';
            
            this.actualValue = options.actualValue || 0;
            this.actualLabel = options.actualLabel || '';
            
            this.target = options.target || false;
            this.targetValue = options.targetValue || 0;
            this.targetLabel = options.targetLabel || '';
            
            this.percentage = options.percentage || false;
            this.percentageValue = options.percentageValue || 0;
            
            this.trend = options.trend || false;
            this.trendLabel = 'neutral'; // up, down, neutral
            
            this.onClick = options.onClick || null;
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                self._calculateKPIMetrics();
            });
        },

        _calculateKPIMetrics: function () {
            if (this.targetValue > 0) {
                this.percentageValue = Math.round((this.actualValue / this.target) * 100);
            } else {
                this.percentageValue = 0;
            }
            
            if (this.percentageValue >= 100) {
                this.trend = 'up';
            } else if (this.percentageValue >= 80) {
                this.trend = 'neutral';
            } else {
                this.trend = 'down';
            }
        },

        _formatNumber: function (value) {
            if (typeof value === 'number') {
                return value.toLocaleString();
            }
            return value;
        },

        _formatCurrency: function (value, currency_symbol) {
            if (typeof value === 'number') {
                return (currency_symbol || '$') + ' ' + value.toLocaleString();
            }
            return value;
        },

        _onKpiClick: function (e) {
            if (this.onClick) {
                var clickData = {
                    actual: this.actualValue,
                    target: this.targetValue,
                    percentage: this.percentageValue,
                };
                this.onClick(clickData);
            }
        },

        destroy: function () {
            this._super();
        }
    });

    // New MapCard Widget
    var MapCard = Widget.extend({
        // jsLibs: [
        //     '/c10i_base_dashboard/static/lib/leaflet/leaflet.js',
        // ],
        template: 'c10i_base_dashboard.MapCard',
        events: {
            'click .close-data-panel': '_onClosePanelClick',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            // this.cardId = options.cardId || 'map_' + Math.random().toString(36).substr(2, 9);
            this.title = options.title || 'Map';
            // this.dataEndpoint = options.dataEndpoint || null;
            // this.filters = options.filters || {};
            this.headerColor = options.headerColor || 'primary';
            this.icon = options.icon || 'fa-map-marker';
            
            // Default map center
            this.defaultCenter = options.defaultCenter || [-6.2088, 106.8456]; // Jakarta
            this.defaultZoom = options.defaultZoom || 10;
            this.mapData = options.mapData || [];
            
            // Marker Info
            this.latitudeFieldName = options.latitudeFieldName || 'latitude';
            this.longitudeFieldName = options.longitudeFieldName || 'longitude';
            this.clusterHotSpotMode = options.clusterHotSpotMode || false;
            this.clusterHotSpotColors = options.clusterHotSpotColors || {
                7: '#1faef0ff', // Blue
                5: '#FFD700', // Yellow
                3: '#FF6B35', // Orange-Red  
                1: '#8B0000'  // Dark Red
            };

            // Panel Info
            this.panelTitle = options.panelTitle || 'Vendors at Locations';
            this.panelItemFieldName = options.panelItemFieldName || 'name';
            this.panelItemFields = options.panelItemFields || [];

            // Event
            this.onItemClick = options.onItemClick || null;

            // For rendering
            this.mapInstance = null;
            this.markers = [];
            this.selectedItems = [];
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                self._initializeMap();
            });
        },

        _initializeMap: function () {
            var self = this;
            
            // Check if Leaflet is available
            if (typeof L === 'undefined') {
                console.error('Leaflet library not found');
                self._showError('Map library not available. Please include Leaflet CSS and JS.');
                return;
            }

            // Configure Leaflet icon paths for local assets
            L.Icon.Default.mergeOptions({
                iconRetinaUrl: '/c10i_base_dashboard/static/lib/leaflet/images/marker-icon-2x.png',
                iconUrl: '/c10i_base_dashboard/static/lib/leaflet/images/marker-icon.png',
                shadowUrl: '/c10i_base_dashboard/static/lib/leaflet/images/marker-shadow.png',
            });

            var mapElement = this.$('.map-element')[0];
            if (!mapElement) {
                console.error('Map container not found');
                return;
            }

            try {
                // Initialize map
                this.mapInstance = L.map(mapElement, {
                    center: this.defaultCenter,
                    zoom: this.defaultZoom,
                    zoomControl: true
                });

                // Add tile layer
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 18
                }).addTo(this.mapInstance);

                // Force resize after a delay
                setTimeout(function() {
                    if (self.mapInstance) {
                        self.mapInstance.invalidateSize();
                        if (self.mapData) {
                            self._updateMap();
                        }
                    }
                }, 200);
            } catch (error) {
                console.error('Error initializing map:', error);
                this._showError('Failed to initialize map');
            }
        },

        _updateMap: function () {
            if (!this.mapInstance || !this.mapData) {
                return;
            }

            var self = this;
            
            // Clear existing markers
            this.markers.forEach(function(marker) {
                self.mapInstance.removeLayer(marker);
            });
            this.markers = [];

            var bounds = [];
            
            // Group items by location
            var locationGroups = {};
            this.mapData.forEach(function(item) {
                var lat = item[self.latitudeFieldName];
                var lng = item[self.longitudeFieldName];

                if (lat && lng) {
                    var key = lat.toFixed(6) + ',' + lng.toFixed(6);
                    if (!locationGroups[key]) {
                        locationGroups[key] = {
                            latitude: lat,
                            longitude: lng,
                            items: []
                        };
                    }
                    locationGroups[key].items.push(item);
                }
            });

            // Create markers for each location group
            Object.keys(locationGroups).forEach(function(key) {
                var group = locationGroups[key];
                var marker;

                if ( self.clusterHotSpotMode ) {
                    var percentage = Math.round((group.items.length/self.mapData.length) * 100);
                    var color = self.getHotspotColor(percentage);
                    var hotspotKeys = Object.keys(self.clusterHotSpotColors).map(Number).sort((a, b) => a - b);
                    var iconSize = [100, 100]
                    if (group.items.length === 1) {
                        var total = hotspotKeys.length;
                        iconSize = [1.5 * 100 / total, 1.5 * 100 / total];
                    } else {
                        var matchedKey = hotspotKeys.find(function(k) { return percentage <= k; });
                        if (matchedKey === undefined) {
                            matchedKey = hotspotKeys[hotspotKeys.length - 1];
                        }
                        var total = hotspotKeys.length;
                        var index = hotspotKeys.indexOf(matchedKey) + 1;
                        iconSize = [100 * index / total, 100 * index / total];
                    }
                    
                    iconHtml = '<div class="hotspot-cluster" style="background: ' + color + ';">' + 
                        '<span class="cluster-count">' + group.items.length + '</span>' +
                        '</div>';
                    var customIcon = L.divIcon({
                        html: iconHtml,
                        className: 'custom-div-icon',
                        iconSize: iconSize,
                        iconAnchor: [20, 20]
                    });
                    
                    marker = L.marker([group.latitude, group.longitude], {icon: customIcon})
                        .addTo(self.mapInstance);
                } else {
                    if (group.items.length === 1) {
                        marker = L.marker([group.latitude, group.longitude])
                            .addTo(self.mapInstance);
                    } else {
                        var iconHtml = '<div class="data-cluster">' + group.items.length + '</div>';
                        var customIcon = L.divIcon({
                            html: iconHtml,
                            className: 'custom-div-icon',
                            iconSize: [50, 50],
                            iconAnchor: [20, 20]
                        });
                        
                        marker = L.marker([group.latitude, group.longitude], {icon: customIcon})
                            .addTo(self.mapInstance);
                    }
                }
                    
                // Add click event to marker
                marker.on('click', function() {
                    self._showDataPanel(group.items);
                });
                
                self.markers.push(marker);
                bounds.push([group.latitude, group.longitude]);
            });

            // Fit map to show all markers
            if (bounds.length > 0) {
                this.mapInstance.fitBounds(bounds, {padding: [20, 20]});
            }
        },

        getHotspotColor: function(percentage) {
            var colors = this.clusterHotSpotColors;
            var thresholds = Object.keys(colors).map(Number).sort((a, b) => a - b);
            
            var selected_index;
            for (var i = 0; i < thresholds.length; i++) {
                if (percentage >= thresholds[i]) {
                    selected_index = i;
                }
            }
            return this.createGradientColor(colors[thresholds[selected_index]], percentage, thresholds[selected_index]);
        },

        createGradientColor: function(baseColor, percentage, threshold) {
            // Create a radial gradient effect with darker center and transparent edges
            var intensity = Math.min(percentage / threshold, 1);
            
            // Convert hex to RGB
            var hex = baseColor.replace('#', '');
            var r = parseInt(hex.substr(0, 2), 16);
            var g = parseInt(hex.substr(2, 2), 16);
            var b = parseInt(hex.substr(4, 2), 16);
            
            // Create radial gradient CSS
            var centerOpacity = 0.8 + (intensity * 0.2); // 0.8 to 1.0
            var edgeOpacity = 0.2 + (intensity * 0.2);   // 0.2 to 0.4
            
            return 'radial-gradient(circle, rgba(' + r + ',' + g + ',' + b + ',' + centerOpacity + ') 30%, ' +
                'rgba(' + r + ',' + g + ',' + b + ',' + edgeOpacity + ') 70%, ' +
                'rgba(' + r + ',' + g + ',' + b + ', 0) 100%)';
        },

        _showDataPanel: function (items) {
            var self = this;
            this.selectedItems = items;
            
            // Update panel title
            this.$('.panel-title').text(this.panelTitle);
            
            // Build data list HTML
            var dataListHtml = '';
            items.forEach(function(item) {
                var itemName = item[self.panelItemFieldName] || 'Unnamed';
                var detailsHtml = '';
                
                // Build details from configured fields
                self.panelItemFields.forEach(function(fieldName) {
                    if (item[fieldName] !== undefined && item[fieldName] !== null) {
                        var label = fieldName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                        var value = item[fieldName];
                        detailsHtml += '<small class="text-muted">' + label + ': ' + value + '</small><br>';
                    }
                });
                
                dataListHtml += '<div class="data-item" data-item-id="' + (item.id || '') + '">' +
                    '<div class="item-name">' + itemName + '</div>' +
                    '<div class="item-details">' + detailsHtml + '</div>' +
                    '</div>';
            });
            
            this.$('.data-list').html(dataListHtml);
            this.$('.data-details-panel').show();
            
            // Add click handlers for items if callback provided
            if (this.onItemClick) {
                this.$('.data-item').on('click', function() {
                    var itemId = $(this).data('item-id');
                    var item = items.find(i => i.id == itemId);
                    if (item) {
                        self.onItemClick(item);
                    }
                });
            }
        },

        _showLoading: function (show) {
            if (show) {
                this.$('.map-loading').show();
                this.$('.map-container').hide();
            } else {
                this.$('.map-loading').hide();
                this.$('.map-container').show();
            }
        },

        _showError: function (message) {
            this.$('.map-container').html(
                '<div class="alert alert-danger text-center">' +
                '<i class="fa fa-exclamation-triangle"></i> ' + message +
                '</div>'
            );
        },

        _onClosePanelClick: function () {
            this.$('.data-details-panel').hide();
        },

        destroy: function () {
            if (this.mapInstance) {
                this.mapInstance.remove();
            }
            this._super();
        }
    });

    return {
        ChartCard: ChartCard,
        StatusCard: StatusCard,
        KpiCard: KpiCard,
        ListCard: ListCard,
        ListCardItem: ListCardItem,
        MapCard: MapCard
    };
});
