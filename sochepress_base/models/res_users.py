# -*- coding: utf-8 -*-


import logging

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    agence_id = fields.Many2one('sochepress.destination', string="Agence")
    agence_ids = fields.Many2many('sochepress.destination', string="Agences secondaires")

    @api.depends('agence_id', 'agence_ids')
    def reset_user(self):
        for r in self:
            if r.has_group('base.group_user'):
                group = self.env.ref('sochepress_base.customer_request_user')
                group.users -= r
                group.users += r

    # def _auth_timeout_check(self):
    #     print("============================")
    #     res = super(ResUsers, self)._auth_timeout_check()
    #     session = requests.Session()
    #     session.cookies.clear()
    #     print("============================")


class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=', vals.get('res_model')),
                                                      ('res_id', '=', vals.get('res_id')),
                                                      ('partner_id', '=', vals.get('partner_id'))])
            if len(dups):
                for p in dups:
                    p.unlink()
        return super(Followers, self).create(vals)
