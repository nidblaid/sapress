# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SlsSmsType(models.Model):
    _name = 'sls.sms.type'
    _description = 'Sls Sms Type'

    cible = fields.Selection(
        [('recipient', "Recipient"), ('sender', "Sender"),
         ('customer', "Customer"), ('recipient_sender', "Recipient & Sender"),
         ('recipient_customer', "Recipient & Customer"), ('sender_customer', "Sender & "
                                                                             "Customer"),
         ('customer_sender_recipient', "Customer, Sender & Recipient"),
         ], string="Cible", required=True)
    name = fields.Char(string="Code", readonly=True)
    timing = fields.Selection(
        [('AVR', "Before Pickup"), ('AVL', "Before Delivery"),
         ('APL', "After Delivery"), ('AP', 'After pickup')], string="Timing",
        required=True)
    Contenu = fields.Text(string="Content")
    tarif = fields.Float("Price")

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('sls.sms.type') or 'TSMS'
        vals['name'] = 'SMS' + seq
        return super(SlsSmsType, self).create(vals)
