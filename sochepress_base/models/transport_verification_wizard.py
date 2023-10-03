# -*- coding: utf-8 -*-
from odoo import models, fields
# from odoo.tools.misc import profile
from odoo.tools.profiler import profile


class TransportVerification(models.TransientModel):
    _name = 'transport.verification.wizard'
    _description = "Transport Verification Wizard"

    ot_id = fields.Many2one('soch.transport.order', string="Transport Order")

    def next_position(self):
        # print('Hello from Wizard')
        vals = self.ot_id.next_position(next_position_checked=True)
        if vals is not None:
            action = vals.get('action', vals)
            return action
