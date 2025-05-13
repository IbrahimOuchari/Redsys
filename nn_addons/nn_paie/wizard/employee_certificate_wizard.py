# wizard/employee_certificate_wizard.py

from odoo import models, fields, api
from odoo.exceptions import UserError  # Correct import statement


class EmployeeCertificateWizard(models.TransientModel):
    _name = 'employee.certificate.wizard'
    _description = 'Assistant de sélection des employés pour le certificat'

    etat_annuelle_id = fields.Many2one(
        'etat.annuelle.employee',
        string='État Annuel',
        required=True
    )

    employee_line_ids = fields.Many2many(
        'etat.annuelle.employee.line',
        string='Employés',
        domain="[('etat_annuelle_employee_id', '=', etat_annuelle_id)]"
    )

    def print_selected_certificates(self):
        self.ensure_one()
        if not self.employee_line_ids:
            raise UserError("Veuillez sélectionner au moins un employé.")

        # Assurez-vous que les lignes sélectionnées appartiennent bien à l'État Annuel
        invalid_lines = self.employee_line_ids.filtered(
            lambda line: line.etat_annuelle_employee_id != self.etat_annuelle_id
        )

        if invalid_lines:
            raise UserError("Certaines lignes ne correspondent pas à l'État Annuel sélectionné.")

        data = {
            'employee_line_ids': self.employee_line_ids.ids,
            'etat_annuelle_id': self.etat_annuelle_id.id
        }

        return self.env.ref('nn_paie.report_etat_annuelle_employee').report_action(
            self.etat_annuelle_id,
            data=data
        )


