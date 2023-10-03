# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SochepressContract(models.Model):
    _name = 'sochepress.contract'
    _description = "Sochepress contract model"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_stage_id(self):
        return self.env['sochepress.contract.stage'].search([], order='sequence',
                                                            limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.sudo().search([], order=order)

    name = fields.Char(string="Contract", default='CTR')
    code = fields.Char(string="Code")
    partner_id = fields.Many2one('res.partner', string="Customer", required=True,
                                 track_visibility='onchange')
    start_date = fields.Date("Start date", track_visibility='onchange')
    end_date = fields.Date("End date", track_visibility='onchange')
    user_id = fields.Many2one('res.users', string="User",
                              default=lambda self: self._uid)
    to_renew = fields.Boolean("To renew")
    # facturation_mode = fields.Selection([('forfait', "Forfait"), ('tarif',
    # "Tarification grill")],
    #                                     string="Invoicing mode", default='forfait',
    #                                     track_visibility='onchange')
    # fix_price = fields.Float("Fix price", track_visibility='onchange')
    tarification_grill_id = fields.Many2one('soch.price.list',
                                            string="Tarification grill",
                                            track_visibility='onchange')
    reference = fields.Char("Reference", track_visibility='onchange')
    conditions = fields.Text("General terms")
    stage_id = fields.Many2one('sochepress.contract.stage', string="Stage", index=True,
                               default=lambda s: s._get_default_stage_id(),
                               copy=False, group_expand='_read_group_stage_ids',
                               tracking=True)
    # invoice_ids = fields.One2many('account.move', 'sochepress_contract_id', string="Invoices")
    insurance_rate = fields.Float("Insurrance rate", track_visibility='onchange')
    destination_ids = fields.Many2many('sochepress.destination',
                                       string="Destinations")
    type_policy = fields.Selection([
        ('text', "Text"),
        ('file', "File"),
    ], string="Return Policy Format")
    return_policy = fields.Text(string="Return Policy")
    policy_file = fields.Binary(string="Policy File")
    output_nom = fields.Char('File name', default='Policy_file')
    retun_rate = fields.Float(string="Percentage of returns invoiced", default=50)
    acceptation_delay = fields.Integer(string="Return acceptance period")
    cod_percent = fields.Float(string="Percentage of the amount to be recovered")
    max_amount = fields.Float(string="Maximum amount")
    min_amount = fields.Float(string="Minimum amount")
    pod_amount = fields.Float(string="POD amount")
    documentary_return = fields.Boolean('Documentary Return')
    invoice_count = fields.Integer('Count Invoices', compute='_count_invoice', store=1)
    demande_count = fields.Integer('Count Demandes', compute='_count_demandes', store=1)
    expeditions_count = fields.Integer('Count Expeditions', compute='_count_expeditions', store=1)
    colis_count = fields.Integer('Count Colis', compute='_count_colis', store=1)

    # @api.onchange('tarification_grill_id', 'tarification_grill_id.price_list_ids')
    # def _compute_max(self):
    #     for r in self:
    #         r.max_weight = 0
    #         r.max_volume = 0
    #         if r.tarification_grill_id:
    #             # if r.max_weight >= 0 and r.max_volume >= 0:
    #             # r.max_weight = False
    #             # r.max_volume = False
    #             request_max_weight = """
    #                         select max(max_value) from soch_price_list_rule
    #                         where variable like '%s' and price_list_id = %s
    #                 """ % ('weight', r.tarification_grill_id.id)
    #             request_max_volume = """
    #                                     select max(max_value) from soch_price_list_rule
    #                                     where variable like '%s' and price_list_id = %s
    #                             """ % ('volume', r.tarification_grill_id.id)
    #             self.env.cr.execute(request_max_weight)
    #             # print("==============> MAX WEIGHT", self.env.cr.fetchone()[0] or 0.0)
    #             r.max_weight = float(self.env.cr.fetchone()[0] or 0)
    #
    #             self.env.cr.execute(request_max_volume)
    #             # print("==============> MAX volume", self.env.cr.fetchone()[0] or 0.0)
    #             r.max_volume = float(self.env.cr.fetchone()[0] or 0)

    # def compute_max(self):
    #     for r in self:
    #         request_max_weight = """
    #                     select max(max_value) from soch_price_list_rule
    #                     where variable like '%s' and price_list_id = %s
    #             """ % ('weight', r.tarification_grill_id.id)
    #         request_max_volume = """
    #                                 select max(max_value) from soch_price_list_rule
    #                                 where variable like '%s' and price_list_id = %s
    #                         """ % ('volume', r.tarification_grill_id.id)
    #         self.env.cr.execute(request_max_weight)
    #         # print("==============> MAX WEIGHT", self.env.cr.fetchone()[0] or 0.0)
    #         r.max_weight = float(self.env.cr.fetchone()[0] or 0)
    #
    #         self.env.cr.execute(request_max_volume)
    #         # print("==============> MAX volume", self.env.cr.fetchone()[0] or 0.0)
    #         r.max_volume = float(self.env.cr.fetchone()[0] or 0)

    # @api.onchange('insurance_rate')
    # def update_colis_prices(self):
    #     for r in self:
    #         all_requests = self.env['sochepress.customer.request'].search(
    #             [('customer_id', '=', r.partner_id.id)])
    #         for request in all_requests:
    #             for line in request.request_line_ids:
    #                 line.compute_price()

    @api.depends('partner_id')
    def _count_invoice(self):
        for r in self:
            invoices = self.env['account.move'].search([('partner_id', '=', r.partner_id.id)])
            r.invoice_count = len(invoices)

    def see_invoices(self):
        invoices = self.env['account.move'].search([('partner_id', '=', self.partner_id.id)])
        if len(invoices) != 0:
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            action['domain'] = [('partner_id', '=', self.partner_id.id)]
            action['views'] = [(self.env.ref('account.view_invoice_tree').id, 'tree'),
                               (self.env.ref('account.view_move_form').id, 'form')]
        else:
            raise UserError(_('Any invoice for the client of this contract '))
        return action

    @api.depends('partner_id')
    def _count_demandes(self):
        for r in self:
            demandes = self.env['sochepress.customer.request'].search([('customer_id', '=', r.partner_id.id)])
            r.demande_count = len(demandes)

    def see_demandes(self):
        demandes = self.env['sochepress.customer.request'].search([('customer_id', '=', self.partner_id.id)])
        if len(demandes) != 0:
            action = self.env.ref('sochepress_base.customer_request_action').read()[0]
            action['domain'] = [('customer_id', '=', self.partner_id.id)]
            action['views'] = [(self.env.ref('sochepress_base.customer_request_tree_view_tt').id, 'tree'),
                               (self.env.ref('sochepress_base.customer_request_form_view').id, 'form')]
        else:
            raise UserError(_('Any demandes for the client of this contract '))

        return action

    @api.depends('partner_id')
    def _count_expeditions(self):
        for r in self:
            expeditions = self.env['sochepress.declaration'].search([('customer_id', '=', r.partner_id.id)])
            r.expeditions_count = len(expeditions)

    def see_expeditions(self):
        expeditions = self.env['sochepress.declaration'].search([('customer_id', '=', self.partner_id.id)])
        if len(expeditions) != 0:
            action = self.env.ref('sochepress_base.sochepress_declaration_action').read()[0]
            action['domain'] = [('customer_id', '=', self.partner_id.id)]
            action['views'] = [(self.env.ref('sochepress_base.view_sochepress_declaration_tree').id, 'tree'),
                               (self.env.ref('sochepress_base.view_sochepress_declaration_form').id, 'form')]
        else:
            raise UserError(_('Any Expeditions for the client of this contract '))

        return action

    @api.depends('partner_id')
    def _count_colis(self):
        for r in self:
            colis = self.env['sochepress.customer.request.line'].search([('customer_id', '=', r.partner_id.id)])
            r.colis_count = len(colis)

    def see_colis(self):
        colis = self.env['sochepress.customer.request.line'].search([('customer_id', '=', self.partner_id.id)])
        if len(colis) != 0:
            action = self.env.ref('sochepress_base.customer_request_line_action').read()[0]
            action['domain'] = [('customer_id', '=', self.partner_id.id)]
            action['views'] = [(self.env.ref('sochepress_base.customer_request_line_tree2_view').id, 'tree'),
                               (self.env.ref('sochepress_base.customer_request_line_form_view').id, 'form')]
        else:
            raise UserError(_('Any Colis for the client of this contract '))
        return action

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('sochepress.contract') or 'CTR'
        vals['code'] = seq
        vals['name'] = "%s - %s" % (
            self.env['res.partner'].browse(vals['partner_id']).name, seq)
        return super(SochepressContract, self).create(vals)

    @api.constrains('partner_id')
    def _change_name(self):
        for r in self:
            if r.partner_id:
                r.name = "%s - %s" % (r.partner_id.name, r.code)

    # @api.onchange('tarification_grill_id')
    # @api.depends('tarification_grill_id', 'tarification_grill_id.price_list_ids')
    # def compute_destinations(self):
    #     for r in self:
    #         r.destination_ids = []
    #         if r.tarification_grill_id:
    #             sources = []
    #             request_sources = """
    #                 select distinct source_id from soch_price_list_rule where price_list_id = %s
    #             """ % r.tarification_grill_id.id
    #             self.env.cr.execute(request_sources)
    #             data_rub = self.env.cr.dictfetchall()
    #             for d in data_rub:
    #                 sources.append(d['source_id'])
    #
    #             request_destinations = """
    #                             select distinct destination_id from soch_price_list_rule where price_list_id = %s
    #                         """ % r.tarification_grill_id.id
    #             self.env.cr.execute(request_destinations)
    #             data_rub = self.env.cr.dictfetchall()
    #             for d in data_rub:
    #                 if d['destination_id'] not in sources:
    #                     sources.append(d['destination_id'])
    #             r.destination_ids = [(6, 0, sources)]


class SochepressContractStage(models.Model):
    _name = 'sochepress.contract.stage'
    _order = 'sequence, id'
    _description = 'Contracts stage'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(
        "Requirements",
        help="Enter here the internal requirements for this stage. It will appear "
             "as a tooltip over the stage's name.", translate=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when there '
                               'are not records in that stage to display.')
