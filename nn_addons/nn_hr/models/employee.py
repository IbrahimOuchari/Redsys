from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.constrains("compte_banque")
    def check_compte_banque(self):
        for record in self:
            if record.compte_banque and len(record.compte_banque) != 20:
                raise ValidationError(_("Le RIB Bancaire doit contenir 20 Chiffres"))

    _sql_constraints = [
        ('num_banque_unique', 'UNIQUE(compte_banque)', "Le numéro du compte bancaire doit être unique"), ]



    state_employee = fields.Selection([
        ('actif', 'Actif'),
        ('tempinactif', 'Temporairement Inactif'),
        ('inactif', 'Inactif'),

    ], string='State Employé', copy=False, index=True, tracking=True, store=True, default="actif")




    def action_set_actif(self):
        for record in self:
            record.state_employee = 'actif'

    def action_set_tempinactif(self):
        for record in self:
            record.state_employee = 'tempinactif'

    def action_set_inactif(self):
        for record in self:
            record.state_employee = 'inactif'
