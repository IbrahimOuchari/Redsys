from odoo import  models , api ,fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    barcode = fields.Char("PN")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode = fields.Char("PN")


