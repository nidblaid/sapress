# -*- coding: utf-8 -*-

from itertools import groupby
from odoo import models, fields, api
from operator import itemgetter


class TypeColis(models.Model):
    _name = 'sochepress.type.colis'
    _description = "Sochepress type colis model"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name")
    weight = fields.Float(string="Weight")
    volume = fields.Float(string="Volume")
    characteristics = fields.Text("Characteristics")


class TracabiliteColis(models.Model):
    _name = 'sochepress.tracabilite.colis'
    _description = "Sochepress colis model"
    _order = 'date'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name")
    operation_type = fields.Selection([
        ('charge', "Charge"),
        ('discharge', "Discharge"),
        ('delivered', "Livraison"),
        ('refused', "Refuse"),
        ('not_pickup', "Not pickup"),
        ('report', "Reported"),
        ('non_delivered', "Non delivered"),
        ('retract', "Retractation"),
    ], default='charge', track_visibility='onchange')
    source_id = fields.Many2one('sochepress.destination', string="Place",
                                track_visibility='onchange')
    # destination_id = fields.Many2one('sochepress.destination',
    # string="Destination", track_visibility='onchange')
    operator_id = fields.Many2one('res.users', string="Operator",
                                  default=lambda self: self.env.uid,
                                  track_visibility='onchange')
    date = fields.Datetime(string="Date", default=fields.Datetime.now(),
                           track_visibility='onchange')
    colis_id = fields.Many2one('sochepress.customer.request.line', string="Colis")
    order_id = fields.Many2one(related='colis_id.order_id', string="Transport order")
    position_final = fields.Char("Position", compute='get_all_address', store=1)
    active = fields.Boolean(default=True)

    @api.depends('operation_type')
    def get_all_address(self):
        for r in self:
            colis = r.colis_id

            if r.operation_type == 'delivered':
                dest = colis.destinator_id
                name = dest.name + ", " if dest.name and len(dest.name) > 0 else ""
                street1 = dest.street + ", " if dest.street and len(
                    dest.street) > 0 else ""
                street2 = dest.street2 + ", " if dest.street2 and len(
                    dest.street2) > 0 else ""
                country = dest.country_id.name + " - " if dest.country_id else ""
                r.position_final = "%s%s%s%s%s" % (
                    name, street1, street2, country,
                    r.order_id.current_position_id.name)
            else:
                r.position_final = r.source_id.name

    def correct_tracabilite(self):
        lignes = self.env['sochepress.tracabilite.colis'].browse(
            self._context.get('active_ids', []))
        for key, l in groupby(lignes, lambda z: z.colis_id):
            l = list(l)
            traces = [(t, t.create_date) for t in key.tracabilite_ids]
            nbr_traces = len(key.tracabilite_ids)
            traces.sort(key=itemgetter(1), reverse=True)
            for i in range(0, nbr_traces):
                index = 2 * i + 1
                if index < nbr_traces:
                    if traces[index][0] in l and traces[index][0].operation_type == 'discharge':
                        traces[index][0].operation_type = 'charge'
                else:
                    break
