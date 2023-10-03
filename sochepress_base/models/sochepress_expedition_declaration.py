# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SochepressExpeditionDeclaration(models.Model):
    _name = 'sochepress.declaration'
    _description = 'Sochepress Expedition Declaration '

    name = fields.Char(string="Name", default="DExp")
    request_id = fields.Many2one('sochepress.customer.request',
                                 string="Customer Request")
    customer_id = fields.Many2one('res.partner', string="Customer")
    expeditor_id = fields.Many2one('res.partner', string="Expeditor")
    destinator_id = fields.Many2one('res.partner', string="Destinator")
    return_fund = fields.Selection(related="request_id.return_of_fund",
                                   string="Return of fund")
    sum_in_number = fields.Float(related="request_id.sum_in_number",
                                 string="Sum in number")
    colis_ids = fields.Many2many('sochepress.customer.request.line', string="Packages")
    ot_id = fields.Many2one('soch.transport.order')
    date_acceptation = fields.Char()
    min_date = fields.Char()
    max_date = fields.Char()
    planned_delivery_max_date = fields.Datetime(string="Maximum planned delivery date",
                                                compute='set_dates', store=1)
    planned_delivery_min_date = fields.Datetime(string="Minimum planned delivery date",
                                                compute='set_dates', store=1)
    printed = fields.Boolean()

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('sochepress.declaration') or 'BL'
        vals['name'] = seq
        res = super(SochepressExpeditionDeclaration, self).create(vals)
        return res

    @api.depends('colis_ids')
    def set_dates(self):
        for r in self:
            # filtered = r.colis_ids.filtered(lambda c:)
            max_date_list = [c.planned_delivery_max_date for c in r.colis_ids]
            if max_date_list:
                r.planned_delivery_max_date = sorted(max_date_list)[-1]

            min_date_list = [c.planned_delivery_min_date for c in r.colis_ids]
            if min_date_list:
                r.planned_delivery_min_date = sorted(min_date_list)[0]

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Bordereau de livraison %s de la demande %s' % (self.name, self.request_id.name)
