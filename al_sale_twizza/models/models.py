from odoo import fields, models, api


class DeliveryMode(models.Model):
    _name = 'delivery.mode'
    _description = 'Delivery Mode'

    name = fields.Char(string="Name", required=True)


class PaymentMode(models.Model):
    _name = 'payment.mode'
    _description = 'Payment Mode'

    name = fields.Char(string="Name", required=True)
    bank_acocunt = fields.Text(string="Bank Account")


class PartnerType(models.Model):
    _name = 'res.partner.type'
    _description = 'Partner Type'

    name = fields.Char(string="Name", required=True)


class PartnerArea(models.Model):
    _name = "res.partner.area"
    _description = "Partner Area"

    _sql_constraints = [
        ('unique_name', 'unique (name)', "The name you're trying to use for this area exists already.")
    ]

    name = fields.Char(string='Area', required=True)
    description = fields.Text(string='Description')
