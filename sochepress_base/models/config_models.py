# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from pprint import pprint
class SochepressDestination(models.Model):
    _name = 'sochepress.destination'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sochepress destination model"
    # _parent_name = 'parent_id'
    # _parent_store = True

    active = fields.Boolean(string="Active", default=True)
    def default_internal_user_id(self):
        return self.env.uid if self.env.user.has_group(
            'base.group_user') else False
    def _get_all_internal_users(self):
        internals = []
        for user in self.env['res.users'].search([]):
            if user.has_group('base.group_user'):
                internals.append(user.id)
        return [('id', 'in', internals)]
    name = fields.Char(string="Destination", required=True)
    # parent_path = fields.Char(index=True)
    type = fields.Selection([
        ('plateforme', "Plateforme"),
        ('agence', "Agence"),
        ('client_final', "Client final"),
        ('drop_point', "Point de drop"),
        ('sieges', "Sièges"),
    ], string="Type")
    responsable_caisse_id = fields.Many2one('res.users', string="Responsable de caisse", domain=_get_all_internal_users)
    operational_manager_id = fields.Many2one('res.users', string="Operational Manager", domain=_get_all_internal_users)
    resources_ids = fields.One2many('res.users', 'agence_id', domain=_get_all_internal_users)
    stock_location_id = fields.Many2one('stock.warehouse', string="Stock Location")
    cash_journal_id = fields.Many2one('account.journal', string="Cash Journal", domain=[('type', '=', 'cash')])
    bank_journal_ids = fields.Many2many('account.journal', string="Bank Journals", domain=[('type', '=', 'bank')])
    parent_id = fields.Many2one('sochepress.destination', string="Parent")
    locations_ids = fields.One2many('sochepress.destination', 'parent_id')
    agency_code = fields.Char('Agency Code')
    postal_code = fields.Char('Postal Code', size=6)
    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('agence.seq') or 'AG'
        vals['agency_code'] = seq
        formatted_name = vals['name'][0].upper() + vals['name'][1:].lower()
        name = self.env['sochepress.destination'].search(
            [('name', '=', formatted_name)])
        if name:
            raise UserError(_("Destination  already added"))
        else:
            vals['name'] = formatted_name
            return super(SochepressDestination, self).create(vals)
class SochepressMotifAbandon(models.Model):
    _name = 'sochepress.motif.abandon'
    _description = "Sochepress abandon reason model"
    name = fields.Char(string="Motivation", required=True)
class SochepressStatusActivation(models.Model):
    _name = 'sochepress.status.activation'
    _description = "Sochepress Status Activation model"
    name = fields.Char(string="Status Activation", required=True)
class SochepressTrajet(models.Model):
    _name = 'sochepress.trajet'
    _description = "Sochepress trajet model"
    _order = 'sequence asc'
    sequence = fields.Integer("Sequence")
    destination_id = fields.Many2one('sochepress.destination', string="Destination")
    order_id = fields.Many2one("soch.transport.order", ondelete='cascade')
    name = fields.Char(related='destination_id.name', string='Name')
    # _sql_constraints = [
    #     ('uniqueness_traject', 'UNIQUE(destination_id,order_id)',
    #      'An traject cannot be selected more than once in the mapping. Please
    #      remove duplicate(s) and try again.'),
    # ]
class SochepressMotifAbandonWizard(models.TransientModel):
    _name = 'sochepress.motif.abandon.wizard'
    _description = "Sochepress abandon reason model wizard"
    customer_lost_reason_id = fields.Many2one('sochepress.motif.abandon',
                                              string="Abandon reason", required=1)
    request_id = fields.Many2one('sochepress.customer.request', string="Request")
    def submit(self):
        self.request_id.customer_lost_reason_id = self.customer_lost_reason_id.id
        self.request_id.state = 'canceled'
class SochepressEtatColis(models.Model):
    _name = 'sochepress.etat.colis'
    _description = "State of colis"
    name = fields.Char("Name", required=1)
class IrAttachement(models.Model):
    _inherit = 'ir.attachment'
    second_id = fields.Many2one('sochepress.customer.request')
    doc_type_id = fields.Many2one('sochepress.document.type')
class MailTemplate(models.Model):
    _inherit = 'mail.template'
    doc_type_ids = fields.Many2many('sochepress.document.type', string="Type de document à envoyer")
    def generate_email(self, res_ids, fields=None):
        rslt = super(MailTemplate, self).generate_email(res_ids, fields)
        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False
        res_ids_to_templates = self.get_email_template(res_ids)
        for res_id in res_ids:
            related_model = self.env[self.model_id.model].browse(res_id)
            template = res_ids_to_templates[res_id]
            if related_model._name == 'sochepress.customer.request.line' and template.doc_type_ids:
                attachments = self.env['ir.attachment'].sudo().search(
                    [('res_model', '=', 'sochepress.customer.request.line'), ('res_id', '=', res_id),
                     ('doc_type_id', 'in', template.with_context({'active_test':False}).doc_type_ids.ids)])
                new_attachments = [(at.name, at.datas) for at in attachments]
                attachments_list = multi_mode and rslt[res_id].get('attachments', False) or rslt.get('attachments',
                                                                                                     False)
                if attachments_list:
                    attachments_list.extend(new_attachments)
                else:
                    rslt['attachments'] = new_attachments
        # rslt['attachment_ids'].extend(attachements)
        return rslt
# class SochepressReportDestination(models.Model):
#     _name = 'destination.verif'
#     _description = "Sochepress destination verif"
#
#     custom_localisation = fields.Char("Custom localisation")
#     localisation_id = fields.Many2one('sochepress.destination', string="Localisation")
