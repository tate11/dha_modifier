# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    helpdesk_id = fields.Many2one('helpdesk.ticket', 'Helpdesk ID')
    
    @api.multi
    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        HelpdeskStage = self.env['helpdesk.stage'].sudo()
        if 'stage_id' in vals:
            stage_id = self.env['project.task.type'].search([('id', '=', vals['stage_id'])])
            if stage_id and stage_id.name == 'Done':
                for record in self:
                    if record.helpdesk_id:
                        helpdesk_stage = HelpdeskStage.search([('team_ids','in',[record.helpdesk_id.team_id.id]),('name','=',stage_id.name)],limit=1)
                        if helpdesk_stage:
                            # record.helpdesk_id.write({'stage_id': helpdesk_stage.id})
                            self._cr.execute("""
                                UPDATE helpdesk_ticket
                                SET stage_id = %s
                                Where id= %s
                            """%(helpdesk_stage.id, record.helpdesk_id.id))
        return res