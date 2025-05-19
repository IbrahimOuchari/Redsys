from odoo import fields,api , models
import logging

_logger = logging.getLogger(__name__)

class PurchaseRFQUpdatedWorkflow(models.Model):
    inherit = 'purchase.rfq.line'
    # New fields and functions
    barcode = fields.Char(string="PN",related='product_id.barcode')
