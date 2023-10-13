# -*- coding: utf-8 -*-

from odoo import fields, models


class KzmResCompany(models.Model):
    _inherit = "res.company"

    kzm_amount_letter_invoicing = fields.Boolean(string="Amount letter")
    kzm_code_designation_invoicing = fields.Boolean(string="Code / Designation")
    kzm_taxe_invoicing = fields.Boolean(string="Taxe")
    kzm_discount_invoicing = fields.Boolean(string="Discount")
    kzm_bank_invoicing = fields.Boolean(string="Bank")
    kzm_object_invoicing = fields.Boolean(string="Object")
    kzm_numbering_invoicing = fields.Boolean(string="Numbering Invoicing")
