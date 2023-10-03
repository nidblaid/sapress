# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo import api, fields, models

class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'
    _description = 'Portal User Config'

    def action_apply(self):
        super().action_apply()
        group_portal = self.env.ref('sochepress_portal_extended.all_portal_rights_group')
        for wizard_user in self.sudo().with_context(active_test=False):
            user = wizard_user.partner_id.user_ids[0] if wizard_user.partner_id.user_ids else None
            if user:
                user.write({'groups_id': [(4, group_portal.id)], 'active': True})
    