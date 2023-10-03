from odoo import api, models, fields


class SochepressJustif(models.Model):
    _name = 'sochepress.justif'
    _description = 'Justificatif Livraison'

    name = fields.Char()
    justif = fields.Binary(string='Justif')
    doc_id = fields.Many2one('sochepress.document.type', string='Document')
    colis_id = fields.Many2one('sochepress.customer.request.line', string="Colis")

# class sochepressBarcode(models.Model):
#     _name = 'sochepress.barcode'
#
#     name = fields.Char()
#     colis_id = fields.
