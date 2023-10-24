from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].search([
        ('invoice_ids', '!=', False),
        ('payment_mode_id', '!=', False)
    ])
    for order in orders:
        order.invoice_ids.write({
            'payment_mode_id': order.payment_mode_id.id,
        })
