from odoo import fields, models, api, exceptions, _


class ProductPriceListInherit(models.Model):
    _inherit = "product.pricelist"

    company_id = fields.Many2one(default=lambda x: x.env.company.id)

    # @api.constrains('company_id')
    # def _check_no_company(self):
    #     for rec in self:
    #         if not rec.company_id and not self.env.user.has_group('base.group_system'):
    #             raise exceptions.ValidationError(
    #                 _("Sorry, You're not allowed to modify this price list please contact your administrator.")
    #             )
