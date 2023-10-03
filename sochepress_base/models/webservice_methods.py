# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomerRequest(models.Model):
    _inherit = 'sochepress.customer.request'

    @api.model
    def get_list_colis(self, etat_colis):
        list_colis = []
        for colis in self.env['sochepress.customer.request.line'].search(
            [('step', '=', etat_colis)]):
            res = {}
            res["name"] = colis.name
            res["id"] = colis.id
            res["step"] = colis.step
            res["weight"] = colis.weight
            list_colis.append(res)
        return list_colis

    @api.model
    def get_colis_by_name(self, name):
        res = {}
        for colis in self.env['sochepress.customer.request.line'].search(
            [('name', '=', name)]):
            res["name"] = colis.name
            res["id"] = colis.id
            res["step"] = colis.step
            res["weight"] = colis.weight
        return res

    @api.model
    def update_colis_status_by_name(self, name):
        res = {}
        for colis in self.env['sochepress.customer.request.line'].search(
            [('name', '=', name)]):
            res["name"] = colis.name
            res["id"] = colis.id
            res["step"] = colis.step
            res["weight"] = colis.weight
        return res

    # @api.model
    # def create_demand(self, dict_infos):
    #     colis_ids = []
    #     for colis in dict_infos["colis"]:
    #         # Type de colis
    #         name_colis = colis.get("type_colis")
    #         name_colis.capitalize()
    #         type_colis = self.env['sochepress.type.colis'].search([('name', '=', name_colis)])
    #
    #         # Methode de remboursements
    #         name_methode = colis.get("methode_contre_remboursement")
    #         name_methode.capitalize()
    #         return_method = self.env['sls.return.method'].search([('name', '=', name_methode)])
    #
    #         # Expediteur
    #         expeditor_name = colis.get("expediteur")
    #         expeditor_id = self.env['res.partner'].search([('name', '=', expeditor_name)])
    #
    #         # Type de colis
    #         source_name = colis.get("source")
    #         source_id = self.env['sochepress.destination'].search([('name', '=', source_name)])
    #
    #         # Destinataire
    #         destinator_name = colis.get("destinataire")
    #         destinator_id = self.env['res.partner'].search([('name', '=', destinator_name)])
    #
    #         # Destination
    #         destination_name = colis.get("destination")
    #         destination_id = self.env['sochepress.destination'].search([('name', '=', destination_name)])
    #
    #         data = {
    #             "type_colis_id": type_colis.id,
    #             "expeditor_id": expeditor_id.id,
    #             "source_id": source_id.id,
    #             "destinator_id": destinator_id.id,
    #             "destination_id": destination_id.id,
    #             "weight": colis.get("poids_colis"),
    #             "return_method_id": return_method.id,
    #             "return_amount": colis.get("montant_contre_remboursement"),
    #             "volume": colis.get("volume"),
    #             "ref_ext": colis.get("ref_externe"),
    #         }
    #         colis_ids.append(self.env['sochepress.customer.request.line'].create(data))
    #     colis_ids = [item.id for item in colis_ids]
    #
    #     type_demande = dict_infos["type"]
    #
    #     data = {
    #         'customer_id': self.env['res.partner'].browse(dict_infos['customer_id']).id,
    #         'type': type_demande,
    #         'demand_date': fields.Datetime.now(),
    #         'request_line_ids': colis_ids,
    #         'state': 'waiting'
    #
    #     }
    #     created_demand = self.env['sochepress.customer.request'].create(data)
    #     return created_demand.id
