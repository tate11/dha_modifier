
odoo.define('dha_medic_modifier', function (require) {
    "use strict";
    console.log('enter');
    var Chatter = require('mail.Chatter');
    var core = require('web.core');
    var form_common = require('web.form_common');
    var Model = require('web.Model');
    var KanbanView = require('web_kanban.KanbanView');
    var session = require('web.session');
    var _t = core._t;
    var QWeb = core.qweb;

    KanbanView.include({
        execute_check_customer_action: function() {
            var self = this;
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'wizard.check.partner',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                domain: [],
                context: {},
            })
        },
        render_buttons: function() {
            var self = this;
            var add_button = false;
            if (!this.$buttons) { // Ensures that this is only done once
                add_button = true;
            }
            this._super.apply(this, arguments); // Sets this.$buttons
            if(add_button && this.$buttons) {
                this.$buttons.on('click', '.o_list_button_check_partner', self.execute_check_customer_action.bind(this));
            }
        },
    });
});