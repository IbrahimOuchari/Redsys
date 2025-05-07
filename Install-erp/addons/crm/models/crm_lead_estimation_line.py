from odoo import models, fields, api


class CrmLeadEstimation(models.Model):
    _name = 'crm.lead.estimation.line'
    _description = "Ligne d'Estimation"

    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string="Piste CRM",
        ondelete='cascade'
    )

    barcode = fields.Char(string="PN")
    product_id = fields.Many2one('product.template', string="Produit")
    description = fields.Text(related='product_id.description_sale',string="Description")
    quantity = fields.Float(string="Quantité", default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Unité de mesure")
    currency_id = fields.Many2one('res.currency', string="Devise")
    price_proposed = fields.Float(string="Prix proposé par le fournisseur")

    total = fields.Monetary(
        string="Total",
        currency_field='currency_id',
        compute='_compute_total',
        store=True
    )

    @api.depends('price_proposed', 'quantity')
    def _compute_total(self):
        for line in self:
            line.total = (line.price_proposed or 0.0) * (line.quantity or 0.0)

    sum_of_total = fields.Monetary(
        string="Total des estimations",
        currency_field='currency_id',
        compute='_compute_sum_of_total',
        store=True
    )


    @api.depends('lead_id','price_proposed','total')
    def _compute_sum_of_total(self):
        for line in self:
            if line.lead_id:
                # Get all lines for the same lead
                related_lines = self.search([('lead_id', '=', line.lead_id.id)])
                # Make sure they share the same currency
                total_sum = sum(l.total for l in related_lines if l.currency_id == line.currency_id)
                line.sum_of_total = total_sum
            else:
                line.sum_of_total = 0.0