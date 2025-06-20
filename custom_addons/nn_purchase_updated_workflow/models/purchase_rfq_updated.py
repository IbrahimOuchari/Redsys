from odoo import fields,api , models,_
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)
class PurchaseRFQUpdatedWorkflow(models.Model):
    _inherit = 'purchase.rfq'
    # new fields and function
    suppliers_ids = fields.Many2many(
        'res.partner',
        string="Tous les Fournisseurs",
        domain=[('is_supplier', '=', True)]
    )
    # crm_lead_id = fields.Many2one(
    #     'crm.lead',
    #     string="Piste CRM",
    #     help="Piste CRM liée à cette commande d'achat"
    # )

    @api.onchange('suppliers_ids')
    def _onchange_suppliers_ids(self):
        for record in self:
            record.partner_id = False


    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the EDI purchase template message loaded by default.
        It fetches recipients from `suppliers_ids` instead of `partner_id`.
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data._xmlid_lookup('nn_purchase_updated_workflow.email_template_edi_purchase_rfq_new')[1]
            else:
                template_id = ir_model_data._xmlid_lookup('nn_purchase_updated_workflow.email_template_edi_purchase_rfq_done_new')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        # Build context
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.rfq',
            'default_res_ids': self.ids,
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'mark_rfq_as_sent': True,
            # ✨ Custom line to populate the recipients with suppliers_ids
            'default_partner_ids': [(6, 0, self.suppliers_ids.ids)],
        })

        # Handle language context
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)

        # Label according to state
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def button_creat_po(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'crm_lead_id': self.crm_lead_id.id,
            'rfq_seq': self.name,
            'partner_ref': self.partner_ref,
            'payment_term_id': self.payment_term_id.id,
            'order_line': [(0, 0, {
                'display_type': line.display_type,
                'product_id': line.product_id.id,
                'name': line.name,
                'product_qty': line.product_qty,
                'price_unit': line.price_unit,
            }) for line in self.order_line],
        })
        # Store the relation to the newly created PO
        self.write({
            'purchase_order_id': purchase_order.id,
            'state': "purchase"
        })
        return {
            'name': 'Purchase Order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_view_crm(self):
        self.ensure_one()
        crm_lead = self.env['crm.lead'].search([('purchase_rfq_ids','=',self.id)],limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'CRM',
            'res_model': 'crm.lead',
            'res_id': crm_lead.id,
            'view_mode': 'form',
            'target': 'current',
        }


    crm_lead_exist = fields.Boolean(
        string='Crm Lead',
        compute='_compute_crm_lead_exist'
    )
    def _compute_crm_lead_exist(self):
        self.ensure_one()
        purchase_order = self.env['crm.lead'].search([('purchase_rfq_ids','=',self.id)])
        if purchase_order:
            self.crm_lead_exist = True
        else:
            self.crm_lead_exist = False

    sale_quotation_confirmed = fields.Boolean(string="Devis confirmé",default=False)

    def action_confirm_sale(self):
        for rec in self:
            if not rec.sale_quotation_confirmed:
                for line in rec.order_line:
                    if line.price_unit <= 0:
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Prix Invalide',
                                'message': "Le prix unitaire ne peut pas être inférieur ou égal à zéro.",
                                'type': 'warning',  # options: success, warning, danger, info
                                'sticky': False,  # stays until clicked if True
                            }
                        }

                rec.sale_quotation_confirmed = True
