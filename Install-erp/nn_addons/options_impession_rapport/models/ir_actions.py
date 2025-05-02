
from odoo import fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report'

    default_print_option = fields.Selection(selection=[
        ('print', 'Imprimer'),
        ('download', 'Télécharger'),
        ('open', 'Ouvrir')
    ], string='Option impression par défaut')
