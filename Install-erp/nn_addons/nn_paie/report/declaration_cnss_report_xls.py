from odoo import models
from xlsxwriter.utility import xl_rowcol_to_cell
from datetime import datetime


class DeclarationCNSSXlsx(models.AbstractModel):
    _name = 'report.nn_paie.declaration_cnss_xls'
    _inherit = 'report.report_xlsx.abstract'



    def generate_xlsx_report(self, workbook, data, cnss_records):
        try:
            for declaration in cnss_records:
                # Vérification de l'existence des attributs nécessaires
                annee = getattr(declaration, 'annee', '')
                trimestre = getattr(declaration, 'trimestre', '')
                report_name = f"Déclaration CNSS {annee} {trimestre}"
                sheet = workbook.add_worksheet(report_name[:31])

                # Formats
                bold = workbook.add_format({'bold': True, 'align': 'center'})
                title_format = workbook.add_format({
                    'bold': True,
                    'align': 'center',
                    'font_size': 16,
                })
                header_info_format = workbook.add_format({
                    'bold': True,
                    'align': 'left',
                    'font_size': 11
                })
                merge_format = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'bold': True,
                    'border': 1
                })
                number_format = workbook.add_format({
                    'num_format': '# ##0.000',
                    'align': 'right'
                })
                total_format = workbook.add_format({
                    'bold': True,
                    'num_format': '# ##0.000',
                    'align': 'right',
                    'top': 1,
                    'bottom': 1
                })
                default_format = workbook.add_format({
                    'align': 'left'
                })

                # Column widths
                sheet.set_column('A:A', 10)
                sheet.set_column('B:B', 20)
                sheet.set_column('C:C', 30)
                sheet.set_column('D:D', 20)
                sheet.set_column('E:E', 25)
                sheet.set_column('F:I', 15)

                # Company Header
                sheet.merge_range('A1:I1', 'CAISSE NATIONALE DE SÉCURITÉ SOCIALE', title_format)
                sheet.merge_range('A2:I2', 'DÉCLARATION TRIMESTRIELLE DES SALAIRES', title_format)

                # Header Information - Row 3
                company_name = declaration.company_id.name if hasattr(declaration,
                                                                      'company_id') and declaration.company_id else ''
                matricule_cnss = getattr(declaration, 'matricule_cnss', '') or ''

                # sheet.write(3, 0, 'Employeur:', header_info_format)
                # sheet.merge_range(3, 1, 3, 3, company_name, default_format)
                #
                # sheet.write(4, 0, 'Matricule CNSS:', header_info_format)
                # sheet.merge_range(4, 1, 4, 3, matricule_cnss, default_format)

                sheet.write(5, 0, 'Trimestre:', header_info_format)
                sheet.merge_range(5, 1, 5, 3, trimestre, default_format)

                sheet.write(6, 0, 'Année:', header_info_format)
                sheet.merge_range(6, 1, 6, 3, annee, default_format)

                sheet.write(7, 0, "Date d'édition:", header_info_format)
                sheet.merge_range(7, 1, 7, 3, datetime.now().strftime('%d/%m/%Y'), default_format)

                # Headers - Row 9
                current_row = 9
                sheet.merge_range(current_row, 0, current_row + 1, 0, "N° Ordre", merge_format)
                sheet.merge_range(current_row, 1, current_row + 1, 1, "Matricule de l'Assuré", merge_format)
                sheet.merge_range(current_row, 2, current_row + 1, 2, "Identité du Salarié", merge_format)
                sheet.merge_range(current_row, 3, current_row + 1, 3, "N° chez l'Employeur", merge_format)
                sheet.merge_range(current_row, 4, current_row + 1, 4, "Catégorie Professionnelle", merge_format)
                sheet.merge_range(current_row, 5, current_row, 7, "REMUNERATION MENSUELLE", merge_format)

                # Month labels based on trimester
                month_labels = {
                    'T1': ['Janvier', 'Février', 'Mars'],
                    'T2': ['Avril', 'Mai', 'Juin'],
                    'T3': ['Juillet', 'Août', 'Septembre'],
                    'T4': ['Octobre', 'Novembre', 'Décembre']
                }
                current_months = month_labels.get(trimestre, ['', '', ''])

                sheet.write(current_row + 1, 5, current_months[0], bold)
                sheet.write(current_row + 1, 6, current_months[1], bold)
                sheet.write(current_row + 1, 7, current_months[2], bold)
                sheet.merge_range(current_row, 8, current_row + 1, 8, "TOTAL GENERAL", merge_format)

                # Data rows
                current_row += 2
                total_month1 = 0.0
                total_month2 = 0.0
                total_month3 = 0.0
                total_general = 0.0

                # Get lines safely
                lines = getattr(declaration, 'declaration_cnss_line_ids', []) or []

                for index, line in enumerate(lines, start=1):
                    month1_value = float(getattr(line, 'brut_m_month1', 0.0) or 0.0)
                    month2_value = float(getattr(line, 'brut_m_month2', 0.0) or 0.0)
                    month3_value = float(getattr(line, 'brut_m_month3', 0.0) or 0.0)

                    employe_name = line.employe_id.name if hasattr(line, 'employe_id') and line.employe_id else ''

                    sheet.write(current_row, 0, index)
                    sheet.write(current_row, 1, getattr(line, 'matricule', '') or '')
                    sheet.write(current_row, 2, employe_name)
                    sheet.write(current_row, 3, getattr(line, 'numer_chez_employe', '') or '')
                    sheet.write(current_row, 4, getattr(line, 'category', '') or '')
                    sheet.write(current_row, 5, month1_value, number_format)
                    sheet.write(current_row, 6, month2_value, number_format)
                    sheet.write(current_row, 7, month3_value, number_format)

                    row_total = month1_value + month2_value + month3_value
                    sheet.write(current_row, 8, row_total, number_format)

                    total_month1 += month1_value
                    total_month2 += month2_value
                    total_month3 += month3_value
                    total_general += row_total

                    current_row += 1

                # Total row
                sheet.write(current_row, 4, "TOTAL GÉNÉRAL", bold)
                sheet.write(current_row, 5, total_month1, total_format)
                sheet.write(current_row, 6, total_month2, total_format)
                sheet.write(current_row, 7, total_month3, total_format)
                sheet.write(current_row, 8, total_general, total_format)

        except Exception as e:
            # En cas d'erreur, créer une feuille d'erreur
            error_sheet = workbook.add_worksheet('Erreur')
            error_sheet.write(0, 0, f"Une erreur s'est produite lors de la génération du rapport: {str(e)}")



