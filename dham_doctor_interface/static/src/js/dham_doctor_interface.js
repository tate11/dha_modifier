odoo.define('dham_doctor_interface.main', function (require) {
"use strict";

    var core = require('web.core'),
        Widget = require('web.Widget'),
        Model = require('web.Model'),
        FormView = require('web.FormView'),
        session = require('web.session'),
        ResUser = new Model('res.users'),
        HrEmployee = new Model('hr.employee'),
        Contract = new Model('res.partner.company.check'),
        MedicalBill = new Model('medic.medical.bill'),
        _t = core._t,
        _lt = core._lt,
        QWeb = core.qweb,
        buildings_types = ["Siêu Âm","Internal Medicine","Ophthalmology","ENT (Ear - Nose - Throat)","Dentomaxillofacial System","Dermatology","Surgery","Obstetrics and Gynecology"],
        doctor_id = null,
        buildings_type = null,
        select_contract = null;

    var DHAM_DOCTOR_INTERFACE = Widget.extend({
        template: 'DHAMDoctorWidget',
        init: function(parent, data) {
            var self = this,
                res = self._super.apply(self, arguments);

            Contract.call('get_contract_info', [], {'context': {'id': session.uid}})
                .then(function(result) {
                    if (!result['success']) return alert('Please try again');
                    // Set doctor info
                    doctor_id = result['doctor_id'];
                    buildings_type = result['buildings_type'];

                    $('.contract_content').append(QWeb.render('DoctorContract', {'contracts': result['contracts']}));
                    $('.contract_content div').on('click', function(e) {
                        var clicked_class = $(this).find('div').attr('class'),
                            name = $(this).find('span').text();
                        if (clicked_class) {
                            select_contract = clicked_class.split('_')[1];
                        }

                        $('.contract_content').css('display','none');

                        // Show patient infor
                        $('.patient_content .contract_name').attr('contract_id',select_contract).text(name);
                        $('.patient_content .patient_id').off('keypress').on('keypress', function(e) {
                            if(e.which == 13) {
                                self.get_patient_infor(this);
                            }
                        });
                        $('.patient_content').css('display','');
                        $('.ui_title').text('Patient');
                    })
                    return res;
                })
        },
        get_patient_infor: function(selector) {
            var self = this,
                patient_id = $(selector).val();

            if (patient_id.length > 0) {
                MedicalBill.call('get_patient_bill', [], {'context': {
                    'customer_id': patient_id,
                    'company_check_id': select_contract,
                    'doctor_id': doctor_id,
                    'buildings_type': buildings_type,
                }}).then(function(result) {
                    console.log(result);
                    // Filled patient info
                    $('.patient_content .patient_name').text(result['customer']);
                    $('.patient_content .patient_dob').text(result['day_of_birth']);
                    $('.patient_content .patient_sex    ').text(result['sex']);

                    // Show treatmented
                    $('.treatmented .treatmented_content').empty().append(QWeb.render('Treatmented', {'treatmented': result['treatmented']}));
                    $('.treatmented').css('display','');

                    self.do_action({
                        res_model: 'medic.medical.sub.treatment',
                        res_id: result['sub_treatment_id'] || false,
                        name: 'Sub Treatment',
                        type: 'ir.actions.act_window',
                        views: [[false, 'form']],
                        view_mode: 'form',
                        target: 'new',
                        flags: {action_buttons: true, headless: true},
                        context: {
                            'default_buildings_type': buildings_type,
                            'default_doctor_id': doctor_id,
                            'default_parent_id': result['parent_id'],
                        }
                    });

                    self.check_modal();
                })
            }
        },
        check_modal: function() {
            var self = this,
                count = 0;

            var check_interval = setInterval(function() {
                if (count > 50) clearInterval(check_interval);
                if ($('.modal').data('bs.modal').isShown) {
                    clearInterval(check_interval);
                    $('.modal').find('button.o_form_button_save').addClass('doctor_ui');
                    $('.modal').find('button.o_form_button_cancel').css('display','none');
                };
                count++;
            }, 500)
        }
    });

    FormView.include({
        on_button_save: function() {
            var self = this;
            if (this.is_disabled) {
                return;
            }
            this.disable_button();

            return this.save().then(function(result) {
                self.trigger("save", result);
                if(self.$buttons.find('.o_form_button_save').hasClass('doctor_ui')) {
                    self.$el.parents('.modal.in').modal('hide')
                };

                return self.reload().then(function() {
                    self.to_view_mode();
                    core.bus.trigger('do_reload_needaction');
                    core.bus.trigger('form_view_saved', self);
                }).always(function() {
                    self.enable_button();
                });
            }).fail(function() {
                self.enable_button();
            });
        },
    })


    core.action_registry.add('dham.doctor.ui', DHAM_DOCTOR_INTERFACE);

    return DHAM_DOCTOR_INTERFACE;

});