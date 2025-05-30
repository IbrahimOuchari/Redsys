from odoo import fields,api,models
from odoo.exceptions import UserError


class PurchaseRfq(models.Model):
    _inherit = 'purchase.rfq'


    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )

    def button_confirm(self):
        for rec in self:
            if not rec.suppliers_ids:
                raise UserError("Veuillez sélectionner au moins un fournisseur.")
        self.write({'state': 'rfq'})

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )