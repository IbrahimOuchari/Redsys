# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo import exceptions
from odoo.exceptions import UserError


class EmployeeLoanPayment(models.Model):
    _name = "employee.loan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Prêt Employé"

    name = fields.Char(string='Nom', readonly=True, default=lambda self: 'Prêt/')
    employee_id = fields.Many2one('hr.employee', string='Employée', required=True, help="Employee")
    date_demande = fields.Date(string='Date de demande', required=True, default=lambda self: fields.Date.today(),
                               help="Date de la demande")
    date_debut = fields.Date(string='Date de début', required=True, help="Date de début du remboursement")
    duree_mois = fields.Integer(string='Durée (mois)', required=True, help="Durée du prêt en mois")
    reason = fields.Text(string='Motif du prêt', help="Raison de la demande de prêt")
    currency_id = fields.Many2one('res.currency', string='Devise', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Société', required=True,
                                 default=lambda self: self.env.user.company_id)
    montant_pret = fields.Float(string='Montant du prêt', required=True)
    mensualite = fields.Float(string='Mensualité', compute='_compute_mensualite', store=True)
    payment_method = fields.Many2one('account.journal', string='Mode de Paiement')
    department = fields.Many2one('hr.department', string='Départment')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submit', 'Envoyé'),
        ('waiting_approval', 'En Attente d\'Approbation'),
        ('approve', 'Approuvé'),
        ('cancel', 'Annulé'),
        ('reject', 'Rejeté')
    ], string='Status', default='draft', track_visibility='onchange')

    employee_contract_id = fields.Many2one('hr.contract', string='Contrat')
    reste_a_payer = fields.Float(string='Reste à payer', compute='_compute_reste_a_payer', store=True)
    echeancier_ids = fields.One2many('employee.loan.line', 'loan_id', string='Échéancier')
    taux_interet = fields.Float(string='Taux d\'intérêt annuel (%)', default=0.0)
    piece_justificative = fields.Binary(string='Pièce justificative')
    piece_justificative_name = fields.Char(string='Nom du fichier')

    @api.depends('montant_pret', 'duree_mois', 'taux_interet')
    def _compute_mensualite(self):
        for loan in self:
            if loan.duree_mois and loan.montant_pret:
                taux_mensuel = (loan.taux_interet / 100) / 12
                if taux_mensuel > 0:
                    # Formule de calcul PMT (Payment)
                    loan.mensualite = (loan.montant_pret * taux_mensuel * (1 + taux_mensuel) ** loan.duree_mois) / (
                                (1 + taux_mensuel) ** loan.duree_mois - 1)
                else:
                    loan.mensualite = loan.montant_pret / loan.duree_mois
            else:
                loan.mensualite = 0.0

    @api.depends('echeancier_ids.montant', 'echeancier_ids.state')
    def _compute_reste_a_payer(self):
        for loan in self:
            montant_paye = sum(line.montant for line in loan.echeancier_ids.filtered(lambda l: l.state == 'paid'))
            loan.reste_a_payer = loan.montant_pret - montant_paye

    @api.constrains('date_demande', 'date_debut')
    def _check_dates(self):
        for record in self:
            if record.date_demande and record.date_debut and record.date_demande > record.date_debut:
                raise UserError(_("La date de demande doit être inférieure ou égale à la date de début"))

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """Update department and contract information when employee changes"""
        self.department = False
        self.employee_contract_id = False

        if self.employee_id and self.employee_id.department_id:
            self.department = self.employee_id.department_id

            # Search for valid contract with proper domain and error handling
            current_contract = self.env['hr.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

            if current_contract:
                self.employee_contract_id = current_contract.id  # Utilisez l'ID au lieu de l'objet

    @api.constrains('montant_pret', 'duree_mois')
    def _check_loan_amount_and_duration(self):
        """Validate loan amount and duration"""
        for loan in self:
            if loan.montant_pret <= 0:
                raise UserError(_("Le montant du prêt doit être supérieur à 0"))
            if loan.duree_mois <= 0:
                raise UserError(_("La durée du prêt doit être supérieure à 0"))

    def generate_echeancier(self):
        """Générer l'échéancier de remboursement"""
        self.ensure_one()
        self.echeancier_ids.unlink()
        date_echeance = self.date_debut
        for i in range(self.duree_mois):
            self.env['employee.loan.line'].create({
                'loan_id': self.id,
                'date_echeance': date_echeance,
                'montant': self.mensualite,
                'sequence': i + 1,
            })
            date_echeance = self.env['employee.loan.line']._get_next_month(date_echeance)

    def submit_to_manager(self):
        self.generate_echeancier()
        self.state = 'submit'
        if self.employee_id.parent_id.user_id:
            self.message_post(
                body=_(f"Une nouvelle demande de prêt a été soumise par {self.employee_id.name} "
                       f"pour un montant de {self.montant_pret} {self.currency_id.symbol}."),
                partner_ids=[self.employee_id.parent_id.user_id.partner_id.id]
            )

    def approve_request(self):
        self.state = 'waiting_approval'
        accountant_group = self.env.ref('account.group_account_manager', raise_if_not_found=False)
        if accountant_group:
            accountant_users = accountant_group.users
            partner_ids = accountant_users.mapped('partner_id').ids
            self.message_post(
                body=_(f"Une demande de prêt pour {self.employee_id.name} "
                       f"nécessite une validation comptable. Montant: {self.montant_pret} {self.currency_id.symbol}"),
                partner_ids=partner_ids
            )

    def approve_request_acc_dept(self):
        if not self.montant_pret:
            raise UserError('Vous devez saisir le montant du prêt')
        self.state = 'approve'
        if self.employee_id.user_id:
            self.message_post(
                body=_("Votre demande de prêt a été approuvée."),
                partner_ids=[self.employee_id.user_id.partner_id.id]
            )
        return True

    def cancel(self):
        self.state = 'cancel'
        if self.employee_id.user_id:
            self.message_post(
                body=_("Votre demande de prêt a été annulée."),
                partner_ids=[self.employee_id.user_id.partner_id.id]
            )

    def reject(self):
        self.state = 'reject'
        if self.employee_id.user_id:
            self.message_post(
                body=_("Votre demande de prêt a été rejetée."),
                partner_ids=[self.employee_id.user_id.partner_id.id]
            )

    @api.model
    def create(self, vals):
        """Override create to add sequence and validation"""
        if vals.get('employee_id'):
            # Verify employee exists
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            if not employee.exists():
                raise UserError(_("L'employé sélectionné n'existe pas"))

            # Check for active contract
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'open'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

            if not contract:
                raise UserError(_("L'employé doit avoir un contrat actif pour demander un prêt"))

        # Get sequence
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.loan.seq') or _('Nouveau')

        return super(EmployeeLoanPayment, self).create(vals)


class EmployeeLoanLine(models.Model):
    _name = 'employee.loan.line'
    _description = 'Ligne d\'échéancier de prêt'
    _order = 'sequence'

    loan_id = fields.Many2one('employee.loan', string='Prêt', required=True)
    date_echeance = fields.Date(string='Date d\'échéance', required=True)
    montant = fields.Float(string='Montant', required=True)
    sequence = fields.Integer(string='Séquence', required=True)
    state = fields.Selection([
        ('draft', 'À payer'),
        ('paid', 'Payé')
    ], string='État', default='draft')
    date_payment = fields.Date(string='Date de paiement')

    @api.model
    def _get_next_month(self, date):
        """Calculer la date du mois suivant"""
        date_obj = fields.Date.from_string(date)
        next_month = date_obj.replace(day=1)
        next_month = next_month.replace(month=next_month.month % 12 + 1)
        if next_month.month == 1:
            next_month = next_month.replace(year=next_month.year + 1)
        return fields.Date.to_string(next_month)