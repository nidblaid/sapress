from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _get_price_available(self, order):
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        # IMPORTANT !! - this method is overrided to changer `amount_total` with `amount_untaxed`
        total = (order.amount_untaxed or 0.0) - total_delivery

        total = self._compute_currency(order, total, 'pricelist_to_company')

        return self._get_price_from_picking(total, weight, volume, quantity)
