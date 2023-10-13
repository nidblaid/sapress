# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    kzm_amount_letter_invoicing = fields.Boolean(
        related="company_id.kzm_amount_letter_invoicing",
        string="Amount letter", readonly=False)
    kzm_code_designation_invoicing = fields.Boolean(
        related="company_id.kzm_code_designation_invoicing",
        string="Code / Designation", readonly=False)
    kzm_taxe_invoicing = fields.Boolean(related="company_id.kzm_taxe_invoicing",
                                        string="Disable Taxe", readonly=False)
    kzm_discount_invoicing = fields.Boolean(related="company_id.kzm_discount_invoicing",
                                            string="Discount",
                                            readonly=False)
    kzm_bank_invoicing = fields.Boolean(related="company_id.kzm_bank_invoicing",
                                        string="Bank", readonly=False)
    kzm_object_invoicing = fields.Boolean(related="company_id.kzm_object_invoicing",
                                          string="Object", readonly=False)
    kzm_numbering_invoicing = fields.Boolean(
        related="company_id.kzm_numbering_invoicing", string="Numbering Invoicing",
        readonly=False)
    group_without_header_footer_account = fields.Boolean(
        implied_group='kzm_invoice_report.group_without_header_footer_account',
        string="Without Header and Footer")




