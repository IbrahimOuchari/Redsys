from odoo import models

class OrdreVirementXlsx(models.AbstractModel):
    _name = 'report.nn_paie.ordre_virement_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, ordre_virement_records):
        for ordre_virement in ordre_virement_records:
            # Nom de la feuille Excel
            report_name = f"Ordre Virement {ordre_virement.name}"
            sheet = workbook.add_worksheet(report_name[:31])

            # Formats
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            header_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
            cell_format = workbook.add_format({'align': 'center', 'border': 1})
            number_format = workbook.add_format({'align': 'right', 'border': 1, 'num_format': '#,##0.000'})

            # Titre et en-tête
            sheet.merge_range('A1:E1', f'Ordre de virement des salaires {ordre_virement.mois} {ordre_virement.annee}',
                              bold)
            sheet.merge_range('A2:E2', f'Date de virement: {ordre_virement.date_virement}', bold)

            # En-têtes du tableau
            headers = [
                "Matricule",
                "Nom et Prénom",
                "Banque",
                "Compte Bancaire",
                "Salaire Net à Payer"
            ]

            # Écriture des en-têtes
            for col, header in enumerate(headers):
                sheet.write(3, col, header, header_format)
                sheet.set_column(col, col, 20)  # Largeur de colonne

            # Données
            row = 4
            for line in ordre_virement.ordre_virement_line_ids:
                sheet.write(row, 0, line.matricule or "", cell_format)
                sheet.write(row, 1, line.employe_id.name or "", cell_format)
                sheet.write(row, 2, line.bank or "", cell_format)
                sheet.write(row, 3, line.bank_account or "", cell_format)
                sheet.write(row, 4, line.netap or 0.0, number_format)
                row += 1

            total_salaire_net = sum(ordre_virement.ordre_virement_line_ids.mapped('netap'))
            sheet.write(row, 3, "Total Salaire Net à Payer:", bold)
            sheet.write(row, 4, total_salaire_net,number_format)
