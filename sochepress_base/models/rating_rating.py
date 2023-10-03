# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RatingRating(models.Model):
    _inherit = 'rating.rating'

    destinator_id = fields.Many2one('res.partner', string='Destinator')

    @api.constrains('res_name')
    def get_colis(self):
        for r in self:
            colis_list = self.env['sochepress.customer.request.line'].search([
                ('name', '=', r.res_name), ('destinator_id', '=', r.destinator_id.id),
                ('request_id.customer_id', '=', r.partner_id.id),
                ('new_livreur_id.partner_id', '=', r.rated_partner_id.id)])
