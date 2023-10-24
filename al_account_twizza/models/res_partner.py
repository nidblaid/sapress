from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    default_intrastat_id = fields.Many2one(
        comodel_name="account.intrastat.code",
        string="Default intrastat code",
        domain=[('type', '=', 'transaction')]
    )
    default_intrastat_transport_id = fields.Many2one(
        comodel_name="account.intrastat.code",
        string="Default intrastat Transport mode",
        domain=[('type', '=', 'transport')]
    )
    default_incoterm_id = fields.Many2one('account.incoterms', string='Incoterm')
    allow_lock = fields.Boolean(string="Allow Lock on sales", default=True)
    lock_on_sales = fields.Boolean(string="Locked in sales", compute="_lock_on_sales")

    def _lock_on_sales(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.lock_on_sales = False
            if rec.parent_id:
                rec.lock_on_sales = rec.allow_lock and rec.parent_id.lock_on_sales
            if rec.allow_lock and rec.total_overdue > 0.0:
                for aml in rec.unreconciled_aml_ids:
                    if aml.company_id == self.env.company and not aml.blocked:
                        date_lock = (
                            aml.date_maturity if aml.date_maturity else aml.date
                        ) + relativedelta(days=aml.move_id.invoice_payment_term_id.max_payment_delay)
                        if today > date_lock:
                            rec.lock_on_sales = True

    def action_view_partner_invoices(self):
        action = super(ResPartnerInherit, self).action_view_partner_invoices()
        if not self.env.user.has_group('account.group_account_manager'):
            action['context'].update({
                'create': False,
                'edit': False
            })
        return action

    @api.model
    def _commercial_fields(self):
        return super(ResPartnerInherit, self)._commercial_fields() + ['allow_lock']
