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
                        'unit_price': product.list_price,
                    }))
                    line_product_found = True
                else:
                    # Create new product in product.template
                    new_product = self.env['product.template'].create({
                        'name': line.name or f'New Product {barcode}',
                        'barcode': barcode,
                        'uom_id': line.unit_of_measure_id.id,
                        'uom_po_id': line.unit_of_measure_id.id,  # Using the same UOM for purchase
                        'type': 'product',  # Set default type, adjust if needed
                        'detailed_type': 'product',  # Ensure it is a storable product
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
                        'unit_price': new_product.list_price,
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

        purchase_rfq_vals = {
            'partner_id': self.partner_id.id,
            'crm_lead_id': self.id,
            # Ajoute ici les autres champs requis de purchase.rfq
        }

        purchase_rfq = self.env['purchase.rfq'].sudo().create(purchase_rfq_vals)

        for rfq_line in self.final_product_list_ids:
            if not rfq_line.product_id:
                raise UserError("Produit manquant dans une ligne.")
            self.env['purchase.rfq.line'].sudo().create({
                'order_id': purchase_rfq.id,
                'product_id': rfq_line.product_id.id,
                'barcode': rfq_line.barcode,
                'name': rfq_line.description,
                'product_qty': rfq_line.quantity,
                'product_uom': rfq_line.uom_id.id,
            })

        # ➕ Si tu veux lier manuellement, assure-toi que c’est un Many2many
        # Sinon ne fais rien ici, rely on the inverse field on purchase.rfq
        # self.purchase_rfq_ids = [(4, purchase_rfq.id)]  # Supprimer ou corriger

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
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'crm_lead_id',
        string="Purchase Orders"
    )


    # Related fields of Cost Price Purchase Price
    cost_line_ids = fields.One2many('purchase.order.cost.line','order_id',compute = '_compute_cost_line_ids',string="Cost Lines",store= False)


    def _compute_cost_line_ids(self):
        for lead in self:
            lead.cost_line_ids = lead.purchase_order_ids.cost_line_ids

    estimation_line_ids = fields.One2many(
        'crm.lead.estimation.line',
        'lead_id',
        string="Estimations"
    )

    # this function will copy the lines from final product list to emtimation
    @api.onchange('final_product_list_ids')
    def _onchange_copy_final_products_to_estimations(self):
        for lead in self:
            lines = []
            for final_product in lead.final_product_list_ids:
                lines.append((0, 0, {
                    'product_id': final_product.product_id.id,
                    'barcode': final_product.barcode,
                    'quantity': final_product.quantity,
                    'uom_id': final_product.uom_id.id,
                    'price_proposed': final_product.unit_price,
                }))
            lead.estimation_line_ids = [(5, 0, 0)] + lines

    # this function will calculate the SUM OF FIELD total inside the esmtimation lines
    # @api.depends('estimation_line_ids')
    # def _onchange_estimation_line_ids(self):
    #     for lead in self :
    #         lead.estimation_line_ids.sum_of_total = sum(line.total for line in lead.estimation_line_ids)
    #

    # EXTRA FIELD dd cert trnasport transit
    # DD Fields
    dd_amount = fields.Float(related='purchase_order_ids.dd_amount', string="DD Amount", store=True)
    dd_currency_id = fields.Many2one('res.currency', related='purchase_order_ids.dd_currency_id', string="DD Currency",
                                     store=True)
    dd_amount_dinar = fields.Float(related='purchase_order_ids.dd_amount_dinar', string="DD Amount in Dinar",
                                   store=True)

    transport_amount = fields.Float(related='purchase_order_ids.transport_amount', string="Transport Amount",
                                    store=True)
    transport_currency_id = fields.Many2one('res.currency', related='purchase_order_ids.transport_currency_id',
                                            string="Transport Currency", store=True)
    transport_amount_dinar = fields.Float(related='purchase_order_ids.transport_amount_dinar',
                                          string="Transport Amount in Dinar", store=True)

    transit_amount = fields.Float(related='purchase_order_ids.transit_amount', string="Transit Amount", store=True)
    transit_currency_id = fields.Many2one('res.currency', related='purchase_order_ids.transit_currency_id',
                                          string="Transit Currency", store=True)
    transit_amount_dinar = fields.Float(related='purchase_order_ids.transit_amount_dinar',
                                        string="Transit Amount in Dinar", store=True)

    cert_amount = fields.Float(related='purchase_order_ids.cert_amount', string="Cert Amount", store=True)
    cert_currency_id = fields.Many2one('res.currency', related='purchase_order_ids.cert_currency_id',
                                       string="Cert Currency", store=True)
    cert_amount_dinar = fields.Float(related='purchase_order_ids.cert_amount_dinar', string="Cert Amount in Dinar",
                                     store=True)

    total_amount_dinar = fields.Float(related='purchase_order_ids.total_amount_dinar', string="Total Amount in Dinar",
                                      store=True)
    cost_by_product = fields.Float(related='purchase_order_ids.cost_by_product', string="Cost by product", store=True)



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

    @api.onchange('final_product_list_ids')
    def _onchange_copy_final_products_to_estimations(self):
        for lead in self:
            lines = []
            for final_product in lead.final_product_list_ids:
                lines.append((0, 0, {
                    'product_id': final_product.product_id.id,
                    'barcode': final_product.barcode,
                    'quantity': final_product.quantity,
                    'uom_id': final_product.uom_id.id,
                    'price_proposed': final_product.unit_price,
                }))
            lead.estimation_line_ids = [(5, 0, 0)] + lines