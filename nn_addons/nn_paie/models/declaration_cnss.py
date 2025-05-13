from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime


class DeclarationCNSS(models.Model):
    _name = 'declaration.cnss'
    _description = 'Déclaration CNSS'
    _order = 'annee, trimestre'

    @api.model
    def _get_years(self):
        current_year = datetime.datetime.now().year
        years = []
        # Générer une liste d'années (5 ans avant l'année courante jusqu'à 5 ans après)
        for year in range(current_year - 5, current_year + 6):
            years.append((str(year), str(year)))
        return years

    name = fields.Char(string="Nom", compute="_compute_name", store=True)
    trimestre = fields.Selection(
        selection=[
            ('T1', 'Trimestre 1 (Janvier, Février, Mars)'),
            ('T2', 'Trimestre 2 (Avril, Mai, Juin)'),
            ('T3', 'Trimestre 3 (Juillet, Août, Septembre)'),
            ('T4', 'Trimestre 4 (Octobre, Novembre, Décembre)'),
        ],
        string="Trimestre",
        required=True
    )

    # annee = fields.Integer(string='Année', required=True)
    annee = fields.Selection(
        selection='_get_years',
        string='Année',
        required=True,
        default=lambda self: str(datetime.datetime.now().year)
    )
    declaration_cnss_line_ids = fields.One2many(
        'declaration.cnss.line', 'declaration_cnss_id',
        string="Lignes Déclaration CNSS", readonly=True
    )
    state = fields.Selection(
        [('draft', 'Brouillon'), ('confirmed', 'Confirmé'),('close', 'lock'),],
        string="Statut", default='draft'
    )
    logo = fields.Binary(string='Logo', related='company_id.logo',
                         store=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    employe_id = fields.Many2one('hr.employee', string='Employé', required=False)
    code_exploitation_cnss = fields.Char(related="company_id.code_exploitation_cnss",string='Code Exploitation CNSS')

    def action_manual_state_change(self):
        for record in self:
            record.state = 'draft'

    @api.depends('trimestre', 'annee')
    def _compute_name(self):
        for record in self:
            record.name = f"CNSS {record.annee} {record.trimestre}"

    def action_cnss_lock(self):
        return self.write({'state': 'close'})





    def generate_cnss_lines(self):
        if not self.trimestre or not self.annee:
            raise UserError("Veuillez définir l'année et le trimestre avant de générer les lignes.")

        # Mapping des trimestres aux mois
        trimester_months = {
            'T1': ['01', '02', '03'],
            'T2': ['04', '05', '06'],
            'T3': ['07', '08', '09'],
            'T4': ['10', '11', '12'],
        }

        # Supprimer les lignes existantes
        self.declaration_cnss_line_ids.unlink()

        # Récupérer tous les employés avec des contrats imposables
        employees = self.env['hr.employee'].search([])

        for employee in employees:
            # Vérifier si l'employé a un contrat imposable
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'open'),
                ('imposition', '=', 'imp')  # Filtrer uniquement les contrats imposables
            ], limit=1)

            if not contract:
                continue  # Passer à l'employé suivant si pas de contrat imposable

            monthly_brut_m = {month: 0.0 for month in trimester_months[self.trimestre]}
            has_payslip = False

            # Calculer le BRUT_M pour chaque mois du trimestre
            for month in trimester_months[self.trimestre]:
                date_from = f"{self.annee}-{month}-01"
                last_day = \
                    str(datetime.date(int(self.annee), int(month), 1).replace(day=1).replace(
                        month=int(month) + 1).replace(
                        day=1) - datetime.timedelta(days=1)).split('-')[2]
                date_to = f"{self.annee}-{month}-{last_day}"

                # Rechercher toutes les fiches de paie du mois pour cet employé
                payslips = self.env['hr.payslip'].search([
                    ('employee_id', '=', employee.id),
                    ('date_from', '>=', date_from),
                    ('date_to', '<=', date_to),
                    ('state', '=', 'done')
                ])

                if payslips:
                    has_payslip = True
                    # Sommer tous les BRUT_M du mois
                    for payslip in payslips:
                        for line in payslip.line_ids:
                            if line.code == 'BRUT_M':
                                monthly_brut_m[month] += line.total

            # Créer la ligne de déclaration si l'employé a au moins une fiche de paie
            if has_payslip:
                self.env['declaration.cnss.line'].create({
                    'declaration_cnss_id': self.id,
                    'employe_id': employee.id,
                    'numer_chez_employe': employee.identification_id,
                    'category': '',
                    'brut_m_month1': monthly_brut_m[trimester_months[self.trimestre][0]],
                    'brut_m_month2': monthly_brut_m[trimester_months[self.trimestre][1]],
                    'brut_m_month3': monthly_brut_m[trimester_months[self.trimestre][2]],
                })

        self.state = 'confirmed'

    def action_update_declaration(self):
        if not self.trimestre or not self.annee:
            raise UserError("Veuillez définir l'année et le trimestre avant de générer les lignes.")

        # Mapping des trimestres aux mois
        trimester_months = {
            'T1': ['01', '02', '03'],
            'T2': ['04', '05', '06'],
            'T3': ['07', '08', '09'],
            'T4': ['10', '11', '12'],
        }

        # Supprimer les lignes existantes
        self.declaration_cnss_line_ids.unlink()

        # Récupérer tous les employés avec des contrats imposables
        employees = self.env['hr.employee'].search([])

        for employee in employees:
            # Vérifier si l'employé a un contrat imposable
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'open'),
                ('imposition', '=', 'imp')  # Filtrer uniquement les contrats imposables
            ], limit=1)

            if not contract:
                continue  # Passer à l'employé suivant si pas de contrat imposable

            monthly_brut_m = {month: 0.0 for month in trimester_months[self.trimestre]}
            has_payslip = False

            # Calculer le BRUT_M pour chaque mois du trimestre
            for month in trimester_months[self.trimestre]:
                date_from = f"{self.annee}-{month}-01"
                last_day = str(datetime.date(int(self.annee), int(month), 1).replace(day=1).replace(
                    month=int(month) + 1).replace(day=1) - datetime.timedelta(days=1)).split('-')[2]
                date_to = f"{self.annee}-{month}-{last_day}"

                # Rechercher toutes les fiches de paie du mois pour cet employé
                payslips = self.env['hr.payslip'].search([
                    ('employee_id', '=', employee.id),
                    ('date_from', '>=', date_from),
                    ('date_to', '<=', date_to),
                    ('state', '=', 'done')
                ])

                if payslips:
                    has_payslip = True
                    # Sommer tous les BRUT_M du mois
                    for payslip in payslips:
                        for line in payslip.line_ids:
                            if line.code == 'BRUT_M':
                                monthly_brut_m[month] += line.total

            # Créer la ligne de déclaration si l'employé a au moins une fiche de paie
            if has_payslip:
                self.env['declaration.cnss.line'].create({
                    'declaration_cnss_id': self.id,
                    'employe_id': employee.id,
                    'numer_chez_employe': employee.identification_id,
                    'category': '',
                    'brut_m_month1': monthly_brut_m[trimester_months[self.trimestre][0]],
                    'brut_m_month2': monthly_brut_m[trimester_months[self.trimestre][1]],
                    'brut_m_month3': monthly_brut_m[trimester_months[self.trimestre][2]],
                })

        return True

    def generate_cnss_txt_file(self):
        """
        Generate a TXT file for CNSS declaration with custom format:

        """
        from io import StringIO
        import base64
        import unicodedata

        # Create a buffer for writing the TXT file
        file_content = StringIO()

        # Get company information
        company = self.company_id
        mat_cnss_company = company.mat_cnss or ''
        code_exploitation = self.code_exploitation_cnss or '0000'  # Get code exploitation
        # Get year and trimester information
        year = self.annee
        trimester = self.trimestre[1]  # Extract the trimester number

        # Process each employee record
        page_number = 1
        line_number = 0

        for line in self.declaration_cnss_line_ids:
            line_number += 1
            # Reset line number to 1 after every 12 lines
            if line_number > 12:
                line_number = 1
                page_number += 1

            employee = line.employe_id

            # Get employee details
            employee_cnss = line.matricule or '00000000'

            # Format employee name: convert to uppercase
            employee_name = (employee.name or '').upper()

            # Remove accents from employee name
            normalized_name = unicodedata.normalize('NFKD', employee_name)
            employee_name = ''.join([c for c in normalized_name if not unicodedata.combining(c)])

            # Pad/truncate to 60 characters
            employee_name = employee_name.ljust(60)[:60]

            employee_cin = line.employe_id.num_cin or ''

            # Calculate total for the employee (sum of all three months)
            employee_total = line.total

            # Format the total: remove decimal point and pad with zeros to 10 digits
            # First multiply by 1000 to get 3 decimal places, then convert to integer to remove decimal point
            total_as_int = int(employee_total * 1000)
            # Format as string with leading zeros to make it 10 digits
            formatted_total = str(total_as_int).zfill(10)

            # Add 10 empty spaces after the total
            empty_space = ' ' * 10

            # Format page number to 3 digits with leading zeros
            formatted_page_number = str(page_number).zfill(3)

            # Format line number to 2 digits with leading zeros
            formatted_line_number = str(line_number).zfill(2)

            # Format the record according to specified format with formatted page and line numbers
            record = f"{mat_cnss_company}{code_exploitation}{trimester}{year}{formatted_page_number}{formatted_line_number}{employee_cnss}{employee_name}{employee_cin}{formatted_total}{empty_space}"

            # Add employee line to file
            file_content.write(record + "\n")

            # No longer increment page number here - it's now handled in the line_number reset logic above

        # Convert content to base64 for download
        file_data = base64.b64encode(file_content.getvalue().encode('utf-8'))

        # Create the new filename according to the requested format
        new_filename = f'DS{mat_cnss_company}{code_exploitation}.{trimester}{year}'

        # Create attachment with the new filename
        attachment = self.env['ir.attachment'].create({
            'name': new_filename + '.txt',
            'type': 'binary',
            'datas': file_data,
            'store_fname': new_filename + '.txt',
            'mimetype': 'text/plain',
            'res_model': self._name,
            'res_id': self.id,
        })

        # Return action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def amount_to_text(self, amount):
        """Convertit un montant numérique en texte en français avec millimes"""

        if amount == 0:
            return 'zéro'

        def _convert_nn(val):
            """ Convertit un nombre < 100 en texte """
            unites = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix', 'onze',
                      'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf']
            dizaines = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante', 'soixante-dix', 'quatre-vingt',
                        'quatre-vingt-dix']

            if val < 20:
                return unites[val]
            if val == 71:
                return 'soixante et onze'
            if val == 80:
                return 'quatre-vingts'
            if val == 91:
                return 'quatre-vingt-onze'

            unite = val % 10
            dizaine = val // 10

            if dizaine == 1:
                return unites[val]
            elif dizaine == 7:
                if unite == 1:
                    return dizaines[dizaine] + ' et ' + unites[unite]
                else:
                    return dizaines[dizaine] + '-' + unites[10 + unite]
            elif dizaine == 9:
                if unite == 0:
                    return dizaines[dizaine]
                else:
                    return dizaines[dizaine - 1] + '-' + unites[10 + unite]
            elif unite == 0:
                if dizaine == 8:
                    return dizaines[dizaine] + 's'
                return dizaines[dizaine]
            elif unite == 1 and dizaine != 8:
                return dizaines[dizaine] + ' et ' + unites[unite]
            else:
                return dizaines[dizaine] + '-' + unites[unite]

        def _convert_nnn(val):
            """ Convertit un nombre < 1000 en texte """
            centaine = val // 100
            reste = val % 100

            if centaine == 0:
                return _convert_nn(reste)
            elif centaine == 1:
                if reste == 0:
                    return 'cent'
                else:
                    return 'cent ' + _convert_nn(reste)
            else:
                if reste == 0:
                    return _convert_nn(centaine) + ' cents'
                else:
                    return _convert_nn(centaine) + ' cent ' + _convert_nn(reste)

        # Arrondir à 3 décimales et séparer les parties entière et décimale
        amount = round(amount, 3)
        int_part = int(amount)
        decimal_part = int(round((amount - int_part) * 1000))

        # Convertir la partie entière
        result = ""
        millions = int_part // 1000000
        thousands = (int_part % 1000000) // 1000
        units = int_part % 1000

        if millions > 0:
            if millions == 1:
                result += 'un million '
            else:
                result += _convert_nnn(millions) + ' millions '

        if thousands > 0:
            if thousands == 1:
                result += 'mille '
            else:
                result += _convert_nnn(thousands) + ' mille '
        else:
            if units > 0 and millions > 0:
                result += 'et '

        if units > 0:
            result += _convert_nnn(units)

        # Ajout de la partie décimale (millimes)
        if decimal_part > 0:
            result += ' virgule ' + _convert_nnn(decimal_part) + ' millimes'

        return result

class DeclarationCNSSLine(models.Model):
    _name = 'declaration.cnss.line'
    _description = 'Ligne Déclaration CNSS'
    _order = 'matricule asc'

    declaration_cnss_id = fields.Many2one(
        'declaration.cnss', string="Déclaration CNSS",
        required=True, ondelete='cascade'
    )
    employe_id = fields.Many2one('hr.employee', string='Employé', required=True)
    matricule = fields.Char(related='employe_id.matricule_cnss',string='Matricule CNSS', readonly=True)
    numer_chez_employe = fields.Char(string='Numéro chez Employé', readonly=True)
    category = fields.Char(string='Catégorie')  # Placeholder pour ajouter une logique future
    # brutjt_total = fields.Float(string='Total BRUTJT', readonly=True)


    # Champs pour les montants BRUT_M mensuels
    brut_m_month1 = fields.Float(string='BRUT_M Mois 1', readonly=True)
    brut_m_month2 = fields.Float(string='BRUT_M Mois 2', readonly=True)
    brut_m_month3 = fields.Float(string='BRUT_M Mois 3', readonly=True)



    @api.depends('brut_m_month1', 'brut_m_month2', 'brut_m_month3')
    def _compute_total(self):
        for record in self:
            record.total = record.brut_m_month1 + record.brut_m_month2 + record.brut_m_month3

    @api.depends('declaration_cnss_id.trimestre')
    def _compute_month_labels(self):
        month_mapping = {
            'T1': ['Janvier', 'Février', 'Mars'],
            'T2': ['Avril', 'Mai', 'Juin'],
            'T3': ['Juillet', 'Août', 'Septembre'],
            'T4': ['Octobre', 'Novembre', 'Décembre']
        }
        for record in self:
            trimester = record.declaration_cnss_id.trimestre
            if trimester:
                months = month_mapping[trimester]
                record.month1_label = months[0]
                record.month2_label = months[1]
                record.month3_label = months[2]

    month1_label = fields.Char(compute='_compute_month_labels', string='Mois 1')
    month2_label = fields.Char(compute='_compute_month_labels', string='Mois 2')
    month3_label = fields.Char(compute='_compute_month_labels', string='Mois 3')
    total = fields.Float(string='Total Trimestre', compute='_compute_total', store=True)

