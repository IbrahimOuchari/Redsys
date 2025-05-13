from odoo import models

class JournalPaieXlsx(models.AbstractModel):
    _name = 'report.nn_paie.journal_paie_xls'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, journal_paie_records):
        for journal_paie in journal_paie_records:
            report_name = f"Journal Paie {journal_paie.name}"
            sheet = workbook.add_worksheet(report_name[:31])

            # Formats
            bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#F2F2F2'})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            number_format = workbook.add_format({'num_format': '#,##0.000'})
            integer_format = workbook.add_format({'num_format': '#,##0'})
            bold_number_format = workbook.add_format({
                'bold': True,
                'num_format': '#,##0.000',
                'bg_color': '#F2F2F2'
            })

            # Set column widths
            sheet.set_column('A:A', 10)  # Matricule
            sheet.set_column('B:B', 30)  # Nom et Prénom
            sheet.set_column('C:Q', 15)  # Other columns

            # Title
            sheet.merge_range('A1:Q1', f'Journal de Paie - {journal_paie.mois} {journal_paie.annee}', bold)
            sheet.write('A2', f'Édité le: {journal_paie.edit_date}', bold)

            # Headers
            headers = [
                "Matricule", "Nom et Prénom", "NBJ", "Congé payé", "Salaire Base",
                "Brut", "CNSS", "CAVIS", "Total Charge", "S.IMP", "IRPP",
                "CSS", "Impôt", "Assurance Groupe", "Prêt", "Avance", "Net à Payer"
            ]

            for col, header in enumerate(headers):
                sheet.write(3, col, header, bold)

            # Fill data rows
            row = 4
            totals = [0] * len(headers)  # Totals for each column
            start_column_for_totals = 4  # Start calculating totals from "Salaire Base" (column index 4)

            for line in journal_paie.journal_paie_line_ids:
                data = [
                    line.matricule or "",
                    line.employe_id.name or "",
                    line.nbj or 0.0,
                    line.congep or 0.0,
                    line.salaire_base or 0.0,
                    line.brutjt or 0.0,
                    line.cnss or 0.0,
                    line.cavis or 0.0,
                    line.total_charge or 0.0,
                    line.c_imp or 0.0,
                    line.irpp or 0.0,
                    line.css or 0.0,
                    line.impot or 0.0,
                    line.assurance_group or 0.0,
                    line.pret or 0.0,
                    line.avance or 0.0,
                    line.netap or 0.0,
                ]

                for col, value in enumerate(data):
                    if col in [2, 3]:  # Colonnes NBJ et Congé payé
                        sheet.write(row, col, value, integer_format)
                    elif isinstance(value, (int, float)):
                        sheet.write(row, col, value, number_format)
                        if col >= start_column_for_totals:  # Only sum columns from "Salaire Base" onwards
                            totals[col] += value
                    else:
                        sheet.write(row, col, value)

                row += 1

            # Write totals
            sheet.write(row, 0, "TOTALS", bold)
            for col, total in enumerate(totals):
                if col >= start_column_for_totals:  # Only display totals for relevant columns
                    sheet.write(row, col, total, bold_number_format)

