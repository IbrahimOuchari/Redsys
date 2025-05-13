
from odoo import api, fields, models, _
from datetime import date


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    schedule_pay = fields.Selection([
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
        ('semi-annually', 'Semestriel'),
        ('annually', 'Annuel'),
        ('weekly', 'Hebdomadaire'),
        ('bi-weekly', 'Bihebdomadaire'),
        ('bi-monthly', 'Bimensuel'),
    ], string='Scheduled Pay', index=True, default='monthly',
        help="Defines the frequency of the wage payment.")
    resource_calendar_id = fields.Many2one(required=True, help="Employee's working schedule.")
    base_nombre_jours = fields.Integer(' Base Nombre De Jours', size=64)
    base_nombre_heure = fields.Float(' Base Nombre D\'heures', size=64)
    base_tranche = fields.Integer(' Base Tranche', size=64, default=12)

    ind_presence = fields.Monetary(string='Prime de Présence')
    ind_transport = fields.Monetary(string='Prime de Transport')
    ind_panier = fields.Monetary(string='Prime de Panier')
    ind_responsabilite = fields.Monetary(string='Prime Responsabilité')
    prime_divers = fields.Monetary(string='Prime Divers')
    autre_prime = fields.Monetary(string='Autre Prime')

    assurance_groupe = fields.Boolean(string="Adhésion Assurance Groupe", default=False)
    montant_assurance_groupe = fields.Monetary(string='Assurance Groupe')

    interet_logement = fields.Boolean(string="Adhésion Programme Premier Logement", default=False)
    montant_interet_logement = fields.Monetary(string='Intérêt premier logement')

    assurance_vie = fields.Boolean(string="Adhésion Epargne Assurance Vie", default=False)
    montant_assurance_vie = fields.Monetary(string='Epargne Assurance Vie')
    imposition = fields.Selection(
        related='struct_id.imposition',
        string='Imposition',
        store=True,
    )
    line_ids = fields.One2many('hr.contract.salary.line', 'contract_id', string='Salary Lines', readonly=True)
    salary_brut = fields.Float(string='Salaire Brut Contractuel', compute='_compute_salary_values', store=True, digits='Payroll')
    salary_net = fields.Float(string='Salaire Net', compute='_compute_salary_values', store=True, digits='Payroll')

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):
        return self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1)[attribute]

    def set_attribute_value(self, code, active):
        for contract in self:
            if active:
                value = self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:
                contract[code] = 0.0

    def compute_contract_salary(self):
        self.ensure_one()

        # Supprimer les anciennes lignes du nouveau modèle
        self.env['hr.contract.salary.line'].search([('contract_id', '=', self.id)]).unlink()

        if not self.struct_id:
            return False

        # Créer un bulletin de paie temporaire
        payslip = self.env['hr.payslip'].create({
            'name': _('Salary Simulation for %s') % self.employee_id.name,
            'employee_id': self.employee_id.id,
            'contract_id': self.id,
            'struct_id': self.struct_id.id,
            'date_from': date.today().replace(day=1),
            'date_to': date.today().replace(day=28),
        })

        # Créer une entrée de jours travaillés (important pour BRUTJT)
        self.env['hr.payslip.worked_days'].create({
            'name': 'Normal Working Days',
            'code': 'WORK100',
            'number_of_days': self.base_nombre_jours or 22,  # Utilisez la valeur du contrat ou une valeur par défaut
            'number_of_hours': (self.base_nombre_jours or 22) * 8,  # Heures basées sur les jours
            'contract_id': self.id,
            'payslip_id': payslip.id,
        })

        # Calculer le bulletin
        payslip.compute_sheet()

        # Copier les lignes calculées vers le contrat en utilisant le nouveau modèle
        for line in payslip.line_ids:
            self.env['hr.contract.salary.line'].create({
                'contract_id': self.id,
                'name': line.name,
                'code': line.code,
                'category_id': line.category_id.id if line.category_id else False,
                'sequence': line.sequence,
                'quantity': line.quantity,
                'rate': line.rate,
                'amount': line.amount,
                'total': line.total,
                'salary_rule_id': line.salary_rule_id.id if line.salary_rule_id else False,
            })

        # Supprimer le bulletin temporaire
        payslip.unlink()

        return True

    @api.depends('line_ids', 'line_ids.code', 'line_ids.total')
    def _compute_salary_values(self):
        for contract in self:
            brut_line = contract.line_ids.filtered(lambda l: l.code == 'BRUT_contract')
            net_line = contract.line_ids.filtered(lambda l: l.code == 'NET')

            contract.salary_brut = brut_line.total if brut_line else 0.0
            contract.salary_net = net_line.total if net_line else 0.0


class HrContractAdvantageTemplate(models.Model):
    _name = 'hr.contract.advantage.template'
    _description = "Employee's Advantage on Contract"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    lower_bound = fields.Float('Lower Bound', digits='Payroll', help="Lower bound authorized by the employer for this advantage")
    upper_bound = fields.Float('Upper Bound', digits='Payroll', help="Upper bound authorized by the employer for this advantage")
    default_value = fields.Float('Default value for this advantage', digits='Payroll')




class HrContractSalaryLine(models.Model):
    _name = 'hr.contract.salary.line'
    _description = 'Contract Salary Simulation Line'

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    code = fields.Char(string='Code', required=True)
    category_id = fields.Many2one('hr.salary.rule.category', string='Category')
    sequence = fields.Integer(string='Sequence', default=5)
    quantity = fields.Float(string='Quantity', default=1.0)
    rate = fields.Float(string='Rate (%)', default=100.0)
    amount = fields.Float(string='Amount', digits='Payroll')
    total = fields.Float(string='Total', digits='Payroll')
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Rule')

