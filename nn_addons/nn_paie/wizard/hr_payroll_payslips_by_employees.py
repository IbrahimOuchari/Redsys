
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _name = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    # Modification du domaine pour ne sélectionner que les employés inactifs
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees',
                                    domain=[('state_employee', '=', 'actif')])

    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        # Filtrage supplémentaire pour garantir que seuls les employés inactifs sont traités
        inactive_employees = self.env['hr.employee'].browse(data['employee_ids']).filtered(
            lambda e: e.state_employee == 'actif')

        for employee in inactive_employees:
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise UserError(_("No contract found for employee %s.") % employee.name)
            payslip_values = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'payslip_run_id': active_id,
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', [])],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }

            # Recalculer les inputs
            payslip = self.env['hr.payslip'].new(payslip_values)
            inputs = payslip.get_inputs([contract_id], from_date, to_date)
            payslip_values['input_line_ids'] = [(0, 0, x) for x in inputs]

            # Créer le bulletin
            payslips += self.env['hr.payslip'].create(payslip_values)

        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}


