# -*- coding: utf-8 -*-
import re
from Levenshtein import distance
from difflib import SequenceMatcher
from fastDamerauLevenshtein import damerauLevenshtein
from odoo import models, fields, _
from odoo.exceptions import UserError
from operator import itemgetter


class SochepressOTPCodeWizard(models.TransientModel):
    _name = 'sochepress.otp.code.wizard'
    _description = "Sochepress OTP Code Wizard"

    colis_id = fields.Many2one('sochepress.customer.request.line', string="Colis")
    otp_code = fields.Char('OTP Code')
    mobile = fields.Boolean('Mobile ?')

    def resend_otp(self):
        return self.colis_id.resend_otp()

    def verify(self):
        for r in self:
            if not r.otp_code:
                raise UserError("Please enter the OTP code")
            if r.colis_id.otp_code == r.otp_code:
                colis = r.colis_id
                if colis.step != 'delivered':
                    view_id = self.env.ref(
                        'sochepress_base.sochepress_justif_wizard_form').id
                    wiz_id = self.env['sochepress.justif.wizard'].create(
                        {'colis_id': colis.id, 'mobile': self.mobile})
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
                    # if self.mobile:
                    #     return {
                    #         'action': action
                    #     }
                    # else:
                    return action
            else:
                raise UserError(_('Le code OTP renseigné est incorrect.'))


class SochepressVerifWizard(models.TransientModel):
    _name = 'sochepress.verif.wizard'
    _description = "Sochepress Verification Wizard"

    source_colis_ids = fields.Many2many('sochepress.customer.request.line', 'partners_group_rel', 'andpc_id',
                                        string="Colis sources")
    destination_colis_ids = fields.Many2many('sochepress.customer.request.line', string="Colis destinations")
    request_id = fields.Many2one('sochepress.customer.request', string="Commande")
    destination_id = fields.Many2one('sochepress.destination', string='Localisation')
    type = fields.Selection([('source', "Verification source"), ('destination', "Verification destination")],
                            string="Type", )
    finished = fields.Boolean()
    custom = fields.Char()

    # company_id = fields.Many2one('res.company')

    def remove_accent(self, chaine):
        accent = ['é', 'è', 'ê', 'à', 'ù', 'û', 'ç', 'ô', 'î', 'ï', 'â']
        sans_accent = ['e', 'e', 'e', 'a', 'u', 'u', 'c', 'o', 'i', 'i', 'a']

        for i in range(0, len(accent)):
            chaine = chaine.replace(accent[i], sans_accent[i])

        return chaine

    #
    # def test(self):
    #     print(self.existing_location(self.custom))

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
        # #             #
        # #
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

    # def resend_otp(self):
    #     return self.colis_id.resend_otp()

    def confirm(self):
        self.invalidate_cache()
        values = {}
        if self.type == 'source':
            # print("======== checking source ============")
            for col in self.source_colis_ids:
                col.source_id = self.destination_id
                col.expeditor_id.destination_id = self.destination_id
                col.corrected_source = True
            colis_sources = self.request_id.request_line_ids.filtered(lambda l: not l.source_id)
            if colis_sources:
                # print("############ SOURCES ##################")
                colis_source_dict = {}
                for x in colis_sources:
                    if x.custom_source not in colis_source_dict:
                        colis_source_dict[x.custom_source] = [x.id]
                    else:
                        colis_source_dict[x.custom_source].append(x.id)
                init_colis = []
                destination_id = False
                for key in colis_source_dict:
                    destination_id = self.existing_location(key)
                    init_colis = colis_source_dict[key]
                    break

                values.update({
                    'request_id': self.request_id,
                    'type': 'source',
                    'destination_id': destination_id.id if destination_id else False,
                    'source_colis_ids': [(6, 0, init_colis)]
                })
            else:
                self.type = 'destination'
            # self.colis_ids = False

        if self.type == 'destination':
            # print("############ DESTINATIONS ##################")
            for col in self.destination_colis_ids:
                col.destination_id = self.destination_id
                col.destinator_id.destination_id = self.destination_id
                col.corrected_destination = True
            colis_destinations = self.request_id.request_line_ids.filtered(lambda l: not l.destination_id)
            if colis_destinations:
                colis_source_dict = {}
                for x in colis_destinations:
                    if x.custom_destination not in colis_source_dict:
                        colis_source_dict[x.custom_destination] = [x.id]
                    else:
                        colis_source_dict[x.custom_destination].append(x.id)
                init_colis = []
                destination_id = False
                for key in colis_source_dict:
                    # print('====>', key)
                    destination_id = self.existing_location(key)
                    init_colis = colis_source_dict[key]
                    break

                values.update({
                    'request_id': self.request_id,
                    'type': 'destination',
                    'destination_id': destination_id.id if destination_id else False,
                    'destination_colis_ids': [(6, 0, init_colis)]
                })
            else:
                self.finished = True

        if values:
            self.write(values)

        if not self.finished:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            self.request_id.state = 'verified'
            self.request_id.set_source_ids()
            self.request_id.generate_expedition()
            # self.request_id.set_destination_ids()
            cor_sources = self.request_id.request_line_ids.filtered(lambda l: l.corrected_source)
            cor_destinations = self.request_id.request_line_ids.filtered(lambda l: l.corrected_destination)
            # self.request_id.request_line_ids.compute_price()
            if cor_destinations or cor_sources:
                template_after_verification = self.env.ref('sochepress_base.email_after_verification')
                template_after_verification.write({
                    'partner_to': self.request_id.customer_id.id
                })
                x = self.request_id.compute_corrected_colis()
                if self.request_id.company_id.otp_code_mail_emplate1_bool_client and x:
                    self.env['mail.template'].browse(template_after_verification.id).send_mail(self.request_id.id,
                                                                                               force_send=True,
                                                                                               raise_exception=True)
