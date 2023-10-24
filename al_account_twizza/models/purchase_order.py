from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_view_invoice(self):
        action = super(PurchaseOrder, self).action_view_invoice()
        if not self.env.user.has_group('account.group_account_manager'):
            action['context'].update({
                'create': False,
                'edit': False
            })
        if self.incoterm_id:
            action['context'].update({
                'default_invoice_incoterm_id': self.incoterm_id.id,
            })
        return action

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        super(PurchaseOrder, self).onchange_partner_id()
        if self.partner_id.default_incoterm_id:
            self.incoterm_id = self.partner_id.default_incoterm_id.id


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        res.update({
            'intrastat_transaction_id': self.order_id.partner_id.default_intrastat_id[:1].id,
        })
        return res
