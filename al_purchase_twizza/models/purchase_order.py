from odoo import models, api
import logging
import json
from lxml import etree

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # @api.onchange('picking_type_id')
    # def _onchange_picking_type_id(self):
    #     if self.picking_type_id.default_location_dest_id.usage != 'customer':
    #         self.dest_address_id = False
    #         self.order_line.write({
    #             'analytic_distribution': self.order_id.picking_type_id.analytic_account_id.id or False
    #         })
    #     else:   # Dropship operation
    #         for line in self.order_line:
    #             line.analytic_distribution = line.sale_order_id.team_id.analytic_account_id.id or False

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        for line in self.order_line:
            analytic_distribution = {}
    
            if self.picking_type_id.default_location_dest_id.usage != 'customer':
                self.dest_address_id = False
                analytic_distribution[self.picking_type_id.analytic_account_id.id] = 100.0
            # else:  # Dropship operation
            #     analytic_distribution[self.dest_address_id.team_id.analytic_account_id.id] = 100.0
    
            line.analytic_distribution = analytic_distribution

    @api.onchange('dest_address_id')
    def _onchange_dest_adress_id(self):
        for line in self.order_line:
            analytic_distribution = {}
            if self.dest_address_id:
                analytic_distribution[self.dest_address_id.team_id.analytic_account_id.id] = 100.0
            line.analytic_distribution = analytic_distribution






    # @staticmethod
    # def modifier_set_readonly(res, expression):
    #     doc = etree.XML(res['arch'])
    #     for node in doc.xpath(expression):
    #         node.set('force_save', '1')
    #         modifiers = json.loads(node.get("modifiers"))
    #         modifiers['readonly'] = True
    #         node.set("modifiers", json.dumps(modifiers))
    #     res['arch'] = etree.tostring(doc)

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         has_price_unit_access = self.env.user.has_group('al_purchase_twizza.group_purchase_unit_price_access')
    #         res_line_form = res['fields']['order_line']['views']['form']
    #         res_line_tree = res['fields']['order_line']['views']['tree']
    #         if not has_price_unit_access:
    #             self.modifier_set_readonly(res=res_line_form, expression="//field[@name='price_unit']")
    #             self.modifier_set_readonly(res=res_line_tree, expression="//field[@name='price_unit']")
    #     return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

        
    # @api.model
    # def create(self, values):
    #     line = super(PurchaseOrderLine, self).create(values)
    #     if line.order_id.picking_type_id.default_location_dest_id.usage != 'customer':
    #         line.analytic_distribution = line.order_id.picking_type_id.analytic_account_id.id or False
    #     else:
    #         line.analytic_distribution = line.sale_order_id.team_id.analytic_account_id.id or False
    #     return line

    @api.model
    def create(self, values):
        line = super(PurchaseOrderLine, self).create(values)
        analytic_distribution = {}
        if line.order_id.picking_type_id.default_location_dest_id.usage != 'customer':
            analytic_distribution[line.order_id.picking_type_id.analytic_account_id.id] = 100.0 
        elif line.order_id.dest_address_id :
            analytic_distribution[line.order_id.dest_address_id.team_id.analytic_account_id.id] = 100.0
        line.analytic_distribution = analytic_distribution
        
        return line
