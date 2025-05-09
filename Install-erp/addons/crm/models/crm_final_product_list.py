from odoo import models, fields

class FinalProductList(models.Model):
    _name = 'crm.final.product.list'
    _description = 'Final Product List'

    barcode = fields.Char(string="PN", help="Part Number")
    product_id = fields.Many2one(
        comodel_name='product.template',
        string="Product"
    )
    description = fields.Text(related='product_id.description_purchase',string="Description")
    quantity = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        ondelete='restrict'
    )
    unit_price = fields.Float(string="Unit Price")
    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string="CRM Lead",
        ondelete='cascade'
    )
    prix_revient = fields.Float(
        string="Prix de Revient", store=True
    )