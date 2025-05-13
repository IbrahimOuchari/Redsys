from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
import calendar


class JournalPaie(models.Model):
    _name = 'journal.paie'
    _description = 'Journal Paie'

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
    mois = fields.Selection(
        selection=[
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
        ],
        string='Mois',
        required=True
    )
    # annee = fields.Integer(string='Année', required=True)
    annee = fields.Selection(
        selection='_get_years',
        string='Année',
        required=True,
        default=lambda self: str(datetime.datetime.now().year)
    )
    edit_date = fields.Date(string='Éditer le')
    journal_paie_line_ids = fields.One2many('journal.paie.line', 'journal_paie_id', string='Lignes des Journal Paie',
                                            readonly=True)
    logo = fields.Binary(string='Logo', related='company_id.logo',
                         store=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    def action_manual_state_change(self):
        for record in self:
            record.state = 'draft'

    def action_journal_lock(self):
        return self.write({'state': 'close'})

    def generate_journal_paie_lines(self):
        """ Generate the payroll journal lines based on the hr.payslip model and its lines """
        try:
            mois = int(self.mois)
            annee = int(self.annee)
        except ValueError:
            raise UserError("Le mois et l'année doivent être des entiers valides.")

        if not mois or not annee:
            raise UserError("Le mois et l'année doivent être définis pour générer les lignes de paie.")

        # Format the date correctly - get the last day of the month
        date_from = f'{annee}-{mois:02d}-01'  # Start of the month

        # Calculate the last day of the month correctly
        last_day = calendar.monthrange(annee, mois)[1]
        date_to = f'{annee}-{mois:02d}-{last_day}'  # Last day of the month

        # Fetch payslips for the given month and year
        valid_payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', '=', 'done')
        ])

        # Collect valid employee IDs from payslips
        valid_employee_ids = valid_payslips.mapped('employee_id.id')

        # Remove existing journal lines for employees without valid payslips
        existing_lines = self.env['journal.paie.line'].search([
            ('journal_paie_id', '=', self.id),
            ('employe_id', 'not in', valid_employee_ids)
        ])
        existing_lines.unlink()

        # Update or create new journal lines based on the payslips
        for payslip in valid_payslips:
            # Calculate total worked days
            nbj = sum(wd.number_of_days for wd in payslip.worked_days_line_ids)

            # Initialize congep to 0
            congep = 0

            # Initialize values dictionary
            values = {
                'employe_id': payslip.employee_id.id,
                'matricule': payslip.employee_id.identification_id,
            }

            # Map payslip line codes to field names
            code_to_field = {
                'BASE': 'salaire_base',
                'GROSS': 'salaire_brute',
                # 'BRUT_M': 'brut_m',
                'BRUTJT': 'brutjt',
                'CNSS': 'cnss',
                'CAVIS': 'cavis',
                'C_IMP': 'c_imp',
                'IRPP': 'irpp',
                'CSS': 'css',
                'IMPOT': 'impot',
                'ASSG': 'assurance_group',
                'Pret': 'pret',
                'Avance': 'avance',
                'CNSS_PAT': 'cnss_patronale',
                'TOT_PAT': 'total_charge_patronale',
                'ACC_TRAV': 'accident_travail',
                'TFP': 'tfp',
                'ASS_GRP_PAT': 'assurance_group_patr',
                'NETAP': 'netap',
                'congep': 'congep'
            }

            # Fill in values from payslip lines
            for line in payslip.line_ids:
                if line.code in code_to_field:
                    values[code_to_field[line.code]] = line.total
                    # If it's a congep line, store the value
                    if line.code == 'congep':
                        congep = line.total

            # Adjust nbj by subtracting congep
            values['nbj'] = nbj - congep if congep else nbj

            # Search for existing journal line
            journal_line = self.env['journal.paie.line'].search([
                ('journal_paie_id', '=', self.id),
                ('employe_id', '=', payslip.employee_id.id)
            ], limit=1)

            if journal_line:
                # Update existing line
                journal_line.write(values)
            else:
                # Create new line
                values.update({
                    'journal_paie_id': self.id,
                })
                self.env['journal.paie.line'].create(values)

        # Update journal state to confirmed after processing
        self.write({'state': 'confirmed'})

    def update(self):
        """
        Update payroll journal by regenerating lines for the current month and year
        """
        self.ensure_one()
        if self.state == 'confirmed':
            try:
                mois = int(self.mois)
                annee = int(self.annee)
            except ValueError:
                raise UserError("Le mois et l'année doivent être des entiers valides.")

            if not mois or not annee:
                raise UserError("Le mois et l'année doivent être définis pour générer les lignes de paie.")

            # Format the date correctly - get the last day of the month
            date_from = f'{annee}-{mois:02d}-01'  # Start of the month

            # Calculate the last day of the month correctly
            last_day = calendar.monthrange(annee, mois)[1]
            date_to = f'{annee}-{mois:02d}-{last_day}'  # Last day of the month

            # Fetch payslips for the given month and year
            valid_payslips = self.env['hr.payslip'].search([
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
                ('state', '=', 'done')
            ])

            # Delete all existing lines first
            self.journal_paie_line_ids.unlink()

            # Update or create new journal lines based on the payslips
            for payslip in valid_payslips:
                # Calculate total worked days
                nbj = sum(wd.number_of_days for wd in payslip.worked_days_line_ids)

                # Initialize congep to 0
                congep = 0

                # Initialize values dictionary
                values = {
                    'journal_paie_id': self.id,
                    'employe_id': payslip.employee_id.id,
                    'matricule': payslip.employee_id.identification_id,
                }

                # Map payslip line codes to field names
                code_to_field = {
                    'BASE': 'salaire_base',
                    'GROSS': 'salaire_brute',
                    # 'BRUT_M': 'brut_m',
                    'BRUTJT': 'brutjt',
                    'CNSS': 'cnss',
                    'CAVIS': 'cavis',
                    'C_IMP': 'c_imp',
                    'IRPP': 'irpp',
                    'CSS': 'css',
                    'IMPOT': 'impot',
                    'ASSG': 'assurance_group',
                    'Pret': 'pret',
                    'Avance': 'avance',
                    'CNSS_PAT': 'cnss_patronale',
                    'TOT_PAT': 'total_charge_patronale',
                    'ACC_TRAV': 'accident_travail',
                    'TFP': 'tfp',
                    'ASS_GRP_PAT': 'assurance_group_patr',
                    'NETAP': 'netap',
                    'congep': 'congep'
                }

                # Fill in values from payslip lines
                for line in payslip.line_ids:
                    if line.code in code_to_field:
                        values[code_to_field[line.code]] = line.total
                        # If it's a congep line, store the value
                        if line.code == 'congep':
                            congep = line.total

                # Adjust nbj by subtracting congep
                values['nbj'] = nbj - congep if congep else nbj

                # Create new line with updated values
                self.env['journal.paie.line'].create(values)

            # Keep the state as confirmed
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        return True

    def action_save(self):
        """Save changes and set state back to confirmed"""
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'confirmed'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Succès',
                    'message': 'Les modifications ont été sauvegardées',
                    'sticky': False,
                    'type': 'success',
                }
            }
        return True

    def get_total_columns(self):
        """Calculate totals for each column in journal paie lines"""
        totals = {}
        column_names = [
            'salaire_base', 'salaire_brute', 'brutjt', 'nbj', 'congep',
            'cnss', 'cavis', 'total_charge', 'c_imp', 'irpp', 'css',
            'impot', 'assurance_group', 'pret', 'avance', 'cnss_patronale',
            'total_charge_patronale', 'accident_travail', 'tfp',
            'assurance_group_patr', 'netap'
        ]

        for column in column_names:
            totals[column] = sum(line[column] for line in self.journal_paie_line_ids)

        return totals

    def _compute_total_charge(self):
        """Calculate total charge across all journal paie lines"""
        for record in self:
            record.total_charge = sum(line.total_charge for line in record.journal_paie_line_ids)

    total_charge = fields.Float(
        string='Total Charge',
        compute='_compute_total_charge',
        store=False
    )


class JournalPaieLine(models.Model):
    _name = 'journal.paie.line'
    _description = 'Ligne de Journal Paie'
    _order = 'matricule asc'

    journal_paie_id = fields.Many2one('journal.paie', string='Journal Paie', required=True, ondelete='cascade')

    employe_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Nom et Prénom',
        required=True
    )
    matricule = fields.Char(
        string='Matricule',
        related='employe_id.identification_id',
        store=True,
        readonly=True
    )
    nbj = fields.Float(string='Nombre de Jours', )
    congep = fields.Float(string='Congés Payés', )
    salaire_base = fields.Float(string='Salaire de Base', )
    salaire_brute = fields.Float(string='Salaire Brut', )
    # brut_m = fields.Float(string='Salaire Brut Mensuel',)
    brutjt = fields.Float(string='Salaire Brut Base des Jours Travaillés', )
    cnss = fields.Float(string='CNSS', )
    cavis = fields.Float(string='CAVIS', )  # Updated field name
    total_charge = fields.Float(
        string='Total Charges',
        compute='_compute_total_charge',
        store=True
    )
    # salaire_imposable = fields.Float(string='Salaire Imposable' )
    c_imp = fields.Float(string='Salaire Imposable Mensuel')
    irpp = fields.Float(string='IRPP Mensuel')
    css = fields.Float(string='Contribution Sociale de Solidarité Mensuelle')
    impot = fields.Float(
        string='Impôt',
        compute='_compute_impot',
        store=True
    )
    assurance_group = fields.Float(string='Assurance Groupe')
    pret = fields.Float(string='Prêt', required=False)
    avance = fields.Float(string='Avance', required=False)
    cnss_patronale = fields.Float(string='CNSS Patronale')
    total_charge_patronale = fields.Float(string='Total Charge Patronale')
    accident_travail = fields.Float(string='Accident de Travail')
    tfp = fields.Float(string='TFP')
    assurance_group_patr = fields.Float(string='Assurance Groupe Patronale')
    netap = fields.Float(string='Salaire Net à Payer')

    @api.depends('cnss', 'cavis')
    def _compute_total_charge(self):
        for record in self:
            record.total_charge = record.cnss + record.cavis

    @api.depends('irpp', 'css')
    def _compute_impot(self):
        for record in self:
            record.impot = record.irpp + record.css

    total_general = fields.Float(
        string='Total Général',
        compute='_compute_total_general',
        store=True
    )

    @api.depends('salaire_base', 'salaire_brute', 'brutjt', 'cnss', 'cavis',
                 'c_imp', 'irpp', 'css', 'impot', 'assurance_group',
                 'pret', 'avance', 'cnss_patronale', 'total_charge_patronale',
                 'accident_travail', 'tfp', 'assurance_group_patr', 'netap')
    def _compute_total_general(self):
        for record in self:
            record.total_general = (
                    record.salaire_base +
                    record.salaire_brute +
                    record.brutjt +
                    record.cnss +
                    record.cavis +
                    record.c_imp +
                    record.irpp +
                    record.css +
                    record.impot +
                    record.assurance_group +
                    record.pret +
                    record.avance +
                    record.cnss_patronale +
                    record.total_charge_patronale +
                    record.accident_travail +
                    record.tfp +
                    record.assurance_group_patr +
                    record.netap
            )