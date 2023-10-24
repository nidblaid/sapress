from odoo import fields, models, api


class CrmTeam(models.Model):
    _inherit = "crm.team"

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', copy=False,
        help="The analytic account to use by default in a sales order."
    )
