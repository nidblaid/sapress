# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    see_details = fields.Boolean("See Details")
    sochepress_contract_id = fields.Many2one('sochepress.contract', string="Contract")

    # def see_customer_request_details(self):
    #     action = self.env.ref('sochepress_invoicing.customer_request_line_action').read()[0]
    #     # requests = self.env['sochepress.customer.request'].search(
    #     #     [('invoice_ids', 'in', self.id)])
    #     # lines = []
    #     # for request in requests:
    #     #     lines += [line.id for line in request.request_line_ids]
    #     # # print(lines)
    #     # if len(lines) > 0:
    #     #     action = \
    #     #         self.env.ref('sochepress_base.customer_request_line_action').read()[0]
    #     #     action['domain'] = [('id', 'in', lines), ('invoice_id', '=', self.id)]
    #     #     return action
