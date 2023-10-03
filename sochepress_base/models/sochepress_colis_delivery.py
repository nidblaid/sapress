# -*- coding: utf-8 -*-

from odoo import models, fields


class SochepressColisDelivery(models.Model):
    _name = 'sochepress.colis.delivery'
    _description = "Sochepress Colis Delivery"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(default='True')
