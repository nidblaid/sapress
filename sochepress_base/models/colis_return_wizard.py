# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ColisReturnWizard(models.TransientModel):
    _name = 'colis.return.wizard'
    _description = "Colis Return Wizard"

    colis_ids = fields.Many2many('sochepress.customer.request.line', string="Colis",
                                 domain=[('step', '=', 'delivered')])
    request_id = fields.Many2one('sochepress.customer.request', string="Request")
    return_ids = fields.Many2many('sochepress.customer.request', string="Return requests")
    source = fields.Integer(default=1)

    def create_copy(self):

        colis_by_request = {}
        for colis in self.colis_ids.filtered(lambda l: l.is_to_return):
            if colis.request_id in colis_by_request:
                colis_by_request[colis.request_id].append(colis)
            else:
                colis_by_request[colis.request_id] = [colis]

        for record in colis_by_request:
            record = record.sudo()
            concerned_colis = colis_by_request[record]
            if len(concerned_colis) == 0:
                raise ValidationError(_(
                    "Aucun colis n'est à retourner"
                ))
            else:
                data = {
                    'customer_id': record.customer_id.id,
                    'type': record.type,
                    'demand_date': fields.Datetime.now(),
                    'destinator_id': record.expeditor_id.id,
                    'expeditor_id': record.destinator_id.id,
                    'contract_id': record.contract_id.id,
                    'exp_destination_id': record.dest_destination_id.id,
                    'dest_destination_id': record.exp_destination_id.id,
                    'is_return': True,
                    'state': 'accepted',
                    'portal': 11,
                }
                copy = self.env['sochepress.customer.request'].create(data)
                copy.source_request_id = record.id
                copy.is_return = True
                # copy.source_request_id = r.request_id.id
                copy.validation_date = fields.Datetime.now()
                copy.validator_id = self._uid
                time_diff = copy.validation_date - copy.demand_date
                copy.treatment_delay = float(time_diff.days) * 24 + (
                    float(time_diff.seconds) / 3600)
                self.return_ids = [(4, copy.id)]
                for colis in concerned_colis:
                    r_colis = colis
                    tracking = self.env["sochepress.tracabilite.colis"].sudo()
                    data = {
                        'operation_type': 'retract',
                        'source_id': r_colis.destination_id.id,
                        'operator_id': self.env.uid,
                        'date': fields.Datetime.now(),
                        'colis_id': r_colis.id,
                    }
                    tracking.create(data)
                    r_colis.write({'return_request_id': copy.id,
                                   # 'request_id': copy.id,
                                   # 'order_id': False,
                                   # 'invoiced': False,
                                   'step': 'retracted',
                                   'destinator_id': colis.expeditor_id.id,
                                   'expeditor_id': colis.destinator_id.id,
                                   'source_id': colis.destination_id.id,
                                   'destination_id': colis.source_id.id,
                                   'return_method_id': False,
                                   'return_amount': 0,
                                   'r_return_fund_id': colis.return_method_id.id,
                                   'r_return_amount': colis.return_amount,
                                   'retract': 'yes',
                                   'portal': 11,
                                   'is_return': True,
                                   })
                    # r_colis.set_delivery_dates()
                copy.generate_expedition()

        if self.source == 1:
            if len(self.return_ids) == 1:
                action = {
                    'type': 'ir.actions.act_window',
                    'name': _('Return request'),
                    'res_model': 'sochepress.customer.request',
                    'view_mode': 'form',
                    'res_id': self.return_ids.id
                }
            else:
                action = {
                    'type': 'ir.actions.act_window',
                    'name': _('Return request'),
                    'res_model': 'sochepress.customer.request',
                    'view_mode': 'tree',
                    'domain': [('id', 'in', self.return_ids.ids)]
                }
        else:
            action = self.return_ids

        return action
