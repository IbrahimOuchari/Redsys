from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_nn_paie_account = fields.Boolean(string='Payroll Accounting')
    signature_responsable_paie = fields.Binary(string='Signature Responsable Paie', store = True)



class ResCompany(models.Model):
    _inherit = 'res.company'

    signature_responsable_paie = fields.Binary(string='Signature Responsable Paie')
    compte_bancaire = fields.Char(string="RIB Bancaire")
    banque = fields.Char(string="Banque")  # Added this missing field
    agence = fields.Char(string="Agence")
    mat_cnss = fields.Char(string="Immatriculation CNSS", required=True)
    code_exploitation_cnss = fields.Char(string='Code Exploitation CNSS')
    bureau = fields.Char(string='Bureau')

    @api.constrains('code_exploitation_cnss')
    def _check_code_exploitation_cnss(self):
        for record in self:
            if record.code_exploitation_cnss and len(record.code_exploitation_cnss) != 4:
                raise ValidationError(_("Le Code Exploitation CNSS doit comporter exactement 4 caractères."))

    @api.constrains('mat_cnss')
    def _check_mat_cnss(self):
        for record in self:
            if record.mat_cnss and len(record.mat_cnss) != 10:
                raise ValidationError(_("L'immatriculation CNSS doit comporter exactement 10 caractères."))
