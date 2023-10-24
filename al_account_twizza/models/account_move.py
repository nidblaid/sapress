from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    payment_mode_id = fields.Many2one("payment.mode", string="Payment Mode")

    def post(self):
        # bypass access right check on action_post if group_create_invoices_from_sales
        if self.env.user.has_group('al_account_twizza.group_account_invoice_adv'):
            self = self.sudo()
        return super(AccountMoveInherit, self).post()

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super()._onchange_partner_id()
        if self.partner_id.default_intrastat_transport_id:
            self.intrastat_transport_mode_id = self.partner_id.default_intrastat_transport_id.id
        else:
            self.intrastat_transport_mode_id = False


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tarif_uom = fields.Monetary(compute='_compute_tarif', string='Net Price Unit (uom)', readonly=True)
    tarif_unit = fields.Monetary(compute='_compute_tarif', string='Net Price Unit (unit)', readonly=True)

    @api.depends('product_id', 'price_unit', 'product_uom_id', 'discount')
    def _compute_tarif(self):
        for line in self:
            tarif = line.price_unit * (1.0 - line.discount / 100)
            line.tarif_uom = tarif
            if line.product_uom_id.uom_type == 'bigger':
                line.tarif_unit = tarif / line.product_uom_id.factor_inv
            elif line.product_uom_id.uom_type == 'smaller':
                line.tarif_unit = tarif / line.product_uom_id.factor
            else:
                line.tarif_unit = tarif
