from odoo import models, fields,api
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderCostLine(models.Model):
    _name = 'crm.lead.cost.line'
    _description = 'Cost Price Line'

    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )
    product_id = fields.Many2one('product.product', string='Product', required=True)
    barcode = fields.Char(string='PN', related='product_id.barcode', store=True)
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    purchase_price = fields.Float(string='Purchase Price')
    cost_by_product = fields.Float(
        string="Cost by product",
        store=True,
        related= 'crm_lead_id.cost_by_product'
    )


    # This Field is controlled by  FUNCTION from purchase Order _onchange_cost_line_ids
    prix_de_revient = fields.Float(
        string='Cost Price',
    )

