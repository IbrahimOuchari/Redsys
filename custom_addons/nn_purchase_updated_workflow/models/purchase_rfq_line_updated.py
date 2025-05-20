from odoo import fields, api, models
import logging

_logger = logging.getLogger(__name__)


class PurchaseRfqLineInherited(models.Model):
    _inherit = 'purchase.rfq.line'

    # Make sure to define or check if order_id exists in the parent model
    # If it doesn't exist in parent model but is needed for relationships, add it:
    # order_id = fields.Many2one('purchase.order', string='Order Reference')

    # Your new fields
    barcode = fields.Char(string="PN", related='product_id.barcode')
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price', readonly=False, store=True)