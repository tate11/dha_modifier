# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.http import request
import MySQLdb
from odoo.exceptions import UserError, AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class WizardGetLabRes(models.TransientModel):
    _name = 'wizard.lab.res.flex'

    name = fields.Char('Flex Lab Number', required=1)
    line_ids = fields.Many2many('wizard.lab.res.flex.line', relation='wizard_lab_res_flex_lines_rel', col1='parent_id',
                                col2='line_id', string='Results')

    @api.onchange('name')
    def action_get_data(self):
        Product = self.env['product.product']
        if self.name:
            conn = MySQLdb.connect(host='113.161.80.198', user='root', passwd='dha@123@', db='flexclinic',
                                   port=13306, use_unicode=True, charset='utf8')
            cur = conn.cursor()
            count = cur.execute("""
                    select service_id, service_detail_id, result, index_normal 
                    from hpm_inspect_detail 
                    where inspect_id = '%s';
                """ % (self.name))
            if count > 0:
                datas = cur._rows
                for data in datas:
                    if not data[2] or not data[3]:
                        continue
                    if data[0]:
                        product_id = Product.search([('barcode', '=', data[0])])
                        if product_id:
                            if data[1]:
                                cur.execute(
                                    """SELECT service_detail from hpm_service_detail where id= '%s'""" % (data[1]))
                                rows = cur._rows
                                if len(rows) > 0:
                                    name = rows[0][0]
                                    result = data[2]
                                    normal_range = data[3]
                                    # .decode('utf8')
                                    self.line_ids += self.line_ids.new(
                                        {'name': name.encode('utf-8'), 'result': result, 'product_id': product_id.id,
                                         'normal_range': normal_range})
                                else:
                                    continue
                            else:
                                cur.execute(
                                    """SELECT service_name from hpm_service where service_id= '%s'; """ % (data[0]))
                                rows = cur._rows
                                if len(rows) > 0:
                                    name = rows[0][0]
                                    result = data[2]
                                    normal_range = data[3]
                                    self.line_ids += self.line_ids.new(
                                        {'name': name, 'result': result, 'product_id': product_id.id,
                                         'normal_range': normal_range})
            cur.close()
            conn.close()

    @api.multi
    def do_action(self):
        LabTestRes = self.env['medic.medical.lab.resultcriteria']
        TestObj = self.env['medic.test']
        ModelObj = self.env['medic.medical.bill'].browse(self.env.context.get('active_id', False))
        lines = self.line_ids
        while len(lines) > 0 and ModelObj:
            same_lines = lines.filtered(lambda r: r.product_id == lines[0].product_id)
            test_id = ModelObj.medic_lab_test_compute_ids.filtered(
                lambda r: r.product_test.id == lines[0].product_id.id)
            if not test_id:
                raise UserError(_('%s not existed!' % (lines[0].product_id.name)))

            test_id.write({'lab_test_criteria': [(6, 0, [])], 'state': 'done'})
            data = []
            for same in same_lines:
                LabTestRes.create({
                    'name': same.name,
                    'result': same.result,
                    'normal_range': same.normal_range,
                    # 'units' = fields.Many2one('medic.medical.lab.units', string='Units'),
                    # 'sequence' = fields.Integer(string='Sequence')
                    'medical_lab_test_id': test_id.id,
                })
            lines -= same_lines
        return

    @api.model
    def _get_lab_test_result(self):
        Product = self.env['product.product']
        Contract = self.env['res.partner.company.check']
        Test = self.env['medic.test']
        Medical = self.env['medic.medical.bill']
        TestLine = self.env['medic.medical.lab.resultcriteria']
        contract_ids = Contract.search([('state', '=', 'processing'), ('flex_id', '!=', False)])
        for contract_id in contract_ids:
            conn = MySQLdb.connect(host='113.161.80.198', user='root', passwd='dha@123@', db='flexclinic',
                                   port=13306, use_unicode=True, charset='utf8')
            cur = conn.cursor()
            count = cur.execute("""
                            select inspect_id, patient_id
                            from hpm_inspect
                            where contract_id = '%s' and result_flag = 1;
                        """ % (contract_id.flex_id))
            if count > 0:
                datas = cur._rows
                for data in datas:
                    if data[0].startswith('XN') and data[1]:
                        medical_ids = Medical.search(
                            [('company_check_id', '=', contract_id.id), ('customer.flex_id', '=', data[1])])
                        for medical_id in medical_ids:
                            try:
                                for test in Test.search(
                                        [('id', 'in', medical_id.medic_lab_test_compute_ids.ids),
                                         ('state', '!=', 'done')]):

                                    count = cur.execute("""
                                                            select service_detail_id, result, index_normal
                                                            from hpm_inspect_detail
                                                            where inspect_id = '%s' and service_id='%s'
                                                            ORDER BY service_detail_id asc;
                                                        """ % (data[0], test.product_test.barcode))
                                    if count > 0:
                                        test.write({'lab_test_criteria': [(6, 0, [])], 'state': 'done'})
                                        res_datas = datas = cur._rows
                                        index = 1
                                        for res in res_datas:
                                            if not res[1] or not res[2]:
                                                continue
                                            if res[0]:
                                                count = cur.execute(
                                                    """SELECT service_detail from hpm_service_detail where id= '%s'""" % (
                                                        res[0]))
                                                if count > 0:
                                                    name = cur._rows[0][0]
                                                    result = res[1]
                                                    normal_range = res[2]
                                                    TestLine.create({
                                                        'name': name,
                                                        'result': result,
                                                        'normal_range': normal_range,
                                                        'medical_lab_test_id': test.id,
                                                        'sequence': index
                                                    })
                                                    index += 1
                                            else:
                                                TestLine.create({
                                                    'name': test.product_test.name or '',
                                                    'result': res[1],
                                                    'normal_range': res[2],
                                                    'medical_lab_test_id': test.id,
                                                    'sequence': index
                                                })
                                                index += 1
                                    self._cr.commit()
                            except Exception as e:
                                _logger.error(e)
            for test in Test.search(
                    [('company_check_id', '=', contract_id.id), ('state', '!=', 'done'), ('is_adding', '=', True),
                     ('customer.flex_id', '!=', False)]):

                try:

                    count = cur.execute("""
                                            select d.service_detail_id, d.result, d.index_normal
                                            from hpm_inspect as i
                                            INNER JOIN hpm_inspect_detail as d
                                                ON i.inspect_id = d.inspect_id
                                            WHERE i.patient_id = '%s' and i.result_flag = 1 and d.service_id='%s'
                                            ORDER BY i.create_date DESC, d.service_detail_id asc;
                                        """ % (test.customer.flex_id, test.product_test.barcode))

                    if count > 0:
                        test.write({'lab_test_criteria': [(6, 0, [])], 'state': 'done'})
                        res_datas = datas = cur._rows
                        index = 1
                        for res in res_datas:
                            if not res[1] or not res[2]:
                                continue
                            if res[0]:
                                count = cur.execute(
                                    """SELECT service_detail from hpm_service_detail where id= '%s'""" % (
                                        res[0]))
                                if count > 0:
                                    name = cur._rows[0][0]
                                    result = res[1]
                                    normal_range = res[2]
                                    TestLine.create({
                                        'name': name,
                                        'result': result,
                                        'normal_range': normal_range,
                                        'medical_lab_test_id': test.id,
                                        'sequence': index
                                    })
                                    index += 1
                            else:
                                TestLine.create({
                                    'name': test.product_test.name or '',
                                    'result': res[1],
                                    'normal_range': res[2],
                                    'medical_lab_test_id': test.id,
                                    'sequence': index
                                })
                                index += 1
                    self._cr.commit()
                except Exception as e:
                    _logger.error(e)
            cur.close()
            conn.close()
        return True


class WizardGetLabResLines(models.TransientModel):
    _name = 'wizard.lab.res.flex.line'
    _order = 'product_id'

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', 'Service')
    result = fields.Char('Result')
    normal_range = fields.Char('Normal Range')
