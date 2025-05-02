from odoo import models, fields, api

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax'

    is_timbre = fields.Boolean(string="Is Timbre", default=False)

