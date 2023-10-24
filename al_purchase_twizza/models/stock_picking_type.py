from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', copy=False, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account to use by default in a purchase order."
    )


