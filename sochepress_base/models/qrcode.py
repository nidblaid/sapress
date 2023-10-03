# -*- coding: utf-8 -*-

import base64
import io
from odoo import models, fields, api, _

import qrcode


class QRGenerator(models.Model):
    _name = 'qr.generator'
    _description = 'qr.generator'

    @api.model
    def get_qr_code(self, data):
        if data != "":
            img = qrcode.make(data)
            result = io.BytesIO()
            img.save(result, format='PNG')
            result.seek(0)
            img_bytes = result.read()
            base64_encoded_result_bytes = base64.b64encode(img_bytes)
            base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
            return base64_encoded_result_str


class ColisQRGenerator(models.Model):
    _inherit = 'sochepress.customer.request.line'

    my_qr_image = fields.Binary("QR Code", compute='_generate_my_qr_code')
    qr_code = fields.Char('Qr code')

    def _generate_my_qr_code(self):
        for r in self:
            code = '\n'.join(
                [r.name, r.request_id.name, str(r.order_id.id) or '0', str(r.id), str(r.type_colis_id.name),
                 '%s - %s' % (str(r.expeditor_id.name), str(r.destinator_id.name)),
                 '%s - %s' % (str(r.expeditor_id.street), str(r.destinator_id.street)),
                 '%s - %s' % (r.source_id.name or '', r.destination_id.name or ''),
                 str(r.weight),
                 r.barcode])

            # print(code)
            # print("=====>", _generate_my_qr_code(code))
            r.my_qr_image = get_qr_code(code)
            return code

    def _generate_qr_code(self):
        service = 'BCD'
        # Check if BIC exists: version 001 = BIC, 002 = no BIC
        if self.id:
            version = '001'
        else:
            version = '002'
        code = '1'
        function = 'SCT'
        matricule = self.id or ''
        company = self.company_id.name

        reference = self.name
        lf = '\n'
        ibanqr = lf.join([service, version, code, function, matricule, company, '', '', reference])
        if len(ibanqr) > 331:
            raise exceptions.except_orm(_('Error'),
                                        _('IBAN QR code "%s" length %s exceeds 331 bytes') % (ibanqr, len(ibanqr)))
        self.qr_image = generate_qr_code(ibanqr)


def generate_qr_code(value):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_img = base64.b64encode(temp.getvalue())
    return qr_img


def get_qr_code(data):
    if data != "":
        img = qrcode.make(data)
        # img.make_image(fill_color="black", back_color="white")
        result = io.BytesIO()
        img.save(result, format='PNG')
        result.seek(0)
        img_bytes = result.read()
        base64_encoded_result_bytes = base64.b64encode(img_bytes)
        # base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
        return base64_encoded_result_bytes
