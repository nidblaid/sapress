# -*- coding: utf-8 -*-
import base64
import json
import logging
import math
import pyotp
import random
import re
import string
from Levenshtein import distance
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from fastDamerauLevenshtein import damerauLevenshtein
from itertools import groupby, islice
from lxml import etree
import logging
from odoo import models, fields, api, _
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.exceptions import UserError, ValidationError
from odoo.tools.profiler import profile
from odoo.tools.profiler import profile
from operator import itemgetter
from pprint import pprint


_logger = logging.getLogger(__name__)
class CustomerRequest(models.Model):
    _name = 'sochepress.customer.request'
    _order = 'name desc'
    _description = "Customer requests model"
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
    def _default_demande_date(self):
        return datetime.now()
    name = fields.Char("Name", default="DM")
    customer_id = fields.Many2one('res.partner', string="Customer", required=True,
                                  track_visibility='onchange',
                                  default=lambda self: self.env['res.partner'].search(
                                      [('user_id', '=', self._uid)]),
                                  domain=[('customer_rank', '>', 0)])
    expeditor_id = fields.Many2one('res.partner', string="Expeditor",
                                   track_visibility='onchange')
    e_street = fields.Char('Expeditor Street', related='expeditor_id.street',
                           readonly=False, store=True)
    e_street2 = fields.Char('Expeditor Street2', related='expeditor_id.street2',
                            readonly=False, store=True)
    e_country_id = fields.Many2one('res.country', string='Expeditor Country',
                                   related='expeditor_id.country_id',
                                   store=True, readonly=False)
    exp_destination_id = fields.Many2one('sochepress.destination', string="Source",
                                         track_visibility='onchange', readonly=False,
                                         related='expeditor_id.destination_id',
                                         store=True)
    destinator_id = fields.Many2one('res.partner', string="Destinator",
                                    track_visibility='onchange')
    d_street = fields.Char('Destinator Street', related='destinator_id.street',
                           readonly=False, store=True)
    d_street2 = fields.Char('Destinator Street2', related='destinator_id.street2',
                            readonly=False)
    d_country_id = fields.Many2one('res.country', string='Destinator Country',
                                   related='destinator_id.country_id',
                                   readonly=False, store=True)
    dest_destination_id = fields.Many2one('sochepress.destination',
                                          string="Destination",
                                          track_visibility='onchange', readonly=False,
                                          related='destinator_id.destination_id',
                                          store=True)
    demand_date = fields.Datetime("Demand date", default=_default_demande_date,
                                  readonly=1, track_visibility='onchange')
    validation_date = fields.Datetime("Treatment date", readonly=1,
                                      track_visibility='onchange')
    validator_id = fields.Many2one('res.users', string="Validator", readonly=1,
                                   track_visibility='onchange')
    treatment_delay = fields.Float("Treatment delay", readonly=True)
    type = fields.Selection([('normal', "Normal"), ('transport', "Dedicted transport"),
                             ('course', "Urgent course")],
                            string="Type", track_visibility='onchange')
    contract_id = fields.Many2one('sochepress.contract', string="Contract",
                                  track_visibility='onchange')
    # destination_id = fields.Many2one('sochepress.destination',
    # string="Destination", track_visibility='onchange')
    request_line_ids = fields.One2many('sochepress.customer.request.line', 'request_id',
                                       string="Request lines")
    return_request_line_ids = fields.One2many('sochepress.customer.request.line', 'return_request_id',
                                              string="Request lines returns")
    customer_lost_reason_id = fields.Many2one('sochepress.motif.abandon',
                                              string="Abandon reason",
                                              track_visibility='onchange')
    return_of_fund = fields.Selection(
        [('simple', "Simple"), ('espece', "Especes"), ('check', "Cheque"),
         ('trait', "Traite")], default='simple',
        string="Return of fund")
    sum_in_number = fields.Float("Sum in number")
    return_doc_invoice = fields.Boolean("Return document: Invoice")
    return_doc_bl = fields.Boolean("Return document: BL")
    invoice_ref = fields.Char("Invoice ref")
    bl_ref = fields.Char("BL ref")
    invoiced = fields.Boolean("Invoiced", default=False, compute='_count_invoice')
    # invoice_ids = fields.One2many('account.move', 'sochepress_request_id',
    # string="Invoices")
    invoice_ids = fields.Many2many("account.move", string='Invoices', readonly=True,
                                   copy=False)
    order_id = fields.Many2one("soch.transport.order")
    return_count = fields.Integer('Count returns', compute='_count_return')
    invoice_count = fields.Integer('Count', compute='_count_invoice')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    vehicule_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    vehicule_weight = fields.Float("Vehicule weight",
                                   related='vehicule_id.vehicule_weight')
    vehicule_volume = fields.Float("Vehicule volume", related='vehicule_id.vehicule_volume')
    nbre_colis = fields.Integer('Number of colis', compute='compute_sums')
    nbre_colis_report = fields.Integer('Number of colis report', compute='compute_sums')
    total_colis_weight = fields.Float('Colis Total weight', compute='compute_sums', )
    total_colis_volume = fields.Float('Colis Total volume', compute='compute_sums', )
    total_price = fields.Float('Total price', compute='compute_sums')
    total_return_amount = fields.Float('Total return amount', compute='compute_sums')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda x: x.env.user.company_id.currency_id)
    etat_facturation = fields.Selection([
        ('rien_facture', "Rien a facturé"),
        ('a_facture', "A facturée"),
        ('en_facturation', "En facturation"),
        ('facturee', "Facturée")
    ], string="Etat de facturation", compute="compute_etat_facturation", store=True)
    source_request_id = fields.Many2one('sochepress.customer.request')
    is_prepaye = fields.Boolean(string="is_prepaye")
    is_return = fields.Boolean(default=False)
    declaration_ids = fields.One2many('sochepress.declaration', 'request_id',
                                      string="Declarations")
    dest = fields.Char()
    dest2 = fields.Char()
    removal_name = fields.Char("Removal name")
    show_ref_bl_ref_doc = fields.Boolean("Show Ref BL Ref Doc", compute="_compute_show_ref_bl_ref_doc", store=1)
    creation_type = fields.Selection([
        ('manual', "Manual"),
        ('importation', "Importation"),
    ], default='manual', string="Creation type")
    error_line = fields.Text("Lignes d'erreurs")
    warning_line = fields.Text("Lignes de warning")
    created_deliveries = fields.Integer("Colis crées")
    nb_colis = fields.Integer("Colis")
    correct_colis = fields.Integer("Colis corrects")
    rejected_colis = fields.Integer("Colis rejetés")
    non_conform_id = fields.Many2one('sochepress.customer.request')
    not_conform_request = fields.Boolean("Not command conform")
    send_type = fields.Selection([
        ('send', "Send"),
        ('return_on_requests', "Return on requests"),
    ], string="Send type", compute='compute_send_type', store=1)
    source_ids = fields.Many2many('sochepress.destination', 'source_request_rel', 'request_id', 'source_id',
                                  string='Sources')
    destination_ids = fields.Many2many('sochepress.destination', 'destination_request_rel', 'request_id',
                                       'destination_id', string='Destinations')
    @api.depends('request_line_ids', 'return_request_line_ids')
    def set_source_ids(self):
        for r in self:
            sources = []
            destinations = []
            for colis in r.request_line_ids + r.return_request_line_ids:
                if colis.source_id:
                    sources.append(colis.source_id.id)
                if colis.destination_id:
                    destinations.append(colis.destination_id.id)
            r.source_ids = [(6, 0, sources)]
            r.destination_ids = [(6, 0, destinations)]
    # def set_destination_ids(self):
    #     for r in self:
    #         destinations = []
    #         for colis in r.request_line_ids + r.return_request_line_ids:
    #             if colis.destination_id:
    #                 destinations.append(colis.destination_id.id)
    #         r.destination_ids = [(6, 0, destinations)]
    active = fields.Boolean(default=True)
    @api.depends('source_request_id')
    def compute_send_type(self):
        for r in self:
            if not r.source_request_id:
                r.send_type = 'send'
            else:
                r.send_type = 'return_on_requests'
                r.is_return = True
    era_is_sended = fields.Boolean(default=False)
    @api.depends('contract_id')
    def _compute_show_ref_bl_ref_doc(self):
        for r in self:
            if r.contract_id.documentary_return:
                r.show_ref_bl_ref_doc = True
            else:
                r.show_ref_bl_ref_doc = False

    def get_grouped_colis(self, expeditor=False):
        self.compute_sums()
        domain = [('id', 'in', self.request_line_ids.ids + self.return_request_line_ids.ids)]
        if expeditor:
            domain.append(('expeditor_id', 'in', expeditor))
        colis = self.env['sochepress.customer.request.line'].search(domain,
                                                                    order='type_colis_id, destination_name')
        vals = {}
        for r in colis:
            if r.expeditor_id in vals:
                vals[r.expeditor_id].append(r)
            else:
                vals[r.expeditor_id] = [r]
        return vals

    def correct_word(self, name):
        space_replace = name.lower().replace(" ", "")
        unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
        return self.remove_accent(unscane_replace)
    # @api.constrains('request_line_ids', 'return_request_line_ids'
    def generate_expedition(self):
        for rec in self:
            lines = rec.request_line_ids if not rec.is_return else rec.return_request_line_ids
            new_lines = self.env['sochepress.declaration']
            listbl = []
            d = {}
            for l in lines:
                partner = l.destinator_id
                listbl.append({partner.id:l.id})
            for lbl in listbl:
                for k in list(lbl.keys()):
                    d.setdefault(k, []).append(lbl[k])
            _logger.info(d)
            for p in list(d.keys()):
                _logger.info("<<<<<<<<<<<<<<<<<<begin <<<<<<<<<<<<<<<<<<"+str(p)+str(d.get(p,False)))

                new_values = {'request_id':rec.id,'portal':rec.portal,'customer_id':rec.customer_id.id,
                'expeditor_id': rec.expeditor_id.id,'destinator_id':p,'colis_ids':[(6,0,d[p])]}
                colis = d[p]
                decl = []
                for dd in rec.declaration_ids:
                    if dd.destinator_id.id == p:
                        decl.append(dd)
                if len(decl) > 1:
                        for dec in  decl:
                            dec.unlink()
                        decl = False
                if decl:
                    for col in colis:
                        decl[0].colis_ids = [(4, col)]
                else:
                    decl = new_lines.create(new_values)
                _logger.info("#################"+str(decl))
                for y in colis:
                    self.env['sochepress.declaration'].sudo().browse(y).expedition_id = decl[0].id

    def check_create_copy(self):
        if (datetime.now() - self.request_line_ids.delivery_date) > \
            self.contract_id.acceptation_delay:
            raise ValidationError(_(
                "Le délai d'acceptation des retours est dépassé.\n"
            ))
    def days_between(d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)
    def create_copy(self):
        for r in self:
            if not r.request_line_ids:
                return
            view_id = self.env.ref(
                'sochepress_base.colis_return_wizard_form').id
            for d in r.request_line_ids:
                d.is_to_return = False
            wiz_id = self.env['colis.return.wizard'].create(
                {'request_id': r.id, 'colis_ids': r.request_line_ids.ids})
            action = {
                'name': _('Colis Return'),
                'res_model': 'colis.return.wizard',
                'view_mode': 'form',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'type': 'ir.actions.act_window',
                'res_id': wiz_id.id,
                'target': 'new'
            }
            return action
    def notif_request(self):
        for r in self:
            template = self.env.ref('sochepress_base.request_created22')
            template.write({
                'partner_to': ",".join(
                    [str(self.customer_id.id)]),
            })
            self.env['mail.template'].browse(template.id). \
                send_mail(self.id, force_send=False, raise_exception=True)
    @api.depends('request_line_ids', 'request_line_ids.step',
                 'request_line_ids.invoiced')
    def compute_etat_facturation(self):
        for r in self:
            nbr = r.nbre_colis
            cpt_l = 0
            cpt_f = 0
            for c in r.request_line_ids:
                if c.step == "delivered":
                    cpt_l += 1
                if c.invoiced:
                    cpt_f += 1
            if nbr:
                if cpt_l < nbr:
                    if cpt_l == 0:
                        r.etat_facturation = 'rien_facture'
                    else:
                        if cpt_f > 0:
                            r.etat_facturation = 'en_facturation'
                        else:
                            r.etat_facturation = 'a_facture'
                else:
                    if cpt_f == nbr:
                        r.etat_facturation = 'facturee'
                    else:
                        if cpt_f == 0:
                            r.etat_facturation = 'a_facture'
                        else:
                            r.etat_facturation = 'en_facturation'
            else:
                r.etat_facturation = 'rien_facture'
    @api.depends('request_line_ids', 'request_line_ids.order_id')
    def compute_sums(self):
        for r in self:
            r.nbre_colis = len(r.request_line_ids)
            r.nbre_colis_report = len(
                [t.order_id.id for t in r.request_line_ids if t.order_id])
            r.total_colis_weight = sum([line.weight for line in r.request_line_ids])
            r.total_colis_volume = sum([line.volume for line in r.request_line_ids])
            r.total_price = sum([line.price for line in r.request_line_ids])
            r.total_return_amount = sum(
                [line.return_amount for line in r.request_line_ids])
    @api.depends('invoice_ids')
    def _count_invoice(self):
        for r in self:
            r.invoice_count = len(r.invoice_ids)
            r.invoiced = not (len(r.invoice_ids.filtered(
                lambda invoice: invoice.state == 'cancel')) == r.invoice_count)
    def action_return(self):
        for r in self:
            action = self.env.ref('sochepress_base.customer_request_action').read()[0]
            action['domain'] = [('source_request_id', '=', r.id)]
        return action
    @api.depends('invoice_ids')
    def _count_return(self):
        for r in self:
            r.return_count = self.env['sochepress.customer.request'].search_count(
                [('source_request_id', '=', r.id)])
    def action_contract_invoice(self):
        if len(self.invoice_ids) != 0:
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            action['domain'] = [('id', 'in', self.invoice_ids.ids)]
            return action
        else:
            raise UserError(_('Any invoice for this contract'))
    def set_removal_name(self):
        for r in self:
            if not r.removal_name:
                r.removal_name = self.env['ir.sequence'].next_by_code(
                    'customer.request.removal.order') or 'BE'
    portal = fields.Integer("Portal", default=1, )

    def write(self, vals):
        res = super().write(vals)
        if vals.get('nbre_colis'):
            for rec in self:
                if rec.request_line_ids and rec.customer_id.auto_accept_demand and rec.state in ('draft','waiting'):
                    verified = rec.verified_action_automatique()
                    if verified:
                        rec.accepted_action()
        return res

    @api.model
    def create(self, vals):
        seq = self.sudo().env['ir.sequence'].next_by_code(
            'sochepress.customer.request') or 'CR'
        vals['name'] = seq
        vals['removal_name'] = self.sudo().env['ir.sequence'].next_by_code(
            'customer.request.removal.order') or 'BE'
        # print("====>", vals)
        # if 'request_line_ids' not in vals:
        #     raise ValidationError("La demande n'a pas de colis !")
        res = super(CustomerRequest, self.sudo()).create(vals)
        res.print_all()
        res.print_be()
        res.set_source_ids()
        # res.set_destination_ids()
        res.send_creation_mail()
        for rec in res:
            if res.request_line_ids and rec.customer_id.auto_accept_demand and rec.state in ('draft','waiting'):
                        verified = rec.verified_action_automatique()
                        if verified:
                            rec.accepted_action()
        #if res.customer_id.auto_accept_demand:
        #    res.verified_action()
        #    res.accepted_action()
        #print('creat sochepress.customer.request'+str(res.id))
        return res
    localisation_ids = fields.Many2many('sochepress.destination')
    creation_mail_send = fields.Boolean("Creation mail send")
    # def write(self, values):
    #     res = super(CustomerRequest, self).write(values)
    #     self.send_creation_mail()
    #     return res
    def send_creation_mail(self):
        for res in self:
            if not res.error_line and not res.creation_mail_send:
                template = self.env.ref('sochepress_base.send_mail_request_creation')
                message = False
                declaration = res.declaration_ids and res.declaration_ids[0]
                if res.customer_id and res.customer_id.email and declaration:
                    res.dest = res.customer_id.name
                    #template.write({
                    #    'partner_to': res.customer_id.id
                    #q})
                    if res.company_id.send_mail_request_creation_bool_client:
                        self.env['mail.template'].browse(template.id).send_mail(declaration.id, force_send=True,
                                                                                raise_exception=True)
                        res.creation_mail_send = True
                else:
                    message = True
                if message:
                    title = _("Configuration des mails destinataires!")
                    message = _("Votre client n'a pas d'adresse mail défini!")
                    action = {'type': 'simple_notification', 'title': title, 'message': message,
                              'sticky': False,
                              'warning': True}
                    self.env['bus.bus'].sendone(
                        (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), action)
    def get_ots(self):
        ots = [col.order_id.name for col in self.request_line_ids if col.order_id]
        if ots:
            return ", ".join(ots)
        else:
            return False
    def get_ordered_colis(self):
        self.sudo().compute_sums()
        if self.source_request_id:
            lines = self.return_request_line_ids
        else:
            lines = self.request_line_ids
        return self.env['sochepress.customer.request.line'].search(
            [('id', 'in', self.request_line_ids.ids + self.return_request_line_ids.ids)],
            order='type_colis_id, destination_name')
    def send_email_after_pickup(self):
        for r in self:
            template_after_pickup = self.env.ref('sochepress_base.email_after_pickup_template')
            template_after_pickup.write({
                'partner_to': r.customer_id.id
            })
            if r.company_id.email_after_pickup_template_bool_client:
                self.env['mail.template'].browse(template_after_pickup.id).send_mail(self.id, force_send=True,
                                                                                     raise_exception=True)
    # def get_to_ramass_colis(self, date_item):
    #     self.compute_sums()
    #     ramass = len(o.request_line_ids.filtered(lambda r: not r.order_id and
    #     r.type_colis_id==date_item))
    #     ramass = len(self.request_line_ids.filtered(lambda r: r.type_colis_id ==
    #     date_item))
    #     return ramass
    def get_contract(self):
        for r in self:
            r.contract_id = self.env['sochepress.contract'].search(
                [('partner_id', '=', r.customer_id.id),
                 ('stage_id', '=', self.env.ref(
                     'sochepress_base.sochepress_contract_stage_in_progress').id)],
                limit=1)
            r.localisation_ids = [(6, 0,
                                   r.contract_id.destination_ids.ids if
                                   r.contract_id.destination_ids else [])]
    @api.onchange('customer_id', 'dest_destination_id', 'exp_destination_id')
    def _set_subscription_domain(self):
        for r in self:
            res = {}
            if r.customer_id:
                if r.contract_id and r.contract_id.partner_id.id != r.customer_id.id:
                    r.expeditor_id = False
                    r.destinator_id = False
                r.get_contract()
                child = ('id', 'in',
                         r.customer_id.child_ids.ids if r.customer_id.child_ids else [])
                exp_domain = r.contract_id.destination_ids.ids if \
                    r.contract_id.destination_ids else []
                dest_domain = r.contract_id.destination_ids.ids if \
                    r.contract_id.destination_ids else []
                if r.dest_destination_id:
                    exp_domain = r.contract_id.destination_ids.filtered(
                        lambda dest: dest.id != r.dest_destination_id.id).ids if \
                        r.contract_id.destination_ids else []
                if r.exp_destination_id:
                    dest_domain = r.contract_id.destination_ids.filtered(
                        lambda dest: dest.id != r.exp_destination_id.id).ids if \
                        r.contract_id.destination_ids else []
                res['domain'] = {
                    'expeditor_id': [('destination_id', 'in', exp_domain), child],
                    'destinator_id': [('destination_id', 'in', dest_domain), child],
                    'exp_destination_id': [('id', 'in', exp_domain)],
                    'dest_destination_id': [('id', 'in', dest_domain)]
                }
            else:
                r.expeditor_id = False
                r.destinator_id = False
                res['domain'] = {'expeditor_id': [('id', '=', 0)],
                                 'destinator_id': [('id', '=', 0)],
                                 'exp_destination_id': [('id', '=', 0)],
                                 'dest_destination_id': [('id', '=', 0)],
                                 }
            return res
    state = fields.Selection(
        [('traitement_sys', "Traitement systeme"), ('draft', "Draft"), ('waiting', "Waiting"), ('verified', "Verified"), ('accepted', "Accepted"),
         ('closed', "Closed"), ('canceled', "Canceled")], string="State", default='draft',
        track_visibility='onchange')
    report_type = fields.Selection([('a4', "A4"), ('dix', "10x10")], default='a4',
                                   string="Type d'impression",
                                   track_visibility='onchange')
    def draft_action(self):
        self.state = 'draft'
    def cancel(self):
        self.state = 'canceled'
        self.customer_lost_reason_id = self.env.ref(
            "sochepress_base.sochepress_motif_abandon_client")
    def action_return(self):
        for r in self:
            action = self.env.ref('sochepress_base.customer_request_action').read()[0]
            action['domain'] = [('source_request_id', '=', r.id)]
        return action
    def waiting_action(self):
        # template = self.env.ref('sochepress_base.request_created22')
        # if not self.destinator_id:
        #     if self.customer_id and self.customer_id.email:
        #         self.dest = self.customer_id.name
        #         template.write({
        #             'partner_to': self.customer_id.id
        #         })
        #         self.env['mail.template'].browse(template.id).send_mail(self.id,
        #         force_send=True,raise_exception=True)
        #     else:
        #         if self.company_id.check_mail:
        #             raise ValidationError(_(" Please define an email address for
        #             your customer"))
        # else:
        #     if self.destinator_id and self.destinator_id.email:
        #         self.dest = self.destinator_id.name
        #         template.write({
        #             'partner_to': self.destinator_id.id
        #         })
        #         self.env['mail.template'].browse(template.id).send_mail(self.id,
        #         force_send=True,raise_exception=True)
        #     else:
        #         if self.company_id.check_mail:
        #             raise ValidationError(
        #                 _("Please enter an email address to the customer %s" % (
        #                 self.destinator_id.name)))
        self.state = 'waiting'

        services = self.env['request.invoicing.line'].sudo().search([('demand_id', '=', self.id)])
        for serv in services:
            serv.sudo().write({"demand_id": False})

        for r in self:
            for col in r.request_line_ids:
                col.related_service_line_ids.sudo().unlink()
                col.sudo().write({"service_lines_count_sec": 0})
        self.sudo().write({"service_lines_count_sec": 0})

    def remove_accent(self, chaine):
        accent = ['é', 'è', 'ê', 'à', 'ù', 'û', 'ç', 'ô', 'î', 'ï', 'â']
        sans_accent = ['e', 'e', 'e', 'a', 'u', 'u', 'c', 'o', 'i', 'i', 'a']
        for i in range(0, len(accent)):
            chaine = chaine.replace(accent[i], sans_accent[i])
        return chaine
    test = fields.Char()
    def test_action(self):
        loc = self.existing_location(self.test)
        raise UserError(loc.name if loc else False)
    def existing_location(self, name):
        corrected_name = " ".join(name.split())
        allin_one = corrected_name.lower().replace(" ", "")
        mots = corrected_name.split(" ")
        destinations = []
        exacts = []
        starts = []
        ends = []
        dists = []
        senconds = []
        motsss = mots
        leven = []
        if len(mots) > 1:
            motsss += [allin_one]
        space_replace = allin_one.lower().replace(" ", "")
        unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
        unaccented_string_name = self.remove_accent(unscane_replace)
        for partner in self.env['sochepress.destination'].sudo().search([('type', '=', 'client_final')]):
            space_replace = partner.name.lower().replace(" ", "")
            unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
            unaccented_string_partner = self.remove_accent(unscane_replace)
            cond1 = (unaccented_string_partner in unaccented_string_name)
            cond2 = (unaccented_string_name in unaccented_string_partner)
            cond3 = (unaccented_string_name == unaccented_string_partner)
            cond4 = unaccented_string_partner.startswith(unaccented_string_name)
            cond5 = unaccented_string_partner.endswith(unaccented_string_name)
            if cond3:
                exacts.append(partner)
            if cond1 or cond2:
                if partner not in destinations:
                    destinations.append(partner)
            if cond4:
                starts.append(partner)
            if cond5:
                ends.append(partner)
            senconds.append(
                (partner, SequenceMatcher(None, unaccented_string_name, unaccented_string_partner).ratio()))
            leven.append((partner, distance(unaccented_string_partner, unaccented_string_name)))
            dists.append(
                (partner, damerauLevenshtein(unaccented_string_name, unaccented_string_partner, similarity=False)))
        #             # if cond3:
        # for m in motsss:
        #     if len(m) > 3:
        #         space_replace = m.lower().replace(" ", "")
        #         unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
        #         unaccented_string_name = self.remove_accent(unscane_replace)
        #         for partner in self.env['sochepress.destination'].sudo().search([('type', '=', 'client_final')]):
        #             space_replace = partner.name.lower().replace(" ", "")
        #             unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
        #             unaccented_string_partner = self.remove_accent(unscane_replace)
        #             cond1 = (unaccented_string_partner in unaccented_string_name)
        #             cond2 = (unaccented_string_name in unaccented_string_partner)
        #             cond3 = (unaccented_string_name == unaccented_string_partner)
        #             cond4 = unaccented_string_partner.startswith(unaccented_string_name)
        #             cond5 = unaccented_string_partner.endswith(unaccented_string_name)
        #             if cond3:
        #                 exacts.append(partner)
        #             if cond1 or cond2:
        #                 if partner not in destinations:
        #                     destinations.append(partner)
        #             if cond4:
        #                 starts.append(partner)
        #             if cond5:
        #                 ends.append(partner)
        # #             # if cond3:
        # #             #     for p in self.env['sochepress.destination'].sudo().search([('type', '=', 'client_final'), ('id', '!=', partner.id)]):
        # #             # return partner
        # # # print([d.name for d in destinations])
        # # # print([d.name for d in exacts])
        # # # return [d.name for d in destinations], exacts
        # print('====>', [d.name for d in exacts])
        # print('====>', [d.name for d in destinations])
        # print('====>', [d.name for d in starts])
        # print('====>', [d.name for d in ends])
        senconds.sort(key=itemgetter(1))
        leven.sort(key=itemgetter(1))
        # # print('=====>', dists)
        # print('=====>', [(x[0].name, x[1]) for x in senconds[-3:]])
        # print('=====>', [(x[0].name, x[1]) for x in leven[:3]])
        # # max = dists[0][1]
        # # init = False
        # # for x in senconds:
        # #     print("=====>", x[0], x[1])
        # #     if max < x[1]:
        # #         init = x
        # #         max = x[1]
        # # print("====> ", init)
        regle_1 = senconds[-1] if senconds else False
        regle_2 = leven[0] if leven else False
        if regle_1 and regle_2:
            if regle_2[1] <= 1 or regle_1[1] >= 0.7:
                if regle_2[0] == regle_1[0]:
                    return regle_1[0]
        if len(starts) == 1:
            return starts[0]
        if len(ends) == 1:
            return ends[0]
            # else:
            #     return False
        return False
        # if exacts and len(destinations) <= 1:
        #     return exacts[0]
        # if len(destinations) == 1:
        #     return destinations[0]
        # return False
    # verification_ids = fields.Many2many('destination.verif', "Verifications")
    def verified_action(self):
        document_type_id = 34
        #self.env.ref('sochepress_base').id
        for r in self:
            for col in r.request_line_ids:
                if col.return_method_id.name == 'Chèque' and document_type_id not in col.document_ids.mapped('document_type_id').ids:
                    print('bonjour', col.document_ids.mapped('document_type_id').ids)
                    self.env['sochepress.document.colis'].sudo().create({
                        'document_type_id': document_type_id,
                        'colis_id': col.id,
                    })
                col.set_custom_source()
                col.set_custom_destination()
                if not col.source_id and not col.custom_source:
                    raise UserError("The colis %s has no source and no custom source" % col.name)
                if not col.destination_id and not col.custom_destination:
                    raise UserError("The colis %s has no destination and no custom destination" % col.name)
            colis_sources = r.request_line_ids.filtered(lambda l: not l.source_id)
            colis_destinations = r.request_line_ids.filtered(lambda l: not l.destination_id)
            view_id = self.env.ref('sochepress_base.sochepress_verif_wizard_form').id
            if colis_sources:
                key = colis_sources[0].custom_source
                init_colis = colis_sources.filtered(lambda l: l.custom_source == key)
                destination_id = self.existing_location(key)
                action = {
                    'name': _('Localisation Verification'),
                    'res_model': 'sochepress.verif.wizard',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'views': [(view_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_destination_id': destination_id.id if destination_id else False,
                                'default_request_id': r.id,
                                'default_source_colis_ids': [(6, 0, init_colis.ids)], 'default_type': 'source'}
                }
                return action
            if colis_destinations:
                key = colis_destinations[0].custom_destination
                init_colis = colis_destinations.filtered(lambda l: l.custom_destination == key)
                destination_id = self.existing_location(key)
                action = {
                    'name': _('Localisation Verification'),
                    'res_model': 'sochepress.verif.wizard',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'views': [(view_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_destination_id': destination_id.id if destination_id else False,
                                'default_request_id': r.id,
                                'default_destination_colis_ids': init_colis.ids, 'default_type': 'destination'}
                }
                return action
        # self.request_line_ids.compute_price()
        if self.request_line_ids:
            self.set_source_ids()
            # self.set_destination_ids()
            self.generate_expedition()
            self.state = 'verified'
        else:
            raise ValidationError(_(
                    "Aucun colis n'existe dans la demande."
                ))

    def verified_action_automatique(self):
        for r in self:
            for col in r.request_line_ids:
                col.set_custom_source()
                col.set_custom_destination()
                if not col.source_id:
                    return False
                if not col.destination_id:
                    return False
            colis_sources = r.request_line_ids.filtered(lambda l: not l.source_id)
            colis_destinations = r.request_line_ids.filtered(lambda l: not l.destination_id)
            view_id = self.env.ref('sochepress_base.sochepress_verif_wizard_form').id
            if colis_sources:
                key = colis_sources[0].custom_source
                init_colis = colis_sources.filtered(lambda l: l.custom_source == key)
                destination_id = self.existing_location(key)
                action = {
                    'name': _('Localisation Verification'),
                    'res_model': 'sochepress.verif.wizard',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'views': [(view_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_destination_id': destination_id.id if destination_id else False,
                                'default_request_id': r.id,
                                'default_source_colis_ids': [(6, 0, init_colis.ids)], 'default_type': 'source'}
                }
                return False
            if colis_destinations:
                key = colis_destinations[0].custom_destination
                init_colis = colis_destinations.filtered(lambda l: l.custom_destination == key)
                destination_id = self.existing_location(key)
                action = {
                    'name': _('Localisation Verification'),
                    'res_model': 'sochepress.verif.wizard',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'views': [(view_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_destination_id': destination_id.id if destination_id else False,
                                'default_request_id': r.id,
                                'default_destination_colis_ids': init_colis.ids, 'default_type': 'destination'}
                }
                return False
        # self.request_line_ids.compute_price()
        if self.request_line_ids:
            self.set_source_ids()
            # self.set_destination_ids()
            self.generate_expedition()
            self.state = 'verified'
            return True
        else:
            return False    

    def compute_corrected_colis(self):
        list_to_send = []
        for col in self.request_line_ids:
            if col.corrected_source or col.corrected_destination:
                if col.custom_source != col.source_id.name:
                    if col.custom_source not in [x[0] for x in list_to_send]:
                        list_to_send.append([col.custom_source, col.source_id.name])
                if col.custom_destination != col.destination_id.name:
                    if col.custom_destination not in [x[0] for x in list_to_send]:
                        list_to_send.append([col.custom_destination, col.destination_id.name])
        return list_to_send
    def _get_report_base_filename(self):
        self.ensure_one()
        return "Bon d'enlèvement %s" % (self.name)
    def _get_removal_base_filename(self):
        self.ensure_one()
        return 'Barcode of the request %s' % self.name
    def _get_declaration_base_filename(self):
        self.ensure_one()
        return 'Delivery Slips %s' % self.name
    bordereau_ids = fields.Many2many('ir.attachment', string="Bordereau")
    codes_barres = fields.Many2many('ir.attachment', 'conf_code_rel_erp', 'conf_id', 'code_id', string="Codes-Barres 10*10")
    codes_barres_a4 = fields.Many2many('ir.attachment', 'conf_code_rel_erp3', 'conf_id3', 'code_id3', string="Codes-Barres A4")
    be_ids = fields.Many2many('ir.attachment', 'conf_code_rel_erp2', 'conf_id2', 'code_id2', string="BE")
    partners = fields.Many2many('res.partner')
    to_generate = fields.Boolean()
    def generate_codes(self):
        for r in self:
            max_barcodes = r.company_id.max_barcodes or 450
            declarations = self.request_line_ids
            self.generate_colis_barcodes()
            # for d in declarations:
            #     d.ot_id = r.id
            if r.codes_barres:
                r.codes_barres.unlink()
            if r.codes_barres_a4:
                r.codes_barres_a4.unlink()
            ref = 'sochepress_base.action_report_colis_barcode'
            chunks = []
            if len(declarations) >= 10:
                chunks = [declarations[x:x + max_barcodes] for x in range(0, len(declarations), max_barcodes)]
            i = 0
            for x in chunks:
                pdf = self.env.ref(ref).with_context(force_report_rendering=True).render_qweb_pdf(x.ids)
                b64_pdf = base64.b64encode(pdf[0])
                # save pdf as attachment
                # req = declarations[0]
                if len(x) >= 2:
                    plage = '%s - %s' % (x[0].name, x[-1].name)
                else:
                    plage = x.name
                name = 'Codes barres A4 %s' % plage
                self.codes_barres_a4 = [(4, self.env['ir.attachment'].create({
                    'name': name,
                    'type': 'binary',
                    'datas': b64_pdf,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                }).id)]
                i += 1
            # if self.report_type == 'dix':
            ref = 'sochepress_base.action_report_colis_barcode_dix'
            if len(declarations) >= int(max_barcodes / 4):
                chunks = [declarations[x:x + int(max_barcodes / 4)] for x in
                          range(0, len(declarations), int(max_barcodes / 4))]
            i = 0
            for x in chunks:
                pdf = self.env.ref(ref).render_qweb_pdf(x.ids)
                b64_pdf = base64.b64encode(pdf[0])
                # save pdf as attachment
                # req = declarations[0]
                if len(x) >= 2:
                    plage = '%s - %s' % (x[0].name, x[-1].name)
                else:
                    plage = x.name
                name = 'Codes barres 10*10 %s' % plage
                self.codes_barres = [(4, self.env['ir.attachment'].create({
                    'name': name,
                    'type': 'binary',
                    'datas': b64_pdf,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                }).id)]
                i += 1
    def print_all(self):
        for r in self:
            max_bl = r.company_id.max_bl or 200
            declarations = self.declaration_ids
            if declarations and len(declarations) <= max_bl:
                return self.env.ref("sochepress_base.report_customer_request").report_action(declarations.ids,
                                                                                             config=False)
            # for d in declarations:
            #     d.ot_id = r.id
            if r.bordereau_ids:
                r.bordereau_ids.unlink()
            chunks = [declarations[x:x + max_bl] for x in range(0, len(declarations), max_bl)]
            i = 0
            for x in chunks:
                pdf = self.env.ref('sochepress_base.report_customer_request').render_qweb_pdf(x.ids)
                b64_pdf = base64.b64encode(pdf[0])
                # save pdf as attachment
                # req = declarations[0]
                plage = ''
                if len(x) >= 2:
                    plage = '%s - %s' % (x[0].name, x[-1].name)
                else:
                    plage = x.name
                name = 'Bordereaux de livraison %s' % plage
                self.bordereau_ids = [(4, self.env['ir.attachment'].create({
                    'name': name,
                    'type': 'binary',
                    'datas': b64_pdf,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                }).id)]
                # print("=====> Bash   ====>", i)
                i += 1
    def chunks(self, data, SIZE=10000):
        it = iter(data)
        for i in range(0, len(data), SIZE):
            yield {k: data[k] for k in islice(it, SIZE)}
    def print_be(self, back=True):
        for r in self:
            max_be = r.company_id.max_be or 200
            declarations = self.get_grouped_colis()
            if len(declarations) < max_be:
                self.partners = [d.id for d in declarations]
                return self.env.ref('sochepress_base.report_customer_request_second').report_action([self.id])
            else:
                self.to_generate = True
                if r.be_ids:
                    r.be_ids.unlink()
                # chunks = [declarations[x:x + 40] for x in range(0, len(declarations), 40)]
                # print(chunks)
                i = 0
                for x in self.chunks(declarations, max_be):
                    self.partners = [d.id for d in x]
                    pdf = self.env.ref('sochepress_base.report_customer_request_second').render_qweb_pdf(self.id)
                    b64_pdf = base64.b64encode(pdf[0])
                    plage = self.removal_name
                    # if len(x) >= 2:
                    #     plage = '%s - %s' % (x[0].name, x[-1].name)
                    # else:
                    #     plage = x.name
                    name = "Bon d'enlèvement %s" % plage
                    self.be_ids = [(4, self.env['ir.attachment'].create({
                        'name': name,
                        'type': 'binary',
                        'datas': b64_pdf,
                        'res_model': self._name,
                        'res_id': self.id,
                        'mimetype': 'application/pdf'
                    }).id)]
                    print("=====> Bash   ====>", i)
                    i += 1
            # self.partners = False
    def generate_colis_barcodes(self):
        slf = self.sudo()
        lines = slf.request_line_ids or slf.return_request_line_ids
        if not lines:
            raise UserError(_(
                "You can't generate a barcode for an empty request. Please add a "
                "colis."))
        for colis in lines:
            if not colis.barcode:
                colis.generate_barcodes()
    def print_colis_barcodes(self):
        slf = self
        lines = slf.request_line_ids if not slf.is_return else slf.return_request_line_ids
        print("=======>", lines)
        max_barcodes = slf.company_id.max_barcodes or 450
        if not lines:
            raise UserError(_("You can't print an empty request. Please add a colis."))
        if slf.report_type == 'a4':
            if len(lines) < 10:
                return self.env.ref(
                    'sochepress_base.action_report_colis_barcode').report_action(
                    lines.ids,
                    config=False)
            else:
                self.generate_codes()
        else:
            if len(lines) < 10:
                return self.env.ref(
                    'sochepress_base.action_report_colis_barcode_dix').report_action(
                    lines.ids,
                    config=False)
            else:
                self.generate_codes()
    def accepted_action(self):
        self.state = 'accepted'
        self.validation_date = datetime.now()
        self.validator_id = self._uid
        time_diff = self.validation_date - self.demand_date
        self.treatment_delay = float(time_diff.days) * 24 + (
            float(time_diff.seconds) / 3600)
        # print("====================>>>1")
        # for colis in self.request_line_ids:
        #     colis.sudo().check_prepaye()
        # ean = generate_ean(str(colis.id)) seq_customer_request_line
        #     if colis.is_prepaye:
        #         colis.send_otp()
        # # self.notif_request()
        # print("====================>>>2")
        template = self.env.ref('sochepress_base.send_mail_request_acceptation')
        template2 = self.env.ref(
            'sochepress_base.send_mail_request_acceptation_destinator')
        d = self.declaration_ids and self.declaration_ids[0]
        if d.customer_id and d.customer_id.email and not self.era_is_sended:
            self.dest = d.customer_id.name
            # d.min_date = d.planned_delivery_min_date.strftime(
            #     '%d/%m/%Y %H:%M:%S')
            # d.max_date = d.planned_delivery_max_date.strftime(
            #     '%d/%m/%Y %H:%M:%S')
            #template.write({
            #    'partner_to': d.customer_id.id
            #})
            if self.company_id.send_mail_request_acceptation_bool_client:
                self.env['mail.template'].browse(template.id). \
                    send_mail(d.id, force_send=True, raise_exception=True)
                self.era_is_sended = True
        else:
            message = True
        try:
            if self.declaration_ids:
                for d in self.declaration_ids:
                    message = False
                    d.sudo().set_dates()
                    # print("====================>>>3")
                    if d.planned_delivery_min_date:
                        d.min_date = d.planned_delivery_min_date.strftime(
                            '%d/%m/%Y %H:%M:%S')
                    if d.planned_delivery_max_date:
                        d.max_date = d.planned_delivery_max_date.strftime(
                            '%d/%m/%Y %H:%M:%S')
                    if d.destinator_id and d.destinator_id.email:
                        self.dest2 = d.destinator_id.name
                        if d.request_id.validation_date:
                            d.date_acceptation = d.request_id.validation_date.strftime(
                                '%d/%m/%Y %H:%M:%S')
                        template2.write({
                            'partner_to': d.destinator_id.id
                        })
                        if self.company_id.send_mail_request_acceptation_bool_final_destinator:
                            self.env['mail.template'].browse(template2.id). \
                                send_mail(d.id, force_send=True, raise_exception=True)
                    else:
                        message = True
                    if message:
                        title = _("Configuration des mails destinataires!")
                        message = _(
                            "Certains de vos clients n'ont pas d'adresse mails définis!")
                        self.env['bus.bus'].sendone(
                            (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
                            {'type': 'simple_notification', 'title': title,
                             'message': message, 'sticky': False,
                             'warning': True})
        except MailDeliveryException as error:
            self.message_post(
                body=(_("Error when sending mail with Declarations: %s") % (error.args[0]))
            )
        # self.print_all()
        # call fucntion if customer is validation livraison
        for rec in self:
            if rec.customer_id.validation_livraison:
                rec.print_colis_barcodes()
        # call fucntion if customer is validation livraison
    def closed_action(self):
        for r in self:
            for l in r.request_line_ids:
                if l.step != 'delivered':
                    raise UserError(_(
                        'All packages must be delivered to close this request.'))
                if not l.invoiced:
                    raise UserError(_(
                        'Tous les colis doivent être facturés pour clôturer cette '
                        'demande.'))
            r.state = 'closed'
    def canceled_action(self):
        self.state = 'canceled'
        self.validation_date = datetime.now()
        self.validator_id = self._uid
        time_diff = self.validation_date - self.demand_date
        self.treatment_delay = float(time_diff.days) * 24 + (
            float(time_diff.seconds) / 3600)
        for l in self.request_line_ids:
            l.canceled_button()
    def _prepare_invoice(self):
        self.ensure_one()
        # journal = self.env['account.move'].with_context(
        # force_company=self.company_id.id,
        # default_type='out_invoice')._get_default_journal()
        # if not journal:
        #     raise UserError(_('Please define an accounting sales journal for the
        #     company %s (%s).') % (self.company_id.name, self.company_id.id))
        invoice_vals = {
            'ref': '',
            'type': 'out_invoice',
            'invoice_user_id': self.validator_id and self.validator_id.id,
            'partner_id': self.customer_id,
            'invoice_origin': self.name,
            'invoice_line_ids': [],
        }
        return invoice_vals
    def create_invoices(self):
        # precision = self.env['decimal.precision'].precision_get(
        #     'Product Unit of Measure')
        invoice_vals_list = []
        for order in self:
            invoice_vals = order._prepare_invoice()
            if not invoice_vals['invoice_line_ids']:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered '
                    'quantities invoicing policy, please make sure that a quantity '
                    'has been delivered.'))
            for line in order.request_line_ids:
                invoice_vals['invoice_line_ids'].append(
                    (0, 0, line._prepare_invoice_line()))
            invoice_vals_list.append(invoice_vals)
        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered '
                'quantities invoicing policy, please make sure that a quantity has '
                'been delivered.'))
        # Create invoices.
        moves = self.env['account.move'].with_context(
            default_type='out_invoice').create(invoice_vals_list)
        # moves += self.env['account.move'].with_context(
        # default_type='out_refund').create(refund_invoice_vals_list)
        # for move in moves:
        #     move.message_post_with_view('mail.message_origin_link',
        #         values={'self': move, 'origin': move.line_ids.mapped(
        #         'sale_line_ids.order_id')},
        #         subtype_id=self.env.ref('mail.mt_note').id
        #     )
        if moves:
            self.invoice_ids = [(4, moves.id)]
        return moves
    # ///////////////////////////////////////////////////////////////////////
    # def action_create_invoices(self):
    #     requests = self.env['sochepress.customer.request'].browse(
    #     self._context.get('active_ids', []))
    #
    #     for key, customer_requests in groupby(requests,
    #                                           lambda x: (x.customer_id,
    #                                                      fields.Date.from_string(
    #                                                      x.demand_date).month,
    #                                                      fields.Date.from_string(
    #                                                      x.demand_date).year)
    #                                           ):
    #         customer_requests = list(customer_requests)
    #         key = list(key)
    #         invoice_vals = None
    #         origins = set()
    #         price = 0
    #         line_ids = []
    #         for req in customer_requests:
    #             # if req.state == 'closed':
    #             #     raise UserError('la demande %s est déjà fermée' % (req.name))
    #
    #             print("===> REQUEST", req.name)
    #             if not invoice_vals:
    #                 invoice_vals = {
    #                     'type': 'out_invoice',
    #                     'invoice_user_id': req.validator_id and req.validator_id.id,
    #                     'partner_id': req.customer_id,
    #                     'invoice_origin': req.name,
    #                     'invoice_line_ids': [],
    #                 }
    #
    #
    #             # if concerned_colis:
    #             for line in req.request_line_ids:
    #                 if line.step == "delivered" and not line.invoiced:
    #                     xprice = line.price
    #                     if line.request_id.source_request_id:
    #                         xprice = line.request_id.contract_id.retun_rate * price
    #                         / 100
    #                     price += xprice
    #                     line_ids.append(line.id)
    #                     origins.add(line.request_id.name)
    #
    #         if len(line_ids) > 0:
    #             # origins.add(req.name)
    #             # if price:
    #
    #             line = {
    #                 'name': "Frais de messagerie du mois " + str(key[1]) + "/" +
    #                 str(key[2]),
    #                 'quantity': 1,
    #                 'price_unit': price,
    #             }
    #             invoice_vals['invoice_line_ids'].append((0, 0, line))
    #
    #             invoice_vals.update({
    #                 'invoice_origin': ', '.join(origins),
    #
    #             })
    #             pprint(invoice_vals)
    #         else:
    #             raise UserError(
    #                 "La demande %s a été entièrement facturée ou aucun de ces colis
    #                 n'a été livré" % (req.name))
    #
    #         moves = self.env['account.move'].with_context(
    #         default_type='out_invoice').create(invoice_vals)
    #         for req in customer_requests:
    #             if moves:
    #                 print(moves.ids)
    #                 req.invoice_ids = [(4, moves.id)]
    #                 for l in req.request_line_ids:
    #                     if l.id in line_ids:
    #                         l.invoice_id = moves.id
    def action_create_invoices(self):
        requests = self.env['sochepress.customer.request'].browse(
            self._context.get('active_ids', []))
        for key, customer_requests in groupby(requests,
                                              lambda x: (x.customer_id,
                                                         fields.Date.from_string(
                                                             x.demand_date).month,
                                                         fields.Date.from_string(
                                                             x.demand_date).year)
                                              ):
            customer_requests = list(customer_requests)
            key = list(key)
            invoice_vals = None
            origins = set()
            price = 0
            line_ids = []
            for req in customer_requests:
                # if req.state == 'closed':
                #     raise UserError('la demande %s est déjà fermée' % (req.name))
                if not invoice_vals:
                    invoice_vals = {
                        'type': 'out_invoice',
                        'invoice_user_id': req.validator_id and req.validator_id.id,
                        'partner_id': req.customer_id,
                        'invoice_origin': req.name,
                        'invoice_line_ids': [],
                    }
                for line in req.request_line_ids:
                    if line.step == "delivered" or line.step == "refused" and not \
                        line.invoiced:
                        xprice = line.price
                        if line.request_id.source_request_id:
                            xprice = line.request_id.contract_id.retun_rate * \
                                     line.price / 100
                        price += xprice
                        line_ids.append(line.id)
                origins.add(req.name)
            if price > 0:
                line = {
                    'name': "Frais de messagerie du mois " + str(key[1]) + "/" + str(
                        key[2]),
                    'quantity': 1,
                    'price_unit': price,
                }
                invoice_vals['invoice_line_ids'].append((0, 0, line))
                invoice_vals.update({
                    'invoice_origin': ', '.join(origins),
                })
                moves = self.env['account.move'].with_context(default_type='out_invoice').create(invoice_vals)
                for req in customer_requests:
                    if moves:
                        req.invoice_ids = [(4, moves.id)]
                        for l in req.request_line_ids:
                            if l.id in line_ids:
                                l.invoice_id = moves.id
            else:
                raise UserError(
                    "Un de vos colis n'a pas été livré ou a déjà été facturé.")
    def refresh_prices(self):
        for r in self:
            for rl in r.request_line_ids:
                pass
                # rl.compute_price()
    # def unlink(self):
    #     for rec in self:
    #         if rec.state in ['accepted', 'closed', 'canceled']:
    #             raise UserError(
    #                 _("Vous ne pouvez pas supprimer une demande de messagerie fermée ou acceptée ou annulée!"))
    #     return super(CustomerRequest, self).unlink()
class Colis(models.Model):
    _name = 'sochepress.customer.request.line'
    _description = "Customer requests lines model"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    def default_position(self):
        return self.request_id.exp_destination_id
    nb_charged = fields.Integer(default=0)
    operation_done = fields.Boolean(default=False, )
    active = fields.Boolean(default=True)
    origin_id = fields.Many2one('sochepress.customer.request.line')
    doc_colis_ids = fields.One2many('sochepress.customer.request.line', 'origin_id', string="Colis documents")
    colis_received = fields.Boolean(default=False, track_visibility='onchange')
    type = fields.Selection(related="origin_id.type")
    traking_diff_order = fields.Boolean("Suivi diff position OT")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(Colis, self).fields_view_get(view_id=view_id,
                                                 view_type=view_type,
                                                 toolbar=toolbar,
                                                 submenu=submenu)
        if view_type in ['form']:  # Applies only for form view
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field"):
                # print("====>", node.get('name', 'TTTT'))
                if node.get('name', 'TTTT') not in ['delivery_delay_reason_id', 'document_ids', 'null_amount',
                                                    'return_amount']:
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = not self.env.user.has_group('sochepress_base.edit_colis_form')
                    node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
    @api.constrains('order_id')
    def reset_avancement(self):
        for r in self:
            # r.charged = 0
            # # r.nb_charged = 0
            # r.discharged = 0
            # r.operation_done = False
            # r.a_livrer = False
            # r.write({
            #     'charged': 0,
            #     'discharged': 0,
            #     'operation_done': False,
            #     'a_livrer': False
            # })
            req = """UPDATE sochepress_customer_request_line SET charged=0, discharged=0, operation_done='false', a_livrer='false' WHERE id=%s""" % r.id
            self._cr.execute(req)
    def get_contract(self):
        for r in self:
            r.request_id.contract_id = self.env['sochepress.contract'].search(
                [('partner_id', '=', r.request_id.customer_id.id),
                 ('stage_id', '=', self.env.ref(
                     'sochepress_base.sochepress_contract_stage_in_progress').id)],
                limit=1)
    @api.depends('product_id')
    def reset_model(self):
        for r in self:
            if not r.product_id.is_conform:
                r.weight = r.product_id.weight_vol
            else:
                r.weight = r.declared_weight
            if r.weight < 1:
                r.weight = 1
    not_colis_conform = fields.Boolean(string="Not Conform colis", compute='compute_colis_conform', store=1)
    @api.depends('product_id', 'company_id')
    def compute_colis_conform(self):
        for r in self:
            cond0 = r.product_id.colis_pourtour > r.company_id.max_pourtour
            cond1 = (r.product_id.length > r.company_id.max_dimension) or (
                r.product_id.height > r.company_id.max_dimension) or (
                        r.product_id.width > r.company_id.max_dimension)
            r.not_colis_conform = cond1 or cond0
    def _default_delivery_delay_reason_id(self):
        return False
    request_id = fields.Many2one('sochepress.customer.request', string="Request", track_visibility='onchange')
    return_request_id = fields.Many2one('sochepress.customer.request', string="Return Request",
                                        track_visibility='onchange')
    horaire_wanted_id = fields.Many2one('delivery.timing', string="Horaires wanted")
    horaires = fields.Char("horaires")
    request_state = fields.Selection(related='request_id.state', string='Request state', store=True)
    return_request_state = fields.Selection(related='return_request_id.state', string='Return Request state',
                                            store=True)
    current_request_state = fields.Selection(
        [('draft', "Draft"), ('waiting', "Waiting"), ('verified', "Verified"), ('accepted', "Accepted"),
         ('closed', "Closed"), ('canceled', "Canceled")], string="Current Request State",
        compute="_set_current_request_state",
        track_visibility='onchange', store=True)
    type_colis_id = fields.Many2one('sochepress.type.colis', string="Type of colis")
    weight = fields.Float("Weight", track_visibility='onchange')
    name = fields.Char(string="Declaration number", track_visibility='onchange')
    declared_value = fields.Float("Declared value")
    price = fields.Float("Price", readonly=False, store=True, track_visibility='onchange')
    source_id = fields.Many2one('sochepress.destination', string='Source', store=True, track_visibility='onchange')
    destination_id = fields.Many2one('sochepress.destination', string='Destination', store=True,
                                     track_visibility='onchange')
    destination_name = fields.Char(related='destination_id.name', store=1, string='Destination name')
    contract_id = fields.Many2one('sochepress.contract', string="Contract",
                                  related='request_id.contract_id', track_visibility='onchange')
    insurrance_rate = fields.Float(related='contract_id.insurance_rate', track_visibility='onchange')
    company_id = fields.Many2one(related='request_id.company_id', string='Company',
                                 store=True, readonly=True,
                                 index=True)
    demand_date = fields.Datetime("Demand date", related='request_id.demand_date',
                                  store=True,
                                  track_visibility='onchange')
    portal = fields.Integer("Portal", default=1)
    # invoice_ids = fields.Many2many(related='request_id.invoice_ids',
    # string="Invoices", store=True)
    nbre_colis = fields.Integer('Number of colis', default=1, track_visibility='onchange')
    order_id = fields.Many2one("soch.transport.order", track_visibility='onchange')
    date = fields.Datetime(related='order_id.date', track_visibility='onchange')
    customer_id = fields.Many2one(related='request_id.customer_id', store=True, track_visibility='onchange')
    ref = fields.Char(related='customer_id.ref')
    category_id = fields.Many2many(related='customer_id.category_id')
    invoice_id = fields.Many2one("account.move")
    state_colis_id = fields.Many2one('sochepress.etat.colis', string="State of colis",
                                     track_visibility='onchange')
    expeditor_id = fields.Many2one('res.partner', string="Expeditor",
                                   track_visibility='onchange')
    expeditor_name = fields.Char(related='expeditor_id.name')
    expeditor_phone = fields.Char(related='expeditor_id.phone')
    destinator_id = fields.Many2one('res.partner', string="Destinator", track_visibility='onchange')
    destinator_phone = fields.Char(related='destinator_id.phone', string="Destinator phone")
    destinator_name = fields.Char(related='destinator_id.name', string='Destinator name')
    destinator_mail = fields.Char(related='destinator_id.email', string='Destinator mail')
    d_street = fields.Char(related='destinator_id.street', readonly=False, store=True)
    d_street2 = fields.Char(related='destinator_id.street2', readonly=False)
    custom_destination = fields.Char("Destination created by customer")
    custom_source = fields.Char("Source created by customer")
    ref_ext = fields.Char("External Reference")
    corrected_source = fields.Boolean("Source corrected")
    corrected_destination = fields.Boolean("Destination corrected")
    expedition_id = fields.Many2one('sochepress.declaration', string="Expedition")
    is_to_return = fields.Boolean("To return", default=True)
    send_type = fields.Selection([
        ('send', "Send"),
        ('return_on_requests', "Return on requests"),
    ], compute='compute_send_type', string="Send type", store=True)
    notes = fields.Char(sting="Notes")  # modif
    @api.depends('return_request_id')
    def compute_send_type(self):
        for r in self:
            if not r.return_request_id:
                r.send_type = 'send'
            else:
                r.send_type = 'return_on_requests'
    first_tracabilite_date = fields.Datetime(string="First Tracabilite Date", compute='get_first_tracabilite_date')
    status_activation_id = fields.Many2one('sochepress.status.activation',
                                              string="Validation livraison",
                                              track_visibility='onchange')
    validation_livraison = fields.Boolean('Validation livraison', related='expeditor_id.parent_id.validation_livraison',
                           readonly=False)
    @api.depends('expeditor_id')
    def set_custom_source(self):
        for r in self:
            if not r.custom_source:
                if r.expeditor_id.destination_id:
                    r.custom_source = r.expeditor_id.destination_id.name
                else:
                    r.custom_source = r.expeditor_id.city
    @api.depends('destinator_id')
    def set_custom_destination(self):
        for r in self:
            if not r.custom_destination:
                if r.destinator_id.destination_id:
                    r.custom_destination = r.destinator_id.destination_id.name
                else:
                    r.custom_destination = r.destinator_id.city
    @api.depends('send_type', 'request_state', 'return_request_state')
    def _set_current_request_state(self):
        for r in self:
            if r.send_type == 'send':
                # print('send')
                r.current_request_state = r.request_id.state
            if r.send_type == 'return_on_requests':
                # print('return_on_requests')
                r.current_request_state = r.return_request_id.state
    charged = fields.Integer(string="charged", default=0)
    discharged = fields.Integer(string="discharged", default=0)
    current_request = fields.Char("Active Request", compute='get_crequest', store=1)
    reference_bl = fields.Char("Ref BL")
    delivery_delay = fields.Float(string="Delivry delay", compute="get_delivery_day",
                                  store=True, )
    planned_delivery_delay = fields.Float(string="planned Delivry date",
                                          compute="get_planned_delivery_day",
                                          store=True, track_visibility='onchange')
    canceled = fields.Boolean(string="Canceled")
    reference_doc = fields.Boolean(string="Ref Doc")
    delivery_state = fields.Selection(
        [('in_progress', "In Progress"), ('delivered', "Delivered"), ('returned_to_expeditor', "Return to expeditor"),
         ('in_return', "In return to expeditor"), ('non_delivered', "Non Delivered")],
        string="Delivery State", compute='_compute_delivery_state', store="1", track_visibility='onchange')
    delivery_delay_reason_id = fields.Many2one('sochepress.colis.delivery', string="Commentaire",
                                               default=_default_delivery_delay_reason_id, )
    show_ref_bl_ref_doc = fields.Boolean('Show Ref BL AND Ref DOC', related="request_id.show_ref_bl_ref_doc", store=1)
    # ==> A CAHNGER LA REFERENCE APRES LE MERGE
    # reference = fields.Char(related="product_id.default_code_soch")
    reference = fields.Char(related="product_id.default_code", store=True)
    document_ids = fields.One2many('sochepress.document.colis', 'colis_id')
    sms_type_id = fields.Many2one('sls.sms.type', string="SMS Type")
    declared_weight = fields.Float('Declared Weight')
    nbr_documents = fields.Integer(compute='compute_nbr_documents',default=0)
    nbr_documents_digit = fields.Integer(compute='compute_nbr_documents_digit',default=0)
    nbr_documents_phys = fields.Integer(compute='compute_nbr_documents_phys',default=0)


    @api.depends('document_ids')
    def compute_nbr_documents(self):
        for r in self:
            r.nbr_documents = len(r.document_ids)

    @api.depends('document_ids')
    def compute_nbr_documents_digit(self):
        for r in self:
            r.nbr_documents_digit = len(r.document_ids.filtered(lambda v: v.return_type == 'digital'))

    @api.depends('document_ids')
    def compute_nbr_documents_phys(self):
        for r in self:
            r.nbr_documents_phys = len(r.document_ids.filtered(lambda v: v.return_type == 'physical'))

    @api.depends('request_id')
    def get_crequest(self):
        for c in self:
            if c.return_request_id:
                c.current_request = c.return_request_id.name
            else:
                c.current_request = c.request_id.name
    def correct_barcodes(self):
        for r in self:
            # text = "%s%s%s" % (r.request_id.customer_id.ref or '',
            # r.request_id.name, r.id)
            # print("text =====>", text)
            # code = generate_ean(str(r.id))
            colis = r.code_barre_exist(r.barcode)
            # print("=====>", r.barcode)
            # print('====>', colis)
            if len(colis) >= 2:
                for c in colis:
                    ean = int(self.env['ir.sequence'].next_by_code('sochepress.customer.request.line'))
                    ean = generate_ean(str(ean))
                    # ean = '0000000000671'
                    # colis.set_delivery_dates()
                    while r.code_barre_exist(ean):
                        ean = int(self.env['ir.sequence'].next_by_code('sochepress.customer.request.line'))
                        ean = generate_ean(str(ean))
                        # print("============>", ean)
                    # colis.barcode = ean
                    c.barcode = ean
            # print("===>", code, '=========', r.barcode)
    def generate_barcodes(self):
        for r in self:
            if not r.barcode:
                # text = "%s%s%s" % (r.request_id.customer_id.ref or '',
                # r.request_id.name, r.id)
                # print("text =====>", text)
                # code = generate_ean(str(r.id))
                ean = int(self.env['ir.sequence'].next_by_code('sochepress.customer.request.line'))
                ean = generate_ean(str(ean))
                # ean = '0000000000671'
                # colis.set_delivery_dates()
                while r.code_barre_exist(ean):
                    ean = int(self.env['ir.sequence'].next_by_code('sochepress.customer.request.line'))
                    ean = generate_ean(str(ean))
                    # print("============>", ean)
                # colis.barcode = ean
                r.barcode = ean
                # print("===>", code, '=========', r.barcode)
    def canceled_button(self):
        for r in self:
            r.canceled = True
            r.order_id = False
    def reset_cancel_colis(self):
        for r in self:
            r.canceled = False
            print(r.canceled,"r.canceled")
    @api.depends('delivery_date', 'request_id')
    def get_delivery_day(self):
        for r in self:
            if r.delivery_date:
                validation_date = (
                    r.request_id.validation_date if r.request_id.validation_date else
                    r.create_date).date()
                delay = r.delivery_date - validation_date
                r.delivery_delay = delay.days
            else:
                # print("else")
                r.delivery_delay = False
    @api.depends('delivery_date', 'planned_delivery_max_date')
    def get_planned_delivery_day(self):
        for r in self:
            if r.delivery_date and r.planned_delivery_max_date:
                planned_max_date = (r.planned_delivery_max_date).date()
                delay = r.delivery_date - planned_max_date
                # print(delay.days)
                r.planned_delivery_delay = delay.days
            else:
                # print("else")
                r.planned_delivery_delay = False
    # En étiquetage >> Ramassé >> En plateforme >> En route >> En agence >> Encours
    # de livraison >> Livré
    state = fields.Selection([
        ('in_labeling', 'In labeling'),
        ('in_labeling', 'Picked up'),
        ('in_platform', 'In platform'),
        ('on_the_way', 'On the way'),
        ('in_agency', 'In agency'),
        ('in_delivering', 'In delivering'),
        ('delivered', 'Delivered'),
    ], default="in_labeling", string="State")
    # @api.constrains('step')
    def constrains_state(self):
        for colis in self:
            # if colis.step == 'delivered' and len(colis.document_ids) > 0:
            for doc in colis.document_ids.filtered(lambda v: v.return_type == 'physical'):
                data = {
                    "request_id": colis.request_id.id,
                    "origin_id": colis.id,
                    "destinator_id": colis.expeditor_id.id,
                    "expeditor_id": colis.destinator_id.id,
                    "portal": 5 if doc.document_type_id.return_type == 'digital' else 6,
                    "destination_id": colis.source_id.id,
                    "source_id": colis.destination_id.id,
                    "type_colis_id": colis.type_colis_id.id,
                    "weight": 1,
                    "reference_bl": doc.name,
                    'order_id': colis.order_id.id,
                    'step': 'charged',
                    'barcode': doc.barcode,
                }
                print("=============+>", data, "=========> CREATION")
                col = self.env['sochepress.customer.request.line'].create(data)
                print("=============+>", col, "=========> CREATION")
                value_declaration = {'request_id': colis.request_id.id, 'portal': 9,
                                     'customer_id': colis.request_id.customer_id.id,
                                     'expeditor_id': col.expeditor_id.id,
                                     'destinator_id': col.destinator_id.id,
                                     'colis_ids': [(6, 0, [col.id])]}
                decl = self.env['sochepress.declaration'].create(value_declaration)
                col.expedition_id = decl
                # new_colis.generate_barcodes()
    step = fields.Selection([
        ('new', _("New")),
        ('charged', _("Charged")),
        ('discharged', _("Discharged")),
        ('delivered', _("Delivered")),
        ('in_progress', _("In Progress")),
        ('non_delivered', _("Non delivered")),
        ('not_pickup', _("Not pickup")),
        ('refused', _("Refused")),
        ('reported', _("Reported")),
        ('retracted', _("Retracted")),
        ('closed', _("closed")),
    ], default='new', string="Step", track_visibility='onchange')
    volume = fields.Float("Volume", track_visibility='onchange', readonly=False)
    invoiced = fields.Boolean("Invoiced", store=True, compute="compute_invoiced")
    barcode = fields.Char("Barcode", track_visibility='onchange', index=True)
    tracabilite_ids = fields.One2many("sochepress.tracabilite.colis", "colis_id",
                                      )
    track = fields.Boolean("Track", default=False)
    a_livrer = fields.Boolean(default=False, compute="compute_a_livrer", store=1)
    current_position = fields.Many2one('sochepress.destination', string="Position",
                                       track_visibility='onchange')
    nature_marchandise = fields.Many2one('sochepress.merchandise',
                                         string="Nature de marchandise")
    otp_code = fields.Char(string="OTP Code", compute="_generate_otp_code")
    return_state = fields.Selection([
        ('cashed', _("Cashed")),
        ('poured_out', _("Poured out")),
        ('refunded', _("Refunded"))
    ], string="Return of funds statements", track_visibility='onchange')
    return_method_id = fields.Many2one('sls.return.method', string="Return of funds",
                                       store=True, track_visibility='onchange')
    return_amount = fields.Float(string="Amount to be returned", store=True, track_visibility='onchange')
    return_amount_text = fields.Char(string="Amount to be returned char",
                                     compute='get_amount_text', store=1)
    null_amount = fields.Boolean(related='return_method_id.null_amount', store=1)
    # modif
    def get_last_operation(self):
        # last_op = False
        # for record in self:
        #     recs = record.tracabilite_ids.search([], order='date desc')
        #     if recs:
        #         last_op = recs[0]
        last_op = self.env["sochepress.tracabilite.colis"].search([('id', 'in', self.tracabilite_ids.ids)],
                                                                  order="date desc", limit=1)
        return last_op
    @api.depends('return_amount')
    def get_amount_text(self):
        for r in self:
            r.return_amount_text = "%s %s" % (r.return_amount, r.currency_id.name)
    ot_state_return = fields.Selection(related='order_id.transport_type')
    delivery_date = fields.Date(string="Delivery date")
    returned_amount = fields.Float(string="Amount returned", store=True)
    is_prepaye = fields.Boolean(string="is_prepaye", compute="check_prepaye", store=1)
    childs_ids = fields.Many2many('res.partner', string="CHILD", compute="check_childs",
                                  store=True)
    x = fields.One2many(related="customer_id.child_ids")
    localisation_ids = fields.Many2many('sochepress.destination',
                                        # compute="compute_destinations",
                                        string="Destinations",
                                        store=True)
    planned_delivery_max_date = fields.Datetime(string="Maximum planned delivery date")
    planned_delivery_min_date = fields.Datetime(string="Minimum planned delivery date")
    is_refused = fields.Boolean(string="Is refused", default=False,
                                compute="computed_is_refused")
    eap_is_sended = fields.Boolean(default=False)
    r_return_fund_id = fields.Many2one('sls.return.method', string="Initial return of fund", )
    r_return_amount = fields.Float(string="Inital Amount to be returned", )
    remise = fields.Boolean(default=False, track_visibility='onchange')
    @api.constrains('destinator_id')
    def destinator_id_constrains(self):
        for r in self:
            if not r.destinator_id:
                raise UserError(
                    _("Vous ne pouvez pas videz le champs Destinataire"))
    def write(self, vals):
        new_destinator_id = vals.get('destinator_id', False)
        for r in self:
            return_request_id = self.env['sochepress.customer.request'].browse(
                vals.get('return_request_id', r.return_request_id.id))
            request = return_request_id or r.request_id
            declarations = r.request_id.declaration_ids if not return_request_id else return_request_id.declaration_ids
            if new_destinator_id:
                new_destinator_id = self.env['res.partner'].browse(new_destinator_id)
                old_declarations = False
                existant_declarations = False
                for d in declarations:
                    if d.destinator_id and r.request_id.correct_word(
                        d.destinator_id.name) == r.request_id.correct_word(new_destinator_id.name):
                        existant_declarations = d
                        break
                for d in declarations:
                    if r.destinator_id:
                        if d.destinator_id and r.request_id.correct_word(
                            d.destinator_id.name) == r.request_id.correct_word(r.destinator_id.name):
                            old_declarations = d
                            break
                if existant_declarations:
                    existant_declarations.colis_ids += r
                else:
                    value_declaration = {'request_id': request.id, 'portal': r.portal,
                                         'customer_id': r.customer_id.id, 'expeditor_id': r.expeditor_id.id,
                                         'destinator_id': new_destinator_id.id, 'colis_ids': [(4, r.id)]}
                    self.env['sochepress.declaration'].create(value_declaration)
                if old_declarations:
                    old_declarations.colis_ids -= r
                    if not old_declarations.colis_ids:
                        old_declarations.unlink()
        res = super(Colis, self).write(vals)
        if new_destinator_id:
            self.request_id.sudo().set_source_ids()
        return res
    # @api.depends('step')
    def _compute_delivery_state(self):
        for r in self:
            if r.step in ['refused', 'non_delivered']:
                r.delivery_state = 'non_delivered'
            elif r.step == 'delivered':
                if r.send_type == 'return_on_requests':
                    r.delivery_state = 'returned_to_expeditor'
                else:
                    r.delivery_state = 'delivered'
            else:
                if r.send_type == 'return_on_requests':
                    r.delivery_state = 'in_return'
                else:
                    r.delivery_state = 'in_progress'
    @api.model
    def code_barre_exist(self, code):
        bcode = self.env['sochepress.customer.request.line'].search([('barcode', '=', code)])
        docs_bcodes = self.env['sochepress.document.colis'].search([('barcode', '=', code)])
        if bcode or docs_bcodes:
            return bcode or docs_bcodes
        return False
    @api.model
    def code_barre_exist_search_indexed_without_all_conditions(self, code):
        bcode = self.env['sochepress.customer.request.line'].search([('barcode', '=', code)], limit=1)
        if bcode:
            return bcode
        return False
    @api.model
    def code_barre_exist_search(self, code):
        bcode = self.env['sochepress.customer.request.line'].search(
            [('step', '!=', 'closed'), ('new_livreur_id', '=', self.env.uid), ('barcode', '=', code)], limit=1)
        if bcode:
            return bcode
        return False
    @api.model
    def code_barre_exist_sql(self, code):
        self._cr.execute(
            """SELECT * FROM sochepress_customer_request_line colis WHERE colis.step != 'closed'
            AND colis.barcode = '%s'  AND active = 'true' LIMIT 1""" % code
        )
        bcode = self._cr.dictfetchone()
        if bcode:
            return bcode
        return False
    @api.model
    def code_barre_exist_sql_without_conditions(self, code):
        self._cr.execute(
            """
            SELECT * FROM sochepress_customer_request_line colis
            WHERE colis.barcode = %(code)s LIMIT 1
            """,
            {"code": code},
        )
        bcode = self._cr.dictfetchone()
        if bcode:
            return bcode
        return False
    bcode_exist = fields.Boolean(compute='code_barre_exist_field', string="Barcode exists", store=1)
    def code_barre_exist_field(self):
        for r in self:
            bcode = self.env['sochepress.customer.request.line'].search([('barcode', '=', r.barcode)])
            if len(bcode) > 1:
                return True
            return False
    # POUR AMELIORER LE TEMPS DACCEPTATION DES DEMANDES, LA GENERATION DES DATES DE LIVRAISON DEVIENT ALLOURDI LE SYSTEME
    @api.depends('source_id', 'destination_id')
    def set_delivery_dates(self):
        for r in self:
            # contract = r.request_id.contract_id
            # source = r.source_id
            # destination = r.destination_id
            # type = r.request_id.type
            validation_date = r.request_id.validation_date
            min_date = validation_date + timedelta(hours=24)
            max_date = validation_date + timedelta(hours=48)
            r.planned_delivery_max_date = max_date
            r.planned_delivery_min_date = min_date
            min_duration = 24
            max_duration = 48
            r.planned_delivery_max_date = validation_date + timedelta(
                hours=max_duration)
            r.planned_delivery_min_date = validation_date + timedelta(
                hours=min_duration)
            # if contract.tarification_grill_id and source and destination:
            #     prices = contract.tarification_grill_id.price_list_ids
            #     # print("PRICES", prices)
            #     # if not source or not destination:
            #     #     raise UserError(_("Please specify destination and source"))
            #     if prices:
            #         # weight  = max([p.max_value for p in prices])
            #         # if r.weight > weight:
            #         #     raise ValidationError("Le poids de votre colis excede le
            #         #     poids maximal autorisé")
            #
            #         fprice = prices.filtered(lambda price:
            #                                  (price.source_id.id in [source.id,
            #                                                          destination.id] and
            #                                   price.destination_id.id in
            #                                   [source.id, destination.id]) and
            #                                  (
            #                                          price.min_value <= r.weight
            #                                          <= price.max_value) and
            #                                  (price.demand_type == type)
            #                                  )
            #
            #         if len(fprice) > 1:
            #             # the_price = False
            #             for p in fprice:
            #                 # print('price', p
            #                 cond1 = (
            #                         p.destination_id.id == destination.id and
            #                         p.source_id.id == source.id)
            #                 cond2 = (
            #                         p.source_id.id == destination.id and
            #                         p.destination_id.id == source.id)
            #                 # if destination.id == p.destination_id.id:
            #                 if cond1 or cond2:
            #                     fprice = p
            #                     break
            #         for l in fprice:
            #             min_duration = l.duration_min
            #             max_duration = l.duration_max
            #             r.planned_delivery_max_date = validation_date + timedelta(
            #                 hours=max_duration)
            #             r.planned_delivery_min_date = validation_date + timedelta(
            #                 hours=min_duration)
    def unlink(self):
        for rec in self:
            if rec.step != 'new':
                raise UserError(
                    _("Vous ne pouvez pas supprimer un colis qui n'est pas nouveau"))
        return super(Colis, self.sudo()).unlink()
    @api.onchange('expeditor_id')
    def check_exp_request_line(self):
        for r in self:
            r.source_id = r.expeditor_id.destination_id
            # r.destination_id = r.destinator_id.destination_id
    @api.onchange('destinator_id')
    def check_destination_request_line(self):
        for r in self:
            # r.source_id = r.expeditor_id.destination_id
            r.destination_id = r.destinator_id.destination_id
    @api.onchange('product_id')
    def check_weight_request_line(self):
        for r in self:
            if not r.product_id.is_conform:
                r.weight = r.product_id.weight_vol
    @api.depends("step")
    def computed_is_refused(self):
        for r in self:
            if r.step == 'refused':
                r.is_refused = True
            else:
                r.is_refused = False
    # @api.depends('request_id')
    # def _get_partern_domains(self):
    #     res = {'domain': {}}
    #     childs = []
    #     print(self.request_id)
    #     print(self.customer_id)
    #     if self.request_id and self.request_id.customer_id and
    #     self.request_id.customer_id.child_ids:
    #         for l in self.request_id.customer_id.child_ids:
    #             if l.parent_id:
    #                 childs.append(l.parent_id.id)
    #
    #     print("======+++>", childs, '=====================')
    #     return [('id', 'in', childs)]
    # @api.onchange('request_id', 'customer_id')
    # def _update_partern_domains(self):
    #     res = {'domain': {}}
    #     childs = []
    #     if self.request_id and self.request_id.customer_id and
    #     self.request_id.customer_id.child_ids:
    #         for l in self.request_id.customer_id.child_ids:
    #             if l.parent_id:
    #                 childs.append(l.parent_id.id)
    #
    #     res['domain']['destinator_id'] = [('id', 'in', childs)]
    #     res['domain']['expeditor_id'] = [('id', 'in', childs)]
    #
    #     return res
    @api.depends('request_id')
    def check_childs(self):
        # res = {'domain': {}}
        for r in self:
            childs = []
            r.childs_ids = False
            if r.request_id and r.request_id.customer_id and \
                r.request_id.customer_id.child_ids:
                for l in r.request_id.customer_id.child_ids:
                    if l.parent_id:
                        childs.append(l.parent_id.id)
                r.childs_ids = [(6, 0, childs)]
            # pprint(childs)
    # @api.depends('contract_id', 'contract_id.tarification_grill_id.price_list_ids')
    # def compute_destinations(self):
    #     for r in self:
    #         sources = []
    #         request_sources = """
    #             select distinct source_id from soch_price_list_rule where price_list_id = %s
    #         """ % r.contract_id.tarification_grill_id.id
    #         self.env.cr.execute(request_sources)
    #         data_rub = self.env.cr.dictfetchall()
    #         pprint(data_rub)
    #         for d in data_rub:
    #             sources.append(d['source_id'])
    #
    #         request_destinations = """
    #                         select distinct destination_id from soch_price_list_rule where price_list_id = %s
    #                     """ % r.contract_id.tarification_grill_id.id
    #         self.env.cr.execute(request_destinations)
    #         data_rub = self.env.cr.dictfetchall()
    #         pprint(data_rub)
    #         for d in data_rub:
    #             if d['destination_id'] not in sources:
    #                 sources.append(d['destination_id'])
    #         r.localisation_ids = [(6, 0, [])]
    @api.depends('return_method_id')
    def check_prepaye(self):
        self = self.sudo()
        for r in self:
            if r.return_method_id == self.env.ref('sochepress_base.return_method_4'):
                r.is_prepaye = True
            else:
                r.is_prepaye = False
    # @api.onchange('request_id', 'weight', 'contract_id', 'customer_id')
    # def check_weight(self):
    #     for r in self:
    #         if r.portal == 1 and r.weight > r.request_id.contract_id.max_weight:
    #             raise ValidationError(_("The weight defined exceeds the maximum weight of your price list."))
    # @api.constrains('request_id', 'request_id.contract_id', 'request_id.customer_id')
    # def check_volume(self):
    #     for r in self:
    #         if r.volume > r.request_id.contract_id.max_volume:
    #             raise ValidationError(_("The volume defined exceeds the maximum
    #             volume of your price list."))
    @api.depends('order_id')
    def get_ordername(self):
        for r in self:
            r.ot_name = r.order_id.name
    # portal = fields.Integer("Portal", default=1)
    # @api.onchange('return_method_id')
    # def amount_greater_than_zero(self):
    #     for r in self:
    #         if r.portal == 1:
    #             if r.return_method_id and r.return_amount <= 0 and not r.return_method_id == self.env.ref(
    #                 'sochepress_base.return_method_4'):
    #                 raise ValidationError(_(" Please enter the return amount"))
    def _generate_otp_code(self):
        for r in self:
            r.otp_code = False
            if r.request_id.state == 'accepted':
                hotp = pyotp.HOTP('base32secret3232')
                r.otp_code = hotp.at(r.id)
    dest = fields.Char()
    def send_otp(self):
        template = self.env.ref('sochepress_base.otp_code_mail_emplate1')
        for l in self:
            if not l.destinator_id:
                if self.customer_id and self.customer_id.email:
                    self.dest = self.customer_id.name
                    template.write({
                        'partner_to': self.customer_id.id
                    })
                    self._generate_otp_code()
                    if l.company_id.otp_code_mail_emplate1_bool_client:
                        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True,
                                                                                raise_exception=True)
                else:
                    if self.company_id.check_mail:
                        raise ValidationError(
                            _(" Please define an email address for your customer"))
            else:
                if l.destinator_id and l.destinator_id.email:
                    self.dest = l.destinator_id.name
                    template.write({
                        'partner_to': l.destinator_id.id
                    })
                    if l.company_id.otp_code_mail_emplate1_bool_final_destinator:
                        self.env['mail.template']. \
                            browse(template.id).send_mail(l.id, force_send=True,
                                                          raise_exception=True)
                else:
                    if self.company_id.check_mail:
                        raise ValidationError(
                            _("Please enter an email address to the customer %s" % (
                                l.destinator_id.name)))
    def resend_otp(self):
        self._generate_otp_code()
        self.send_otp()
    def get_next_position(self):
        # trajects = [(tr.sequence, tr.name) for tr in self.order_id.traject_ids]
        position = ""
        if self.order_id and self.order_id.traject_ids:
            trajects = [tr.destination_id for tr in self.order_id.traject_ids]
            cur_index = trajects.index(self.order_id.current_position_id.destination_id)
            next_index = (cur_index + 1) % len(trajects)
            next_position = trajects[next_index]
            position = _("Loading to ") + next_position.name
        return position
    @api.depends('invoice_id', 'invoice_id.state')
    def compute_invoiced(self):
        for r in self:
            if r.invoice_id and r.invoice_id.state != 'cancel':
                r.invoiced = True
            else:
                r.invoiced = False
    @api.depends('step', 'destination_id', 'order_id', 'order_id.destination_id')
    def compute_a_livrer(self):
        for r in self:
            cond0 = r.step not in ['reported', 'delivered', 'non_delivered', 'discharged', 'not_pickup']
            cond1 = r.destination_id == r.order_id.current_position_id.destination_id
            if r.order_id.traject_ids:
                cond2 = r.order_id.current_position_id != r.order_id.traject_ids[0]
            else:
                cond2 = False
            if cond0 and cond1 and cond2:
                r.a_livrer = True
            else:
                r.a_livrer = False
    def _compute_name(self):
        name = ''
        colis = True
        while colis:
            name = ''.join(
                random.choice(string.ascii_letters + '0123456789') for x in
                range(8))
            name = name.upper()
            value = """SELECT id FROM sochepress_customer_request_line as ot WHERE ot.name = '%s' LIMIT 1""" % name
            self._cr.execute(value)
            colis = self._cr.dictfetchone()
            # colis = self.env['sochepress.customer.request.line'].search(
            #     [('name', '=', name)])
        return name
    @api.model
    def create(self, vals):
        start_time = datetime.now()
        print("start create")
        res = super(Colis, self.sudo()).create(vals)
        for r in res:
            # pos = self.env['sochepress.trajet'].search([('destination_id','=',
            # r.source_id)],limit=1)
            if not r.current_position:
                r.current_position = r.source_id
            # print("ID", r.id)
            end_time = datetime.now()
            print("Time load before _compute_name = " + str(end_time - start_time))
            r.name = r._compute_name()
            end_time = datetime.now()
            print("Time load after _compute_name = " + str(end_time - start_time))
            r.set_custom_source()
            end_time = datetime.now()
            print("Time load after set_custom_source = " + str(end_time - start_time))
            r.set_custom_destination()
            end_time = datetime.now()
            print("Time load after set_custom_destination = " + str(end_time - start_time))

            # if r.barcode:
            #
            # else:
            #     r.name = str(r.id)
        # related_vals = {}
        # for field in ['barcode_rule_id', 'barcode_base']:
        #     if vals.get(field, False):
        #         related_vals[field] = vals[field]
        #     if related_vals:
        #         res.write(related_vals)
        end_time = datetime.now()
        print("end create = " + str(end_time - start_time))
        return res
    # @api.constrains('barcode')
    # def compute_barcode_name(self):
    #     for r in self:
    #         print(r.barcode)
    #         if r.barcode:
    #             r.name = "%s_%s" % (r.id, r.barcode)
    #         else:
    #             r.name = str(self.id)
    # def write(self, vals):
    #     print("WWWWWW")
    #     print(vals.get('barcode', False))
    #     if vals.get('barcode', False):
    #         if vals.get('barcode', False) != "":
    #             vals['name'] = "%s_%s" % (self.id, self.barcode)
    #         else:
    #             vals['name'] = str(self.id)
    #     print(vals['name'])
    #
    #     return super(Colis, self).write(vals)
    return_doc_invoice = fields.Boolean("Return document: Invoice",
                                        related='request_id.return_doc_invoice',
                                        store=1)
    return_bl = fields.Boolean("Facturation Retour DOC")
    product_id = fields.Many2one('product.template', string="Colis model")
    type = fields.Selection([('normal', "Normal"), ('transport', "Dedicted transport"),
                             ('course', "Urgent course")],
                            string="Type", track_visibility='onchange')
    # @api.depends('weight', 'declared_value', 'return_amount', 'contract_id',
    #              'source_id', 'destination_id',
    #              'customer_id', 'return_doc_invoice', 'return_bl')
    # def compute_price(self):
    #     for r in self:
    #         contract = r.request_id.contract_id
    #         source = r.source_id
    #         destination = r.destination_id
    #         if r.weight != 0:
    #             if contract:
    #                 pod_amount = 0
    #                 cod_amount = 0
    #                 if r.return_bl:
    #                     pod_amount = contract.pod_amount
    #                 if r.return_amount > 0:
    #                     x = r.return_amount * contract.cod_percent / 100
    #                     if x <= contract.min_amount:
    #                         cod_amount = contract.min_amount
    #                     elif contract.min_amount < x < contract.max_amount:
    #                         cod_amount = x
    #                     elif x >= contract.max_amount:
    #                         cod_amount = contract.max_amount
    #
    #                 if contract.tarification_grill_id:
    #                     prices = contract.tarification_grill_id.price_list_ids
    #                     if not source or not destination:
    #                         if r.portal == 1:
    #                             raise UserError(_("Please specify destination and source"))
    #                     if prices:
    #                         # weight  = max([p.max_value for p in prices])
    #                         # if r.weight > weight:
    #                         #     raise ValidationError("Le poids de votre colis
    #                         #     excede le poids maximal autorisé")
    #                         #
    #                         # fprice = prices.filtered(lambda price:
    #                         #                          (price.source_id.id in [
    #                         #                          source.id, destination.id] and
    #                         #                           price.destination_id.id in [
    #                         #                           source.id, destination.id]) and
    #                         #                          (price.min_value <= r.weight
    #                         #                          <= price.max_value))
    #                         # print("====FFFFFFFFF===>",fprice)
    #                         x = 0
    #                         r.price = 0
    #                         for p in prices:
    #                             # print('price', p
    #                             cond3 = (p.min_value <= r.weight <= p.max_value)
    #                             cond1 = (p.destination_id.id == destination.id and
    #                                      p.source_id.id == source.id)
    #                             cond2 = (p.source_id.id == destination.id and
    #                                      p.destination_id.id == source.id)
    #
    #                             # if destination.id == p.destination_id.id:
    #                             if cond3 and (cond1 or cond2):
    #                                 # print('==== THE PRICE', p)
    #                                 x = 1
    #                                 r.price = \
    #                                     p.price + contract.insurance_rate * \
    #                                     r.declared_value / 100 + pod_amount + cod_amount
    #                                 break
    #
    #                         # if x == 1:
    #                         #     print("==================", x, fprice)
    #                         #
    #                         # else:
    #                         #     r.price = 0
    #
    #                         # if len(fprice) > 1:
    #                         #     # the_price = False
    #                         #
    #                         #
    #                         # elif len(fprice) == 1:
    #                         #
    #                         #     r.price = fprice.price + contract.insurance_rate *
    #                         #     r.declared_value / 100 + pod_amount + cod_amount
    #                         #
    #                         # else:
    #                         #     r.price = 0.0
    #                         # raise Exception("Any price rule fits this colis")
    #                     else:
    #                         r.price = 0.0
    #                         # raise Exception(_("Any price rule find for this
    #                         # tarification grill"))
    #                 else:
    #                     r.price = 0.0
    #                     # raise Exception(_("Any tarification grill for this contract"))
    #             else:
    #                 r.price = 0.0
    #                 # raise Exception(_("Please select a contract"))
    #         else:
    #             r.price = 0.0
    #         r.request_id.compute_sums()
    def _compute_charging_colis(self):
        for r in self:
            return len(r.tracabilite_ids.filtered(lambda t: not t.operation_type == 'charge'))
    def get_first_tracabilite_date(self):
        for r in self:
            r.first_tracabilite_date = self.env['sochepress.tracabilite.colis'].search([('colis_id', '=', r.id)],
                                                                                       order="date asc", limit=1).date
    def _prepare_invoice_line(self):
        self.ensure_one()
        return {
            'name': "aaa",
            # 'type_colis_id': self.type_colis_id.id,
            'quantity': 1,
            'price_unit': self.price,
        }
    # @api.constrains('step')
    # def compute_forward_button(self):
    #     for r in self:
    #         r = r.order_id
    #         print(len(r.colis.filtered(lambda col: col.step == 'discharged')))
    #         print('-------------------------------------------')
    #         print(len(r.colis))
    #         print('-------------------------------------------')
    #         print(len(r.colis.filtered(lambda col: col.step == 'charged')))
    #         cond1 = len(r.colis.filtered(lambda col: col.step == 'discharged')) ==
    #         len(r.colis)
    #         cond2 = len(r.colis.filtered(lambda col: col.step == 'charged')) == 0
    #         r.hide_forward = cond1 or cond2
    #         print(r.hide_forward)
    retract = fields.Selection([('yes', "Yes"), ('no', "No")],
                               string="Retracted", track_visibility='onchange')
    def refuse(self):
        for r in self:
            # if r.operation_done:
            #     raise ValidationError(
            #         _("You can't make more than one movement per position !"))
            r = r.sudo()
            # if r.step == 'delivered':
            #     raise ValidationError(_(
            #         "Vous ne pouvez pas refusé un colis livré.\n"
            #     ))
            returns = False
            if r.step == 'refused':
                raise ValidationError(_(
                    "Vous avez déjà refusé ce colis."
                ))
            else:
                tracking = self.env["sochepress.tracabilite.colis"].sudo()
                data = {
                    'operation_type': 'refused',
                    'source_id': r.order_id.current_position_id.destination_id.sudo().id,
                    'operator_id': self.env.uid,
                    'date': fields.Datetime.now(),
                    'colis_id': r.id,
                }
                r.operation_done = True
                print("====> 666666 before generation expedition")
                tracking.sudo().create(data)
                r.current_position = r.order_id.current_position_id.destination_id.sudo()
                data = {
                    'customer_id': r.request_id.sudo().customer_id.id,
                    'type': r.request_id.type,
                    'demand_date': fields.Datetime.now(),
                    'destinator_id': r.request_id.sudo().expeditor_id.id,
                    'expeditor_id': r.request_id.sudo().destinator_id.id,
                    'contract_id': r.request_id.sudo().contract_id.id,
                    'exp_destination_id': r.request_id.sudo().dest_destination_id.sudo().id,
                    'dest_destination_id': r.request_id.sudo().exp_destination_id.sudo().id,
                    'is_return': True,
                    'state': 'accepted',
                    'portal': 10 if r.step != 'delivered' else 12,
                }
                returns = self.env['sochepress.customer.request'].sudo().create(data)
                returns.source_request_id = r.request_id.sudo().id
                returns.is_return = True
                returns.validation_date = fields.Datetime.now()
                returns.validator_id = self._uid
                time_diff = returns.sudo().validation_date - returns.sudo().demand_date
                returns.treatment_delay = float(time_diff.days) * 24 + (
                    float(time_diff.seconds) / 3600)
                # re_colis = r.copy()
                print("====> 222222 before generation expedition")
                r.sudo().write({'return_request_id': returns.sudo().id,
                                # 'order_id': False,
                                'invoiced': False,
                                'step': 'refused',
                                'destinator_id': r.expeditor_id.id,
                                'expeditor_id': r.destinator_id.id,
                                'source_id': r.destination_id.sudo().id,
                                'destination_id': r.source_id.sudo().id,
                                'delivery_delay_reason_id': self.env.ref(
                                    'sochepress_base.motif_delivery_refused').id,
                                'return_amount': 0,
                                'return_method_id': False,
                                'r_return_fund_id': r.return_method_id.id,
                                'r_return_amount': r.return_amount,
                                'portal': 10 if r.step != 'delivered' else 12,
                                'is_return': True,
                                })
                print("====> before generation expedition")
                returns.generate_expedition()
                # print(re_colis)
            # modif
            return returns
    def retract_method(self):
        for r in self:
            # if r.operation_done:
            #     raise ValidationError(
            #         _("You can't make more than one movement per position !"))
            r = r.sudo()
            # if r.step == 'delivered':
            #     raise ValidationError(_(
            #         "Vous ne pouvez pas refusé un colis livré.\n"
            #     ))
            returns = False
            if r.step != 'retracted':
                r.step = 'retracted'
                tracking = self.env["sochepress.tracabilite.colis"].sudo()
                data = {
                    'operation_type': 'retract',
                    'source_id': r.order_id.current_position_id.destination_id.sudo().id,
                    'operator_id': self.env.uid,
                    'date': fields.Datetime.now(),
                    'colis_id': r.id,
                }
                r.operation_done = True
                tracking.sudo().create(data)
                r.current_position = r.order_id.current_position_id.destination_id.sudo()
                data = {
                    'customer_id': r.request_id.customer_id.id,
                    'type': r.request_id.type,
                    'demand_date': fields.Datetime.now(),
                    'destinator_id': r.request_id.expeditor_id.id,
                    'expeditor_id': r.request_id.destinator_id.id,
                    'contract_id': r.request_id.contract_id.id,
                    'exp_destination_id': r.request_id.dest_destination_id.sudo().id,
                    'dest_destination_id': r.request_id.exp_destination_id.sudo().id,
                    'is_return': True,
                    'state': 'accepted',
                    'portal': 11,
                }
                returns = self.env['sochepress.customer.request'].sudo().create(data)
                returns.source_request_id = r.request_id.sudo().id
                returns.is_return = True
                returns.validation_date = fields.Datetime.now()
                returns.validator_id = self._uid
                time_diff = returns.sudo().validation_date - returns.sudo().demand_date
                returns.treatment_delay = float(time_diff.days) * 24 + (
                    float(time_diff.seconds) / 3600)
                # re_colis = r.copy()
                r.sudo().write({'return_request_id': returns.id,
                                # 'order_id': False,
                                'invoiced': False,
                                'step': 'retracted',
                                'destinator_id': r.expeditor_id.id,
                                'expeditor_id': r.destinator_id.id,
                                'source_id': r.destination_id.sudo().id,
                                'destination_id': r.source_id.sudo().id,
                                'delivery_delay_reason_id': self.env.ref(
                                    'sochepress_base.motif_delivery_refused').id,
                                'return_amount': 0,
                                'return_method_id': False,
                                'r_return_fund_id': r.return_method_id.id,
                                'r_return_amount': r.return_amount,
                                'portal': 10 if r.step != 'delivered' else 12,
                                'is_return': True,
                                'retract': 'yes',
                                })
                returns.generate_expedition()
                returns.generate_colis_services()
                returns.generate_expeditions_services()
            return returns
    def set_to_return(self):
        for r in self:
            r.remise = False
            if not r.remise:
                if r.order_id:
                    traces = [(t, t.create_date) for t in r.tracabilite_ids]
                    traces.sort(key=itemgetter(1), reverse=True)
                    # print("traces", traces)
                    # return
                    for x in traces:
                        t = x[0]
                        if t.operation_type == 'refused':
                            t.operation_type = 'report'
                            break
                    if r.step == 'refused':
                        r.step = 'reported'
                    # r.report2()
                else:
                    raise ValidationError(_(
                        "Veuillez affecter un OT à ce colis pour le Remettre.\n"
                    ))
                r.current_position = r.order_id.current_position_id.destination_id
                req = r.return_request_id
                r.write({'return_request_id': False,
                         'destinator_id': r.expeditor_id.id,
                         'expeditor_id': r.destinator_id.id,
                         'source_id': r.destination_id.id,
                         'destination_id': r.source_id.id,
                         'return_method_id': r.r_return_fund_id.id,
                         'return_amount': r.r_return_amount,
                         'remise': True,
                         'retract': 'no',
                         'delivery_state': 'in_progress'
                         })
                        #  'delivery_delay_reason_id': False,
                req.declaration_ids.unlink()
                req.unlink()
                # print(re_colis)
            return {'success': _("Colis returned")}
        else:
            return {'success': _("This colis has been alredy returned")}
    def non_delivered(self):
        for r in self:
            # if r.operation_done:
            #     raise ValidationError(
            #         _("You can't make more than one movement per position !"))
            if r.step != 'non_delivered':
                r.step = 'non_delivered'
                if not r.delivery_delay_reason_id or r.delivery_delay_reason_id == \
                    self._default_delivery_delay_reason_id():
                    raise UserError(
                        "Veuillez indiquez sur le colis le commentaire de non "
                        "livraison")
                r.current_position = r.order_id.current_position_id.destination_id
                r.delivery_state = 'non_delivered'
                # r.delivery_date = fields.Date.today()
                tracking = self.env["sochepress.tracabilite.colis"].sudo()
                data = {
                    'operation_type': 'non_delivered',
                    'source_id': r.order_id.current_position_id.destination_id.id,
                    'operator_id': self.env.uid,
                    'date': fields.Datetime.now(),
                    'colis_id': r.id,
                }
                r.operation_done = True
                if r.step == 'delivered':
                    raise ValidationError(_(
                        "Vous ne pouvez pas mouvementer un colis livré.\n"
                    ))
                tracking.create(data)
        return {'warning': _("This colis is not delivered, please refresh your OT")}
    def report2(self):
        for r in self:
            # if r.operation_done:
            #     raise ValidationError(
            #         _("You can't make more than one movement per position !"))
            # if r.step != 'non_delivered':
            # r.step = 'non_delivered'
            # if not r.delivery_delay_reason_id or r.delivery_delay_reason_id ==
            # self._default_delivery_delay_reason_id():
            # r.delivery_delay_reason_id = self.env.ref(
            # 'sochepress_base.motif_delivery_report').id
            if not r.delivery_delay_reason_id or r.delivery_delay_reason_id == \
                self._default_delivery_delay_reason_id():
                raise UserError(
                    "Veuillez entrez une commentaire de report de livraison")
            if r.step == 'delivered':
                raise ValidationError(_(
                    "Vous ne pouvez pas reporté un colis livré."
                ))
            r.step = 'reported'
            r.current_position = r.order_id.current_position_id.destination_id
            r.delivery_state = 'in_progress'
            # r.delivery_date = fields.Date.today()
            tracking = self.env["sochepress.tracabilite.colis"].sudo()
            data = {
                'operation_type': 'report',
                'source_id': r.order_id.current_position_id.destination_id.id,
                'operator_id': self.env.uid,
                'date': fields.Datetime.now(),
                'colis_id': r.id,
            }
            r.operation_done = True
            if r.step == 'delivered':
                raise ValidationError(_(
                    "Vous ne pouvez pas reporter un colis livré.\n"
                ))
            tracking.create(data)
        # title = _("Mouvement de colis")
        # message = "La livraison du colis %s a été reporté" % self.name
        # action = {'type': 'simple_notification', 'title': title, 'message':
        # message, 'sticky': True,
        #           'warning': False}
        # self.env['bus.bus'].sendone(
        #     (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), action)
        # return self.get_action(old_ot)
    # nb_charged = fields.Integer
    @api.model
    def report(self, col):
        colis = self.env['sochepress.customer.request.line'].browse(col[0])
        for r in colis:
            # if r.operation_done:
            #     raise ValidationError(
            #         _("You can't make more than one movement per position !"))
            # if r.step != 'non_delivered':
            # r.step = 'non_delivered'
            if not r.delivery_delay_reason_id or r.delivery_delay_reason_id == \
                self._default_delivery_delay_reason_id():
                raise UserError(
                    "Veuillez entrez une commentaire de report de livraison")
            if r.step == 'delivered':
                raise ValidationError(_(
                    "Vous ne pouvez pas reporté un colis livré."
                ))
            # r.delivery_delay_reason_id = self.env.ref(
            # 'sochepress_base.motif_delivery_report').id
            # r.step = 'reported'
            # r.current_position = r.order_id.current_position_id.destination_id
            delivery_state = 'in_progress'
            # r.delivery_date = fields.Date.today()
            tracking = self.env["sochepress.tracabilite.colis"].sudo()
            data = {
                'operation_type': 'report',
                'source_id': r.order_id.current_position_id.destination_id.id,
                'operator_id': self.env.uid,
                'date': fields.Datetime.now(),
                'colis_id': r.id,
            }
            # r.operation_done = True
            # if r.send_type == 'return_on_requests':
            #     delivery_state = 'in_return'
            # else:
            #     delivery_state = 'in_progress'
            # r.nb_charged += 1
            req = """UPDATE sochepress_customer_request_line SET
                            step='reported',
                            track = 'true',
                            operation_done = 'true',
                            current_position=%s,
                            step2='Reported',
                            delivery_state='%s'
                            WHERE id=%s""" % (
                r.order_id.current_position_id.destination_id.id, delivery_state, r.id)
            self._cr.execute(req)
            tracking.create(data)
        title = _("Mouvement de colis")
        message = "La livraison du colis %s a été reporté" % colis.name
        action = {'type': 'simple_notification', 'title': title, 'message': message,
                  'sticky': True,
                  'warning': False}
        self.env['bus.bus'].sendone(
            (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), action)
        return self.get_action(colis.order_id.id)
    # @api.model
    # def report(self, col):
    #     colis = self.env['sochepress.customer.request.line'].browse(col[0])
    #     for r in colis:
    #         # if r.operation_done:
    #         #     raise ValidationError(
    #         #         _("You can't make more than one movement per position !"))
    #         # if r.step != 'non_delivered':
    #         # r.step = 'non_delivered'
    #         if not r.delivery_delay_reason_id or r.delivery_delay_reason_id == \
    #             self._default_delivery_delay_reason_id():
    #             raise UserError(
    #                 "Veuillez entrez une commentaire de report de livraison")
    #         if r.step == 'delivered':
    #             raise ValidationError(_(
    #                 "Vous ne pouvez pas reporté un colis livré."
    #             ))
    #
    #         # r.delivery_delay_reason_id = self.env.ref(
    #         # 'sochepress_base.motif_delivery_report').id
    #         r.step = 'reported'
    #         r.current_position = r.order_id.current_position_id.destination_id
    #         r.delivery_state = 'in_progress'
    #         # r.delivery_date = fields.Date.today()
    #         tracking = self.env["sochepress.tracabilite.colis"].sudo()
    #         data = {
    #             'operation_type': 'report',
    #             'source_id': r.order_id.current_position_id.destination_id.id,
    #             'operator_id': self.env.uid,
    #             'date': fields.Datetime.now(),
    #             'colis_id': r.id,
    #         }
    #         r.operation_done = True
    #         if r.step == 'delivered':
    #             raise ValidationError(_(
    #                 "Vous ne pouvez pas reporter un colis livré.\n"
    #             ))
    #         tracking.create(data)
    #
    #     title = _("Mouvement de colis")
    #     message = "La livraison du colis %s a été reporté" % colis.name
    #     action = {'type': 'simple_notification', 'title': title, 'message': message,
    #               'sticky': True,
    #               'warning': False}
    #     self.env['bus.bus'].sendone(
    #         (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), action)
    #
    #     return self.get_action(colis.order_id.id)
    def charger2(self):
        for r in self:
            if r.operation_done:
                raise UserError(_(
                    "You can't make more than one movement per position !"))
            if r.step == 'delivered':
                raise ValidationError(_(
                    "Vous ne pouvez pas chargé un colis livré."
                ))
            r.current_position = r.order_id.current_position_id.destination_id
            r.track = True
            r.order_id.customer_id_be = r.customer_id
            tracking = self.env["sochepress.tracabilite.colis"].sudo()
            data = {
                'operation_type': 'charge',
                'source_id': r.current_position.id,
                # 'destination_id': self.current_position_id.destination_id.id,
                'operator_id': self.env.uid,
                'date': fields.Datetime.now(),
                'colis_id': r.id,
            }
            r.operation_done = True
            tracking.create(data)
            r.nb_charged += 1
            r.step = 'charged'
    def charger(self):
        for r in self:
            if r.operation_done:
                raise UserError(_(
                    "You can't make more than one movement per position !"))
            if r.step == 'delivered':
                raise ValidationError(_(
                    "Vous ne pouvez pas chargé un colis livré."
                ))
            # r.current_position = r.order_id.current_position_id.destination_id
            # r.track = True
            # r.order_id.customer_id_be = r.customer_id
            req = """UPDATE soch_transport_order SET customer_id_be=%s WHERE id=%s""" % (
                r.customer_id.id, r.order_id.id)
            self._cr.execute(req)
            tracking = self.env["sochepress.tracabilite.colis"].sudo()
            if r.order_id.type_ot == 'collecting' and r.step == 'new' :
                source_id =  r.source_id.id
                if source_id !=  r.order_id.current_position_id.destination_id.id:
                    r.traking_diff_order = True
            else:
                source_id = r.order_id.current_position_id.destination_id.id
            data = {
                'operation_type': 'charge',
                'source_id': source_id,
                # 'destination_id': self.current_position_id.destination_id.id,
                'operator_id': self.env.uid,
                'date': fields.Datetime.now(),
                'colis_id': r.id,
            }
            # r.operation_done = True
            tracking.create(data)
            if r.send_type == 'return_on_requests':
                delivery_state = 'in_return'
            else:
                delivery_state = 'in_progress'
            # r.nb_charged += 1
            req = """UPDATE sochepress_customer_request_line SET
                               step='charged',
                               track = 'true',
                               operation_done = 'true',
                               nb_charged=nb_charged+1,
                               current_position=%s,
                               step2='Charged',
                               delivery_state='%s'
                               WHERE id=%s""" % (
                r.order_id.current_position_id.destination_id.id, delivery_state, r.id)
            self._cr.execute(req)
            #r.get_sls_api_charged_sql()
            # r._compute_delivery_state()
            # r.get_step()
            # r.step = 'charged'
    # def charger(self):
    #     for r in self:
    #         if r.operation_done:
    #             raise UserError(_(
    #                 "You can't make more than one movement per position !"))
    #         if r.step == 'delivered':
    #             raise ValidationError(_(
    #                 "Vous ne pouvez pas chargé un colis livré."
    #             ))
    #
    #         r.current_position = r.order_id.current_position_id.destination_id
    #         r.track = True
    #         r.order_id.customer_id_be = r.customer_id
    #         tracking = self.env["sochepress.tracabilite.colis"].sudo()
    #         data = {
    #             'operation_type': 'charge',
    #             'source_id': r.current_position.id,
    #             # 'destination_id': self.current_position_id.destination_id.id,
    #             'operator_id': self.env.uid,
    #             'date': fields.Datetime.now(),
    #             'colis_id': r.id,
    #         }
    #         r.operation_done = True
    #         tracking.create(data)
    #         r.nb_charged += 1
    #         r.step = 'charged'
    def not_pickup(self):
        for r in self:
            # if r.operation_done:
            #     raise ValidationError(_(
            #         "You can't make more than one movement per position !"))
            # if not r.order_id.finished:
            #     raise UserError(
            #         "Merci de finaliser l'OT avant de livrer.")
            r.step = 'not_pickup'
            r.track = True
            r.current_position = r.order_id.current_position_id.destination_id
            tracking = self.env["sochepress.tracabilite.colis"].sudo()
            # self.delivery_date = fields.Date.today()
            data = {
                'operation_type': r.step,
                'source_id': r.order_id.current_position_id.destination_id.id,
                'operator_id': r.env.uid,
                'date': fields.Datetime.now(),
                'colis_id': r.id,
            }
            r.operation_done = True
            tracking.create(data)
    def livrer(self):
        for r in self:
            # if r.operation_done:
            #     raise ValidationError(_(
            #         "You can't make more than one movement per position !"))
            # <<<<<<< HEAD
            # if r.return_method_id == self.env.ref('sochepress_base.return_method_4'):
            #     view_id = self.env.ref(
            #         'sochepress_base.sochepress_code_otp_wizard_form').id
            #     wiz_id = self.env['sochepress.otp.code.wizard'].create(
            #         {'colis_id': r.id, 'mobile': False})
            #     action = {
            #         'name': _('Code OTP Verification'),
            #         'res_model': 'sochepress.otp.code.wizard',
            #         'view_mode': 'form',
            #         'view_id': view_id,
            #         'views': [(view_id, 'form')],
            #         'type': 'ir.actions.act_window',
            #         'res_id': wiz_id.id,
            #         'target': 'new'
            #     }
            #     return action
            if r.send_type == 'send':
                list_doc = []
                for ll in r.document_ids:
                    list_doc.append(ll.document_type_id.id)
                _logger.info("#################"+str(list_doc))
                #justif = self.env['sochepress.justif'].search([('doc_id','in',list_doc)],limit=2)
                #_logger.info("#################"+str(justif))
                line_doc = []
                for ld in list_doc:
                    line_doc.append((0,0,{'doc_id':ld}))
                _logger.info(line_doc)
                view_id = self.env.ref(
                    'sochepress_base.sochepress_justif_wizard_form').id
                wiz_id = self.env['sochepress.justif.wizard'].create(
                    {'colis_id': r.id, 'mobile': False,'line_ids':line_doc
                        })#,'
                action = {
                    'name': _('Add Justifs'),
                    'res_model': 'sochepress.justif.wizard',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'views': [(view_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'res_id': wiz_id.id,
                    'target': 'new'
                }
                return action
            else:
                mobile = False
                val = self.livrer_trac(mobile)
                return val
    @api.model
    def livrer2(self, colis):
        colis = self.env['sochepress.customer.request.line'].browse(colis[0])
        # if colis.return_method_id == self.env.ref('sochepress_base.return_method_4'):
        #     view_id = self.env.ref(
        #         'sochepress_base.sochepress_code_otp_wizard_form').id
        #     wiz_id = self.env['sochepress.otp.code.wizard'].create(
        #         {'colis_id': colis.id, 'mobile': True})
        #     action = {
        #         'name': _('Code OTP Verification'),
        #         'res_model': 'sochepress.otp.code.wizard',
        #         'view_mode': 'form',
        #         'view_id': view_id,
        #         'views': [(view_id, 'form')],
        #         'type': 'ir.actions.act_window',
        #         'res_id': wiz_id.id,
        #         'target': 'new'
        #     }
        #     return {
        #         'action': action
        #     }
        if colis.send_type == 'send':
            list_doc = []
            _logger.info("##DOCUMENT##"+str(colis.document_ids))
            for ll in colis.document_ids:
                list_doc.append(ll.document_type_id.id)
            _logger.info("#################"+str(list_doc))
                #justif = self.env['sochepress.justif'].search([('doc_id','in',list_doc)],limit=2)
                #_logger.info("#################"+str(justif))
            view_id = self.env.ref(
                    'sochepress_base.sochepress_justif_wizard_form').id
            line_doc = []
            for ld in list_doc:
                line_doc.append((0,0,{'doc_id':ld}))
            _logger.info(line_doc)
            wiz_id = self.env['sochepress.justif.wizard'].create(
                    {'colis_id': colis.id, 'mobile': True,'line_ids':line_doc})#
            action = {
                'name': _('Add Justifs'),
                'res_model': 'sochepress.justif.wizard',
                'view_mode': 'form',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'type': 'ir.actions.act_window',
                'res_id': wiz_id.id,
                'target': 'new'
            }
            return {
                'action': action
            }
        else:
            mobile = True
            val = colis.livrer_trac(mobile)
            return val
    # def decharger(self):
    #     for r in self:
    #         if r.operation_done:
    #             raise UserError(_(
    #                 "You can't make more than one movement per position !"))
    #         # r.step = 'delivered'
    #         if r.step == 'delivered':
    #             raise ValidationError(_(
    #                 "Vous ne pouvez pas déchargé un colis livré."
    #             ))
    #         r.current_position = r.order_id.current_position_id.destination_id
    #         r.track = True
    #         tracking = self.env["sochepress.tracabilite.colis"].sudo()
    #         data = {
    #             'operation_type': 'discharge',
    #             'source_id': r.current_position.id,
    #             'operator_id': self.env.uid,
    #             'date': fields.Datetime.now(),
    #             'colis_id': r.id,
    #         }
    #         r.operation_done = True
    #         tracking.create(data)
    #         r.step = 'discharged'
    def decharger(self):
        for r in self:
            if r.operation_done:
                raise UserError(_(
                    "You can't make more than one movement per position !"))
            if r.step == 'delivered':
                raise ValidationError(_(
                    "Vous ne pouvez pas déchargé un colis livré."
                ))
            # r.current_position = r.order_id.current_position_id.destination_id
            # r.track = True
            tracking = self.env["sochepress.tracabilite.colis"].sudo()
            data = {
                'operation_type': 'discharge',
                'source_id': r.order_id.current_position_id.destination_id.id,
                'operator_id': self.env.uid,
                'date': fields.Datetime.now(),
                'colis_id': r.id,
            }
            # r.operation_done = True
            tracking.create(data)
            # r.step = 'discharged'
            if r.send_type == 'return_on_requests':
                delivery_state = 'in_return'
            else:
                delivery_state = 'in_progress'
            # r.nb_charged += 1
            req = """UPDATE sochepress_customer_request_line SET
                                step='discharged',
                                track = 'true',
                                operation_done = 'true',
                                current_position=%s,
                                step2='Discharged',
                                delivery_state='%s'
                                WHERE id=%s""" % (
                r.order_id.current_position_id.destination_id.id, delivery_state, r.id)
            self._cr.execute(req)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda x: x.env.user.company_id.currency_id)
    def colis_op_infos(self):
        for r in self:
            colis = r.order_id.colis
            nb_colis = len(colis.filtered(lambda c: c.customer_id == r.customer_id))
            nb_step_colis = len(colis.filtered(
                lambda c: c.customer_id == r.customer_id and c.step == r.step))
            r.get_step()
            if r.order_id.type_ot == 'collecting':
                title = _("Mouvements de colis")
                # message = _("Colis %s/%s  %s chez %s" % (
                #     nb_step_colis, nb_colis, r.step2, r.customer_id.name))
                if nb_step_colis == nb_colis:
                    message = _("Tous les colis de chez %s ont été %ss" % (
                        r.customer_id.name, r.step2.lower()))
                    action = {'type': 'simple_notification', 'title': title, 'message': message,
                              'sticky': True,
                              'warning': False}
                    self.env['bus.bus'].sendone(
                        (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), action)
    def reset_to_new(self):
        for r in self:
            r.step = 'new'
    @api.depends('step')
    def get_step(self):
        for r in self:
            # print(r.step)
            if r.step == 'new':
                r.step2 = _("New")
            elif r.step == 'charged':
                r.step2 = _("Charged")
            elif r.step == 'discharged':
                r.step2 = _("Discharged")
            elif r.step == 'delivered':
                r.step2 = _("Delivered")
            elif r.step == 'non_delivered':
                r.step2 = _("Non delivered")
            elif r.step == 'refused':
                r.step2 = _("Refused")
            elif r.step == 'in_progress':
                r.step2 = _("In progress")
    # livreur_id = fields.Many2one('res.users', string="Delivery man",
    #                              track_visibility='onchange',
    #                              related='order_id.livreur_id', store=True)
    def action_view_tracking(self):
        self.ensure_one()
        action = self.env.ref('sochepress_base.tracking_colis_action').read()[0]
        action['domain'] = [('colis_id', '=', self.id)]
        return action
    # @api.constrains('step', 'return_method_id', 'return_amount')
    # def compute_order_state(self):
    #     for r in self:
    #         r.order_id.set_ot_state_affect()
    # @api.constrains('step')
    def send_satisfaction(self):
        print("send_satisfaction")
        """template2 = self.env.ref(
            'sochepress_base.send_mail_satisfaction_destinator')
        template3 = self.env.ref(
            'sochepress_base.send_mail_satisfaction_customer')
        template_context = {
        }
        message = False
        # if self.step == 'delivered':
        # self.delivery_date = fields.Date.today()
        # self.livreur_id = self.env.uid
        if self.request_id.customer_id and self.request_id.customer_id.email:
            self.dest = self.request_id.customer_id.name
            template3.write({
                'partner_to': self.request_id.customer_id.id,
            })
            template_context['employee'] = self.request_id.customer_id
            if self.company_id.send_mail_satisfaction_destinator_bool_client:
                self.env['mail.template'].with_context(**template_context).browse(
                    template3.id).send_mail(self.id,
                                            force_send=True,
                                            raise_exception=True)
        else:
            message = True
        if self.destinator_id and self.destinator_id.email:
            self.dest = self.destinator_id.name
            template2.write({
                'partner_to': self.destinator_id.id,
            })
            template_context['employee'] = self.destinator_id
            if self.company_id.send_mail_satisfaction_destinator_bool_final_destinator:
                self.env['mail.template'].with_context(**template_context).browse(
                    template2.id).send_mail(self.id,
                                            force_send=True,
                                            raise_exception=True)
        else:
            message = True
        if message:
            title = _("Configuration des mails destinataires!")
            message = _(
                "Certains de vos clients n'ont pas d'adresse mails définis!")
            self.env['bus.bus'].sendone(
                (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
                {'type': 'simple_notification', 'title': title, 'message': message,
                 'sticky': False,
                 'warning': True})"""
    @api.constrains('return_method_id')
    def amount_greater_than_zero(self):
        for r in self:
            # print("================+> base")
            if r.portal == 1:
                if r.return_method_id and r.return_amount <= 0 and r.return_method_id.montant_obligatoire:
                    raise ValidationError(_(" Please enter the return amount"))
            if r.return_method_id and r.return_method_id.null_amount:
                r.return_amount = 0
            # print("================+> base", r.return_amount)
    # def livrer_trac(self, mobile=False):
    #     for r in self:
    #         if r.step != 'delivered':
    #             r.track = True
    #             r.current_position = r.order_id.current_position_id.destination_id
    #             tracking = self.env["sochepress.tracabilite.colis"].sudo()
    #             # self.delivery_date = fields.Date.today()
    #             data = {
    #                 'operation_type': 'delivered',
    #                 'source_id': r.order_id.current_position_id.destination_id.id,
    #                 'operator_id': r.env.uid,
    #                 'date': fields.Datetime.now(),
    #                 'colis_id': r.id,
    #             }
    #             r.operation_done = True
    #             tracking.create(data)
    #             r.step = 'delivered'
    #             print("=============> after delivered")
    #             if mobile:
    #                 title = _("Mouvement de colis")
    #                 message = _("Le colis %s a bien été livré" % (r.name))
    #                 action = {'type': 'simple_notification', 'title': title,
    #                           'message': message, 'sticky': True,
    #                           'warning': False}
    #                 self.env['bus.bus'].sendone(
    #                     (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
    #                     action)
    #                 return self.get_action(r.order_id.id)
    def archive_colis(self):
        groupby_barcode = {}
        # all = self.env['sochepress.customer.request.line'].search([('barcode', '!=', False)])
        all = self
        for r in all:
            if r.barcode in groupby_barcode:
                groupby_barcode[r.barcode].append(r)
            else:
                groupby_barcode[r.barcode] = [r]
        for barcode in groupby_barcode:
            colis = groupby_barcode[barcode]
            if len(colis) > 1:
                all_colis = self.env['sochepress.customer.request.line'].browse([c.id for c in colis])
                colis_mouvemented = [c.id for c in colis if c.step != 'new']
                colis_mouvemented = self.env['sochepress.customer.request.line'].browse(colis_mouvemented)
                to_archive = all_colis - colis_mouvemented
                if len(to_archive) == len(all_colis):
                    cols = [c for c in all_colis]
                    to_archive = cols[1:]
                for c in to_archive:
                    c.write({
                        'active': False
                    })
    def update_delivery_date(self):
        for r in self:
            # delivered = r.tracabilite_ids.filtered(lambda t: t.operation_type == 'delivered')
            delivered = self.env['sochepress.tracabilite.colis'].sudo().search(
                [('id', 'in', r.tracabilite_ids.ids), ('operation_type', '=', 'delivered')], order='date desc')
            #
            # for d in delivered:
            #     print("date", d.id, "666666", d.date)
            if delivered and delivered[0]:
                r.write({
                    'delivery_date': delivered[0].date.date(),
                })
    def livrer_trac(self, mobile=False):
        for r in self:
            if r.step != 'delivered':
                # r.track = True
                r.current_position = r.order_id.current_position_id.destination_id
                tracking = self.env["sochepress.tracabilite.colis"].sudo()
                r.delivery_date = fields.Date.today()
                data = {
                    'operation_type': 'delivered',
                    'source_id': r.order_id.current_position_id.destination_id.id,
                    'operator_id': r.env.uid,
                    'date': fields.Datetime.now(),
                    'colis_id': r.id,
                }
                r.operation_done = True
                tracking.create(data)
                r.step = 'delivered'
                r.step2 = 'Delivered'
                # if r.send_type == 'return_on_requests':
                #     delivery_state = 'returned_to_expeditor'
                # else:
                #     delivery_state = 'delivered'
                # r.nb_charged += 1
                # req = """UPDATE sochepress_customer_request_line SET
                #                 step='delivered',
                #                 track = 'true',
                #                 operation_done = 'true',
                #                 current_position=%s,
                #                 step2='Delivered',
                #                 delivery_state='%s',
                #                 delivery_date = CURRENT_DATE,
                #                 a_livrer = 'false'
                #                 WHERE id=%s""" % (
                #     r.order_id.current_position_id.destination_id.id, delivery_state, r.id)
                # self._cr.execute(req)
                # print("6666666 =========>", r.step)
                # print("6666666 =========>", r.document_ids)
                if r.send_type == 'send':
                    r.constrains_state()
                r.send_satisfaction()
                #r.get_sls_api_delivered_sql()
                r._compute_delivery_state()
                if mobile:
                    title = _("Mouvement de colis")
                    message = _("Le colis %s a bien été livré" % (r.name))
                    action = {'type': 'simple_notification', 'title': title,
                              'message': message, 'sticky': True,
                              'warning': False}
                    self.env['bus.bus'].sendone(
                        (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
                        action)
                    return self.get_action(r.order_id.id)
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
