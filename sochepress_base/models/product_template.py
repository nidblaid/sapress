from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_modele_colis = fields.Boolean("Is a colis modele")
    is_conform = fields.Boolean(string="Is a colis conform", compute='_compute_conform', store=1)
    type_colis_id = fields.Many2one('sochepress.type.colis', string='Colis Type')
    colis_pourtour = fields.Float("Colis pourtour", store=1, compute='_compute_conform')
    client_id = fields.Many2one('res.partner', string='Client')
    length = fields.Float('Length')
    width = fields.Float('Width')
    height = fields.Float('Height')
    weight_vol = fields.Float('Volumetric weigth', compute='_compute_conform', store=1)
    default_code_soch = fields.Char('Default Code')
    designation_chez_client = fields.Char('Designation Chez Client')
    volume = fields.Float('Volume', compute='_calculate_volume', inverse='_set_volume', digits='Volume', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)

    @api.depends('length', 'height', 'width')
    def _compute_conform(self):
        for r in self:
            r.colis_pourtour = r.length + 2 * (r.height + r.width)
            r.is_conform = ((r.length + r.height + r.width) <= r.company_id.max_length)
            r.weight_vol = (r.length * r.height * r.width * r.company_id.volumetric_weight) / 1000000

    @api.depends('length', 'width', 'height')
    def _calculate_volume(self):
        for r in self:
            r.volume = (r.length * r.width * r.height) / 1000000

    @api.onchange('weight', 'length', 'width', 'height')
    def set_correct_colis_type(self):
        for r in self:
            weight = r.weight
            req = self
            colis_type_id = False
            if 1 <= weight <= 30:
                colis_type_id = req.env.ref('sochepress_base.colis_type_colis')
            if 31 <= weight <= 100:
                colis_type_id = req.env.ref('sochepress_base.colis_type_petite_palette')
            if 101 <= weight <= 300:
                colis_type_id = req.env.ref('sochepress_base.colis_type_moyenne_palette')
            if weight >= 301:
                colis_type_id = req.env.ref('sochepress_base.colis_type_grande_palette')
            r.type_colis_id = colis_type_id
            if r.is_modele_colis:
                r.name = ('%s * %s * %s' % (r.length, r.width, r.height)).upper()

    @api.model
    def create(self, vals):
        client = vals.get('client_id', False)
        if client:
            client = self.env['res.partner'].browse(client)
            if not client.article_sequence:
                client.article_sequence = 'product.%s' % client.name.replace(" ", "")
                self.env['ir.sequence'].create({
                    'code': client.article_sequence,
                    'padding': 4,
                    'name': client.name,
                    'implementation': 'no_gap'
                })
            vals["default_code_soch"] = "COL" + self.env["ir.sequence"].next_by_code(client.article_sequence)
        return super(ProductTemplate, self).create(vals)
