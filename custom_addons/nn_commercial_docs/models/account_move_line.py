from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _check_edi_line_tax_required(self):
        # Your custom logic
        if self.product_id.type == 'combo':
            return False
        # Default return True or whatever your logic requires
        return True
