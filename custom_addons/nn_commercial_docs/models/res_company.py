from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    fax = fields.Char(string='Fax')
    background_logo = fields.Binary(string="Logo de fond")
