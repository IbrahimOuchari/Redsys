from odoo import api, fields, models, tools, _

class Company(models.Model):
    _inherit = "res.company"


    company_bank = fields.Many2one('company.bank', string="Company Bank", domain="[('company_id', '=', id)]")
    bank_company_id = fields.Char(string="Bank", related="company_bank.name")
    bank_company_account = fields.Char(string="Bank Account", related="company_bank.bank_company_account")
    agence_id = fields.Char(string="Agence", related="company_bank.agence_id")
