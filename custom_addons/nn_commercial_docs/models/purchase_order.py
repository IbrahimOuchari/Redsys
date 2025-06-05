from odoo import fields, api, models



class InheritPurchaseOrder(models.Model):
    _inherit='purchase.order'

    pdf_logo = fields.Boolean(string="PDF Logo")
