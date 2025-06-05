from odoo import fields, api, models



class InheritPurchaseRFQ(models.Model):
    _inherit='purchase.rfq'

    pdf_logo = fields.Boolean(string="PDF Logo")
