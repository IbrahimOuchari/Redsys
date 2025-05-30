from odoo import models, fields, api


class CrmLeadPointEstimationProduct(models.Model):
    _name = 'crm.lead.estimation.product'
    _description = "Estimation de Produit Point CRM"

    lead_id = fields.Many2one('crm.lead', string="Opportunité", required=True, ondelete='cascade')

    # Currency field with Euro as default
    currency_id = fields.Many2one('res.currency', string="Devise", default=lambda self: self._get_euro_currency(),
                                  required=True)

    # Identifiants
    pn = fields.Char(related='product_id.barcode', string="PN", required=True)
    product_id = fields.Many2one('product.template', string="Pièce", required=True)

    # Quantité & Prix en Euro
    quantity = fields.Integer(string="Quantité", required=True)
    prix_unitaire = fields.Float(string="PU(€)", required=True, digits=(12, 2))
    estimation_transport_devis = fields.Float(string="Est Transport (€)", digits=(12, 2))
    total_devis = fields.Float(string="Total(€)", compute="_compute_total_devis", store=True, digits=(12, 2))

    # Montants en Dinar (DT)
    total_dinar = fields.Float(string="Total (DT)", compute="_compute_total_dinar", store=True, digits=(12, 3))
    estimation_transport_dinar = fields.Float(string="Est Transport (DT)", compute="_compute_transport_dinar",
                                              store=True, digits=(12, 3))

    fee_dd = fields.Float(string="DD", compute='_compute_fee_dd', store=True, digits=(12, 3))
    taux_change = fields.Float(string="Taux de Change", compute='_compute_taux_change', store=True,
                               digits=(12, 3))
    taux_dd_id = fields.Many2one('taux.dd', string="Taux dd")

    transit = fields.Float(string="Transit", digits=(12, 3))
    cert = fields.Float(string="Est CERT", digits=(12, 3))

    prix_revient = fields.Float(string="Prix de Revient", compute='_compute_prix_revient', store=True, digits=(12, 3))
    margin_percentage = fields.Float(string="Pourcentage de marge", digits=(12, 3))
    margin = fields.Float(string="Marge", compute='_compute_margin', store=True, digits=(12, 3))
    prix_final = fields.Float(string="Prix Final (DT)", compute="_compute_prix_final", store=True, digits=(12, 3))
    price_unit = fields.Float(string="Prix total Untaire", compute='_compute_price_unit')
    # -------------------
    # Helper Functions
    # -------------------
    def _get_euro_currency(self):
        """Get Euro currency record"""
        euro = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
        return euro.id if euro else False

    def _get_dinar_currency(self):
        """Get Tunisian Dinar currency record"""
        dinar = self.env['res.currency'].search([('name', '=', 'TND')], limit=1)
        return dinar.id if dinar else False

    # -------------------
    # Compute Functions
    # -------------------

    @api.depends('currency_id')
    def _compute_taux_change(self):
        """Compute dynamic exchange rate from EUR to TND using res.currency.rate"""
        for rec in self:
            if rec.currency_id and rec.currency_id.name == 'EUR':
                # Get the latest EUR rate from res.currency.rate
                eur_rate_record = self.env['res.currency.rate'].search([
                    ('currency_id', '=', rec.currency_id.id),
                    ('company_id', '=', rec.env.company.id)
                ], order='name desc', limit=1)

                if eur_rate_record and eur_rate_record.rate:
                    # In res.currency.rate, rate is stored as: 1 / (1 EUR = X TND)
                    # So to get "1 EUR = X TND", we need: 1 / rate
                    rec.taux_change = 1 / eur_rate_record.rate
                else:
                    rec.taux_change = 3.5  # Fallback rate
            else:
                rec.taux_change = 3.5  # Fallback rate

    @api.depends('quantity', 'prix_unitaire')
    def _compute_total_devis(self):
        for rec in self:
            rec.total_devis = rec.quantity * rec.prix_unitaire

    @api.depends('total_devis', 'estimation_transport_devis', 'taux_change')
    def _compute_total_dinar(self):
        """Convert Euro amounts to Tunisian Dinar using dynamic rate"""
        for rec in self:
            if rec.currency_id and rec.currency_id.name == 'EUR':
                # Get the latest EUR rate from res.currency.rate
                eur_rate_record = self.env['res.currency.rate'].search([
                    ('currency_id', '=', rec.currency_id.id),
                    ('company_id', '=', rec.env.company.id)
                ], order='name desc', limit=1)

                if eur_rate_record and eur_rate_record.inverse_company_rate:
                    # In res.currency.rate, rate is stored as: 1 / (1 EUR = X TND)
                    # So to get "1 EUR = X TND", we need: 1 / rate
                    rec.taux_change = 1 / eur_rate_record.inverse_company_rate
                    rec.total_dinar = (rec.total_devis + rec.estimation_transport_devis) * rec.taux_change
                else:
                    rec.taux_change = 3.5  # Fallback rate
            else:
                rec.taux_change = 3.5  # Fallback rate


    @api.depends('total_dinar', 'taux_dd_id')
    def _compute_fee_dd(self):
        for rec in self:
            if rec.taux_dd_id and rec.taux_dd_id.name:
                rec.fee_dd = rec.total_dinar * (rec.taux_dd_id.name / 100)
            else:
                rec.fee_dd = 0.0

    @api.depends('total_dinar', 'fee_dd', 'transit', 'cert')
    def _compute_prix_revient(self):
        for rec in self:
            rec.prix_revient = rec.total_dinar + rec.fee_dd + rec.transit + rec.cert

    @api.depends('estimation_transport_devis', 'taux_change')
    def _compute_transport_dinar(self):
        for rec in self:
            if rec.estimation_transport_devis and rec.taux_change:
                rec.estimation_transport_dinar = rec.estimation_transport_devis * rec.taux_change
            else:
                rec.estimation_transport_dinar = 0.0

    @api.depends('prix_revient', 'margin_percentage')
    def _compute_margin(self):
        for rec in self:
            if rec.prix_revient and rec.margin_percentage:
                rec.margin = rec.prix_revient * (rec.margin_percentage / 100)
            else:
                rec.margin = 0.0

    @api.depends('prix_revient', 'margin')
    def _compute_prix_final(self):
        for rec in self:
            rec.prix_final = rec.prix_revient + rec.margin
    @api.depends('prix_final','quantity')
    def _compute_price_unit(self):
        for rec in self :
            if rec.quantity and rec.prix_final:
                rec.price_unit = rec.prix_final/ rec.quantity
            else:
                rec.price_unit = 0.0
