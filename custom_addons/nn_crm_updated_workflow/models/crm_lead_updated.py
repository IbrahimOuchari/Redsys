from odoo import fields,api , models
from odoo.exceptions import UserError, ValidationError


class CrmUpdatedWorkflow(models.Model):
    _inherit = 'crm.lead'



    # New Added fields and functions
    initial_product_list_ids = fields.One2many(
        comodel_name='crm.initial.product.list',
        inverse_name='lead_id',
        string='Initial Product List'
    )
    final_product_list_generated = fields.Boolean(string="Final Product is generated" , readonly=False,default= False)

    final_product_list_ids = fields.One2many(
    comodel_name='crm.final.product.list',
    inverse_name='lead_id',
    string="Final Product Lines"
    )

    # Helper function to handle the notification display and page reload
    def notify_product_status(self, product_found):
        if product_found:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'next': {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
                    'title': "Success",
                    'message': "The product already exists.",
                    'type': 'success',
                    'sticky': False,
                }}  # Use 'next' to trigger reload
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'next': {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
                    'title': "Success",
                    'message': "A new product has been created.",
                    'type': 'success',
                    'sticky': False,
                }}  # Use 'next' to trigger reload
            }
    # Main function to generate final product lines
    def action_generate_final_product_lines(self):
        for lead in self:
            final_lines = []
            product_found = False  # Flag to track if any product is found

            for line in lead.initial_product_list_ids:
                barcode = line.barcode
                product = self.env['product.template'].search([('barcode', '=', barcode)], limit=1)

                line_product_found = False  # Track if this specific line's product exists
                if product:
                    # Existing product - fill with info from product.template
                    final_lines.append((0, 0, {
                        'barcode': barcode,
                        'product_id': product.id,
                        'description': line.description,
                        'quantity': line.quantity,
                        'uom_id': product.uom_id.id,
                        'price_unit': product.list_price,
                    }))
                    line_product_found = True
                else:
                    # Create new product in product.template
                    new_product = self.env['product.template'].create({
                        'name': line.name or f'New Product {barcode}',
                        'barcode': barcode,
                        'uom_id': line.unit_of_measure_id.id,
                        'taxes_id': [(6,0,line.taux_tva.ids)],
                        'uom_po_id': line.unit_of_measure_id.id,  # Using the same UOM for purchase
                        'type': line.detailed_type,  # Set default type, adjust if needed
                        'detailed_type': line.detailed_type,  # Ensure it is a storable product
                        'list_price': 0.0,  # Default price
                        'description_purchase': line.description,
                    })

                    # Use the newly created product
                    final_lines.append((0, 0, {
                        'barcode': barcode,
                        'product_id': new_product.id,
                        'description': line.description,
                        'quantity': line.quantity,
                        'uom_id': new_product.uom_id.id,
                        'price_unit': new_product.list_price,
                    }))

                # Update the overall product_found flag if any product was found
                if line_product_found:
                    product_found = True

            # Update the final product list
            lead.final_product_list_ids = [(5, 0, 0)] + final_lines
            lead.final_product_list_generated = True  # Set this flag regardless

            # Call the notification function with appropriate message
            return self.notify_product_status(product_found)

        return None

    def action_create_rfq(self):
        self.ensure_one()

        if not self.id:
            raise UserError("Vous devez enregistrer l'enregistrement avant de créer le RFQ.")

        if not self.final_product_list_ids or not self.final_product_list_generated:
            raise UserError("Aucune liste de produits finaux n’a été générée.")
        if not self.partner_id:
            raise UserError("Veuillez sélectionner un client d'abord.")
        if not self.partner_id.email:
            raise UserError("Le client doit avoir au moins une adresse e-mail.")

        # 🔍 Filtrer les lignes avec produits physiques uniquement
        valid_lines = self.final_product_list_ids.filtered(
            lambda line: line.product_id and line.product_id.detailed_type != 'service'
        )

        if not valid_lines:
            raise UserError("Aucun produit physique à ajouter au RFQ (tous les produits sont de type 'service').")

        # 🧾 Créer le RFQ
        purchase_rfq_vals = {
            'partner_id': self.partner_id.id,
            'crm_lead_id': self.id,
        }
        purchase_rfq = self.env['purchase.rfq'].sudo().create(purchase_rfq_vals)

        for rfq_line in valid_lines:
            self.env['purchase.rfq.line'].sudo().create({
                'order_id': purchase_rfq.id,
                'product_id': rfq_line.product_id.product_variant_id.id,
                'barcode': rfq_line.barcode,
                'name': rfq_line.description,
                'product_qty': rfq_line.quantity,
                'product_uom': rfq_line.uom_id.id,
                'price_unit': rfq_line.price_unit or 0.0,
            })

        self.rfq_created = True

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.rfq',
            'view_mode': 'form',
            'res_id': purchase_rfq.id,
            'target': 'current',
        }

    purchase_rfq_ids = fields.One2many(
        'purchase.rfq',
        'crm_lead_id',
        string="Purchase Orders"
    )
    order_line = fields.One2many(related='purchase_rfq_ids.order_line', string='RFQ Lines', copy=True)
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'crm_lead_id',
        string="Purchase Orders"
    )


    # Related fields of Cost Price Purchase Price
    cost_line_ids = fields.One2many(
        'crm.lead.cost.line',
        'crm_lead_id',
        string="Cost Lines",
        compute='_compute_copy_to_cost_line',
        store=True , # Change to True if you want to store the values
        readonly=False
    )



    estimation_line_ids = fields.One2many(
        'crm.lead.estimation.line',
        'lead_id',
        compute='_compute_copy_to_cost_estimation',
        string="Estimations",
        store= True,
    )



    # this function will calculate the SUM OF FIELD total inside the esmtimation lines
    # @api.depends('estimation_line_ids')
    # def _onchange_estimation_line_ids(self):
    #     for lead in self :
    #         lead.estimation_line_ids.sum_of_total = sum(line.total for line in lead.estimation_line_ids)
    #

    # EXTRA FIELD dd cert trnasport transit
    # DD Fields
    dd_amount = fields.Float( string="DD Amount", store=True)
    dd_currency_id = fields.Many2one('res.currency',  string="DD Currency",
                                     store=True)
    dd_amount_dinar = fields.Float( string="DD Amount in Dinar",
                                   store=True)

    transport_amount = fields.Float(string="Transport Amount",
                                    store=True)
    transport_currency_id = fields.Many2one('res.currency',
                                            string="Transport Currency", store=True)
    transport_amount_dinar = fields.Float(
                                          string="Transport Amount in Dinar", store=True)

    transit_amount = fields.Float(string="Transit Amount", store=True)
    transit_currency_id = fields.Many2one('res.currency',
                                          string="Transit Currency", store=True)
    transit_amount_dinar = fields.Float(
                                        string="Transit Amount in Dinar", store=True)

    cert_amount = fields.Float( string="Cert Amount", store=True)
    cert_currency_id = fields.Many2one('res.currency',
                                       string="Cert Currency", store=True)
    cert_amount_dinar = fields.Float( string="Cert Amount in Dinar",
                                     store=True)

    total_amount_dinar = fields.Float( string="Total Amount in Dinar",
                                      store=True)
    cost_by_product = fields.Float( string="Cost by product", store=True)
    logistic_cost  = fields.Float(string='Logistic Cost',compute='_compute_logistic_cost')
    @api.onchange('transport_amount_dinar','transit_amount_dinar')
    def _compute_logistic_cost(self):
        for record in self:
            if record.sum_quantity:
               record.logistic_cost = (record.transport_amount_dinar +  record.transit_amount_dinar)/ record.sum_quantity
            else:
                record.logistic_cost = 0.0

    currency_id = fields.Many2one(
        'res.currency',
        string="Devise",
        default=lambda self: self.env.company.currency_id.id,
        store=True,
    )

    @api.onchange('currency_id')
    def _compute_currency_change(self):
        for record in self:
            if record.currency_id :
                record.transit_currency_id = record.currency_id
                record.transport_currency_id = record.currency_id

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Default currency_id from company
        if 'currency_id' in fields_list:
            res['currency_id'] = self.env.company.currency_id.id

        # Default transit_currency_id from currency_id
        if 'transit_currency_id' in fields_list:
            res['transit_currency_id'] = res.get('currency_id', self.env.company.currency_id.id)

        return res


    @api.onchange('transport_amount', 'transport_currency_id')
    def _onchange_transport_fields(self):
        if self.transport_amount:
            if self.transport_currency_id.name == 'TND':
                # If currency is Dinar, dinar amount equals original amount
                self.transport_amount_dinar = self.transport_amount
            else:
                # If different currency, convert to Dinar using currency rate
                rate = 1.0
                if self.transport_currency_id:
                    # Get the latest rate for the currency for the current company
                    latest_rate = self.env['res.currency.rate'].search([
                        ('currency_id', '=', self.transport_currency_id.id),
                        ('company_id', '=', self.env.company.id)
                    ], order='name desc', limit=1)

                    if latest_rate:
                        rate = latest_rate.rate
                self.transport_amount_dinar = self.transport_amount * rate

    @api.onchange('transit_amount', 'transit_currency_id')
    def _onchange_transit_fields(self):
        if self.transit_amount:
            if self.transit_currency_id.name == 'TND':
                # If currency is Dinar, dinar amount equals original amount
                self.transit_amount_dinar = self.transit_amount
            else:
                # If different currency, convert to Dinar using currency rate
                rate = 1.0
                if self.transit_currency_id:
                    # Get the latest rate for the currency for the current company
                    latest_rate = self.env['res.currency.rate'].search([
                        ('currency_id', '=', self.transit_currency_id.id),
                        ('company_id', '=', self.env.company.id)
                    ], order='name desc', limit=1)

                    if latest_rate:
                        rate = latest_rate.rate
                self.transit_amount_dinar = self.transit_amount * rate


    sum_quantity = fields.Float(
        string="Sum Quantity",
        compute="_compute_sum_quantity",
        store=True,
    )

    transport_cost = fields.Float(string='Transport Cost', compute='_compute_transport_cost')

    @api.onchange('total_amount_dinar','sum_quantity')
    def _compute_transport_cost(self):
        for record in self:
            if record.sum_quantity >0:
               record.transport_cost = record.total_amount_dinar/ record.sum_quantity or 0.0
            else:
                record.transport_cost = 0

    @api.depends('order_line')
    def _compute_sum_quantity(self):
        for record in self:
            total_qty = 0.0
            for line in record.order_line:
                total_qty += line.product_qty
            record.sum_quantity = total_qty

    @api.depends('final_product_list_ids.prix_revient')
    def _onchange_prix_revient(self):
        """Update 'Prix de Revient' in final product list lines based on estimation lines."""
        for lead in self:
            for estimation_line in lead.estimation_line_ids:
        # Find matching final product line by barcode and product_id
                matching_final_line = lead.final_product_list_ids.filtered(
                    lambda line : line.barcode == estimation_line.barcode and
                                  line.product_id == estimation_line.product_id.id
                )

                # Update prix_revient if found
                if matching_final_line:
                    matching_final_line.prix_revient = estimation_line.prix_revient


    purchase_order_created = fields.Boolean(
        string='Nombre de Commandes',
        compute='_compute_purchase_order_created'
    )
    def _compute_purchase_order_created(self):
        self.ensure_one()
        purchase_order = self.env['purchase.order'].search([('crm_lead_id','=',self.id)])
        if purchase_order:
            self.purchase_order_created = True
        else:
            self.purchase_order_created = False


    def action_view_purchase_rfq(self):
        self.ensure_one()
        purchase_order = self.env['purchase.order'].search([('crm_lead_id','=',self.id)],limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    rfq_created = fields.Boolean(
        string="Nombre de RFQ",default = False
    )

    def action_view_rfqs(self):
        self.ensure_one()
        rfq = self.env['purchase.rfq'].search([('crm_lead_id', '=', self.id)], limit=1)
        if rfq:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Demande de prix',
                'res_model': 'purchase.rfq',
                'res_id': rfq.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Optional: show warning if no RFQ found
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucun RFQ',
                    'message': 'Aucune demande de prix liée à cette opportunité.',
                    'type': 'warning',
                }
            }

    @api.depends('purchase_rfq_ids.order_line')
    def _compute_copy_to_cost_estimation(self):
        print("Testing _compute_copy_to_cost_estimation ")
        for lead in self:
            lines = []
            for rfq in lead.purchase_rfq_ids:
                for line in rfq.order_line:
                    lines.append((0, 0, {
                        'product_id': line.product_id.product_tmpl_id.id,
                        'quantity': line.product_qty,
                        'uom_id': line.product_uom.id,
                        'price_proposed':line.price_unit,
                    }))
            lead.estimation_line_ids = [(5, 0, 0)] + lines

    @api.depends('purchase_rfq_ids.order_line')
    def _compute_copy_to_cost_line(self):
        print("Testing line ")
        for lead in self:
            lines = []
            for rfq in lead.purchase_rfq_ids:
                for line in rfq.order_line:
                    print("Testing line for product:", line.product_id.name)
                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_qty,
                        'uom_id': line.product_uom.id
                    }))
            lead.cost_line_ids = [(5, 0, 0)] + lines
