odoo.define('dha_medic_sms.sms', function (require) {
"use strict";

var core = require('web.core'),
    Widget = require('web.Widget'),
    form_widgets = require('web.form_widgets'),
    ajax = require('web.ajax'),
    core = require('web.core'),
    crash_manager = require('web.crash_manager'),
    data = require('web.data'),
    datepicker = require('web.datepicker'),
    dom_utils = require('web.dom_utils'),
    Priority = require('web.Priority'),
    ProgressBar = require('web.ProgressBar'),
    Dialog = require('web.Dialog'),
    common = require('web.form_common'),
    formats = require('web.formats'),
    framework = require('web.framework'),
    Model = require('web.DataModel'),
    pyeval = require('web.pyeval'),
    session = require('web.session'),
    utils = require('web.utils'),
    _t = core._t,
    QWeb = core.qweb;


core.form_widget_registry.map.char_domain.include({
    on_click: function(event) {
        console.log('123123');
        event.preventDefault();

        var self = this;
        var dialog = new common.DomainEditorDialog(this, {
            res_model: this.options.model || this.field_manager.get_field_value(this.options.model_field),
            default_domain: this.get('value'),
            title: this.get('effective_readonly') ? _t('Selected records') : _t('Select records...'),
            readonly: this.get('effective_readonly'),
            disable_multiple_selection: this.get('effective_readonly'),
            no_create: this.get('effective_readonly'),
            on_selected: function(selected_ids) {
                if (!self.get('effective_readonly')) {
                    self.set_value(dialog.get_domain(selected_ids));
                }
            }
        }).open();
        this.trigger("dialog_opened", dialog);
        return dialog;
    },
});
});