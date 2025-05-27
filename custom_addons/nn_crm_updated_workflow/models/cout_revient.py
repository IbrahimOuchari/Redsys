from odoo import fields,api, models

class CoutDeRevient(models.Model):
    _name ='crm.lead.cout.revient'

    pn = fields.Char(string="PN")
    product_id = fields.Many2one('product.template', string="Produit")
    description = fields.Text(related='product_id.description_purchase', string="Description")
    quantity = fields.Float(string="Quantité")
    prix_dachat_unitaire = fields.Float(string="Prix d'achat unitaire")
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        ondelete='restrict'
    )
    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string="Piste CRM",
        ondelete='cascade'
    )

    fee_dd = fields.Float(string="Frais de douane", compute='_compute_fee_dd_from_estimation')
    @api.depends('product_id', 'lead_id.crm_lead_fee_dd_ids.fee_dd')
    def _compute_fee_dd_from_estimation(self):
        """
        Retrieve fee_dd value from crm.lead.fee.dd for the same product_id
        """
        for rec in self:
            if rec.product_id and rec.lead_id:
                # Find the corresponding fee_dd record with the same product_id
                fee_dd_record = rec.lead_id.crm_lead_fee_dd_ids.filtered(
                    lambda x: x.product_id.id == rec.product_id.id
                )
                if fee_dd_record:
                    # Take the first record if multiple exist (shouldn't happen normally)
                    rec.fee_dd = fee_dd_record[0].fee_dd
                else:
                    rec.fee_dd = 0.0
            else:
                rec.fee_dd = 0.0
    cout_logstic_unitaire = fields.Float(string="Cout Logistique Unitaire")
    cout_certification_uniatire = fields.Float(string="Cout certification Unitaire")
    cout_revient_unitaire = fields.Float(string="Cout Revient Unitaire", compute='_compute_cout_revient_unitaire')
    @api.onchange('prix_dachat_unitaire','fee_dd','cout_logstic_unitaire','cout_certification_uniatire')
    def _compute_cout_revient_unitaire(self):
        for rec in self:
            rec.cout_revient_unitaire = rec.prix_dachat_unitaire+rec.fee_dd+rec.cout_logstic_unitaire+rec.cout_certification_uniatire

    cout_revient_global = fields.Float(string= 'Cout Revient GLobal', compute='_compute_cout_revient_global')

    @api.onchange('cout_revient_unitaire','quantity')
    def _compute_cout_revient_global(self):
        for rec in self:
            rec.cout_revient_global = rec.cout_revient_unitaire * rec.quantity
    taux_marge =fields.Float(string= "Taux de Marge")
    prix_vente_conseille = fields.Float(string="Prix Vente",compute='_compute_prix_ventre')
    @api.onchange('cout_revient_unitaire','taux_marge')
    def _compute_prix_ventre(self):
        for rec in self:
            if rec.taux_marge:
               rec.prix_vente_conseille = (1+rec.taux_marge/100)
            else :
                rec.prix_vente_conseille = 0.0