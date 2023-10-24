from odoo import fields, models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    unit_volume = fields.Float('Unit Volume', digits='Volume')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    duration_type = fields.Selection([
        ('dluo', "DLUO"),
        ('dlc', "DLC"),
    ], string="Duration Type")

    unit_volume = fields.Float(string="Unit Volume", compute='_compute_unit_volume', inverse='_set_unit_volume',
                               digits='Volume', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.unit_volume')
    def _compute_unit_volume(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.unit_volume = template.product_variant_ids.unit_volume
        for template in (self - unique_variants):
            template.unit_volume = 0.0

    def _set_unit_volume(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.unit_volume = template.unit_volume
