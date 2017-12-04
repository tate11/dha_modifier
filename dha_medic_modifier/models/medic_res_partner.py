# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
import base64
from odoo.modules import get_module_path
from ..service.service_read_xlsx import ServiceReadXlsx



ADDRESS_FORMAT_CLASSES = {
    '%(city)s %(state_code)s\n%(zip)s': 'o_city_state',
    '%(zip)s %(city)s': 'o_zip_city'
}

ADDRESS_FIELDS = ('street', 'street2', 'ward', 'district', 'city_dropdown', 'city', 'country_id', 'zip', 'state_id')



class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('city_dropdown')
    def _compute_city_(self):
        for record in self:
            record.city = record.city_dropdown.name or False


    @api.depends('day_of_birth')
    def _compute_age(self):
        for record in self:
            if record.day_of_birth:
                now = datetime.now()
                delta = now - datetime.strptime(record.day_of_birth, '%Y-%m-%d')
                record.age = '%s years %s days' % (delta.days / 365, delta.days % 365)

    @api.model
    def _get_default_vn_(self):
        try:
            return self.env.ref('base.vn').id
        except:
            return False

    # đổi thành kiểu địa chỉ việt nam
    city_dropdown = fields.Many2one('res.partner.city', 'City')
    city = fields.Char('City', compute='_compute_city_', store=1)
    district = fields.Many2one('res.partner.district', 'District')
    ward = fields.Many2one('res.partner.ward', 'Ward')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_get_default_vn_)


    # Mã Bệnh
    customer_id = fields.Char('Customer ID', readonly=1)
    # giới tính
    sex = fields.Selection([('male', 'Male'),('female','Female')], 'Sex')
    # ngày khám cuối cùng
    last_check_in_time = fields.Datetime('Last Check In Time')
    day_of_birth = fields.Date('Day of Birth')
    age = fields.Char('Ages', compute=_compute_age)
    # Dân tộc
    ethnic_id = fields.Many2one('res.partner.ethnic', 'Ethnic ID')
    # quoc tich
    nationality_id = fields.Many2one('res.country', 'Nationality')
    cmnd_passport = fields.Char('CMND/PassPort')
    married_status = fields.Selection([
        ('single', 'Single'),
        ('married','Married'),
        ('divorced', 'Divorced'),
        ('separated', 'Separated'),
    ], 'Married Status')
    # tab gia dinh
    # family_persons = fields.One2many('res.partner.family', 'partner_id', 'Family')
    # tab bao hiem
    insurrance_ids = fields.One2many('res.partner.insurrance', 'partner_id', string='Partner ID')
    # don thuoc
    medicine_order_ids = fields.One2many('medicine.order', 'customer', 'Medicine Order')

    # TESTs
    medic_lab_test_compute_ids = fields.Many2many('medic.test', 'Lab Tests', compute='_get_medic_test_ids')
    medic_image_test_compute_ids = fields.Many2many('medic.test', 'Image Tests', compute='_get_medic_test_ids')
    medic_test_ids = fields.One2many('medic.test', 'customer', 'Tests', domain=[('state', 'in', ['new', 'processing'])])

    # Tien su benh
    # tien_su_gia_dinh = fields.Char('Family history of medical illness')
    # tien_can = fields.Char('Past medical and surgical history')
    # di_ung_thuoc = fields.Char('Drug allergy')
    # thuoc_la = fields.Char('Smoking')
    # ruou = fields.Char('Alcolhol')
    # the_thao = fields.Char('Exercises')
    # tiem_ngua = fields.Char('Vaccination')


    # tab kham cho cong ty
    company_medial_ids = fields.One2many('res.partner.company.check', 'company_id', 'Company Check')
    total_history = fields.Float('Check History', compute='_get_company_check_number')

    is_patient = fields.Boolean('Patient', default=False)
    description = fields.Char('Description')

    @api.onchange('country_id')
    def _onchange_address_country_id(self):
        res = {'domain':{}}
        self.city_dropdown = False
        self.district = False
        self.ward = False
        if self.country_id:
            res['domain']['city_dropdown'] = [('country_id','=', self.country_id.id)]
        return res

    @api.onchange('city_dropdown')
    def _onchange_address_city_dropdown(self):
        res = {'domain': {}}
        self.district = False
        self.ward = False
        if self.city_dropdown:
            if self.city_dropdown.city_type == 'city_in_province':
                res['domain']['ward'] = [('parent_code', '=', self.city_dropdown.code)]
                res['domain']['district'] = [('id','in', [])]
            else:
                res['domain']['district'] = [('parent_code', '=', self.city_dropdown.code)]
        return res

    @api.onchange('district')
    def _onchange_address_district(self):
        res = {'domain': {}}
        self.ward = False
        if self.district:
            res['domain']['ward'] = [('parent_code', '=', self.district.code)]
        return res


    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    @api.multi
    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self.country_id.address_format or \
                         "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
            'company_name': self.commercial_company_name or '',
            'ward_name' : self.ward.name or '',
            'district_name': self.district.name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._address_fields() + [
            'country_id.address_format', 'country_id.code', 'country_id.name',
            'company_name', 'ward.name', 'city_dropdown.name', 'district.name'
        ]

    def _get_company_check_number(self):
        CompanyCheck = self.env['res.partner.company.check']
        for record in self:
            record.total_history = len(CompanyCheck.search([('company_id', '=', record.id)]))

    def _get_medic_test_ids(self):
        MedictTest = self.env['medic.test']
        lab_type = [self.env.ref('dha_medic_modifier.medic_test_type_lab_test').id]
        image_type = [self.env.ref('dha_medic_modifier.medic_test_type_image_test').id,
                      self.env.ref('dha_medic_modifier.medic_test_type_echograph').id,
                      self.env.ref('dha_medic_modifier.medic_test_type_electrocardiogram').id]
        for record in self:
            record.medic_lab_test_compute_ids = MedictTest.search(
                [('customer', '=', record.id), ('type', 'in', lab_type)])
            record.medic_image_test_compute_ids = MedictTest.search(
                [('customer', '=', record.id), ('type', 'in', image_type)])

    _sql_constraints = [
        ('cmnd_passport_uniq', 'unique (cmnd_passport)', _('CMND/PassPort must be unique !'))]

    @api.constrains('day_of_birth')
    def _check_day_of_birth(self):
        for record in self:
            if record.day_of_birth:
                now = datetime.now()
                if datetime.strptime(record.day_of_birth, '%Y-%m-%d') > now:
                    raise ValidationError(_('Day of Birth must be less than now!'))

    @api.multi
    def action_go_person_inv(self):
        for record in self:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': False,
                'context': {'default_partner_id': record.id, 'form_view_ref': 'account.invoice_form',
                            'default_order_type': 'medical'}
            }

    @api.multi
    def open_company_check_history(self):
        for record in self:
            CompanyCheck = self.env['res.partner.company.check']
            ids = CompanyCheck.search([('company_id', '=', record.id)]).ids
            action = self.env.ref('dha_medic_modifier.action_res_partner_company_check')
            action = action.read()[0]
            action['domain'] = [('id', 'in', ids)]
            return action

    @api.multi
    def action_go_select_package(self):
        for record in self:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.parse.package',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': False,
                'context': {'default_customer': record.id}
            }

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res.is_patient:
            if self.env.context.get('from_external_center', False):
                try:
                    code = self.env.ref('dha_medic_modifier.out_center_department').code
                except:
                    code = '999'
            else:
                code = '000'
                EmployeeObj = self.env['hr.employee']
                emp_id = EmployeeObj.search([('user_id', '=', self._uid)], limit=1)
                if emp_id.department_id:
                    center = emp_id.department_id.find_center()
                    if center:
                        code = center.code or '000'
            code = code + self.env['ir.sequence'].next_by_code('customer.id.seq')
            res.write({'customer_id': code})
        return res

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        return res

    @api.multi
    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''

            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s - %s" % (name, partner.commercial_company_name or partner.parent_id.name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res

class PartnerEthnic(models.Model):
    _name = 'res.partner.ethnic'

    name = fields.Char('Name', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('The ethnic group must be unique !'))]

class PartnerFamily(models.Model):
    _name = "res.partner.family"

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', 'Partner ID', required=True, ondelete='cascade')
    person_id = fields.Many2one('res.partner', 'Related Customer', required=True)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Sex')
    day_of_birth = fields.Date('Day of Birth')
    relation = fields.Char('Relationship')
    mobile = fields.Char('Mobile')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.person_id:
            self.mobile = self.person_id.mobile or ''
            self.sex = self.person_id.sex or False
            self.day_of_birth = self.person_id.day_of_birth


class PartnerInsurrance(models.Model):
    _name = 'res.partner.insurrance'

    name = fields.Char('Number')
    type = fields.Many2one('res.partner.insurrance.type')
    join_date = fields.Date('Create Date')
    expiry_date = fields.Date('Expiry Date')
    partner_id = fields.Many2one('res.partner', 'Partner ID', required=True, ondelete='cascade')
    # ma kham chua benh ban dau
    first_code = fields.Char('Code')
    # Noi Kham Chua benh ban dau
    address = fields.Text('Address')
    # kiem tra trai tuyen hay khong
    check_line = fields.Boolean('Check Line', default=False)


class PartnerInsurranceLines(models.Model):
    _name = 'res.partner.insurrance.type'

    name = fields.Char('Name')

class PartnerDistrict(models.Model):
    _name = 'res.partner.district'

    name = fields.Char('Name', required=1)
    code = fields.Char('Code')
    parent_code = fields.Char('Parent Code')

class PartnerCity(models.Model):
    _name = 'res.partner.city'

    name = fields.Char('Name', required=1)
    parent_code = fields.Char('Parent Code')
    city_type = fields.Selection([('city','city'),('city_in_province', 'City in Province')], string='Type', default='city')
    country_id = fields.Many2one('res.country','Country Id')
    code = fields.Char('Code')

class PartnerWard(models.Model):
    _name = 'res.partner.ward'

    name = fields.Char('Name', required=1)
    parent_code = fields.Char('Parent Code')
    code = fields.Char('Code')

class ResCountry(models.Model):
    _inherit = 'res.country'

    @api.model
    def change_viet_nam_address_format(self):
        try:
            vn_country = self.env.ref('base.vn')
            vn_country.write({
                'address_format': "%(street)s %(street2)s\n%(ward_name)s %(district_name)s %(city)s\n%(country_name)s"})
        except:
            pass

    @api.model
    def import_template_country_data(self):
        Service = ServiceReadXlsx()
        City = self.env['res.partner.city']
        Ward = self.env['res.partner.ward']
        District = self.env['res.partner.district']
        VN = self.env.ref('base.vn').id

        module_path = get_module_path('dha_medic_modifier')
        city_file_path = module_path + '/static/file/city_data.xlsx'
        district_file_path = module_path + '/static/file/district_data.xlsx'
        ward_file_path = module_path + '/static/file/ward_data.xlsx'

        file1 = open(city_file_path, 'r')
        datas1 = (file1.read())
        data_obj1 = Service.read_xls(datas1)

        type_switch = {
            '1': City,
            '2': City,
            '3': District,
            '4': Ward,
        }
        data_obj1.next()
        for data in data_obj1:
            tmp_data = {
                'country_id' : VN,
                'city_type' : 'city',
                'name' : data[1],
                'code' : data[0],
            }
            City.create(tmp_data)

        file2 = open(district_file_path, 'r')
        datas2 = (file2.read())
        data_obj2 = Service.read_xls(datas2)
        data_obj2.next()
        for data in data_obj2:
            tmp_data = {
                'parent_code' : data[3],
                'name' : data[1],
                'code' : data[0],
            }
            if data[2] == 2 or data[2] == '2':
                tmp_data.update({
                    'country_id' : VN,
                    'city_type': 'city_in_province',
                })

            data_object = type_switch[str(data[2])]
            data_object.create(tmp_data)

        file3 = open(ward_file_path, 'r')
        datas3 = (file3.read())
        data_obj3 = Service.read_xls(datas3)
        data_obj3.next()
        for data in data_obj3:
            tmp_data = {
                'parent_code': data[3],
                'name': data[1],
                'code': data[0],
            }
            data_object = type_switch[str(data[2])]
            data_object.create(tmp_data)
