# -*- coding: utf-8 -*-

from odoo import models, fields


class SlsReturnMethod(models.Model):
    _name = 'sls.return.method'
    _description = 'Sls Return Method'
    _order = 'sequence'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    montant_obligatoire = fields.Boolean('Obligatory Amount', default=True)
    null_amount = fields.Boolean('Null Amount')
    active = fields.Boolean(default='True')
    sequence = fields.Integer("Sequence", default='6')
