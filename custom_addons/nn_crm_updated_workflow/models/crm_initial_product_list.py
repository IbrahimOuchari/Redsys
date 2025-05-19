from odoo import fields, api, models


class InitialProductList(models.Model):
    _name = 'crm.initial.product.list'
    _description = 'Initial Product List'

    description = fields.Char(string="Description")
    barcode = fields.Char(string="Part Number")
    name = fields.Char(string="Name")
    quantity = fields.Float(string="Quantity", default=1.0)
    unit_of_measure_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        ondelete='restrict'  # Better than cascade for UoM
    )
    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string="CRM Lead",
        ondelete='cascade'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default Unit of Measure to prevent '_unknown' object errors"""
        res = super(InitialProductList, self).default_get(fields_list)
        if 'unit_of_measure_id' in fields_list and not res.get('unit_of_measure_id'):
            # Get reference to default UoM (usually 'Unit(s)')
            default_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            if default_uom:
                res['unit_of_measure_id'] = default_uom.id
        return res

