odoo.define('dha_dashboard.main', function (require) {
"use strict";


    var core = require('web.core');
    var Widget = require('web.Widget');
    var Model = require('web.Model');
    var session = require('web.session');

    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    var DHA_DASHBOARD = Widget.extend({
        template: 'DHADashboardWidget',

        init: function(parent, data){
            this.all_dashboards = ['purchase_request', 'purchase_order', 'leave_request'];
            return this._super.apply(this, arguments);
        },

        start: function(){
            return this.load(this.all_dashboards);
        },

        load: function(dashboards){
            var self = this;
            var loading_done = new $.Deferred();
            session.rpc("/dha_dashboard/data", {}).then(function (data) {
                // Load each dashboard
                var all_dashboards_defs = [];
                console.log('test');
                _.each(dashboards, function(dashboard) {
                    var dashboard_def = self['load_' + dashboard](data);
                    if (dashboard_def) {
                        all_dashboards_defs.push(dashboard_def);
                    }
                });

                // Resolve loading_done when all dashboards defs are resolved
                $.when.apply($, all_dashboards_defs).then(function() {
                    loading_done.resolve();
                });
            });
            return loading_done;
        },

        load_purchase_request: function(data){
            return  new DashboardPR(this, data.pr).replace(this.$('.o_dha_dashboard_purchase_request'));
        },

        load_purchase_order: function(data){
            return  new DashboardPO(this, data.po).replace(this.$('.o_dha_dashboard_purchase_order'));
        },

        load_leave_request: function(data){
            return  new DashboardLR(this, data.lr).replace(this.$('.o_dha_dashboard_leave_request'));
        },
    })

    var DashboardPR = Widget.extend({
        template: 'DashboardPR',
        events: {
            'click .o_pending_pr': 'show_pending_pr',
        },
        init: function(parent, data){
            this.data = data;
            this.data.model = 'purchase.request'
            this.need_approve = data.need_approve;
            this.need_approve_domain = data.need_approve_domain;
            return this._super.apply(this, arguments);
        },

        start: function(){
            return this.load();
        },

        load: function(){
            return  new DashboardContent(this, this.data).replace(this.$('.dha_dashboard_pr_content'));
        },

        show_pending_pr: function(event){
            var self = this;
            console.log('clicked');
            this.do_action({
                name : 'Pending Purchase Request',
                type: 'ir.actions.act_window',
                res_model: 'purchase.request',
                view_mode: 'form',
                view_type: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                context: {},
                domain : self.need_approve_domain,
            })
        }
    })

    var DashboardPO = Widget.extend({
        template: 'DashboardPO',
        events: {
            'click .o_pending_po': 'show_pending_po',
        },
        init: function(parent, data){
            this.data = data;
            this.data.model = 'purchase.order'
            this.need_approve = data.need_approve;
            this.need_approve_domain = data.need_approve_domain;
            return this._super.apply(this, arguments);
        },

        start: function(){
            return this.load();
        },

        load: function(){
            return  new DashboardContent(this, this.data).replace(this.$('.dha_dashboard_po_content'));
        },

        show_pending_po: function(event){
            var self = this;
            console.log('clicked');
            this.do_action({
                name : 'Pending Purchase Order',
                type: 'ir.actions.act_window',
                res_model: 'purchase.order',
                view_mode: 'form',
                view_type: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                context: {},
                domain : self.need_approve_domain,
            })
        }
    })

    var DashboardLR = Widget.extend({
        template: 'DashboardLR',
        events: {
            'click .o_pending_lr': 'show_pending_po',
        },
        init: function(parent, data){
            this.data = data;
            this.data.model = 'hr.holidays'
            this.need_approve = data.need_approve;
            this.need_approve_domain = data.need_approve_domain;
            return this._super.apply(this, arguments);
        },

        start: function(){
            return this.load();
        },

        load: function(){
            return  new DashboardContent(this, this.data).replace(this.$('.dha_dashboard_lr_content'));
        },

        show_pending_po: function(event){
            var self = this;
            console.log('clicked');
            this.do_action({
                name : 'Pending Leave Request',
                type: 'ir.actions.act_window',
                res_model: 'hr.holidays',
                view_mode: 'form',
                view_type: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                context: {},
                domain : self.need_approve_domain,
            })
        }
    })

    var DashboardContent = Widget.extend({
        template: 'DashboardContent',
        events: {
            'click .o_on_click_name': 'show_record',
        },
        init: function(parent, data){
            this.data = data;

            return this._super.apply(this, arguments);
        },
        show_record: function(event){
            var self = this;
            var res_id = parseInt($(event.currentTarget).attr('data-record-id'));
            this.do_action({
                name : 'Pending Job',
                type: 'ir.actions.act_window',
                res_model: self.data.model,
                view_mode: 'form',
                view_type: 'form,tree',
                views: [[false, 'form']],
                target: 'current',
                context: {},
                res_id : res_id,
            })

        }
    })

    core.action_registry.add('dha.dashboard.ui', DHA_DASHBOARD);

    return DHA_DASHBOARD
});
