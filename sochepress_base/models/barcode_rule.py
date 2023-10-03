# -*- coding: utf-8 -*-

from odoo import models, fields


class Kzm_BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    generate_model = fields.Selection(
        selection_add=[('sochepress.customer.request.line', 'Mes colis')])
