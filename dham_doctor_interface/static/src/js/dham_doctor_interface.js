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
        doctor_id = null,
        buildings_type = null,
        select_contract = null,
        state = '#check_in',
        active_tab = '#tiep_nhan';

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
                    $('.contract_content .contract-wrap').on('click', function(e) {
                        var clicked_class = $(this).attr('class'),
                            name = $(this).find('span:first').text();
                        if (clicked_class) {
                            select_contract = clicked_class.split('_')[1];
                        }

                        // Show menu item
                        $('.custom_menu a[data-toggle="tab"]').parent().css('display','');
                        $('a[href="'+active_tab+'"]').trigger('click');

                        $('.contract_content').parent().css('display','none');
                        $('#menu_item').css('display','');
                        $('.wrap_view').css('display','');
                        // Show patient infor
                        $('.patient_content .contract_name').attr('contract_id',select_contract).text(name);
                        $('.patient_content .patient_id').off('keypress').on('keypress', function(e) {
                            if(e.which == 13) {
                                switch (state) {
                                    case '#check_out':
                                        self.patient_check_out(this);
                                        break;

                                    case '#check_in':
                                        self.patient_check_in(this);
                                        break;

                                    case '#kham_benh':
                                        self.get_patient_infor(this);
                                        break;
                                }
                            }
                        });
                    });

                    self.render_menu_item();
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
                    // Filled patient info
                    self.filled_patient_info(result);

                    $('.tab-content').css('display','none');

                    self.do_action({
                        res_model: result['model'],
                        res_id: result['record_id'] || false,
                        name: _t(result.name),
                        type: 'ir.actions.act_window',
                        views: [[result['view_id'], 'form']],
                        view_mode: 'form',
                        target: 'new',
                        context: {
                            'default_buildings_type': buildings_type,
                            'default_doctor_id': doctor_id,
                            'default_parent_id': result['parent_id']
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
                if ($('.modal').length && $('.modal').data('bs.modal').isShown) {
                    clearInterval(check_interval);
                    $('.modal').find('button.o_form_button_save').addClass('doctor_ui');
                    $('.modal').find('button.o_form_button_cancel').css('display','none');
                };
                count++;
            }, 500)
        },
        patient_check_in: function(selector) {
            var self = this,
                patient_id = $(selector).val();

            if (patient_id.length > 0) {
                MedicalBill.call('patient_check_in', [], {'context': {
                    'customer_id': patient_id,
                    'company_check_id': select_contract,
                }}).then(function(result) {
                    self.filled_patient_info(result);
                    $('#check_in').empty();
                    if (result.success) {
                        $('#check_in').append(QWeb.render('SuccessPartner', {'patient': result}))
                    } else {
                        console.log(result)
                        $('#check_in').append(QWeb.render('FailedPartner', {'patient': result}))
                    }
                });
            }
        },
        patient_check_out: function(selector) {
            var self = this,
                patient_id = $(selector).val();

            if (patient_id.length > 0) {
                MedicalBill.call('patient_check_out', [], {'context': {
                    'customer_id': patient_id,
                    'company_check_id': select_contract,
                }}).then(function(result) {
                    self.filled_patient_info(result);
                    $('#check_out').empty();
                    if (result['success']) {
                        $('#check_out').append(QWeb.render('SuccessPartner', {'patient': result}))
                    } else {
                        $('#check_out').append(QWeb.render('FailedPartner', {'patient': result}))
                    }
                });
            }
        },
        get_patient_list: function(target) {
            MedicalBill.call('get_patient_list', [], {'context': {'company_check_id': select_contract}})
            .then(function(result) {
                if (result.length) {
                    $(target).empty().append(QWeb.render('PatientList', {'patients': result}));
                } else {
                    $(target).empty().append('<h3 style="padding-left:30px;">Chưa có bệnh nhân nào tiếp nhận hoặc trả hồ sơ</h3>')
                }
            });
        },
        filled_patient_info: function(data) {
            $('.patient_content .patient_name').text(data['customer']);
            $('.patient_content .patient_dob').text(data['day_of_birth']);
            $('.patient_content .patient_sex').text(data['sex'] == 'female' && 'Nữ' || 'Nam');
            $('.patient_content .patient_check_in').text(data['time_tiep_nhan'] || 'Chưa tiếp nhận');
            $('.patient_content .patient_check_out').text(data['time_tra_lai'] || 'Chưa khám xong');

            // Show treatmented
            $('.treatmented .treatmented_content').empty();
            $('.treatmented .treatmented_content').append(QWeb.render('Treatmented', {'treatmented': data['treatmented'],'not_treatmented': data['not_treatmented']}));
            $('.treatmented').css('display','');
        },
        render_menu_item: function() {
            var self = this;

            $('.o_main_navbar .custom_menu').remove();
            $('.o_main_navbar').append(QWeb.render('DoctorMenu', {}))

            $('.tab-content a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
                var target = $(e.target).attr("href") // activated tab
                switch (true) {
                    case target == '#check_out':
                    case target == '#check_in':
                        state = target;
                        break;
                    case target == '#check_list_in':
                    case target == '#check_list_out':
                        self.get_patient_list(target);
                        break;
                }
            });

            $('.o_menu_sections.custom_menu a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
                var target = $(e.target).attr("href"); // activated tab
                    active_tab = target;

                $('.doctor-ui-title span').text($(e.target).text());
                switch (true) {
                    case target == '#kham_benh':
                        state = target;
                        break;

                    case target == '#tiep_nhan':
                    case target == '#tra_ho_so':
                        var active = $(target).find('li.active a').attr('href');
                        if (active == '#check_out' || active == '#check_in') {
                            state = active;
                        } else if (active == '#check_list_out' || active == '#check_list_in') {
                            self.get_patient_list(active);
                        }
                        break;
                }
            });

            $('.back_to_contract').click(function(e) {
                $('.doctor-ui-title h2').text('Contract');
                $('#contract_view').css('display','');
                $('.contract_content').parent().css('display','');
                $('#menu_item').css('display','none');
                $('.wrap_view').css('display','none');
                $('.custom_menu a[data-toggle="tab"]').parent().css('display','none');
            })
        },
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