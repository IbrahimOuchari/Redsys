from odoo import fields, api, models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    pdf_logo = fields.Boolean(string="PDF Logo")

