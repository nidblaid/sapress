# -*- coding: utf-8 -*-

import filetype
from odoo import models, fields, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

IMAGES_EXTENSIONS = [str(type(k).__name__).lower() for k in list(filetype.image_matchers)]
IMAGES_EXTENSIONS.append('jpg')


class SochepressJustifWizard(models.TransientModel):
    _name = 'sochepress.justif.wizard'
    _description = 'Justificatif Livraison Assistant'

    colis_id = fields.Many2one('sochepress.customer.request.line', string="Colis")
    line_ids = fields.Many2many('sochepress.justif')
    mobile = fields.Boolean()

    def continue_pass(self):
        self.colis_id.livrer_trac(self.mobile)
        if self.mobile:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def confirmer(self):
        # if not self.line_ids:
        #     raise UserError("You must add justificatifs")
        # docs = self.colis_id.document_ids
        # for line in self.line_ids:
        #     docs = docs - line.doc_id

        # if docs:
        #     ac = 's' if len(docs) > 1 else ''
        #     raise UserError(
        #         "Vous n'avez pas intégré de justifications pour le%s document%s: %s" % (
        #             ac, ac, ', '.join([d.name for d in docs])))
        # if len(self.line_ids) < len(self.colis_id.document_ids):
        #     raise UserError("Veuillez intégrer les documents justificatifs pour livrer le colis")
        # else:
        # result = True
        # colis_lines_documents = [l.doc_id for l in self.line_ids]
        # colis_documents = [l.document_type_id for l in self.colis_id.document_ids]
        # for c in set(colis_documents):
        #     if colis_documents.count(c) > colis_lines_documents.count(c):
        #         result = False
        #         break

        # result = all(elem in colis_lines_documents for elem in colis_documents)

        # if not result:
        #     raise UserError("Veuillez intégrer les documents justificatifs pour livrer le colis")

        inserted_docs = [l.doc_id.id for l in self.line_ids if l.doc_id]
        inserted_docs.sort()
        colis_docs = [l.document_type_id.id for l in self.colis_id.document_ids if l.document_type_id]
        colis_docs.sort()
        for c in inserted_docs:
            if c in colis_docs:
                colis_docs.remove(c)

        if colis_docs:
            ac = 's' if len(colis_docs) > 1 else ''
            raise UserError(
                "Vous n'avez pas intégré de justificatifs pour le%s type%s de document%s: %s" % (
                    ac, ac, ac,
                    ', '.join(
                        [self.env['sochepress.document.type'].browse(d).display_name for d in list(set(colis_docs))])))

        # if inserted_docs not in colis_docs:
        #     raise UserError("Veuillez intégrer les documents justificatifs pour livrer le colis")

        for line in self.line_ids:
            if not line.name:
                raise UserError(
                "Vous devez scanner toutes les photos avant de livrer") 
            else:
                data = {
                    'name': "%s.%s" % (line.doc_id.display_name, line.name.split('.')[-1]),
                    'type': "binary",
                    'datas': line.justif,
                    'res_model': self.colis_id._name,
                    'res_id': self.colis_id.id,
                    'mimetype': "application/" + line.name.split('.')[-1],
                    'doc_type_id': line.doc_id.id
                }
                self.env['ir.attachment'].sudo().create(data)
        self.colis_id.livrer_trac(self.mobile)
        if self.mobile:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

