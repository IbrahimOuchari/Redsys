from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from num2words import num2words
from datetime import date

from io import StringIO
import base64

import calendar


class OrdreVirement(models.Model):
    _name = 'ordre.virement'
    _description = 'Ordre de Virement'

    @api.model
    def _get_years(self):
        current_year = datetime.datetime.now().year
        years = []
        # Générer une liste d'années (5 ans avant l'année courante jusqu'à 5 ans après)
        for year in range(current_year - 5, current_year + 6):
            years.append((str(year), str(year)))
        return years

    name = fields.Integer(string='Séquence', default=1)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('close', 'lock'),
    ], string="Statut", default='draft')
    mois = fields.Selection([
        ('01', 'Janvier'),
        ('02', 'Février'),
        ('03', 'Mars'),
        ('04', 'Avril'),
        ('05', 'Mai'),
        ('06', 'Juin'),
        ('07', 'Juillet'),
        ('08', 'Août'),
        ('09', 'Septembre'),
        ('10', 'Octobre'),
        ('11', 'Novembre'),
        ('12', 'Décembre'),
    ], string='Mois', required=True)

    annee = fields.Selection(
        selection='_get_years',
        string='Année',
        required=True,
        default=lambda self: str(datetime.datetime.now().year)
    )
    edit_date = fields.Date(string='Éditer le')

    date_virement = fields.Date(string='Date Virement')  # Modifié de Datetime à Date
    signature_responsable_paie = fields.Binary(string='Signature Responsable Paie',
                                               related='company_id.signature_responsable_paie',
                                               store=True)
    logo = fields.Binary(string='Logo', related='company_id.logo',
                         store=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=False, )
    ordre_virement_line_ids = fields.One2many('ordre.virement.line', 'ordre_virement_id',
                                              string='Lignes d\'Ordre de Virement', readonly=True)

    banque = fields.Char(
        related='company_id.bank_company_id',  # This will get the bank's name
        string='Banque',
        readonly=False,
        store=True
    )
    compte_bancaire = fields.Char(
        related='company_id.bank_company_account',
        string='RIB Bancaire',
        readonly=False,
        store=True
    )

    employee_id = fields.Many2one('hr.employee', string='Employee')

    # bank_id = fields.Many2one('hr.employee.bank', string='Bank Name', required=True)
    bank_name = fields.Char(
        related='employee_id.bank_id',  # This will get the bank's name
        string='Bank Name',
        readonly=True,
        store=True
    )
    acc_number = fields.Char(
        related='employee_id.bank_account',
        string='Account Number',
        readonly=True,
        store=True
    )

    def format_month_in_letters(self, month_number):
        months_in_french = [
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
        ]
        try:
            return months_in_french[int(month_number) - 1]
        except (ValueError, IndexError):
            return ''

    def action_manual_state_change(self):
        for record in self:
            record.state = 'draft'

    def action_order_lock(self):
        return self.write({'state': 'close'})

    def generate_ordre_virement_lines(self):
        # Ensure mois and annee are integers
        try:
            mois = int(self.mois)
            annee = int(self.annee)
        except ValueError:
            raise UserError("Le mois et l'année doivent être des entiers valides.")

        # Check that the year and month are valid
        if not mois or not annee:
            raise UserError("Le mois et l'année doivent être définis pour générer les lignes de virement.")

        # Format the date string correctly
        date_from = f'{annee}-{mois:02d}-01'  # Start of the month

        # Get the last day of the month dynamically
        last_day = calendar.monthrange(annee, mois)[1]
        date_to = f'{annee}-{mois:02d}-{last_day}'  # Last day of the month

        # Fetch payslips based on the year, month, and state
        valid_payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', '=', 'done')
        ])

        # Collect valid employee IDs from payslips
        valid_employee_ids = valid_payslips.mapped('employee_id.id')

        # Remove existing journal lines for employees without valid payslips
        existing_lines = self.env['ordre.virement.line'].search([
            ('ordre_virement_id', '=', self.id),
            ('employe_id', 'not in', valid_employee_ids)
        ])
        existing_lines.unlink()

        # Update or create ordre_virement lines for valid payslips
        for payslip in valid_payslips:
            for line in payslip.line_ids:
                if line.code == 'NETAP':  # Filter based on the specific line code (NETAP)
                    # Find the corresponding ordre_virement line for the employee
                    ordre_virement_line = self.env['ordre.virement.line'].search([
                        ('employe_id', '=', payslip.employee_id.id),
                        ('ordre_virement_id', '=', self.id)
                    ], limit=1)

                    # Calculate the total number of days worked
                    total_days = sum(wd.number_of_days for wd in payslip.worked_days_line_ids)

                    if ordre_virement_line:
                        # If the line already exists, update all the fields
                        ordre_virement_line.write({
                            'netap': line.total,
                            'date_virement': fields.Date.context_today(self),
                            # Update additional fields similar to the update method
                            'salaire_brute': next((sl.total for sl in payslip.line_ids if sl.code == 'GROSS'), 0),
                            'cnss': next((sl.total for sl in payslip.line_ids if sl.code == 'CNSS'), 0),
                            'cavis': next((sl.total for sl in payslip.line_ids if sl.code == 'CAVIS'), 0),
                            'salaire_imposable': next((sl.total for sl in payslip.line_ids if sl.code == 'C_IMP'), 0),
                            'impot': next((sl.total for sl in payslip.line_ids if sl.code == 'IRPP'), 0),
                            'assurance_group': next((sl.total for sl in payslip.line_ids if sl.code == 'ASSG'), 0),
                            'pret': next((sl.total for sl in payslip.line_ids if sl.code == 'Pret'), 0),
                            'avance': next((sl.total for sl in payslip.line_ids if sl.code == 'Avance'), 0),
                            'cnss_patronale': next((sl.total for sl in payslip.line_ids if sl.code == 'CNSS_PAT'), 0),
                            'total_charge_patronale': next(
                                (sl.total for sl in payslip.line_ids if sl.code == 'TOT_PAT'), 0),
                            'accident_travail': next((sl.total for sl in payslip.line_ids if sl.code == 'ACC_TRAV'), 0),
                            'tfp': next((sl.total for sl in payslip.line_ids if sl.code == 'TFP'), 0),
                            'assurance_group_patr': next(
                                (sl.total for sl in payslip.line_ids if sl.code == 'ASS_GRP_PAT'), 0),
                        })
                    else:
                        # If the line doesn't exist, create a new one with the fetched values
                        self.env['ordre.virement.line'].create({
                            'ordre_virement_id': self.id,
                            'employe_id': payslip.employee_id.id,
                            'netap': line.total,
                            'date_virement': fields.Date.context_today(self),
                            # Add additional fields similar to the update method
                            'salaire_brute': next((sl.total for sl in payslip.line_ids if sl.code == 'GROSS'), 0),
                            'cnss': next((sl.total for sl in payslip.line_ids if sl.code == 'CNSS'), 0),
                            'cavis': next((sl.total for sl in payslip.line_ids if sl.code == 'CAVIS'), 0),
                            'salaire_imposable': next((sl.total for sl in payslip.line_ids if sl.code == 'C_IMP'), 0),
                            'impot': next((sl.total for sl in payslip.line_ids if sl.code == 'IRPP'), 0),
                            'assurance_group': next((sl.total for sl in payslip.line_ids if sl.code == 'ASSG'), 0),
                            'pret': next((sl.total for sl in payslip.line_ids if sl.code == 'Pret'), 0),
                            'avance': next((sl.total for sl in payslip.line_ids if sl.code == 'Avance'), 0),
                            'cnss_patronale': next((sl.total for sl in payslip.line_ids if sl.code == 'CNSS_PAT'), 0),
                            'total_charge_patronale': next(
                                (sl.total for sl in payslip.line_ids if sl.code == 'TOT_PAT'), 0),
                            'accident_travail': next((sl.total for sl in payslip.line_ids if sl.code == 'ACC_TRAV'), 0),
                            'tfp': next((sl.total for sl in payslip.line_ids if sl.code == 'TFP'), 0),
                            'assurance_group_patr': next(
                                (sl.total for sl in payslip.line_ids if sl.code == 'ASS_GRP_PAT'), 0),
                        })

        # After updating or creating the ordre_virement lines, change the state to 'confirmed'
        self.write({
            'state': 'confirmed',
            'date_virement': fields.Date.today(),  # Modifié pour utiliser Date au lieu de Datetime
        })

        # Champs supplémentaires

    total_netap = fields.Float(
        string='Total Net à Payer',
        compute='_compute_total_netap',
        store=True
    )

    @api.depends('ordre_virement_line_ids.netap')
    def _compute_total_netap(self):
        for record in self:
            record.total_netap = sum(line.netap for line in record.ordre_virement_line_ids)

    # Méthode pour convertir un montant en lettres

    currency_id = fields.Many2one('res.currency', string="Devise", default=lambda self: self.env.company.currency_id)

    total_netap_texte = fields.Char(
        string='Total en lettres',
        compute='_compute_total_netap_texte',
        store=True
    )

    @api.depends('total_netap', 'currency_id')
    def _compute_total_netap_texte(self):
        for record in self:
            if record.total_netap:
                # Séparer les dinars et millimes
                dinars = int(record.total_netap)
                millimes = round((record.total_netap - dinars) * 1000)  # convertir la partie décimale en millimes

                # Convertir la partie dinars en lettres
                dinars_en_lettres = num2words(dinars, lang='fr').replace('-', ' ').replace(',', ' ')

                # Convertir la partie millimes en lettres
                millimes_en_lettres = num2words(millimes, lang='fr').replace('-', ' ').replace(',', ' ')

                # Format final avec "dinars" et "millimes"
                record.total_netap_texte = f"{dinars_en_lettres} dinars et {millimes_en_lettres} millimes"

    def update(self):
        """
        Update ordre de virement by regenerating lines for the current month and year
        """
        self.ensure_one()
        if self.state == 'confirmed':
            try:
                mois = int(self.mois)
                annee = int(self.annee)
            except ValueError:
                raise UserError("Le mois et l'année doivent être des entiers valides.")

            if not mois or not annee:
                raise UserError("Le mois et l'année doivent être définis pour générer les lignes de virement.")

            # Format the date string correctly
            date_from = f'{annee}-{mois:02d}-01'  # Start of the month
            last_day = calendar.monthrange(annee, mois)[1]
            date_to = f'{annee}-{mois:02d}-{last_day}'

            # Fetch payslips for the given month and year
            valid_payslips = self.env['hr.payslip'].search([
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
                ('state', '=', 'done')
            ])

            # Delete all existing lines first
            self.ordre_virement_line_ids.unlink()

            # Update or create new ordre virement lines based on the payslips
            for payslip in valid_payslips:
                for line in payslip.line_ids:
                    if line.code == 'NETAP':  # Filter based on the specific line code (NETAP)
                        # Create new line with updated values
                        self.env['ordre.virement.line'].create({
                            'ordre_virement_id': self.id,
                            'employe_id': payslip.employee_id.id,
                            'netap': line.total,
                            'date_virement': fields.Date.context_today(self),
                            'salaire_brute': next((sl.total for sl in payslip.line_ids if sl.code == 'GROSS'), 0),
                            'cnss': next((sl.total for sl in payslip.line_ids if sl.code == 'CNSS'), 0),
                            'cavis': next((sl.total for sl in payslip.line_ids if sl.code == 'CAVIS'), 0),
                            'salaire_imposable': next((sl.total for sl in payslip.line_ids if sl.code == 'C_IMP'), 0),
                            'impot': next((sl.total for sl in payslip.line_ids if sl.code == 'IRPP'), 0),
                            'assurance_group': next((sl.total for sl in payslip.line_ids if sl.code == 'ASSG'), 0),
                            'pret': next((sl.total for sl in payslip.line_ids if sl.code == 'Pret'), 0),
                            'avance': next((sl.total for sl in payslip.line_ids if sl.code == 'Avance'), 0),
                            'cnss_patronale': next((sl.total for sl in payslip.line_ids if sl.code == 'CNSS_PAT'), 0),
                            'total_charge_patronale': next(
                                (sl.total for sl in payslip.line_ids if sl.code == 'TOT_PAT'), 0),
                            'accident_travail': next((sl.total for sl in payslip.line_ids if sl.code == 'ACC_TRAV'), 0),
                            'tfp': next((sl.total for sl in payslip.line_ids if sl.code == 'TFP'), 0),
                            'assurance_group_patr': next(
                                (sl.total for sl in payslip.line_ids if sl.code == 'ASS_GRP_PAT'), 0),
                        })

            # Keep the state as confirmed and set the date_virement to today
            self.date_virement = fields.Date.today()

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

        return True


class OrdreVirementLine(models.Model):
    _name = 'ordre.virement.line'
    _description = 'Ligne d\'Ordre de Virement'
    _order = 'matricule asc'

    ordre_virement_id = fields.Many2one('ordre.virement', string='Ordre de Virement', required=True, ondelete='cascade')
    employe_id = fields.Many2one('hr.employee', string='Nom et Prénom', required=True)
    matricule = fields.Char(string='Matricule', related='employe_id.identification_id', store=True, readonly=True)

    # Related fields
    bank = fields.Char(string='Banque', related='employe_id.bank_id', store=True)
    bank_account = fields.Char(string='Compte Bancaire', related='employe_id.bank_account', store=True)
    netap = fields.Float(string='Salaire Net à Payer')
    # montant = fields.Float(string='Montant')
    date_virement = fields.Date(string='Date de Virement', default=fields.Date.context_today)
    # nbj = fields.Float(string='Nombre de Jours', )
    # salaire_base = fields.Float(string='Salaire de Base', )
    salaire_brute = fields.Float(string='Salaire Brut', )
    cnss = fields.Float(string='CNSS', )
    cavis = fields.Float(string='CAVIS', )  # Updated field name
    total_charge = fields.Float(
        string='Total Charges',
        compute='_compute_total_charge',
        store=True
    )
    salaire_imposable = fields.Float(string='Salaire Imposable')
    impot = fields.Float(string='Impôt')
    assurance_group = fields.Float(string='Assurance Groupe')
    pret = fields.Float(string='Prêt', required=False)
    avance = fields.Float(string='Avance', required=False)
    cnss_patronale = fields.Float(string='CNSS Patronale')
    total_charge_patronale = fields.Float(string='Total Charge Patronale')
    accident_travail = fields.Float(string='Accident de Travail')
    tfp = fields.Float(string='TFP')
    assurance_group_patr = fields.Float(string='Assurance Groupe Patronale')

    total_netap = fields.Float(
        string='Total Net à Payer',
        related='ordre_virement_id.total_netap',
        store=False,
        readonly=True)

    @api.depends('cnss', 'cavis')
    def _compute_total_charge(self):
        for record in self:
            record.total_charge = record.cnss + record.cavis
