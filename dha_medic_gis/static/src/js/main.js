odoo.define('dha_medic_gis.main', function (require) {
    "use strict";

    var core = require('web.core'),
        ControlPanelMixin = require('web.ControlPanelMixin'),
        ControlPanel = require('web.ControlPanel'),
        Dialog = require('web.Dialog'),
        Class = require('web.Class'),
        Model = require('web.Model'),
        framework = require('web.framework'),
        ResPartner = new Model('res.partner'),
        QWeb = core.qweb,
        _t = core._t;

    var map, gmarkers = [], cmarkers = {}, drawingManager, historical_overlay = [], layers = {
            'company': "Công Ty",
            'customer':"Khách Hàng",
            'children_house': "Nhà thiếu nhi",
            'culture_center': "Trung tâm văn hóa",
            'sports_center': "Trung tâm thể dục thể thao",
            'sport_culture_center':"Trung tâm văn hóa và thể dục thể thao"
        },
        icon = {
            'customer': '/dha_medic_gis/static/src/img/templatic_map_icons/employment.png',
            'company': '/dha_medic_gis/static/src/img/templatic_map_icons/tires-accessories.png',
            'sport_culture_center': '/dha_medic_gis/static/src/img/templatic_map_icons/dance-clubs.png',
            'cultural_labor': '/dha_medic_gis/static/src/img/templatic_map_icons/community.png',
            'children_house': '/dha_medic_gis/static/src/img/templatic_map_icons/entertainment.png',
            'sports_center': '/dha_medic_gis/static/src/img/templatic_map_icons/games.png',
            'culture_center': '/dha_medic_gis/static/src/img/templatic_map_icons/matrimonial.png'
        },

    DhaMedicMaps = Class.extend({
        start: function() {
            var self = this;

            map = new google.maps.Map(document.getElementById('map'), {
                zoom: 12,
                center: new google.maps.LatLng(10.7860019, 106.6749709),
                mapTypeId: google.maps.MapTypeId.ROADMAP
            });

            self.load_map(0);
            self.load_panel();
            self.load_draw();
            self.set_layer();
            self.change_zoom();
        },
        load_map: function(begin) {
            var self = this;

            ResPartner.call("get_partners", [], {'context': {'begin': begin}})
                .then(function(results) {
                    if (results.success) {
                        // Create Map
                        var data = results.data,
                            infowindow = new google.maps.InfoWindow({}),
                            marker, i,
                            size = self.get_size();

                        for (i = 0; i < data.length; i++) {
                            var position = new google.maps.LatLng(data[i][1], data[i][2]),
                                existed_marker = _.filter(gmarkers, function(m) {
                                    return m.getPosition().equals( position )
                                });

                            if (existed_marker.length) continue;

                            marker = new google.maps.Marker({
                                position: position,
                                icon: {
                                    url: icon[data[i][3]] || icon['customer'],
                                    scaledSize: new google.maps.Size(size[0], size[1])
                                },
                                map: map,
                                type: data[i][3]
                            });

                            gmarkers.push(marker);

                            // count markers
                            if (!cmarkers[data[i][3]]) {
                                cmarkers[data[i][3]] = 1
                            } else {
                                cmarkers[data[i][3]]++
                            }

                            google.maps.event.addListener(marker, 'click', (function (marker, i) {
                                return function () {
                                    infowindow.setContent(data[i][0] + '<br><span>'+data[i][1]+'</span><br><span>'+data[i][2]+'</span>');
                                    infowindow.open(map, marker);
                                }
                            })(marker, i));

                            // load badge
                            setTimeout(self.load_badge, 0)
                        }

                        if (results.begin !== begin) {
                            setTimeout(self.load_map(results.begin), 0);
                        }

                    }
                });
        },
        load_draw: function() {
            drawingManager = new google.maps.drawing.DrawingManager({
                drawingMode: google.maps.drawing.OverlayType.CIRCLE,
                drawingControl: true,
                drawingControlOptions: {
                    position: google.maps.ControlPosition.TOP_CENTER,
                    drawingModes: ['circle', 'polygon', 'rectangle']
                },
                markerOptions: {icon: 'https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png'},
                circleOptions: {
                    fillOpacity: 0.15,
                    strokeWeight: 2,
                    clickable: false,
                    editable: false,
                    zIndex: 1
                }
            });

            google.maps.event.addListener(drawingManager, 'overlaycomplete', function(event) {
                historical_overlay.push(event.overlay);
                var markerCnt = {}, total = 0, select_marker;
                if (event.type == 'circle') {
                    var radius = event.overlay.getRadius();

                    for (var i = 0; i < gmarkers.length; i++) {
                        select_marker = gmarkers[i];
                        var distance = google.maps.geometry.spherical.computeDistanceBetween(select_marker.getPosition(), event.overlay.getCenter());

                        if (distance <= radius) {
                            if (markerCnt[select_marker.type]) {
                                markerCnt[select_marker.type]++
                            } else {
                                markerCnt[select_marker.type] = 1
                            }
                            total ++
                        }
                    }
                } else if (event.type == 'rectangle') {
                    var bounds = event.overlay.getBounds();

                    for (var i = 0; i < gmarkers.length; i++) {
                        select_marker = gmarkers[i];

                        if (bounds.contains(select_marker.getPosition())) {
                            if (markerCnt[select_marker.type]) {
                                markerCnt[select_marker.type]++
                            } else {
                                markerCnt[select_marker.type] = 1
                            }
                            total++;
                        }
                    }
                } else if (event.type == 'polygon') {
                    for (var i = 0; i < gmarkers.length; i++) {
                        select_marker = gmarkers[i];

                        if (google.maps.geometry.poly.containsLocation(select_marker.getPosition(), event.overlay)) {
                            if (markerCnt[select_marker.type]) {
                                markerCnt[select_marker.type]++
                            } else {
                                markerCnt[select_marker.type] = 1
                            }
                            total++;
                        }
                    }
                }
                $('#drawing').empty().append('<h3>Have '+ total +' markers in area selected<h3>');
                _.forEach(markerCnt, function(value, key) {
                    $('#drawing').append('<span>' + value + ' ' + layers[key] + ' <span><br>')
                })
            });
        },
        set_layer: function() {
            // create layer
            var wrap_layer = $('#custom_layer #layer');
            if (!wrap_layer.find('.all_type').length) {
                wrap_layer.append('<div class="all_type"><input type="checkbox" name="all" value="all" checked><h3 class="all_type_checker">All</h3></div>');

                wrap_layer.find('.all_type input').off('click').on('click', function(event) {
                    var checked = $(this).prop('checked');
                    _.forEach(wrap_layer.find('.type_layer_wrap input'), function(item){
                        if (checked != $(item).prop('checked')) {
                            $(item).trigger('click');
                        }
                    })
                });

                wrap_layer.find('.all_type .all_type_checker').click(function() {
                    wrap_layer.find('.all_type input').trigger('click');
                });

            }
            if(!wrap_layer.find('.type_layer_wrap').length) {
                wrap_layer.append('<ul class="tree type_layer_wrap"></ul>')
            }


            function filterMarker(selector) {
                var name = selector.attr('name'), value = selector.attr('value'),
                    checked = selector.prop('checked'), marker;
                for (var i = 0; i < gmarkers.length; i++) {
                    marker = gmarkers[i];
                    // If is same category or category not picked
                    if (marker[name] == value) {
                        if (checked) {
                            marker.setVisible(true);
                        } else {
                            marker.setVisible(false);
                        }
                    }
                }
            }

            // Create Layer
            var wrap_custom_layer = wrap_layer.find('.type_layer_wrap');

            _.forEach(layers, function(value, key) {
                wrap_custom_layer.append('<li class="'+ key +'"><input type="checkbox" name="type" value="'+ key +'" checked><span class="checker_title">' + value +'</span></li>');
            });

            wrap_custom_layer.find('li').removeClass('last');
            wrap_custom_layer.find('li:last').addClass('last');

            $('.checker_title').click(function() {
                $(this).parent().find('input').trigger('click');
            });

            wrap_custom_layer.find('input[type="checkbox"]').off('change').on('change', function(e) {
                filterMarker($(this));
            })
        },
        load_panel: function() {
            $('#custom_layer').append('<ul class="nav nav-tabs map_control"><li class="layer active"><a data-toggle="tab" href="#layer">Layer</a></li><li class="drawing"><a data-toggle="tab" href="#drawing">Drawing</a></li></ul><div class="tab-content"><div id="layer" class="tab-pane fade in active"></div><div id="drawing" class="tab-pane fade in active"></div></div>');
            $('#custom_layer a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
                var target = $(e.target).attr("href"); // activated tab
                if (target == '#drawing') {
                    drawingManager.setMap(map);
                    drawingManager.setOptions({
                        drawingControl: true
                    });
                } else {
                    drawingManager.setOptions({
                        drawingControl: false,
                        drawingMode: null,
                    });
                    _.forEach(historical_overlay, function(item) {
                        item.setMap(null)
                    });
                    historical_overlay = [];
                }
            });
        },
        load_badge: function() {
            var wrap_custom_layer = $('#custom_layer #layer .type_layer_wrap');
            _.forEach(cmarkers, function(value, key) {
                var existed = wrap_custom_layer.find('.' + key + ' .badge.badge-pill.badge-primary');
                if (existed.length) {
                    existed.text(value)
                } else {
                    wrap_custom_layer.find('.' + key).append('<span class="badge badge-pill badge-primary">'+ value +'</span>')
                }
            })
        },
        change_zoom: function () {
            var self = this;
            google.maps.event.addListener(map, 'zoom_changed', function() {
                var size = self.get_size();
                for (var i=0;i < gmarkers.length; i++) {
                    //change the size of the icon
                    gmarkers[i].setIcon(
                        new google.maps.MarkerImage(
                            gmarkers[i].getIcon().url, //marker's same icon graphic
                            null,//size
                            null,//origin
                            null, //anchor
                            new google.maps.Size(size[0], size[1]) //changes the scale
                        )
                    );
                }
            });
        },
        get_size: function () {
            var size = [],
                zoom = map.getZoom();

            switch(true) {
                case (zoom <= 12):
                    size = [15, 20];
                    break;
                case (zoom < 14):
                    size = [21, 28];
                    break;
                case (zoom < 16):
                    size = [27, 36];
                    break;
                case (zoom >= 16):
                    size = [33, 44];
                    break;
            }
            return size
        }
    });

    return DhaMedicMaps;
});
