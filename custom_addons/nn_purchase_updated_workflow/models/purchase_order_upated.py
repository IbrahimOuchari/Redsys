from odoo import fields, api , models
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderUpdated(models.Model):
    inherit = 'purchase.order'
    # New fields and functions

    # New fields and functions
    # DD Fields
    dd_amount = fields.Float(string="DD Amount", digits='Product Price')
    dd_currency_id = fields.Many2one('res.currency', string="DD Currency", compute='_compute_onchange_currency_id',
                                     readonly=False)
    dd_amount_dinar = fields.Float(string="DD Amount in Dinar")

    # Transport Fields
    transport_amount = fields.Float(string="Transport Amount", digits='Product Price')
    transport_currency_id = fields.Many2one('res.currency', string="Transport Currency",
                                            compute='_compute_onchange_currency_id', readonly=False)
    transport_amount_dinar = fields.Float(string="Transport Amount in Dinar")

    # Transit Fields
    transit_amount = fields.Float(string="Transit Amount", digits='Product Price')
    transit_currency_id = fields.Many2one('res.currency', string="Transit Currency",
                                          compute='_compute_onchange_currency_id', readonly=False)
    transit_amount_dinar = fields.Float(string="Transit Amount in Dinar")

    # Cert Fields
    cert_amount = fields.Float(string="Cert Amount", digits='Product Price')
    cert_currency_id = fields.Many2one('res.currency', string="Cert Currency", compute='_compute_onchange_currency_id',
                                       readonly=False)
    cert_amount_dinar = fields.Float(string="Cert Amount in Dinar")

    def _compute_onchange_currency_id(self):
        # Set the currency for DD fields
        self.dd_currency_id = self.currency_id

        # Set the currency for Transport fields
        self.transport_currency_id = self.currency_id

        # Set the currency for Transit fields
        self.transit_currency_id = self.currency_id

        # Set the currency for Cert fields
        self.cert_currency_id = self.currency_id

    # Total Amount of Amount dinars
    total_amount_dinar = fields.Float(string="Total Amount in Dinar", store=True)

    @api.onchange('dd_amount_dinar', 'transport_amount_dinar', 'transit_amount_dinar', 'cert_amount_dinar')
    def _compute_total_amount_dinar(self):
        for record in self:
            record.total_amount_dinar = sum([
                record.dd_amount_dinar or 0.0,
                record.transport_amount_dinar or 0.0,
                record.transit_amount_dinar or 0.0,
                record.cert_amount_dinar or 0.0
            ])

    # Tunisian Dinar currency record for reference

    # @api.onchange('dd_amount', 'dd_currency_id')
    # def _onchange_dd_fields(self):
    #     if self.dd_amount:
    #         if self.dd_currency_id == 'TND':
    #             # If currency is Dinar, dinar amount equals original amount
    #             self.dd_amount_dinar = self.dd_amount
    #         else:
    #             # If different currency, convert to Dinar
    #             self.dd_amount_dinar = self.dd_amount * self.dd_currency_id.rate

    @api.onchange('dd_amount', 'dd_currency_id')
    def _onchange_dd_fields(self):
        if self.dd_amount and self.dd_currency_id:
            if self.dd_currency_id.name == 'TND':
                # If currency is Dinar, dinar amount equals original amount
                self.dd_amount_dinar = self.dd_amount
            else:
                # If different currency, convert to Dinar using the latest rate from rate_ids
                rate = 1.0
                if self.dd_currency_id.rate_ids:
                    # Get the most recent rate from the rate_ids field
                    latest_rate = self.dd_currency_id.rate_ids.sorted('name', reverse=True)[0]
                    rate = latest_rate.inverse_company_rate
                self.dd_amount_dinar = self.dd_amount * rate

    @api.onchange('transport_amount', 'transport_currency_id')
    def _onchange_transport_fields(self):
        if self.transport_amount and self.transport_currency_id:
            if self.transport_currency_id.name == 'TND':
                # If currency is Dinar, transport amount equals original amount
                self.transport_amount_dinar = self.transport_amount
            else:
                # If different currency, convert to Dinar using the latest rate from rate_ids
                rate = 1.0
                if self.transport_currency_id.rate_ids:
                    # Get the most recent rate from the rate_ids field
                    latest_rate = self.transport_currency_id.rate_ids.sorted('name', reverse=True)[0]
                    rate = latest_rate.inverse_company_rate
                self.transport_amount_dinar = self.transport_amount * rate

    @api.onchange('transit_amount', 'transit_currency_id')
    def _onchange_transit_fields(self):
        if self.transit_amount and self.transit_currency_id:
            if self.transit_currency_id.name == 'TND':
                # If currency is Dinar, transit amount equals original amount
                self.transit_amount_dinar = self.transit_amount
            else:
                # If different currency, convert to Dinar using the latest rate from rate_ids
                rate = 1.0
                if self.transit_currency_id.rate_ids:
                    # Get the most recent rate from the rate_ids field
                    latest_rate = self.transit_currency_id.rate_ids.sorted('name', reverse=True)[0]
                    rate = latest_rate.inverse_company_rate
                self.transit_amount_dinar = self.transit_amount * rate

    @api.onchange('cert_amount', 'cert_currency_id')
    def _onchange_cert_fields(self):
        if self.cert_amount and self.cert_currency_id:
            if self.cert_currency_id.name == 'TND':
                # If currency is Dinar, cert amount equals original amount
                self.cert_amount_dinar = self.cert_amount
            else:
                # If different currency, convert to Dinar using the latest rate from rate_ids
                rate = 1.0
                if self.cert_currency_id.rate_ids:
                    # Get the most recent rate from the rate_ids field
                    latest_rate = self.cert_currency_id.rate_ids.sorted('name', reverse=True)[0]
                    rate = latest_rate.inverse_company_rate
                self.cert_amount_dinar = self.cert_amount * rate

    cost_by_product = fields.Float(
        string="Cost by product",
        store=True,
    )

    @api.onchange('total_amount_dinar', 'order_line.product_qty')
    def _compute_additional_cost_by_qty(self):
        for order in self:
            # Total quantity across all lines
            total_qty = sum(line.product_qty for line in order.order_line)
            # Avoid division by zero
            if total_qty:
                order.cost_by_product = order.total_amount_dinar / total_qty

    # cost_line_ids = fields.One2many('purchase.order.cost.line','order_id', string='Cost Lines')

    @api.onchange('cost_line_ids', 'cost_by_product')
    def _onchange_cost_line_ids(self):
        for record in self:
            for lines in record.cost_line_ids:
                lines.prix_de_revient = lines.purchase_price + record.cost_by_product

    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )

    @api.onchange('order_line')
    def _onchange_order_line_to_cost_lines(self):
        new_cost_lines = []
        self.cost_line_ids = [(5, 0, 0)]
        for line in self.order_line:
            new_cost_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'description': line.name,
                'quantity': line.product_qty,
                'uom_id': line.product_uom.id,
                'purchase_price': line.price_unit,
                'cost_by_product': self.cost_by_product,
                # prix_de_revient is left empty for now (optional)
            }))

        self.cost_line_ids = new_cost_lines
