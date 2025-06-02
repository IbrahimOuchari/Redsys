from odoo import models, fields

class FinalProductList(models.Model):
    _name = 'crm.final.product.list'
    _description = 'Final Product List'

    barcode = fields.Char(string="PN", related='product_id.barcode',help="Part Number" ,readonly=False, store=True)
    product_id = fields.Many2one(
        comodel_name='product.template',
        string="Product"
    )
    description = fields.Text(string="Description",readonly=False ,store= True)
    quantity = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2many(
        related='product_id.taxes_id',
        string="Unit of Measure",
        ondelete='restrict'
    )
    price_unit = fields.Float(string="Unit Price")
    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string="CRM Lead",
        ondelete='cascade'
    )
    prix_revient = fields.Float(
        string="Prix de Revient", store=True
    )
    detailed_type = fields.Selection(
        related='product_id.detailed_type',
        string="Product Type",
        store=True
    )