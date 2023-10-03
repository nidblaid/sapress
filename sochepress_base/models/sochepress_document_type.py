# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SochepressDocumentType(models.Model):
    _name = 'sochepress.document.type'
    _description = "Sochepress Document Type"
    _rec_name = 'display_name'

    name = fields.Char(string="Name")
    display_name = fields.Char(string="Display Name", compute='_set_display_name')
    description = fields.Char(string="Description")
    return_type = fields.Selection([
        ('physical', "Physique"),
        ('digital', "Digital"),
    ], string="Return Type", default="physical")
    active = fields.Boolean(default='True')

    @api.onchange('name', 'return_type')
    def _set_display_name(self):
        for r in self:
            return_type = False
            if r.return_type == 'physical':
                return_type = 'Physique'
            elif r.return_type == 'digital':
                return_type = 'Digital'

            if return_type:
                r.display_name = _("%s (%s)") % (r.name, return_type)
            else:
                r.display_name = r.name
