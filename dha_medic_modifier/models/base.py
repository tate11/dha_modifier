# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError



class Base(models.AbstractModel):
    """ The base model, which is implicitly inherited by all models. """
    _inherit = 'base'

    @api.multi
    def unlink(self):
        ModelLimit = ['medic.test', 'medic.medical.bill']
        if self._name in ModelLimit:
            admin = self.env.ref('base.group_system').users
            if all(self._uid != user.id for user in admin):
                raise AccessError (_('Please contact your Administrator to delete %s'%(self._name)))
        return super(Base, self).unlink()