from odoo import fields, api , models
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderUpdated(models.Model):
    _inherit = 'purchase.order'
    # New fields and functions

    # New fields and functions
    # DD Fields



    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Related CRM opportunity or lead"
    )

