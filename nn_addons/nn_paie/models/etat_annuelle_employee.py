from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)



class EtatAnnuelleEmployee(models.Model):
    _name = 'etat.annuelle.employee'
    _description = 'État Annuelle Des Employees'
    _order = 'name asc'

    name = fields.Integer(string='Séquence', default=1)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('annual.employee.report.seq') or '/'
        res_id = super(EtatAnnuelleEmployee, self).create(vals)
        return res_id

    @api.model
    def _get_years(self):
        current_year = datetime.now().year
        years = []
        for year in range(current_year - 5, current_year + 6):
            years.append((str(year), str(year)))
        return years

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('close', 'lock'),
    ], string="Statut", default='draft')

    annee = fields.Selection(
        selection='_get_years',
        string='Année',
        required=True,
        default=lambda self: str(datetime.now().year)
    )
    annual_employee_line_ids = fields.One2many('etat.annuelle.employee.line', 'etat_annuelle_employee_id',
                                               string='Lignes des Employés', readonly=False)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    logo = fields.Binary(string='Logo', related='company_id.logo',
                         store=True)
    def action_etat_lock(self):
        return self.write({'state': 'close'})


    def generate_employee_lines(self):
        """Generate the employee lines based on payslips for the selected year"""
        self.ensure_one()
        try:
            year = int(self.annee)
        except ValueError:
            raise UserError("L'année doit être un entier valide.")

        if not year:
            raise UserError("L'année doit être définie pour générer les lignes.")

        date_from = datetime(year, 1, 1).date()
        date_to = datetime(year, 12, 31).date()

        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', 'in', ['done', 'paid'])
        ])

        # Filtrer uniquement les employés avec des contrats imposables
        filtered_payslips = payslips.filtered(lambda p: p.contract_id.imposition == 'imp')
        employees = filtered_payslips.mapped('employee_id')

        existing_lines = self.env['etat.annuelle.employee.line'].search([
            ('etat_annuelle_employee_id', '=', self.id),
            ('employe_id', 'not in', employees.ids)
        ])
        existing_lines.unlink()

        for employee in employees:
            employee_payslips = filtered_payslips.filtered(lambda p: p.employee_id.id == employee.id)

            # Calcul du total C_IMPDED
            total_c_impded = sum(
                line.total for slip in employee_payslips
                for line in slip.line_ids.filtered(lambda l: l.code == 'C_IMPDED')
            )

            # Récupérer le contrat actif de l'employé
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'open')
            ], limit=1)

            # Calcul du salaire imposable
            if contract and contract.base_tranche:
                total_salaire_imposable = total_c_impded / contract.base_tranche
            else:
                total_salaire_imposable = 0

            total_impot = sum(
                line.total for slip in employee_payslips
                for line in slip.line_ids.filtered(lambda l: l.code == 'IRPP')
            )

            # total_cnss = sum(
            #     line.total for slip in employee_payslips
            #     for line in slip.line_ids.filtered(lambda l: l.code == 'CNSS')
            # )

            values = {
                'etat_annuelle_employee_id': self.id,
                'employe_id': employee.id,
                'matricule': employee.identification_id,
                'salaire_imposable': total_salaire_imposable,
                'impot': total_impot,
                # 'cnss': total_cnss,
            }

            employee_line = self.env['etat.annuelle.employee.line'].search([
                ('employe_id', '=', employee.id),
                ('etat_annuelle_employee_id', '=', self.id)
            ], limit=1)

            if employee_line:
                employee_line.write(values)
            else:
                self.env['etat.annuelle.employee.line'].create(values)

        self.write({'state': 'confirmed'})



    def update(self):
        """Update annual employee report by regenerating lines for the current year"""
        self.ensure_one()
        if self.state != 'confirmed':
            return True

        try:
            year = int(self.annee)
        except ValueError:
            raise UserError("L'année doit être un entier valide.")

        if not year:
            raise UserError("L'année doit être définie pour mettre à jour les lignes.")

        date_from = datetime(year, 1, 1).date()
        date_to = datetime(year, 12, 31).date()

        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', 'in', ['done', 'paid'])
        ])

        self.annual_employee_line_ids.unlink()

        # Filtrer uniquement les employés avec des contrats imposables
        filtered_payslips = payslips.filtered(lambda p: p.contract_id.imposition == 'imp')
        employees = filtered_payslips.mapped('employee_id')

        for employee in employees:
            employee_payslips = filtered_payslips.filtered(lambda p: p.employee_id.id == employee.id)

            # Calcul du total C_IMPDED
            total_c_impded = sum(
                line.total for slip in employee_payslips
                for line in slip.line_ids.filtered(lambda l: l.code == 'C_IMPDED')
            )

            # Récupérer le contrat actif de l'employé
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'open')
            ], limit=1)

            # Calcul du salaire imposable
            if contract and contract.base_tranche:
                total_salaire_imposable = total_c_impded / contract.base_tranche
            else:
                total_salaire_imposable = 0

            total_impot = sum(
                line.total for slip in employee_payslips
                for line in slip.line_ids.filtered(lambda l: l.code == 'IRPP')
            )

            # total_cnss = sum(
            #     line.total for slip in employee_payslips
            #     for line in slip.line_ids.filtered(lambda l: l.code == 'CNSS')
            # )
            total_css = sum(
                line.total for slip in employee_payslips
                for line in slip.line_ids.filtered(lambda l: l.code == 'CSS')
            )

            values = {
                'etat_annuelle_employee_id': self.id,
                'employe_id': employee.id,
                'matricule': employee.identification_id,
                'salaire_imposable': total_salaire_imposable,
                'impot': total_impot,
                # 'cnss': total_cnss,
                'css': total_css,
            }

            self.env['etat.annuelle.employee.line'].create(values)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_manual_state_change(self):
        for record in self:
            record.state = 'draft'



    has_selected_lines = fields.Boolean(string='Has Selected Lines', compute='_compute_has_selected_lines')

    @api.depends('annual_employee_line_ids.selected')
    def _compute_has_selected_lines(self):
        for record in self:
            record.has_selected_lines = any(record.annual_employee_line_ids.mapped('selected'))

    def get_selected_lines(self):
        """Get only selected employee lines"""
        self.ensure_one()
        return self.annual_employee_line_ids.filtered(lambda l: l.selected)

    def toggle_employee_selection(self, line_id, selected):
        """Toggle selection state of an employee line"""
        line = self.env['etat.annuelle.employee.line'].browse(line_id)
        if line:
            line.write({'selected': selected})
            self.env.cr.commit()  # Force commit pour sauvegarder immédiatement
            _logger.info("Selection modifiée pour la ligne %s: %s", line_id, selected)
        return True

    def print_report(self):
        """Print report for selected employee lines"""
        self.ensure_one()

        # Force save before checking selections
        self.env.cr.commit()

        # Récupérer les lignes sélectionnées
        selected_lines = self.annual_employee_line_ids.filtered(lambda l: l.selected)

        _logger.info("Vérification des sélections avant impression:")
        for line in self.annual_employee_line_ids:
            _logger.info("Ligne %s (employé %s): selected = %s",
                         line.id, line.employe_id.name, line.selected)

        if not selected_lines:
            raise UserError("Veuillez sélectionner au moins un employé pour imprimer le rapport.")

        data = {
            'ids': self.ids,
            'model': 'etat.annuelle.employee',
            'form': {
                'selected_line_ids': selected_lines.ids,
                'company_id': self.company_id.id,
                'year': self.annee,
            }
        }

        return self.env.ref('nn_paie.report_etat_annuelle_employee_specific').with_context(
            selected_lines=selected_lines.ids
        ).report_action(self, data=data)

    def get_report_values(self, docids, data=None):
        """Get values for the report template"""
        if not data:
            data = {}

        docs = self.browse(docids)
        selected_line_ids = self.env.context.get('selected_lines', [])

        if selected_line_ids:
            for doc in docs:
                doc.annual_employee_line_ids = doc.annual_employee_line_ids.filtered(
                    lambda l: l.id in selected_line_ids
                )

        return {
            'doc_ids': docs.ids,
            'doc_model': 'etat.annuelle.employee',
            'docs': docs,
            'data': data,
            'selected_lines': selected_line_ids,
        }


class EtatAnnuelleEmployeeLine(models.Model):
    _name = 'etat.annuelle.employee.line'
    _description = 'État Annuelle Des Employees Line'
    _order = 'matricule asc'

    etat_annuelle_employee_id = fields.Many2one('etat.annuelle.employee', string='État Annuelle Des Employees',
                                                required=True, ondelete='cascade')

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
    salaire_imposable = fields.Float(string='Salaire Imposable')
    impot = fields.Float(string='Impôt')
    cnss = fields.Float(string='CNSS')
    css = fields.Float(string='CSS')

    # New computed field for impot_du
    @api.depends('salaire_imposable', 'impot')
    def _compute_impot_du(self):
        for record in self:
            record.impot_du = record.salaire_imposable + record.impot

    impot_du = fields.Float(
        string='Impôt Dû',
        compute='_compute_impot_du',
        store=True,
    )
    # Changed selected field to store its value
    selected = fields.Boolean(string='Sélectionné', default=False, store=True)
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        """Override create to ensure selected is stored"""
        if 'selected' not in vals:
            vals['selected'] = False
        return super(EtatAnnuelleEmployeeLine, self).create(vals)

    def write(self, vals):
        """Override write to ensure selected changes are stored"""
        res = super(EtatAnnuelleEmployeeLine, self).write(vals)
        if 'selected' in vals:
            self.env.cr.commit()  # Force commit pour la sélection
            _logger.info("Sauvegarde de la sélection pour les lignes %s: %s",
                         self.ids, vals['selected'])
        return res


