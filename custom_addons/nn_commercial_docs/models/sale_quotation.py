from odoo import fields, models, api


class InheritSaleQuotation(models.Model):
    _inherit='sale.quotation'

    def _get_order_lines_to_report(self):
        return self.order_line.filtered(lambda line: not line.display_type)
    pdf_logo = fields.Boolean(string="PDF Logo")
