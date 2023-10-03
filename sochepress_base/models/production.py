# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def update_product(self):
        lignes = self.env['product.template'].browse(
            self._context.get('active_ids', []))
        for r in lignes:
            r.is_modele_colis = True
            r.company_id = self.env.company
            r._compute_conform()
