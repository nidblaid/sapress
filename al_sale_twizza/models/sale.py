# -*- coding: utf-8 -*-
from odoo import models, api, fields, exceptions, _
import json
from lxml import etree
# from odoo.tools.safe_eval import safe_eval
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    product_category_id = fields.Many2one('product.category', string="Product Category", related='product_id.categ_id', readonly=True, store=True)
    total_purchase_price = fields.Float(string="Total cost", compute="_compute_cost", store=True, digits='Product Price')
    margin_invoiced = fields.Float(string='Margin Invoiced', compute='_product_margin_invoiced', digits='Product Price', store=True)
    margin_net = fields.Float(string="Net Margin", compute='_compute_margin', digits='Product Price',precompute=True, store=True)
    margin = fields.Float(compute='_compute_margin', digits='Product Price', store=True)
    # add groups sale_manager
    purchase_price = fields.Float(
        groups="sales_team.group_sale_manager,al_sale_twizza.group_direction_twizza_med"
    )
    tarif_uom = fields.Monetary(compute='_compute_tarif', string='Net Price Unit (uom)', readonly=True)
    tarif_unit = fields.Monetary(compute='_compute_tarif', string='Net Price Unit (unit)', readonly=True)

    @api.depends('product_id', 'price_unit', 'product_uom', 'discount')
    def _compute_tarif(self):
        for line in self:
            tarif = line.price_unit * (1.0 - line.discount/100)
            line.tarif_uom = tarif
            if line.product_uom.uom_type == 'bigger':
                line.tarif_unit = tarif / line.product_uom.factor_inv
            elif line.product_uom.uom_type == 'smaller':
                line.tarif_unit = tarif / line.product_uom.factor
            else:
                line.tarif_unit = tarif

    @api.depends('product_id', 'purchase_price', 'qty_invoiced', 'price_unit', 'untaxed_amount_invoiced')
    def _product_margin_invoiced(self):
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            price = line.purchase_price
            margin_invoiced = line.untaxed_amount_invoiced - (price * line.qty_invoiced)
            line.margin_invoiced = currency.round(margin_invoiced) if currency else margin_invoiced

    @api.depends('product_uom_qty', 'purchase_price', 'order_id.currency_id')
    def _compute_cost(self):
        for rec in self:
            total_cost = rec.product_uom_qty * rec.purchase_price
            rec.total_purchase_price = rec.order_id.currency_id.round(total_cost) if rec.order_id.currency_id else total_cost

    @api.depends('order_id.state')
    def _compute_invoice_status(self):
        """ Fixed : Rollback on working case. """
        super(SaleOrderLineInherit, self)._compute_invoice_status()
        for line in self:
            # We handle the following specific situation: a physical product is partially delivered,
            # but we would like to set its invoice status to 'Fully Invoiced'. The use case is for
            # products sold by weight, where the delivered quantity rarely matches exactly the
            # quantity ordered.
            if line.order_id.state == 'done' \
                    and line.invoice_status == 'no' \
                    and line.product_id.type in ['consu', 'product'] \
                    and line.product_id.invoice_policy == 'delivery' \
                    and line.move_ids \
                    and all(move.state in ['done', 'cancel'] for move in line.move_ids):
                line.invoice_status = 'invoiced'

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
    def _compute_margin(self):
        super(SaleOrderLineInherit, self.filtered(
            lambda l: l.product_id.type == "product"
        ))._compute_margin()
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            price = line.purchase_price
            margin_net = line.price_subtotal - (price * line.product_uom_qty)
            line.margin_net = currency.round(margin_net) if currency else margin_net

    # @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
    # def _product_margin(self):
    #     for line in self.filtered(lambda l: l.product_id.type == "product"):
    #         currency = line.order_id.pricelist_id.currency_id
    #         price = line.purchase_price
    #         margin_net = line.price_subtotal - (price * line.product_uom_qty)
    #         line.margin_net = currency.round(margin_net) if currency else margin_net


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    days_to_confirm = fields.Float(string='Days to confirm', compute='_compute_days_to', store=True)
    days_to_invoice = fields.Float(string='Days to invoice', compute='_compute_days_to', store=True)
    delivery_mode_id = fields.Many2one("delivery.mode", string="Delivery Mode")
    payment_mode_id = fields.Many2one("payment.mode", string="Payment Mode")
    margin_rate = fields.Float(string='Margin Rate', compute='_compute_margin_rate', store=True)
    margin_rate_net = fields.Float(string='Net Margin Rate', compute='_compute_margin_rate', store=True)
    margin_net = fields.Monetary(
        string='Net Margin',
        compute='_compute_margin',
        currency_field='currency_id',
        store=True
    )

    @api.depends('order_line.margin', 'order_line.margin_net')
    def _compute_margin(self):
        super(SaleOrderInherit, self)._compute_margin()
        for order in self:
            order.margin_net = sum(order.order_line.filtered(lambda r: r.state != 'cancel').mapped('margin_net'))

    # @api.depends('order_line.margin', 'order_line.margin_net')
    # def _product_margin(self):
    #     for order in self:
    #         order.margin_net = sum(order.order_line.filtered(lambda r: r.state != 'cancel').mapped('margin_net'))


    @api.depends('margin', 'order_line', 'order_line.total_purchase_price', 'order_line.product_id.type')
    def _compute_margin_rate(self):
        for rec in self:
            total_cost = sum(rec.order_line.mapped('total_purchase_price'))
            if total_cost != 0.0:
                rec.margin_rate = (rec.margin / total_cost) * 100
                rec.margin_rate_net = (rec.margin_net / total_cost) * 100
            else:
                rec.margin_rate = 100
                rec.margin_rate_net = 100

    @api.onchange('team_id', 'partner_id','partner_shipping_id','user_id')
    def _onchange_team_id(self):
        self.update({
            'analytic_account_id': self.team_id.analytic_account_id.id or False
        })
        

    # @api.onchange('partner_shipping_id', 'partner_id', 'company_id')
    # def onchange_partner_shipping_id(self):
    #     values = {
    #         'user_id': self.partner_shipping_id.user_id and self.partner_shipping_id.user_id.id,
    #         'team_id': self.partner_shipping_id.team_id and self.partner_shipping_id.team_id.id,
    #     }
    #     self.update(values)
    #     return super(SaleOrderInherit, self).onchange_partner_shipping_id()

    @api.onchange('partner_shipping_id', 'partner_id', 'company_id')
    def onchange_partner_shipping_id(self):
        values = {
            'user_id': self.partner_shipping_id.user_id and self.partner_shipping_id.user_id.id,
            'team_id': self.partner_shipping_id.team_id and self.partner_shipping_id.team_id.id,
        }
        self.update(values)


    

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     self.update({
    #         'delivery_mode_id': self.partner_id.delivery_mode_id.id or False,
    #         'payment_mode_id': self.partner_id.payment_mode_id.id or False,
    #     })
    #     return super(SaleOrderInherit, self).onchange_partner_id()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        values = {
            'delivery_mode_id': self.partner_id.delivery_mode_id.id or False,
            'payment_mode_id': self.partner_id.payment_mode_id.id or False,
        }
        self.update(values)


    @api.depends('create_date', 'date_order', 'state', 'invoice_ids', 'invoice_ids.invoice_date')
    def _compute_days_to(self):
        for rec in self:
            rec.days_to_confirm = (rec.date_order - rec.create_date).days if rec.state in ['sale', 'done'] else 0.0
            delivered_dates = self.env['stock.picking'].search([
                ('sale_id', '=', rec.id),
                ('state', 'in', ['done'])
            ]).mapped('date_done')
            invoiced_dates = rec.invoice_ids.filtered(lambda x: x.state in ['posted']).mapped('invoice_date')
            days_to_invoice = 0.0
            if rec.state in ['sale', 'done'] and delivered_dates and invoiced_dates:
                days_to_invoice = (max(invoiced_dates) - max(delivered_dates).date()).days
            rec.days_to_invoice = days_to_invoice

    # @staticmethod
    # def modifier_set_readonly(res, expression):
    #     doc = etree.XML(res['arch'])
    #     for node in doc.xpath(expression):
    #         node.set('force_save', '1')
    #         modifiers = json.loads(node.get("modifiers"))
    #         modifiers['readonly'] = True
    #         node.set("modifiers", json.dumps(modifiers))
    #     res['arch'] = etree.tostring(doc)

    # @staticmethod
    # def modifier_set_invisible(res, expression):
    #     doc = etree.XML(res['arch'])
    #     for node in doc.xpath(expression):
    #         modifiers = json.loads(node.get("modifiers"))
    #         modifiers['invisible'] = True
    #         node.set("modifiers", json.dumps(modifiers))
    #     res['arch'] = etree.tostring(doc)

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(SaleOrderInherit, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         is_admin_sales = self.env.user.has_group('sales_team.group_sale_manager')
    #         has_price_unit_access = self.env.user.has_group('al_sale_twizza.group_sale_unit_price_access')
    #         has_discount_access = self.env.user.has_group('al_sale_twizza.group_sale_discount_access')
    #         res_line_form = res['fields']['order_line']['views']['form']
    #         res_line_tree = res['fields']['order_line']['views']['tree']
    #         if not is_admin_sales:
    #             self.modifier_set_readonly(res=res_line_form, expression="//field[@name='tax_id']")
    #             self.modifier_set_readonly(res=res_line_tree, expression="//field[@name='tax_id']")
    #             self.modifier_set_invisible(res=res_line_form, expression="//field[@name='product_packaging']")
    #         if not is_admin_sales and not has_price_unit_access:
    #             self.modifier_set_readonly(res=res_line_form, expression="//field[@name='price_unit']")
    #             self.modifier_set_readonly(res=res_line_tree, expression="//field[@name='price_unit']")      
    #         if not is_admin_sales and not has_discount_access:
    #             self.modifier_set_readonly(res=res_line_form, expression="//field[@name='discount']")
    #             self.modifier_set_readonly(res=res_line_tree, expression="//field[@name='discount']")
    #     return res


    def action_cancel(self):
        for rec in self:
            if rec.invoice_status == 'invoiced':
                raise exceptions.ValidationError(_("You can't cancel a totally invoiced sale order."))
        return super().action_cancel()

    def _compute_amount_total_without_delivery(self):
        res = super()._compute_amount_total_without_delivery()
        delivery_cost = self.amount_total - res
        return self.amount_untaxed - delivery_cost
