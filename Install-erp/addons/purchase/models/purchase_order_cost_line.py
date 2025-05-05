from odoo import models, fields,api
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderCostLine(models.Model):
    _name = 'purchase.order.cost.line'
    _description = 'Cost Price Line'

    order_id = fields.Many2one('purchase.order', string='Purchase Order', ondelete='cascade')

    product_id = fields.Many2one('product.product', string='Product', required=True)
    barcode = fields.Char(string='PN', related='product_id.barcode', store=True)
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    purchase_price = fields.Float(string='Purchase Price')


    prix_de_revient = fields.Float(
        string='Cost Price',
    )

