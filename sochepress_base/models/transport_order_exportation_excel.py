from odoo import models


class TransportOrderExportationReport(models.AbstractModel):
    _name = 'report.sochepress_base.transport_order_exportation_report_xslx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'TransportOrderExportationReport'

    def generate_xlsx_report(self, workbook, data, datas):
        l = []
        i = 1
        for rec in datas:
            report_name = 'Table Exportation %s' % (
                rec.name)
            if report_name in l:
                report_name = report_name + "(" + str(i) + ")"
                worksheet = workbook.add_worksheet(report_name)
                i = i + 1
            else:
                worksheet = workbook.add_worksheet(report_name)
            l.append(report_name)

            format1 = workbook.add_format(
                {'font_size': 8, 'bg_color': 'd6dce5', 'align': 'center', 'valign': 'vcenter',
                 'font_color': 'black', 'bold': True, 'border': 1})
            format2 = workbook.add_format(
                {'font_size': 8, 'align': 'center', 'valign': 'vcenter',
                 'font_color': 'black', 'border': 1})

            worksheet.set_row(0, 15)

            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 10)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 15)
            worksheet.set_column('F:F', 20)
            worksheet.set_column('G:G', 15)
            worksheet.set_column('H:H', 15)
            worksheet.set_column('I:I', 15)
            worksheet.set_column('J:J', 10)
            worksheet.set_column('K:K', 15)
            worksheet.set_column('L:L', 15)
            worksheet.set_column('M:M', 10)
            worksheet.set_column('N:N', 20)
            worksheet.set_column('O:O', 16)
            worksheet.set_column('P:P', 16)

            worksheet.write('A1:A1', 'N° OT', format1)
            worksheet.write('B1:B1', 'N° de colis', format1)
            worksheet.write('C1:C1', 'Date', format1)
            worksheet.write('D1:D1', 'Code Client', format1)
            worksheet.write('E1:E1', 'Expéditeur', format1)
            # worksheet.write('E1:E1', 'Nom', format1)
            worksheet.write('F1:F1', 'Ville Expéditeur', format1)
            worksheet.write('G1:G1', 'Destinataire Final', format1)
            worksheet.write('H1:H1', 'Destination', format1)
            worksheet.write('I1:I1', 'Agence SLM', format1)
            worksheet.write('J1:J1', 'Volume', format1)
            worksheet.write('K1:K1', 'Type de colis', format1)
            worksheet.write('L1:L1', 'Valeur déclarée', format1)
            worksheet.write('M1:M1', 'Poids', format1)
            worksheet.write('N1:N1', '	Méthode contre remboursement', format1)
            worksheet.write('O1:O1', 'Montant à retourner', format1)
            worksheet.write('P1:P1', 'Type de demande', format1)
            j = 1

            for col in rec.colis:
                col = col.sudo()
                worksheet.set_row(j, 15)

                worksheet.write(j, 0, rec.name, format2)
                worksheet.write(j, 1, col.name, format2)
                if rec.date:
                    worksheet.write(j, 2, rec.date.strftime("%d/%m/%Y"), format2)
                else:
                    worksheet.write(j, 2, '', format2)
                # if col.customer_id.code_portail:
                #     worksheet.write(j, 2, col.customer_id.code_portail, format2)
                # else:
                worksheet.write(j, 3, col.customer_id.ref or '', format2)
                if col.expeditor_name:
                    worksheet.write(j, 4, col.expeditor_name, format2)
                else:
                    worksheet.write(j, 4, '', format2)
                # if worksheet.write(j, 4, col.destinator_id.lastname, format2):
                #     worksheet.write(j, 4, col.destinator_id.lastname, format2)
                # else:
                #     worksheet.write(j, 4, '', format2)
                if col.source_id.name:
                    worksheet.write(j, 5, col.source_id.name, format2)
                else:
                    worksheet.write(j, 5, '', format2)
                if col.destinator_name:
                    worksheet.write(j, 6, col.destinator_name, format2)
                else:
                    worksheet.write(j, 6, '', format2)
                if col.destination_id.name:
                    worksheet.write(j, 7, col.destination_id.name, format2)
                else:
                    worksheet.write(j, 7, '', format2)
                if rec.destination_id.name:
                    worksheet.write(j, 8, rec.destination_id.name, format2)
                else:
                    worksheet.write(j, 8, '', format2)
                if col.volume:
                    worksheet.write(j, 9, col.volume, format2)
                else:
                    worksheet.write(j, 9, '', format2)
                if col.type_colis_id.name:
                    worksheet.write(j, 10, col.type_colis_id.name, format2)
                else:
                    worksheet.write(j, 10, '', format2)
                if col.declared_value:
                    worksheet.write(j, 11, col.declared_value, format2)
                else:
                    worksheet.write(j, 11, '', format2)
                if col.weight:
                    worksheet.write(j, 12, col.weight, format2)
                else:
                    worksheet.write(j, 12, '', format2)
                if col.return_method_id:
                    worksheet.write(j, 13, col.return_method_id.name, format2)
                else:
                    worksheet.write(j, 13, '', format2)

                worksheet.write(j, 14, col.return_amount or '', format2)
                if col.return_request_id:
                    worksheet.write(j, 15, 'Retour', format2)
                else:
                    worksheet.write(j, 15, 'Envoi', format2)

                j += 1
