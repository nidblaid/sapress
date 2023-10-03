# -*- coding: utf-8 -*-

import base64
from itertools import groupby
from odoo import models, fields, api, _
from odoo.exceptions import UserError
# from odoo.tools.misc import profile
from odoo.tools.profiler import profile
from pprint import pprint


class TransportOrder(models.Model):
    _name = 'soch.transport.order'
    _order = 'name desc'
    _description = "Transport Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # def _get_default_stage_id(self):
    #     return self.env['sochepress.trajet'].search([], order='id', limit=1)

    @api.model
    def clean_destination(self):
        c_destination = self.env['sochepress.trajet'].search([('order_id', '=', False)])
        c_destination.unlink()

    @api.model
    def _read_group_stage_ids(self, positions, domain, order):
        return positions.sudo().search([], order=order)

    name = fields.Char("Name", default="OT")
    color = fields.Integer('Color')
    # responsible = fields.Many2one('res.users', string="Responsible", readonly=1, default=lambda self: self.env.user)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    vehicule_id = fields.Many2one('fleet.vehicle', string="Vehicle", track_visibility="onchange")
    driver_id = fields.Many2one('res.partner', string="Driver", readonly=False,
                                ondelete='cascade', track_visibility="onchange")
    resquest_ids = fields.One2many('sochepress.customer.request', 'order_id', string="Demandes")
    colis = fields.One2many('sochepress.customer.request.line', 'order_id', string="OT Colis",
                            # domain=[('request_state', '=', 'accepted'), ('step', 'in', ['new', 'discharged'])]
                            )
    destination_id = fields.Many2one('sochepress.destination', string="Destination", track_visibility="onchange")
    source_id = fields.Many2one('sochepress.destination', string="Source", track_visibility="onchange")
    transport_type = fields.Selection([('extern', "Extern"), ('intern', "Intern")],
                                      string="Transport type",
                                      default='intern')
    primaire = fields.Boolean(string="Primaire")
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    traject_ids = fields.One2many('sochepress.trajet', 'order_id', string="Trajects")
    matricule = fields.Char("Matricule")
    weight = fields.Float(string="Vehicule Weight")
    volume = fields.Float(string="Vehicule Volume")
    nbre_colis = fields.Integer("Nb Colis", compute='compute_filling_rate', store=True)
    nbre_colis_print = fields.Integer("Nb Colis to print")
    nbre_colis_charged = fields.Integer("Nb Colis Chargé(s)", compute='compute_nbre_colis_charged')
    current_position_id = fields.Many2one('sochepress.trajet',
                                          string="Current position", index=True,
                                          copy=False, domain=[
            ('order_id', '=', lambda self: self.id)],
                                          ondelete='cascade')
    position = fields.Many2one(related="current_position_id.destination_id",
                               string='Position')

    filling_rate = fields.Float(string="Filling rate", compute="compute_filling_rate",
                                store=True)
    filling_weight = fields.Float(string="Filling weight",
                                  compute="compute_filling_weight")
    hide_forward = fields.Boolean(default=False, copy=False, store=True)
    finished = fields.Boolean(default=False, copy=False, track_visibility='onchange')
    driver_phone = fields.Char("Driver phone")
    # barcode = fields.Char("Barcode")
    first_step = fields.Boolean(default=True, copy=False)
    reported_colis = fields.Boolean(default=True, copy=False)
    hide_backward = fields.Boolean(default=True, copy=False)
    eap_is_sended = fields.Boolean(default=False)
    show_finalize = fields.Boolean()
    traject_name = fields.Char("Trajects name", compute='compute_trajects_name', store=True)
    colis_name = fields.Char("Colis number", compute='compute_colis_name', store=True)
    position_id = fields.Many2one('sochepress.trajet', string='Trajet position')
    customer_id = fields.Many2one('res.partner', string="Customer")
    customer_id_be = fields.Many2one('res.partner', string="Customer BE")
    colis_for_email_ids = fields.Many2many('sochepress.customer.request.line', string="Colis for emails")
    type_ot = fields.Selection([('collecting', "Collecting"), ('primary_transport',
                                                               "Primary transport"),
                                ('delivery', "Delivery")],
                               string="Transport order type",
                               default='collecting', track_visibility="onchange")
    ot_state = fields.Selection(
        [('not_started', "Not started"), ('in_progress', "In progress"), ('finalized', "Finalized")],
        string="OT state", track_visibility="onchange", default='not_started')

    mouvement_track = fields.Char("Mouvement tracking", track_visibility="onchange")
    locations_ids = fields.Many2many('sochepress.destination')
    bordereau_ids = fields.Many2many('ir.attachment', string="Bordereau")

    def set_state(self, colis):
        for res in self:
            returns = []
            for c in colis:
                returns.append(c.return_amount)
            all_colis_draft = colis.filtered(lambda x: x.step in ['new', 'discharged'])
            cond1 = any(x != 0 for x in returns)
            condx = all(x == 0 for x in returns)
            cond2 = len(all_colis_draft) == len(colis)
            if res.type_ot == 'delivery':
                if condx:
                    return 'without_cash'
                elif cond1:
                    if not self.state or self.state == 'without_cash':
                        return 'draft'
                    else:
                        return self.state

    @api.depends('colis')
    def update_states(self):
        for r in self:
            r.state = r.set_state(r.colis)
            finished = r.finished
            colis = r.colis
            if finished or colis:
                states = []
                state_in_progress = ['charged', 'delivered', 'in_progress', 'non_delivered', 'not_pickup', 'refused',
                                     'reported', 'retracted']
                if not finished:
                    for c in colis:
                        states.append(c.step)
                    check = any(item in states for item in state_in_progress)
                    if check:
                        ot_state = 'in_progress'
                        # r.state = 'progress'
                    else:
                        ot_state = 'not_started'
                        # r.state = 'draft'
                else:
                    ot_state = 'finalized'
                r.ot_state = ot_state

    def set_ot_state(self):
        states = []
        state_in_progress = ['charged', 'delivered', 'in_progress', 'non_delivered', 'not_pickup', 'refused',
                             'reported', 'retracted']
        if not self.finished:
            for c in self.colis:
                states.append(c.step)
            check = any(item in states for item in state_in_progress)
            if check:
                ot_state = 'in_progress'
                # r.state = 'progress'
            else:
                ot_state = 'not_started'
                # r.state = 'draft'
        else:
            ot_state = 'finalized'
        return ot_state

    def set_ot_state_affect(self):
        states = []
        state_in_progress = ['charged', 'delivered', 'in_progress', 'non_delivered', 'not_pickup', 'refused',
                             'reported', 'retracted']
        for r in self:
            if not r.finished:
                for c in r.colis:
                    states.append(c.step)
                check = any(item in states for item in state_in_progress)
                if check:
                    ot_state = 'in_progress'
                    # r.state = 'progress'
                else:
                    ot_state = 'not_started'
                    # r.state = 'draft'
            else:
                ot_state = 'finalized'
            r.ot_state = ot_state

    def _compute_charging_ot_colis(self):
        for r in self:
            total = 0
            for c in r.colis:
                if c._compute_charging_colis() > 0:
                    total += c._compute_charging_colis()
            return total

    @api.onchange('vehicule_id')
    def _get_driver(self):
        for r in self:
            r.driver_id = r.vehicule_id.driver_id.id
            return False

    def print_all(self):
        for r in self:
            max_bl = r.company_id.max_bl or 200
            declarations = []
            for c in r.colis:
                decs = self.env['sochepress.declaration'].search([('colis_ids', 'in', [c.id])])
                if len(decs) >= 1:
                    decs = self.env['sochepress.declaration'].search([('colis_ids', 'in', [c.id])])[-1]
                    declarations.append(decs.id)
            declarations = self.env['sochepress.declaration'].browse(list(set(declarations)))

            for d in declarations:
                d.ot_id = r.id
            if declarations and len(declarations) <= max_bl:
                return self.env.ref("sochepress_base.report_customer_request").report_action(
                    [dec.id for dec in declarations], config=False)
            elif declarations and len(declarations) > max_bl:
                if r.bordereau_ids:
                    r.bordereau_ids.unlink()
                chunks = [declarations[x:x + max_bl] for x in range(0, len(declarations), max_bl)]
                i = 0
                for x in chunks:
                    pdf = self.env.ref('sochepress_base.report_customer_request').render_qweb_pdf(x)
                    b64_pdf = base64.b64encode(pdf[0])
                    # save pdf as attachment
                    # req = declarations[0]
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
                    i += 1
                    # logmessage = 'Please find your BL here'
                    # self.message_post(body=logmessage, attachments=[(name, pdf)])

                    # tree_view_id = self.env.ref('sochepress_base.view_sochepress_declaration_tree').ids
                    # return {
                    #     'name': _('Delivery slips'),
                    #     'view_mode': 'tree',
                    #     'views': [[tree_view_id, 'tree']],
                    #     'res_model': 'sochepress.declaration',
                    #     'type': 'ir.actions.act_window',
                    #     'domain': [('id', 'in', declarations.ids)]
                    # }

                title = _("Impression of delivery slips")
                action = {'type': 'simple_notification', 'title': title,
                          'message': _(
                              "The number of delivery slips is too huge to be printed once, you can download them in the attachement of the OT"),
                          'sticky': False,
                          'warning': False}
                self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), action)
            else:
                raise UserError(_("None of your packages have been planned"))

    def print_all_return(self):
        for r in self:
            max_bl = r.company_id.max_bl or 200
            declarations = []
            colis_by_customer = {}

            # for c in r.colis:
            #     decs = self.env['sochepress.declaration'].search([('colis_ids', 'in', [c.id])])
            #     if len(decs) >= 1:
            #         decs = self.env['sochepress.declaration'].search([('colis_ids', 'in', [c.id])])[-1]
            #         declarations.append(decs.id)
            # declarations = self.env['sochepress.declaration'].browse(list(set(declarations)))

            for c in r.colis:
                if c.destinator_id in colis_by_customer:
                    colis_by_customer[c.destinator_id].append(c)
                else:
                    colis_by_customer[c.destinator_id] = [c]

            for destinator in colis_by_customer:
                cols = colis_by_customer[destinator]
                value_declaration = {'request_id': cols[0].request_id.id,
                                     'customer_id': cols[0].request_id.customer_id.id,
                                     'expeditor_id': cols[0].expeditor_id.id,
                                     'destinator_id': destinator.id,
                                     'colis_ids': [(6, 0, [col.id for col in cols])]}
                decl = self.env['sochepress.declaration'].create(value_declaration)
                declarations.append(decl)

            for d in declarations:
                d.ot_id = r.id
            if declarations and len(declarations) <= max_bl:
                return self.env.ref("sochepress_base.report_customer_request_return").report_action(
                    [dec.id for dec in declarations], config=False)
            elif declarations and len(declarations) > max_bl:
                if r.bordereau_ids:
                    r.bordereau_ids.unlink()
                chunks = [declarations[x:x + max_bl] for x in range(0, len(declarations), max_bl)]
                i = 0
                for x in chunks:
                    pdf = self.env.ref('sochepress_base.report_customer_request_return').render_qweb_pdf(x)
                    b64_pdf = base64.b64encode(pdf[0])
                    # save pdf as attachment
                    # req = declarations[0]
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
                    i += 1
                    # logmessage = 'Please find your BL here'
                    # self.message_post(body=logmessage, attachments=[(name, pdf)])

                    # tree_view_id = self.env.ref('sochepress_base.view_sochepress_declaration_tree').ids
                    # return {
                    #     'name': _('Delivery slips'),
                    #     'view_mode': 'tree',
                    #     'views': [[tree_view_id, 'tree']],
                    #     'res_model': 'sochepress.declaration',
                    #     'type': 'ir.actions.act_window',
                    #     'domain': [('id', 'in', declarations.ids)]
                    # }

                title = _("Impression of delivery slips")
                action = {'type': 'simple_notification', 'title': title,
                          'message': _(
                              "The number of delivery slips is too huge to be printed once, you can download them in the attachement of the OT"),
                          'sticky': False,
                          'warning': False}
                self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), action)
            else:
                raise UserError(_("None of your packages have been planned"))

    @api.depends('traject_ids', 'traject_ids.sequence')
    def compute_trajects_name(self):
        for r in self:
            if r.traject_ids:
                ordered_trajects = sorted(
                    [(traject.name, traject.sequence) for traject in r.traject_ids],
                    key=lambda traj: traj[1])
                r.traject_name = " > ".join(
                    [traject[0] for traject in ordered_trajects])
            else:
                r.traject_name = False

    @api.depends('colis')
    def compute_colis_name(self):
        for r in self:
            r.colis_name = ', '.join([c.name for c in r.colis])

    @api.depends('colis.step')
    def compute_nbre_colis_charged(self):
        for r in self:
            r.nbre_colis_charged = len(r.colis.filtered(lambda c: c.step == 'charged').ids)

    @api.depends('colis', 'vehicule_id', 'volume', 'vehicule_id.vehicule_volume')
    def compute_filling_rate(self):
        for r in self:
            r.nbre_colis = len(r.colis)
            volume = 0
            for c in r.colis:
                volume += c.type_colis_id.volume
            if r.transport_type == 'intern':
                vol = r.vehicule_id.vehicule_volume
                r.filling_rate = r.vehicule_id and r.vehicule_id.vehicule_volume and 100 * volume / vol or 0
            elif r.transport_type == 'extern':
                vol = r.volume
                r.filling_rate = vol and 100 * volume / vol or 0

        # for r in self:
        #     print(len(r.colis.filtered(lambda col: col.step == 'discharged')))
        #     print('-------------------------------------------')
        #     print(len(r.colis))
        #     print('-------------------------------------------')
        #     print(len(r.colis.filtered(lambda col: col.step == 'charged')))
        #     print('-------------------------------------------')
        #     cond1 = len(r.colis.filtered(lambda col: col.step == 'discharged')) == len(r.colis)
        #     cond2 = len(r.colis.filtered(lambda col: col.step == 'charged')) == 0
        #     r.hide_forward = cond1 or cond2
        #     print(r.hide_forward)

    @api.depends('colis', 'vehicule_id', 'weight', 'vehicule_id.vehicule_weight')
    def compute_filling_weight(self):
        for r in self:
            weight = 0
            wei = 0
            for c in r.colis:
                weight += c.weight
            if r.transport_type == 'intern':
                wei = r.vehicule_id.vehicule_weight
                r.filling_weight = r.vehicule_id and r.vehicule_id.vehicule_weight and 100 * weight / wei or 0
            else:
                wei = r.weight
                r.filling_weight = wei and 100 * weight / wei or 0

    @api.constrains('source_id', 'destination_id')
    def compute_traject(self):
        res = {}
        for r in self:
            s_traject = False
            d_traject = False
            destinations = []
            # print("========+>", [t.name for t in r.traject_ids])
            for t in r.traject_ids:
                if t.sequence == 1 or t.sequence == 10:
                    t.order_id = False
            set_true = False
            set_dest = False
            if self.current_position_id.destination_id == r.source_id:
                set_true = True
            if self.current_position_id.destination_id == r.destination_id:
                set_dest = True

            if r.source_id:
                # r.current_position_id = r.source_id.id
                destinations.append(r.source_id.id)

                if r.source_id.id not in [traject.destination_id.id for traject in
                                          r.traject_ids]:
                    s_traject = self.env['sochepress.trajet'].create({
                        'sequence': 1,
                        'destination_id': r.source_id.id,
                    })
                else:
                    s_traject = r.traject_ids.filtered(
                        lambda t: t.destination_id.id == r.source_id.id)
                    s_traject.write({'sequence': 1})
                if set_true:
                    r.current_position_id = s_traject

            if r.destination_id:
                destinations.append(r.destination_id.id)
                if r.destination_id.id not in [traject.destination_id.id for traject in
                                               r.traject_ids]:
                    d_traject = self.env['sochepress.trajet'].create({
                        'sequence': 10,
                        'destination_id': r.destination_id.id,
                    })

                else:
                    d_traject = r.traject_ids.filtered(
                        lambda t: t.destination_id.id == r.destination_id.id)
                    d_traject.write({'sequence': 10})

                if set_dest:
                    r.current_position_id = d_traject

            trajects = list(set(r.traject_ids.ids + [d_traject.id, s_traject.id]))
            r.traject_ids = [(6, 0, trajects)]
            r.current_position_id = r.traject_ids.filtered(
                lambda t: t.sequence == r.current_position_id.sequence)

            res['domain'] = {
                'traject_ids': [('destination_id', 'not in', destinations)]}
        return res

    @api.constrains('traject_ids')
    def force_sequence(self):
        for r in self:
            seq = 2
            for traject in r.traject_ids.filtered(
                lambda t: (
                    t.destination_id.id not in [r.source_id.id, r.destination_id.id])):
                traject.write({'sequence': seq})
                seq = seq + 1

            if not r.current_position_id:
                ordered_trajects = sorted([(traject, traject.sequence) for traject in r.traject_ids],
                                          key=lambda traj: traj[1])
                r.current_position_id = ordered_trajects[0][0]
            # l = []
            # for x in r.traject_ids:
            #     if x.destination_id:
            #         l.append(x.destination_id.id)
            # r.locations_ids = [(6, 0, l)]

    def next_position(self, next_position_checked=False):
        # print('Hello from next position')

        context = self._context
        # print('context ===>',context)
        source = context.get('source', False)
        if not self.colis:
            raise UserError(_("You can't move forward in a colis where there is any colis"))
        all_colis = self.colis
        charged_colis = self.colis.filtered(lambda c: c.step == 'charged')
        if len(charged_colis) != len(self.colis) and not next_position_checked:
            # self.next_position_checked = True
            action_wiz = self.env.ref(
                'sochepress_base.transport_verification_view_action').read()[0]
            action_wiz['context'] = {
                'default_ot_id': self.id,
            }
            if source == 'interface':
                return action_wiz
            else:
                return {
                    'action': action_wiz
                }
        new_colis = self.colis.filtered(lambda c: c.step == 'new')
        else_colis = self.colis - new_colis
        self.reported_colis = (len(self.colis.filtered(lambda c: c.step in ['refused', 'reported'])) > 0)
        if self.type_ot == 'delivery':
            returns = []
            for c in self.colis:
                returns.append(c.return_amount)
            condx = all(x == 0 for x in returns)
            if self.state == 'draft' or (not condx):
                self.confirm()
            else:
                self.close_session()

        if not new_colis:
            all_t = sorted([traject for traject in self.traject_ids], key=lambda x: x.sequence)
            index = all_t.index(self.sudo().current_position_id) + 1
            if index < len(all_t):
                self.current_position_id = all_t[index]

            if index == len(all_t) - 1:
                self.hide_forward = True
                self.first_step = False

            concerned_colis = self.colis.filtered(lambda col: col.nb_charged == 1 and not col.eap_is_sended)
            # self.confirm()
            # return
            template = self.env.ref('sochepress_base.email_after_pickup_template')
            self.mouvement_track = _("Forwarding to %s") % self.sudo().current_position_id.name
            x = groupby(concerned_colis, lambda x: x.customer_id)
            for c in self.colis:
                c.charged = 0
                c.discharged = 0
                c.operation_done = False
                c.compute_a_livrer()
                if c.step in ['reported', 'refused']:
                    self.hide_backward = False

            self.show_finalize = ((((not self.first_step) and self.hide_forward) or self.reported_colis) and (
                not self.finished)) or (self.show_finalize_once > 0)
            for key, colis in x:
                colis = list(colis)
                self.customer_id = key
                self.colis_for_email_ids = [(6, 0, [c.id for c in colis])]
                if self.colis_for_email_ids:
                    template.write({
                        'partner_to': key.id
                    })
                    if self.company_id.email_after_pickup_template_bool_client and self.type_ot == 'collecting':
                        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True,
                                                                                raise_exception=True)
                        self.eap_is_sended = True
                        for c in self.colis_for_email_ids:
                            c.eap_is_sended = True
            self.hide_backward = False
            if source != 'interface':
                return {
                    'action': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
        else:
            # if len(all_colis) != len(charged_colis):
            #     # print('IIIIIIIIIIF')
            #     # print('len(all_colis) ==>',len(all_colis))
            #     # print('len(charged_colis) ==>',len(charged_colis))
            #     if source == 'interface':
            #         return action_wiz
            #     else:
            #         return {
            #             'action': action_wiz
            #         }
            # else:
            #     # print('Else')
            #     self.next_position()
            for c in else_colis:
                c.operation_done = False
            message = _(
                "%s colis n'%s pas été chargé%s chez %s, si vous avancez un commentaire de non ramassage sera automatiquement ajouté à ces colis, vous pouvez également mettre un nouveau commentaire" %
                (len(new_colis), "ont" if len(new_colis) > 1 else "a", 's' if len(new_colis) > 1 else "",
                 new_colis[0].customer_id.name))
            view_id = self.env.ref('sochepress_base.ordre_transport_trajet_wizard_view_form').id
            vals = {'order_id': self.id,
                    'colis': [(6, 0, new_colis.ids)],
                    'commentaire_id': self.env.ref('sochepress_base.motif_no_pickup').id,
                    'source': source,
                    'message': message}

            ot_id = self.env['moving.wizard'].create(vals)
            action = {
                'name': _('Move to next position'),
                'res_model': 'moving.wizard',
                'view_mode': 'form',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'type': 'ir.actions.act_window',
                'res_id': ot_id.id,
                'target': 'new'
            }
            if source == 'interface':
                return action
            return {
                'action': action
            }

    show_finalize_once = fields.Integer(compute='comp_show_finalize', store=1)

    @api.depends('show_finalize')
    def comp_show_finalize(self):
        for r in self:
            if r.show_finalize:
                r.show_finalize_once += 1

    def previous_position(self):
        context = self._context
        source = context.get('source', False)
        # print("=====>", source)
        all_t = sorted([traject for traject in self.traject_ids], key=lambda x: x.sequence)
        self.reported_colis = (len(self.colis.filtered(lambda c: c.step in ['refused', 'reported'])) > 0)
        index = all_t.index(self.current_position_id) - 1
        if index < len(all_t):
            self.current_position_id = all_t[index]
        self.position_id = self.current_position_id.id
        if self.position_id.name == self.source_id.name:
            self.hide_backward = True
        self.hide_forward = False
        if index == len(all_t) - 1:
            self.hide_forward = True
            self.first_step = False
        for c in self.colis:
            c.compute_a_livrer()
            c.operation_done = False
        self.show_finalize = ((((not self.first_step) and self.hide_forward) or self.reported_colis) and (
            not self.finished)) or (self.show_finalize_once > 0)
        self.mouvement_track = _("Backing to %s") % self.current_position_id.name
        if source != 'interface':
            return {
                'action': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }

    def close(self):
        for r in self:
            if r.type_ot == "delivery":
                for c in r.colis:
                    if c.step not in ["discharged", "delivered", "not_pickup"]:
                        raise UserError(_(
                            'Tous les colis doivent être livrer ou décharger ou non ramassé pour finaliser cet OT.'))
            else:
                for c in r.colis:
                    if c.step not in ["discharged", "not_pickup"]:
                        raise UserError(_(
                            'Tous les colis doivent être décharger ou non ramassé pour finaliser cet OT.'))
            # for c in self.colis:
            #     if c.step in ["discharged"] and c.current_position == c.order_id.current_position_id.destination_id:
            #         data = {
            #             'operation_type': 'discharge',
            #             'source_id': current.destination_id.id,
            #             # 'destination_id': self.current_position_id.destination_id.id,
            #             'operator_id': self.env.uid,
            #             'date': fields.Datetime.now(),
            #             'colis_id': c.id,
            #         }
            #         pprint(data)
            #         tracking.create(data)
            r.ot_state = 'finalized'
            r.finished = True
            r.show_finalize = False

        # if index == len(all_t) - 1:
        #     self.hide_forward = True

        # if self.current_position_id.sequence != 10:
        #     self.current_position_id = self.traject_ids.filtered(
        #         lambda t: t.sequence == self.current_position_id.sequence + 1).id

        # print(self.current_position_id.sequence)

    def see_colis(self):
        action = self.env.ref('sochepress_base.customer_request_line_action_2').read()[
            0]
        action['domain'] = [('id', 'in', self.colis.ids)]
        return action

    @api.model
    def create(self, vals):
        # res = super(TransportOrder, self).create(vals)
        # print("========> after create")
        if vals['type_ot'] == 'collecting':
            seq1 = self.env['ir.sequence'].next_by_code(
                'transport_order_collect')
            vals['name'] = seq1
        elif vals['type_ot'] == 'primary_transport':
            seq2 = self.env['ir.sequence'].next_by_code(
                'transport_order_primary')
            vals['name'] = seq2
        elif vals['type_ot'] == 'delivery':
            seq3 = self.env['ir.sequence'].next_by_code(
                'transport_order_delivery')
            vals['name'] = seq3
        else:
            seq = self.env['ir.sequence'].next_by_code('soch.transport.order')
            vals['name'] = seq
        # print("=====> Writing")
        res = super(TransportOrder, self).create(vals)
        return res

    def action_view_tracking(self):
        self.ensure_one()
        action = self.env.ref('sochepress_base.tracking_colis_action').read()[0]
        action['domain'] = [('colis_id.order_id', '=', self.id)]
        return action

    def get_colis_be(self):
        concerned_colis = self.colis.filtered(
            lambda col: col.step == 'charged' and col.customer_id == self.customer_id_be)
        all_colis = len(self.colis.filtered(lambda col: col.customer_id == self.customer_id_be))
        colis = {}
        req = False
        if concerned_colis:
            req = concerned_colis[0].request_id
        for c in concerned_colis:
            if c.destination_id in colis:
                colis[c.destination_id].append(c)
            else:
                colis[c.destination_id] = [c]
        return colis, all_colis, req

    def set_name(self):
        for r in self:
            old_name = r.name
            new_name = r.name
            if len(old_name) == 7:
                if r.type_ot == 'collecting':
                    new_name = old_name[:2] + 'R' + old_name[3:]
                if r.type_ot == 'primary_transport':
                    new_name = old_name[:2] + 'T' + old_name[3:]
                if r.type_ot == 'delivery':
                    new_name = old_name[:2] + 'L' + old_name[3:]
            if len(old_name) == 6:
                if r.type_ot == 'collecting':
                    new_name = old_name[:1] + 'TR' + old_name[2:]
                if r.type_ot == 'primary_transport':
                    new_name = old_name[:1] + 'TT' + old_name[2:]
                if r.type_ot == 'delivery':
                    new_name = old_name[:1] + 'TL' + old_name[2:]
            r.name = new_name


class MovingWizard(models.TransientModel):
    _name = "moving.wizard"
    _description = 'OT Traject Wizard'

    order_id = fields.Many2one('soch.transport.order')
    colis = fields.Many2many('sochepress.customer.request.line', string="Colis")
    commentaire_id = fields.Many2one('sochepress.colis.delivery', string="Commentaire")
    message = fields.Text("Message")
    source = fields.Char("Source of modification")

    def valider(self):
        order = self.order_id
        for col in self.colis:
            col.delivery_delay_reason_id = self.commentaire_id
            col.not_pickup()
            col.operation_done = False
        all_t = sorted([traject for traject in order.traject_ids], key=lambda x: x.sequence)
        index = all_t.index(order.current_position_id) + 1
        if index < len(all_t):
            order.current_position_id = all_t[index]
        if index == len(all_t) - 1:
            order.hide_forward = True
            order.first_step = False

        concerned_colis = order.colis.filtered(lambda col: col.nb_charged == 1 and not col.eap_is_sended)
        template = self.env.ref('sochepress_base.email_after_pickup_template')
        x = groupby(concerned_colis, lambda x: x.customer_id)
        order.hide_backward = False
        order.show_finalize = ((((not order.first_step) and order.hide_forward) or order.reported_colis) and (
            not order.finished)) or (order.show_finalize_once > 0)
        order.mouvement_track = _("Forwarding to %s") % order.current_position_id.name
        if order.state != 'without_cash':
            if order.state == 'draft':
                order.confirm()
            else:
                order.close_session()
        for key, colis in x:
            colis = list(colis)
            order.customer_id = key
            order.colis_for_email_ids = [(6, 0, [c.id for c in colis])]
            if order.colis_for_email_ids:
                template.write({
                    'partner_to': key.id
                })
                if order.company_id.email_after_pickup_template_bool_client and order.type_ot == 'collecting':
                    self.env['mail.template'].browse(template.id).send_mail(order.id, force_send=True,
                                                                            raise_exception=True)
                    for c in order.colis_for_email_ids:
                        c.eap_is_sended = True

        if self.source != 'interface':
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
