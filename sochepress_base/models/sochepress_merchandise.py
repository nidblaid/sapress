# -*- coding: utf-8 -*-

from odoo import models, fields


class SochepressMarchandise(models.Model):
    _name = 'sochepress.merchandise'
    _description = "Sochepress Marchandise"

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
