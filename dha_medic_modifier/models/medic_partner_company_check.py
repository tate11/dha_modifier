# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
import logging
from bs4 import BeautifulSoup
_logger = logging.getLogger(__name__)


class PartnerCompanyCheck(models.Model):
    _name = 'res.partner.company.check'
    _inherit = 'mail.thread'
    _description = 'Medic Contract'
    _order = 'id desc'

    name = fields.Char('Name', track_visibility='onchange')
    state = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done'), ('invoiced', 'Invoiced')],
                             'Status', default='new', track_visibility='onchange')
    type = fields.Selection([('all', 'Full Payment'), ('part', 'Partial Payment')], 'Payment', default='all', required=1,
                            track_visibility='onchange')
    package_ids = fields.Many2many('medic.package', 'medic_company_check_package_package_ref', 'wizard_id',
                                   'package_id', 'Packages', domain=[('type', '=', 'company')], required=1)
    company_id = fields.Many2one('res.partner', 'Company', track_visibility='onchange', domain=[('is_company','=',True)])
    employees = fields.Many2many('dham.patient', 'company_check_dham_patient_rel', 'company_check', 'patient_id',
                                 'Employees')
    doctor_ids = fields.Many2many('hr.employee', 'company_check_hr_employee_rel', 'company_check', 'emp_id', 'Doctors')
    start_time = fields.Date('Start Date', track_visibility='onchange')
    end_time = fields.Date('End Date', track_visibility='onchange')
    import_seq = fields.Integer('Import Sequence', default=1)
    sale_order_id = fields.Many2one('sale.order', 'Sale Order ID')

    done_count = fields.Char('Medical Done', compute='_compute_medical_bill_done')
    medical_ids = fields.One2many('medic.medical.bill', 'company_check_id', 'Medial Bills')
    schedule_ids = fields.One2many('company.contract.schedule', 'contract_id', 'Schedule Lines')
    package_line_ids = fields.Many2many('medic.package.line','res_partner_contract_medic_package_id_rel','id1','id2', 'Package Line', compute='_compute_package_line')
    need_validate = fields.Boolean('Need Validate', default=False)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', help='Pricelist for current invoice.')

    @api.depends('package_ids')
    def _compute_package_line(self):
        for record in self:
            for line in record.package_ids:
                record.package_line_ids += line.line_ids

    @api.multi
    def unlink(self):
        Medical = self.env['medic.medical.bill']
        Test = self.env['medic.test']
        for record in self:
            medical_ids = Medical.search([('company_check_id','=', record.id)])
            medical_except_new = Medical.search([('company_check_id','=', record.id),('state','!=', 'new')])
            test_ids = Test.search([('company_check_id','=', record.id)])
            test_except_new = Test.search([('company_check_id', '=', record.id), ('state', '!=', 'new')])
            if not medical_except_new and not test_except_new :
                medical_ids.unlink()
                test_ids.unlink()
            else:
                raise UserError (_('Can not delete this contract.'))
        return super(PartnerCompanyCheck, self).unlink()
    
    def _compute_medical_bill_done(self):
        for record in self:
            total = len(record.medical_ids) or 0
            done = len(self.env['medic.medical.bill'].search(
                [('id', 'in', record.medical_ids.ids), ('state', '=', 'done')])) or 0
            record.done_count = '%s / %s' % (done, total)

    @api.multi
    def action_show_medical_bill_done(self):
        action = self.env.ref('dha_medic_modifier.medic_medical_bill_action').read()[0]
        action['context'] = {'search_default_done_bill': 1}
        action['domain'] = [('id', 'in', self.medical_ids.ids)]
        return action

    @api.onchange('company_id')
    def onchange_company_id(self):
        Partner = self.env['res.partner']
        if self.company_id:
            # employee_ids = Partner.search([('parent_id','=',self.company_id.id)])
            # self.employees = employee_ids
            return {'domain': {
                'employees': [('parent_id', '=', self.company_id.id)]
            }}

    @api.multi
    def action_reset_to_processing(self):
        self.write({'state': 'processing'})

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.multi
    def action_invoice(self):
        self.write({'state': 'invoiced'})
        for record in self:
            if record.type == 'all':
                return record._create_invoice_type_all()
            else:
                return record._create_invoice_type_part()

    @api.model
    def _create_invoice_type_all(self):
        MedicalBill = self.env['medic.medical.bill']
        MedicTest = self.env['medic.test']
        len_emp = len(self.employees)
        product_package = self.package_ids.parse_multi_package()

        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        Product = self.env['product.product']

        center = self.env.ref('dha_medic_modifier.out_center_department')

        default_account_id = False
        default_journal = AccountInvoice._default_journal() or False
        if default_journal:
            default_account_id = AccountInvoiceLine.with_context(
                journal_id=default_journal.id)._default_account() or False
        invoice_line_ids = []
        for line in product_package:
            product = Product.browse(int(line[0]))
            invoice_line_ids.append({
                'product_id': int(line[0]),
                'uom_id': product.uom_id.id or False,
                'price_unit': line[1],
                'invoice_line_tax_ids': product.taxes_id.ids or [],
                'name': product.description or product.name,
                'quantity': len_emp,
                'account_id': default_account_id,
            })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': False,
            'context': {'default_partner_id': self.company_id.id,
                        'default_invoice_line_ids': invoice_line_ids, 'form_view_ref': 'account.invoice_form'
                , 'default_center_id': center.id or False, 'no_onchange_package': True,
                        'default_company_check_id': self.id}
        }

    @api.model
    def _create_invoice_type_part(self):
        MedicalBill = self.env['medic.medical.bill']
        MedicTest = self.env['medic.test']
        Package = self.env['medic.package']

        product_and_qty = {}

        medical_bills = MedicalBill.search([('company_check_id', '=', self.id)])
        medic_tests = MedicTest.search([('company_check_id', '=', self.id)])

        for medical in medical_bills:
            for service in medical.service_ids:
                if str(service.id) in product_and_qty:
                    product_and_qty[str(service.id)] += 1
                else:
                    product_and_qty[str(service.id)] = 1
        for test in medic_tests:
            if str(test.product_test.id) in product_and_qty:
                product_and_qty[str(test.product_test.id)] += 1
            else:
                product_and_qty[str(test.product_test.id)] = 1
        return self.go_invoice(product_and_qty)

    @api.model
    def go_invoice(self, lines):
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        Product = self.env['product.product']

        product_package = self.package_ids.parse_multi_package(return_type='dict')
        center = self.env.ref('dha_medic_modifier.out_center_department')

        default_account_id = False
        default_journal = AccountInvoice._default_journal() or False
        if default_journal:
            default_account_id = AccountInvoiceLine.with_context(
                journal_id=default_journal.id)._default_account() or False
        invoice_line_ids = []
        for line in lines.items():
            if str(line[0]) in product_package:
                product = Product.browse(int(line[0]))
                invoice_line_ids.append({
                    'product_id': int(line[0]),
                    'uom_id': product.uom_id.id or False,
                    'price_unit': product_package[str(line[0])],
                    'invoice_line_tax_ids': product.taxes_id.ids or [],
                    'name': product.description or product.name,
                    'quantity': line[1],
                    'account_id': default_account_id,
                })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': False,
            'context': {'default_partner_id': self.company_id.id,
                        'default_invoice_line_ids': invoice_line_ids, 'form_view_ref': 'account.invoice_form'
                , 'default_center_id': center.id or False, 'no_onchange_package': True,
                        'default_company_check_id': self.id}
        }

    @api.model
    def _cron_validate(self):
        contract_ids = self.search([('need_validate','=', True)])
        contract_ids.write({'need_validate' : False})
        contract_ids.action_validate()
        return True

    @api.multi
    def schedule_validate(self):
        self.write({'need_validate' : True})

    @api.multi
    def action_validate(self):
        self.write({'state': 'processing'})
        for record in self:
            _logger.info('Start Validate contract %s.' % (record.name or ''))
            employees_obj = self.env.context.get('action_add_employee') if self.env.context.get('action_add_employee',
                                                                                                False) else record.employees
            index = 1
            for emp in employees_obj:
                _logger.info('Line %s'%(index))
                index += 1
                Product = self.env['product.product']
                MedicalBill = self.env['medic.medical.bill']
                MedicTest = self.env['medic.test']
                Department = self.env['hr.department']
                products = Product

                product_list = record.package_ids.parse_multi_package()
                products += Product.browse(x[0] for x in product_list)

                spec_product = Product.search([('id', 'in', products.ids), ('sex', '!=', False)])
                correct_sex_product = Product.search([('id', 'in', spec_product.ids), ('sex', '=', emp.sex), '|',
                                                      ('married_status', '=', emp.married_status),
                                                      ('married_status', '=', False)])

                products = (products - spec_product) + correct_sex_product

                center = self.env.ref('dha_medic_modifier.out_center_department')

                product_medical = Product.search(
                    [('id', 'in', products.ids), ('type', '=', 'service'), ('create_medical_bill', '=', True)])
                if len(product_medical) > 0:
                    building = False
                    new_bill = MedicalBill.create({
                        'patient_id': emp.id,
                        'service_ids': [(6, 0, product_medical.ids)],
                        'center_id': center.id,
                        'building_id': False,
                        'company_check_id': record.id,
                        'type': 'company',
                        # 'sub_treatment_ids': self.parse_sub_treatment(),
                    })
                    # product_medical -= same_type_pro
                    MedicalBill += new_bill
                MedicalBill.write({
                    'related_medical_bill_ids': [(6, 0, MedicalBill.ids or [])]
                })
                product_test = Product.search(
                    [('id', 'in', products.ids), ('type', '=', 'service'), ('service_type', '!=', False)])
                for pro in product_test:
                    Obj = self.env[pro.service_type.model_name]
                    Obj.create({
                        'type': pro.service_type.id,
                        'company_check_id': record.id,
                        'product_test': pro.id,
                        'patient_id': emp.id,
                        'related_medical_bill': [(6, 0, MedicalBill.ids)],
                    })

    @api.model
    def parse_sub_treatment(self):
        res = []
        khoas = ['khoa_nhi', 'khoa_mat', 'khoa_tai_mui_hong', 'khoa_rang_ham_mat', 'khoa_da_lieu', 'khoa_ngoai',
                 'khoa_san']
        for khoa in khoas:
            res.append((0, 0, {'buildings_type': self.env.ref('dha_medic_modifier.' + khoa).id,
                               'doctor_id': False,
                               'type': 'company',
                               }))
        return res

    @api.multi
    def action_export_data(self):
        for record in self:
            att_id = record._action_export_data()
            if att_id:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Download File Template",
                    'target': 'new',
                    'url': base_url + "/web/content/%s?download=1" % (att_id),
                }
            else:
                raise UserError(_("Can't export data."))

    @api.model
    def _action_export_data(self):
        Service = self.env['service.export.excel']
        datas = self.parse_export_data()
        now = datetime.now() + timedelta(hours=7)
        file_name = '%s_%s_%s.xls' % (
            (str(now.year)[-2:] + now.strftime('%m%d%H%M%S')), self.company_id.name or '', self.name or '')
        att_id = Service.make_file(datas, file_name=file_name)
        return att_id

    @api.model
    def parse_export_data(self):
        Test = self.env['medic.test']
        Medical = self.env['medic.medical.bill']
        SubTreatment = self.env['medic.medical.sub.treatment']
        Noi = self.env.ref('dha_medic_modifier.khoa_nhi')

        res = []
        for emp in self.employees:
            data = []
            sex = ''
            if emp.sex:
                sex = 'Nam' if emp.sex == 'male' else 'Nữ'
            medical_id = Medical.search(
                [('patient_id', '=', emp.id), ('company_check_id', '=', self.id), ('state', '=', 'done')], limit=1)
            if medical_id:
                data.extend([emp.patient_id or '', emp.name or '', emp.mobile or '', emp.description or '',
                             emp.day_of_birth or '', sex, medical_id.height or '', medical_id.weight or '',
                             medical_id.bmi or '', medical_id.note or ''])
                # Cac Khoa
                # Noi Khoa
                sub_tm_noi = SubTreatment.search([('parent_id', '=', medical_id.id), ('buildings_type', '=', Noi.id)],
                                                 limit=1)
                if sub_tm_noi:
                    data.extend(
                        [sub_tm_noi.tuan_hoan or '', sub_tm_noi.phan_loai_tuan_hoan.name or '', sub_tm_noi.ho_hap or '',
                         sub_tm_noi.phan_loai_ho_hap.name or '', sub_tm_noi.tieu_hoa or '',
                         sub_tm_noi.phan_loai_tieu_hoa.name or '',
                         sub_tm_noi.than_tiet_nieu or '', sub_tm_noi.phan_loai_than_tiet_nieu.name or '',
                         sub_tm_noi.co_xuong_khop or '', sub_tm_noi.phan_loai_co_xuong_khop.name or '',
                         sub_tm_noi.than_kinh or '', sub_tm_noi.phan_loai_than_kinh.name or '',
                         sub_tm_noi.tam_than or '', sub_tm_noi.phan_loai_tam_than.name or '', sub_tm_noi.treatment_note or '',
                         sub_tm_noi.phan_loai.name or '', sub_tm_noi.doctor_id.name or '',
                         ])
                else:
                    data.extend([''] for i in range(0, 18))
                # Khoa khac
                for khoa in ['ngoai', 'san', 'mat', 'tmh', 'rhm', 'dl']:
                    data.extend(self._compute_text_val(khoa, medical_id))
                # XN, XQ, SA, DT
                data.extend(self._compute_test_val(medical_id))
                # Ket Luan, De Nghi, Phan Loai, Bac Si

                data.extend([BeautifulSoup(str(medical_id.treatment_note or '')).get_text('\n'), medical_id.phan_loai.name or '', BeautifulSoup(str(medical_id.de_nghi or '')).get_text('\n'), medical_id.doctor_assign.name or '' ])
            else:
                continue
            if len(data) > 0:
                res.append(data)
        return res

    @api.model
    def _compute_test_val(self, medical):
        TestObj = self.env['medic.test']
        res = ['', '', '', '']
        XN = self.env.ref('dha_medic_modifier.medic_test_type_lab_test')
        XQ = [self.env.ref('dha_medic_modifier.medic_test_type_image_test'), 'xq.image.test']
        SA = [self.env.ref('dha_medic_modifier.medic_test_type_echograph'), 'sa.image.test']
        DT = [self.env.ref('dha_medic_modifier.medic_test_type_electrocardiogram'), 'dtd.image.test']
        for xn_id in TestObj.search([('id', 'in', medical.medic_lab_test_compute_ids.ids), ('state','=','done')]):
            if res[0] == '':
                res[0] += xn_id.product_test.name + ': ' + (xn_id.note or '')
            else:
                res[0] += '\n' + xn_id.product_test.name + ': ' + (xn_id.note or '')
        index = 1
        for type,model_name in [XQ, SA, DT]:
            for img in self.env[model_name].search([('id', 'in', medical.medic_image_test_compute_ids.ids),('state','=','done')]):
                if res[index] == '':
                    res[index] += img.product_test.name + ': ' + (img.note or '')
                else:
                    res[index] += '\n' + img.product_test.name + ': ' + (img.note or '')
            index += 1
        return res

    @api.model
    def _compute_text_val(self, type, medical):
        # Param : Type in ('cxk', 'ngoai', 'san', 'mat', 'tmh', 'rhm', 'dl')

        FieldObj = self.env['ir.model.fields'].sudo()
        SubTreatment = self.env['medic.medical.sub.treatment']
        SubTM_ID = self.env['ir.model'].search([('model', '=', 'medic.medical.sub.treatment')])

        swith_type_field = {
            'cxk': ['khoa_co_xuong_khop', ['binh_thuong', 'gu', 'uon', 'hinh_chu_s', 'hinh_chu_c', 'treatment_note']],
            'ngoai': ['khoa_ngoai', ['treatment_note']],
            'san': ['khoa_san', ['treatment_note']],
            'mat': ['khoa_mat', ['phai_ko_kinh', 'phai_co_kinh', 'trai_co_kinh', 'trai_ko_kinh', 'treatment_note']],
            'tmh': ['khoa_tai_mui_hong',
                    ['trai_noi_thuong', 'trai_noi_tham', 'phai_noi_thuong', 'phai_noi_tham', 'treatment_note']],
            'rhm': ['khoa_rang_ham_mat', ['ham_tren', 'ham_duoi', 'treatment_note']],
            'dl': ['khoa_da_lieu', ['treatment_note']],
        }

        res = ''
        TypeID, ListFields = swith_type_field[type]
        TypeID = self.env.ref('dha_medic_modifier.' + TypeID)
        sub_tm_ = SubTreatment.search([('parent_id', '=', medical.id), ('buildings_type', '=', TypeID.id)], limit=1)
        if sub_tm_:
            for f in ListFields:
                if sub_tm_[f]:
                    field_id = FieldObj.search([('model_id', '=', SubTM_ID.id), ('name', '=', f)])
                    field_des = field_id.field_description
                    if field_id.ttype == 'boolean':
                        if res == '':
                            res += field_des
                        else:
                            res += '\n' + field_des
                    else:
                        if res == '':
                            res += field_des + ': ' + sub_tm_[f]
                        else:
                            res += '\n' + field_des + ': ' + sub_tm_[f]
        return [res, sub_tm_.phan_loai.name or '', sub_tm_.doctor_id.name or '']
    
    @api.multi
    def action_show_schedule(self):
        action = self.env.ref('dha_medic_modifier.action_company_contract_schedule').read()[0]
        action['domain'] = [('contract_id','=',self.id)]
        action['context'] = {'default_contract_id': self.id}
        return action

class ContractSchedule(models.Model):
    _name = 'company.contract.schedule'
    # _inherit = 'mail.thread'
    _description = 'Contract Schedule'
    # _order = 'id desc'

    name = fields.Char('Name', required=1)
    time_start = fields.Datetime('Start Time', required=1)
    time_end = fields.Datetime('End Time', required=1)
    note = fields.Text('Note')
    contract_id = fields.Many2one('res.partner.company.check', 'Contract ID', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='contract_id.company_id', string='Partner ID', store=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=1)
    
    @api.depends('name', 'contract_id')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.contract_id.company_id.name :
                name = record.contract_id.company_id.name + ' - ' +name
            record.display_name = name
    