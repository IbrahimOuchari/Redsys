from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CrmLeadEstimation(models.Model):
    _name = 'crm.lead.fee.dd'
    _description = "Ligne d'Estimation"

    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string="Piste CRM",
        ondelete='cascade'
    )

    pn = fields.Char(string="PN")
    product_id = fields.Many2one('product.template', string="Produit")
    description = fields.Text(related='product_id.description_purchase',string="Description")
    quantity = fields.Float(string="Quantité")
    prix_fournisseur = fields.Float(string="Prix fournisseur")
    cout_transport_unitaire = fields.Float(string="Cout Transport Unitaire")
    cout_transport_total_unitaire = fields.Float(string="Cout Transport Total Unitaire", compute='_compute_transport_cost_total')
    @api.onchange('cout_transport_unitaire','quantity')
    def _compute_transport_cost_total(self):
        for record in self:
            if record.cout_transport_unitaire and record.quantity:
                record.cout_transport_total_unitaire= record.cout_transport_unitaire * record.quantity
            else:
                record.cout_transport_total_unitaire= 0.0

    taux_dd_id = fields.Many2one('taux.dd', string="Taux dd")

    fee_dd = fields.Float(string="Frais de douane",compute='_compute_fee_dd')  # ✅ Nouveau champ
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        ondelete='restrict'
    )

    @api.depends('prix_fournisseur', 'cout_transport_total_unitaire', 'taux_dd_id')
    def _compute_fee_dd(self):
        for rec in self:
            if rec.taux_dd_id and rec.taux_dd_id.name:  # Ensure taux exists
                rec.fee_dd = (rec.prix_fournisseur + rec.cout_transport_total_unitaire) * rec.taux_dd_id.name / 100
            else:
                rec.fee_dd = 0.0

    # taux_surcent = fields.Float(string="Taux de Surcent")
    # fraded1 = fields.Float(string="Fraded1", compute='_compute_fraded1', store=True)
    #
    # @api.depends('pre_furnisher', 'code_transport_unitaire', 'taux_surcent')
    # def _compute_fraded1(self):
    #     for rec in self:
    #         rec.fraded1 = (rec.pre_furnisher + rec.code_transport_unitaire) * rec.taux_surcent