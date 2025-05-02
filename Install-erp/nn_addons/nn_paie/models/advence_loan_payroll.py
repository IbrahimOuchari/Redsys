# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Echéances de Prêt", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_inputs(self, contract_ids, date_from, date_to):
        """Compute inputs for advances and loans when employee_id changes."""

        # Si aucun employé n'est sélectionné, réinitialiser les entrées existantes et revenir
        if not self.employee_id:
            self.input_line_ids = [(5, 0, 0)]  # Efface les entrées existantes
            return []

        # Initialiser les entrées pour avances et prêts
        inputs = []
        total_advance = 0

        # Vérifier la règle salariale pour les avances
        salary_rule_avance = self.env['hr.salary.rule'].search([('code', '=', 'Avance')], limit=1)
        if not salary_rule_avance:
            raise UserError(_("La règle salariale 'Avance' n'existe pas ou n'est pas correctement configurée."))

        # Vérifier la règle salariale pour les prêts
        salary_rule_pret = self.env['hr.salary.rule'].search([('code', '=', 'Pret')], limit=1)
        if not salary_rule_pret:
            raise UserError(_("La règle salariale 'Pret' n'existe pas ou n'est pas correctement configurée."))

        # Gérer les avances salariales
        salary_advances = self.env['salary.advance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'approve'),
            ('paid', '=', False),
            ('date_retenu', '>=', date_from),
            ('date_retenu', '<=', date_to),
        ])

        # Calculer le montant total des avances pour la période
        for advance in salary_advances:
            if date_from.month == advance.date_retenu.month:  # Filtrer sur le mois de la date de début
                total_advance += advance.advance

        # Ajouter une entrée pour l'avance salariale si applicable
        if total_advance > 0:
            inputs.append({
                'name': _("Avance sur Salaire"),
                'code': 'Avance',
                'amount': total_advance,
                'entry': salary_rule_avance.id,  # ID de la règle salariale
            })

        # Gérer les prêts
        loans = self.env['hr.loan'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'approve'),
        ])

        # Ajouter une entrée pour chaque prêt
        for loan in loans:
            for loan_line in loan.loan_lines:
                if date_from <= loan_line.date <= date_to and not loan_line.paid:
                    inputs.append({
                        'name': _("Retenue sur Prêt"),
                        'code': 'Pret',
                        'amount': loan_line.amount,
                        'entry': salary_rule_pret.id,  # ID de la règle salariale
                        'loan_line_id': loan_line.id,
                    })

        # Si aucune entrée n'est calculée, retourner une liste vide
        if not inputs:
            return []

        # Réinitialiser les entrées existantes avant d'ajouter les nouvelles
        self.input_line_ids = [(5, 0, 0)]

        # Ajouter les nouvelles entrées
        for input_data in inputs:
            # Ajouter chaque entrée sous forme de dictionnaire
            self.input_line_ids = [(0, 0, input_data)]

        return inputs

    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_loan_amount()
            if line.code == 'Avance':
                salary_advances = self.env['salary.advance'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('state', '=', 'approve'),
                    ('paid', '=', False),  # Trouver les avances liées non payées
                ])
                for advance in salary_advances:
                    advance.paid = True  # Marquer comme payé
        return super(HrPayslip, self).action_payslip_done()

