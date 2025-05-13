from odoo import api, fields, models, tools, _

class Company(models.Model):
    _inherit = "res.company"

    bank_company_id = fields.Char(string="Bank")
    bank_company_account = fields.Char(string="²&&Bank Account")
    agence_id = fields.Char(string="Agence")
    social_number = fields.Char(string="Immatriculation CNSS")