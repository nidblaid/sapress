# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    agence_id = fields.Many2one("sochepress.destination", string="Agence")
    destination_id = fields.Many2one('sochepress.destination', string="Destination",
                                     track_visibility='onchange')
    driver_ids = fields.One2many('fleet.vehicle', 'driver_id', string="Drivers")
    vehicule_nbr = fields.Integer("Vehicle number", store=True,
                                  compute='_compute_vehicule')
    code_es = fields.Char("Code")
    cin = fields.Char('CIN')
    rc = fields.Char('RC')
    patente = fields.Char('Patente')
    article_sequence = fields.Char('Sequence of products')
    client_type = fields.Selection([
        ('ecommercant', "E-commercant"),
        ('b2b', "B2B"),
        ('b2c', "B2C"),
    ], default='b2b', string="Type client")
    code_portail = fields.Char('code portail')
    horaire_wanted_ids = fields.Many2many('delivery.timing', string="Delivery timings wanted")
    horaires = fields.Char(string="Horaires wanted")
    sequence = fields.Char()
    partner_latitude = fields.Float(digits=(16, 7))
    partner_longitude = fields.Float(digits=(16, 7))
    auto_accept_demand = fields.Boolean("Auto accept demand")
    validation_livraison = fields.Boolean("Validation livraison")
    _sql_constraints = [("name_uniq", "CHECK(1=1)", _("Customer's name already exist!")),
                        ("name_uuuu", "CHECK(1=1)", _("Customer's name already exist!"))]
    # _sql_constraints = []
    # @api.model
    # def compute_vehicule_driver(self):
    #     partners = self.env['res.partner'].search([])
    #     for partner in partners:
    #         partner._compute_vehicule()

    def auto_accept_demand_masse(self):
        for rec in self:
            rec.auto_accept_demand = not rec.auto_accept_demand

    @api.depends('driver_ids')
    def _compute_vehicule(self):
        for r in self:
            r.vehicule_nbr = len(r.driver_ids)
    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        for r in res:
            if r.company_type == 'company':
                if not r.sequence:
                    r.sequence = 'res.partner.%s' % r.name.replace(" ", "")
                    self.env['ir.sequence'].create({
                        'code': r.sequence,
                        'padding': 4,
                        'name': r.name,
                        'implementation': 'standard'
                    })
                # r.ref = self.env['ir.sequence'].next_by_code('ref.client') or 'SLS'
            elif r.company_type == 'person' and r.parent_id:
                # print("====> It is a person associeted to ", r.parent_id.name, "with the sequence",
                #       r.parent_id.sequence)
                if not r.parent_id.sequence and r.parent_id.name:
                    r.parent_id.sequence = 'res.partner.%s' % r.parent_id.name.replace(" ", "")
                    self.env['ir.sequence'].create({
                        'code': r.parent_id.sequence,
                        'padding': 4,
                        'name': r.parent_id.name,
                        'implementation': 'standard'
                    })
                code = ""
                if r.type == 'delivery':
                    code = "ADL"
                elif r.type == 'other':
                    code = "ADE"
                r.code_portail = "%s%s" % (code, self.env['ir.sequence'].next_by_code(r.parent_id.sequence))
        return res
    @api.onchange('company_type', 'parent_id')
    def compute_code_portail(self):
        for r in self:
            if r.company_type == 'company':
                if not r.sequence and r.name:
                    r.sequence = 'res.partner.%s' % r.name.replace(" ", "")
                    self.env['ir.sequence'].create({
                        'code': r.sequence,
                        'padding': 4,
                        'implementation': 'no_gap',
                        'name': r.name,
                    })
            elif r.company_type == 'person' and r.parent_id:
                if not r.parent_id.sequence and r.parent_id.name:
                    r.parent_id.sequence = 'res.partner.%s' % r.parent_id.name.replace(" ", "")
                    self.env['ir.sequence'].create({
                        'code': r.parent_id.sequence,
                        'padding': 4,
                        'implementation': 'no_gap',
                        'name': r.parent_id.name,
                    })
                code = ""
                if r.type == 'delivery':
                    code = "ADL"
                elif r.type == 'other':
                    code = "ADE"
                r.code_portail = "%s%s" % (code, self.env['ir.sequence'].next_by_code(r.parent_id.sequence))
            else:
                r.code_portail = ""
    def correction_partner(self, id):
        active_ids = self._context.get('active_ids')
        colis = self.env['sochepress.customer.request.line'].browse(active_ids)
        for c in colis:
            if c.expeditor_id.parent_id.id != id:
                c.customer_id = id


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    _sql_constraints = [
        ('unique_number', 'CHECK(1=1)', 'Account Number must be unique'),
    ]
