from odoo import models, api, fields


class KzmInvoice(models.Model):
    _inherit = 'account.move'

    @api.depends('amount_total')
    def _amount_in_words(self):
        for r in self:
            r.amount_to_text =r.currency_id.amount_to_text(r.amount_total)

    amount_to_text = fields.Text(string='Montant total en lettre',
                                 store=True, readonly=True, compute='_amount_in_words')

    def get_discount(self):
        for r in self:
            disc = 0
            for l in r.invoice_line_ids:
                disc += (l.quantity * l.price_unit - l.price_subtotal)
            return disc

    def total_ht(self):
        total = 0
        for r in self:
            total = sum([l.quantity * l.price_unit for l in r.invoice_line_ids])
        return total

    def get_order_object(self):
        for r in self:
            object = ''
            if r.invoice_line_ids:
                for l in r.invoice_line_ids:
                    for ls in l.sale_line_ids:
                        object = ls.order_id.object
                        break
            return object


class KzmInvoiceLine(models.Model):
    _inherit = "account.move.line"

    def get_designation(self):
        x = 0
        if self.name[x] == "[":
            for i in range(len(self.name)):
                if self.name[i] == "]":
                    x = i + 1
                    break

        return self.name[x:len(self.name)]
