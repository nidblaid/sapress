# -*- coding: utf-8 -*-

from odoo import models, fields


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_disponible = fields.Boolean("Disponibility")
    vehicule_weight = fields.Float("Vehicule weight")
    vehicule_volume = fields.Float("Vehicule volume")
    agence_id = fields.Many2one("sochepress.destination", string="Agence")
    agence_ids = fields.Many2many('sochepress.destination', string="Agences secondaires")
