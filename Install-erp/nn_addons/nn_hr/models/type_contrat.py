# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrContractType(models.Model):
    _name = 'hr.contract.type'
    _description = 'Employee Contract Types'

    name = fields.Char(string="Type Contrat", required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(string="Code")
    term_ids = fields.One2many('hr.contract.type.term', 'contract_type_id')
    country_id = fields.Many2one('res.country', string="Country")


class HrContractTypeTerm(models.Model):
    _name = 'hr.contract.type.term'
    _description = 'Employee Contract Types Terms'

    contract_type_id = fields.Many2one('hr.contract.type')
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    body = fields.Text(required=True)

class HrContract(models.Model):
    _inherit = "hr.contract"

    contract_type_id = fields.Many2one("hr.contract.type", string="Type Contrat")

    #Référence automatique contrat

    name = fields.Char(
        "Référence Contrat", required=False, readonly=True, copy=False, default="/"
    )

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("contract.ref")
        return super(HrContract, self).create(vals)

