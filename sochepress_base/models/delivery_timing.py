# -*- coding: utf-8 -*-
from math import modf

from odoo import models, fields, api, _
from odoo.exceptions import UserError


def format_date(i):
    return "0%s" % i if len(str(i)) == 1 else i


class DeliveryTiming(models.Model):
    _name = 'delivery.timing'
    _description = "Delivery timing"

    name = fields.Char(string="Name", default="New", compute='_get_name')
    start_time = fields.Float(string="Start time")
    end_time = fields.Float(string="End time")
    start_minute = fields.Float(string="Start Minutes", compute='_compute_frac_whole')
    start_hour = fields.Integer(string="Start Hours", compute='_compute_frac_whole')
    end_minute = fields.Float(string="End Minutes", compute='_compute_frac_whole')
    end_hour = fields.Integer(string="End Hours", compute='_compute_frac_whole')
    duration = fields.Float("Duration", compute='compute_duration', store=True, readonly=False)

    @api.depends('start_time', 'end_time')
    def compute_duration(self):
        for r in self:
            r.duration = r.end_time - r.start_time

    @api.onchange('start_time', 'end_time')
    def _compute_frac_whole(self):
        for r in self:
            r.start_minute, r.start_hour = modf(r.start_time) if r.start_time else (0, 0)
            r.end_minute, r.end_hour = modf(r.end_time) if r.end_time else (0, 0)

    @api.depends('start_time', 'end_time')
    def _get_name(self):
        for r in self:
            r.name = "New" if r.start_time == 0.0 and r.end_time == 0.0 else "%s:%s - %s:%s" % (
                format_date(r.start_hour), format_date(int(r.start_minute * 60)), format_date(r.end_hour),
                format_date(int(r.end_minute * 60)))

    @api.onchange('start_time', 'end_time')
    def _constrains_time(self):
        for r in self:
            if not (0.0 <= r.start_time <= 24.0):
                raise UserError(_("Start time must be between 0 and 24"))
            if not (0.0 <= r.end_time <= 24.0):
                raise UserError(_("End time must be between 0 and 24"))
