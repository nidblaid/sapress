# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    check_mail = fields.Boolean(string="Check mail")
    max_barcodes = fields.Integer(string="Colis Barcode Limit", default=450)
    max_be = fields.Integer(string="Colis BE Limit", default=200)
    max_bl = fields.Integer(string="Colis BL Limit", default=200)
    send_mail_request_creation_bool_client = fields.Boolean(
        string="Send mail after creation of the request for the client", default=True)
    send_mail_request_acceptation_bool_client = fields.Boolean(
        string="Send mail after acceptation of the request for the client",
        default=True)
    email_after_pickup_template_bool_client = fields.Boolean(string="Send mail after pickup for the client",
                                                             default=True)
    send_mail_satisfaction_destinator_bool_client = fields.Boolean(
        string="Send mail after delivery for the client", default=True)
    otp_code_mail_emplate1_bool_client = fields.Boolean(string="Send mail of OTP code for the client", default=True)
    send_mail_request_creation_bool_final_destinator = fields.Boolean(
        string="Send mail after creation of the request for the final destinator", default=True)
    send_mail_request_acceptation_bool_final_destinator = fields.Boolean(
        string="Send mail after acceptation of the request for the final destinator",
        default=True)
    email_after_pickup_template_bool_final_destinator = fields.Boolean(
        string="Send mail after pickup for the final destinator",
        default=True)
    send_mail_satisfaction_destinator_bool_final_destinator = fields.Boolean(
        string="Send mail after delivery for the final destinator", default=True)
    otp_code_mail_emplate1_bool_final_destinator = fields.Boolean(
        string="Send mail of OTP code for the final destinator", default=True)
    max_length = fields.Float(string="Maximum length (cm)", default=150)
    volumetric_weight = fields.Float(string="Volumetric lenght coefficient (kg/m³)", default=160)
    max_dimension = fields.Float(string="Maximum dimension (cm)", default=160)
    max_pourtour = fields.Float(string="Maximum pourtour (cm)", default=300)

    recherche_initial_indexed = fields.Boolean(string="Init  Search indexed", default=False)
    search_with_all_conditions = fields.Boolean(string="Search with all conditions", default=False)
    search_by_sql_simple = fields.Boolean(string="Search by simple SQL", default=False)
    search_by_sql_all_condition = fields.Boolean(string="Search by SQL with all conditions", default=False)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    check_mail = fields.Boolean(related="company_id.check_mail", string="Check mail",
                                readonly=False)
    max_barcodes = fields.Integer(related="company_id.max_barcodes", string="Colis Barcode Limit", readonly=False)
    max_be = fields.Integer(related="company_id.max_be", string="Colis BE Limit", readonly=False)
    max_bl = fields.Integer(related="company_id.max_bl", string="Colis BL Limit", readonly=False)
    send_mail_request_creation_bool_client = fields.Boolean(related="company_id.send_mail_request_creation_bool_client",
                                                            string="Send mail after creation of the request for the client",
                                                            readonly=False)
    send_mail_request_acceptation_bool_client = fields.Boolean(
        related="company_id.send_mail_request_acceptation_bool_client",
        string="Send mail after acceptation of the request for the client",
        readonly=False)
    email_after_pickup_template_bool_client = fields.Boolean(
        related="company_id.email_after_pickup_template_bool_client",
        string="Send mail after pickup for the client", readonly=False)
    send_mail_satisfaction_destinator_bool_client = fields.Boolean(
        related="company_id.send_mail_satisfaction_destinator_bool_client",
        string="Send mail after delivery for the client", readonly=False)
    otp_code_mail_emplate1_bool_client = fields.Boolean(related="company_id.otp_code_mail_emplate1_bool_client",
                                                        string="Send mail of OTP code for the client", readonly=False)
    send_mail_request_creation_bool_final_destinator = fields.Boolean(
        related="company_id.send_mail_request_creation_bool_final_destinator",
        string="Send mail after creation of the request for the final destinator", readonly=False)
    send_mail_request_acceptation_bool_final_destinator = fields.Boolean(
        related="company_id.send_mail_request_acceptation_bool_final_destinator",
        string="Send mail after acceptation of the request for the final destinator",
        readonly=False)
    email_after_pickup_template_bool_final_destinator = fields.Boolean(
        related="company_id.email_after_pickup_template_bool_final_destinator",
        string="Send mail after pickup for the final destinator", readonly=False)
    send_mail_satisfaction_destinator_bool_final_destinator = fields.Boolean(
        related="company_id.send_mail_satisfaction_destinator_bool_final_destinator",
        string="Send mail after delivery for the final destinator", readonly=False)
    otp_code_mail_emplate1_bool_final_destinator = fields.Boolean(
        related="company_id.otp_code_mail_emplate1_bool_final_destinator",
        string="Send mail of OTP code for the final destinator", readonly=False)
    max_length = fields.Float(string="Maximum length (cm)", readonly=False, related='company_id.max_length')
    volumetric_weight = fields.Float(string="Volumetric lenght coefficient (kg/m³)", readonly=False,
                                     related='company_id.volumetric_weight')
    max_dimension = fields.Float(string="Maximum dimension (cm)", readonly=False, related='company_id.max_dimension')
    max_pourtour = fields.Float(string="Maximum pourtour (cm)", readonly=False, related='company_id.max_pourtour')

    recherche_initial_indexed = fields.Boolean(related="company_id.recherche_initial_indexed", readonly=False)
    search_with_all_conditions = fields.Boolean(related="company_id.search_with_all_conditions", readonly=False)
    search_by_sql_simple = fields.Boolean(related="company_id.search_by_sql_simple", readonly=False)
    search_by_sql_all_condition = fields.Boolean(related="company_id.search_by_sql_all_condition", readonly=False)
