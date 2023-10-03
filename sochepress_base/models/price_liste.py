# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PriceList(models.Model):
    _name = "soch.price.list"
    _description = "Sochepress price list"

    name = fields.Char(string="Name")
    # source_id = fields.Many2one('sochepress.destination', string="Source")
    # destination_id = fields.Many2one('sochepress.destination', string="Destination")
    price_list_ids = fields.One2many('soch.price.list.rule', 'price_list_id',
                                     'Pricing Rules', copy=True)

    def see_price_rule(self):
        action = self.env.ref('sochepress_base.soche_price_rule_action').read()[0]
        action['views'] = [
            (self.env.ref('sochepress_base.view_delivery_price_rule_tree').id, 'tree'),
            (
                self.env.ref('sochepress_base.view_delivery_price_rule_form').id,
                'form'), ]
        action['domain'] = [('id', 'in', self.price_list_ids.ids)]
        action['limit'] = 80
        return action


class PriceRule(models.Model):
    _name = "soch.price.list.rule"
    _description = "Sochepress price list rules"

    @api.depends('variable', 'min_value', 'max_value', 'price', )
    def _compute_name(self):
        for rule in self:
            name = \
                _('[%s <==> %s] if %s between %s and %s the price is %s') % (
                    rule.source_id.name, rule.destination_id.name, rule.variable,
                    rule.min_value, rule.max_value, rule.price)
            rule.name = name

    name = fields.Char(compute='_compute_name')
    sequence = fields.Integer(required=True, default=10)

    source_id = fields.Many2one('sochepress.destination', string="Source")
    destination_id = fields.Many2one('sochepress.destination', string="Destination")

    price_list_id = fields.Many2one('soch.price.list', 'Carrier',
                                    ondelete='cascade')

    variable = fields.Selection([('weight', 'Weight'), ('volume', 'Volume')],
                                required=True, default='weight')
    min_value = fields.Float('Minimum Value', required=True)
    max_value = fields.Float('Maximum Value', required=True)
    price = fields.Float(string='Price', required=True, default=0.0)
    demand_type = fields.Selection([('normal', 'Normal'), ('transport', 'Transport'),
                                    ('course', 'Course')],
                                   default='normal', string="Request type")
    duration_min = fields.Integer(string="Minimum delivery time")
    duration_max = fields.Integer(string="Maximum delivery time")

    @api.constrains('variable', 'min_value', 'max_value', 'source_id', 'destination_id')
    @api.onchange('variable', 'min_value', 'max_value', 'source_id', 'destination_id')
    def _check_max_min_values(self):
        for r in self:

            line_ids = self.env['soch.price.list.rule'].search(
                [
                    ('variable', '=', r.variable),
                    ('source_id', 'in', [r.source_id.id, r.destination_id.id]),
                    ('destination_id', 'in', [r.destination_id.id, r.source_id.id]),
                    ('price_list_id', '=', r.price_list_id.id),

                ])
            problematic_price = False
            for l in line_ids:
                cond1 = (
                    l.destination_id.id == r.destination_id.id and l.source_id.id
                    == r.source_id.id)
                cond2 = (
                    l.source_id.id == r.destination_id.id and l.destination_id.id
                    == r.source_id.id)
                if cond1 or cond2:
                    problematic_price = l
                    break

            if problematic_price and problematic_price != r and (
                (problematic_price.min_value <= r.min_value
                 <= problematic_price.max_value)
                or (problematic_price.min_value <= r.max_value
                    <= problematic_price.max_value)):
                raise UserError(_("You cannot create price rules with the same "
                                  "source: %s and destination: %s with ranges of nested %s (%s-%s). "
                                  "This price rule has been already created in %s") % (
                                    problematic_price.source_id.name, problematic_price.destination_id.name,
                                    r.variable, problematic_price.min_value, problematic_price.max_value,
                                    problematic_price.price_list_id.name))
            else:
                pass

            # if r.variable and r.source_id and r.destination_id and (r.max_value > 0):
            #     # print("Toutes les conditions sont all")
            #     line = self.env['soch.price.list.rule'].search(
            #         ['&','&','&',
            #          ('variable', '=', r.variable),
            #          ('source_id', 'in', [r.source_id.id, r.destination_id.id]),
            #          '&',
            #          ('destination_id', 'in', [r.destination_id.id, r.source_id.id]),
            #          ('price_list_id', '=', r.price_list_id.id),
            #          '|', '&',
            #              ('min_value', '<=', r.min_value),
            #              ('max_value', '>=', r.min_value),
            #              '&',
            #              ('min_value', '<=', r.max_value),
            #              ('max_value', '>=', r.max_value),
            #          ])
            #     print(line)
            #     print(line.price_list_id)
            #
            #     if line:
            #         raise UserError(_("You cannot create price rules with the same "
            #                           "source and destination with ranges of nested
            #                           %s. "
            #                           "This price rule has been already created in
            #                           %s") % (
            #                             r.variable, line.price_list_id.name))

    # @api.model
    # def create(self, values):
    #     variable = values.get('variable', False)
    #     source_id = values.get('source_id', False)
    #     destination_id = values.get('destination_id', False)
    #     min_value = values.get('min_value', False)
    #     max_value = values.get('max_value', False)
    #
    #     line = self.env['soch.price.list.rule'].search([('variable', '=',
    #     variable), ('source_id', '=', source_id),
    #                                                     ('destination_id', '=',
    #                                                     destination_id),
    #                                                     ('min_value', '<=',
    #                                                     min_value), ('min_value',
    #                                                     '<=', max_value),
    #                                                     ('max_value', '>=',
    #                                                     min_value), ('max_value',
    #                                                     '>=', max_value)])
    #     print(line)
    #     if line:
    #         raise UserError("You cannot create price rules with the same "
    #                         "source and destination with ranges of nested %s" %
    #                         variable)
    #     else:
    #         return super(PriceRule, self).create(values)
