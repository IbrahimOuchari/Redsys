from odoo.tools.misc import formatLang
import logging
from odoo import models, fields, api, _
import json
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_stamp_exempt = fields.Boolean(
        related='partner_id.is_stamp_exempt',
        string="Exonéré Timbre",
        store=False,
        help="Indique si le partenaire est exonéré de la taxe de timbre fiscal"
    )

    @api.onchange('is_stamp_exempt')
    def _onchange_add_fiscal_stamp(self):
        """Ajoute ou retire la ligne de timbre fiscal en fonction de l'exonération."""

        if self.move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund') or self.state != 'draft':
            return

        stamp_tax = self.env['account.tax'].search([('invoice_label', '=', '1DT')], limit=1)
        if not stamp_tax:
            return

        # Suppression des lignes de timbre existantes
        self.invoice_line_ids = self.invoice_line_ids.filtered(
            lambda line: not (line.name == 'Timbre' or (line.tax_ids and stamp_tax in line.tax_ids))
        )

        # Ne rien faire si exonéré
        if self.is_stamp_exempt:
            return

        # Détermination du compte comptable
        income_account = stamp_tax.invoice_repartition_line_ids.filtered(
            lambda l: l.repartition_type == 'base'
        ).account_id or self.journal_id.default_account_id

        if not income_account:
            return  # Sécurité supplémentaire

        # Construction de la ligne de timbre
        stamp_line_vals = {
            'name': 'Timbre',
            'quantity': 1,
            'price_unit': 0,
            'account_id': income_account.id,
            'tax_ids': [(6, 0, [stamp_tax.id])],
        }

        # Ajout de la ligne en première position
        self.update({
            'invoice_line_ids': [(0, 0, stamp_line_vals)] + [(1, line.id, {}) for line in self.invoice_line_ids]
        })

    # Override create method to ensure stamp is applied when creating invoices
    @api.model
    def create(self, vals):
        record = super(AccountMove, self).create(vals)
        if record.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund') and record.state == 'draft':
            record._onchange_add_fiscal_stamp()
        return record

    def write(self, vals):
        result = super(AccountMove, self).write(vals)
        if 'partner_id' in vals or 'is_stamp_exempt' in vals:
            for record in self:
                if record.move_type in (
                        'out_invoice', 'out_refund', 'in_invoice', 'in_refund') and record.state == 'draft':
                    record._onchange_add_fiscal_stamp()
        return result



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_stamp_tax = fields.Boolean(compute='_compute_is_stamp_tax', store=True)

    @api.depends('tax_ids')
    def _compute_is_stamp_tax(self):
        for line in self:
            line.is_stamp_tax = any(tax.name == 'Timbre Fiscal' for tax in line.tax_ids)
