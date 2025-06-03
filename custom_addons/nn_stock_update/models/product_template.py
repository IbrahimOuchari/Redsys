from odoo import models, fields, api
from datetime import datetime

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    creation_date = fields.Date(string="Date de création", readonly=True)
    last_movement_date = fields.Datetime(string="Date du dernier mouvement", compute="_compute_last_movement_date", store=True)

    main_supplier_id = fields.Many2one('res.partner', string="Fournisseur Principal")

    arrival_date = fields.Date(string="Date d’arrivée")
    departure_date = fields.Date(string="Date de sortie")
    supplier_name = fields.Char(string="Nom du fournisseur")
    invoice_reference = fields.Char(string="Référence de la facture")

    purchase_rfq_id = fields.Many2one('purchase.order', string='Dernier RFQ', compute='_compute_purchase_rfq', store=True)

    # @api.model
    # def create(self,vals):
    #     if not vals.get('creation_date'):
    #         vals['creation_date'] = fields.date.context_today(self)
    #     return super(ProductTemplate,self).creat(vals)

    @api.depends('qty_available')
    def _compute_last_movement_date(self):
        for product in self:
            movements = self.env['stock.move'].search([
                ('product_id.product_tmpl_id', '=', product.id)
            ], order="date desc", limit=1)
            product.last_movement_date = movements.date if movements else False

    @api.depends('qty_available')
    def _compute_purchase_rfq(self):
        for rec in self:
            latest_line = self.env['purchase.order.line'].search([
                ('product_id.product_tmpl_id', '=', rec.id)
            ], order="create_date desc", limit=1)
            rec.purchase_rfq_id = latest_line.order_id if latest_line else False