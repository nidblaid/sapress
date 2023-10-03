# -*- coding: utf-8 -*-
import math
import re
from odoo import models, fields, api, _


class SochepressDocumentColis(models.Model):
    _name = 'sochepress.document.colis'
    _description = "Sochepress Document Colis"

    ref_doc = fields.Char(string="Document Reference")
    colis_id = fields.Many2one('sochepress.customer.request.line', string="Package")
    document_type_id = fields.Many2one('sochepress.document.type', string='Document Type')
    name = fields.Char(string="Name", readonly=1)
    return_type = fields.Selection(related="document_type_id.return_type")
    barcode = fields.Char('Barcode')

    def generate_barcodes(self):
        ean = int(self.env['ir.sequence'].next_by_code('sochepress.customer.request.line'))
        ean = generate_ean(str(ean))
        while self.colis_id.code_barre_exist(ean):
            ean = int(self.env['ir.sequence'].next_by_code('sochepress.customer.request.line'))
            ean = generate_ean(str(ean))
        return ean

    @api.model
    def create(self, vals):
        document_type_id = vals.get('document_type_id', False)
        ref_doc = vals.get('ref_doc', False)
        document_type_name = self.env['sochepress.document.type'].sudo().browse(document_type_id).name
        vals['name'] = 'Document'
        if ref_doc and document_type_name:
            vals['name'] = _("%s - %s") % (document_type_name, ref_doc)
        res = super(SochepressDocumentColis, self).create(vals)
        if res.return_type == 'physical':
            res.barcode = res.generate_barcodes()
        return res


def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    ean = re.sub("[A-Za-z]", "0", ean)
    ean = re.sub("[^0-9]", "", ean)
    ean = ean[:13]
    if len(ean) < 13:
        ean = ean + '0' * (13 - len(ean))
    return ean[:-1] + str(ean_checksum(ean))
