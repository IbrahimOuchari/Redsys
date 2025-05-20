from odoo import fields,api,models


class PurchaseRfq(models.Model):
    _inherit = 'purchase.rfq'





    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'





    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )