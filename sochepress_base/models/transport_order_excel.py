from math import *

from odoo import models


class CustomerReport(models.AbstractModel):
    _name = 'report.sochepress_base.customer_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report.sochepress_base.customer_report'

    def generate_xlsx_report(self, workbook, data, datas):
        l = []
        i = 1
        for rec in datas:
            if rec.client_type in ['ecommercant', 'b2c']:
                partner = rec.id
                products = self.env['sochepress.type.colis'].sudo().search([])
                expeditions = self.env['res.partner'].sudo().search(
                    [('parent_id', '=', partner), ('type', '=', 'other')])
                contracts = self.env['sochepress.contract'].sudo().search([
                    ('stage_id', '=', self.env.ref('sochepress_base.sochepress_contract_stage_in_progress').id),
                    ('partner_id', '=', partner)], limit=1)
                child = ('id', 'in', rec.child_ids.ids if partner else [])
                # if rec.client_type == 'ecommercant':
                destinations = self.env['sochepress.destination'].sudo().search([('type', '=', 'client_final')])
                # else:
                #     destinations = self.env['sochepress.destination'].sudo().search(
                #         [('id', 'in', contracts.destination_ids.ids)])
                return_of_funds = self.env['sls.return.method'].sudo().search([], order='sequence')

                partners = self.env['res.partner'].sudo().search(
                    [('destination_id', 'in', contracts.destination_ids.ids), child])
                destinators = self.env['res.partner'].sudo().search(
                    [('parent_id', '=', partner), ('type', '=', 'delivery')])
                modeles_colis = self.env['product.template'].sudo().search([(
                    'client_id', 'in', [rec.id]), ('hidden', '=', False)])
                document_types = self.env['sochepress.document.type'].sudo().search([])
                nature_marchandises = self.env['sochepress.merchandise'].sudo().search([])
                values = {
                    'partners': partners,
                    'expeditions': expeditions,
                    'destinators': destinators,
                    'products': products,
                    'destinations': destinations,
                    'return_of_funds': return_of_funds,
                    'modeles_colis': modeles_colis,
                    'document_types': document_types,
                    'nature_marchandises': nature_marchandises,
                }
                report_name = 'Template E-Commercant'
                if rec.client_type == 'b2c':
                    report_name = 'Template B2C'
                worksheet = workbook.add_worksheet(report_name)
                worksheet2 = workbook.add_worksheet('Paramétrages')

                format1 = workbook.add_format(
                    {'font_size': 12, 'align': 'center', 'valign': 'vcenter',
                     'font_color': 'black', 'bold': True, 'border': 1})
                format1.set_text_wrap()
                format2 = workbook.add_format(
                    {'font_size': 12, 'align': 'center', 'valign': 'vcenter',
                     'font_color': 'black', 'border': 1})
                format2.set_text_wrap()
                # format3 = format2.set_num_format('+')
                # # Light red fill with dark red text.
                # format_red = workbook.add_format({'bg_color': '#FFC7CE',
                #                                'font_color': '#9C0006'})

                worksheet.set_row(0, 30)

                worksheet.set_column('A:A', 20, format2)
                worksheet.set_column('B:B', 20, format2)
                worksheet.set_column('C:C', 20, format2)
                worksheet.set_column('D:D', 20, format2)
                worksheet.set_column('E:E', 20, format2)
                worksheet.set_column('F:F', 20, format2)
                worksheet.set_column('G:G', 20, format2)
                worksheet.set_column('H:H', 20, format2)
                worksheet.set_column('I:I', 20, format2)
                worksheet.set_column('J:J', 20, format2)
                worksheet.set_column('K:K', 20, format2)
                worksheet.set_column('L:L', 20, format2)
                worksheet.set_column('M:M', 20, format2)
                worksheet.set_column('N:N', 20, format2)
                if rec.client_type == 'b2c':
                    worksheet.set_column('O:O', 20, format2)
                    worksheet.set_column('P:P', 30, format2)
                    worksheet.set_column('Q:Q', 20, format2)
                    worksheet.set_column('R:R', 20, format2)
                    worksheet.set_column('S:S', 20, format2)
                    worksheet.set_column('T:T', 20, format2)
                    worksheet.set_column('U:U', 20, format2)
                    worksheet.set_column('V:V', 20, format2)
                    worksheet.set_column('W:W', 20, format2)
                    worksheet.set_column('X:X', 20, format2)
                    worksheet.set_column('Y:Y', 20, format2)
                    worksheet.set_column('Z:Z', 30, format2)
                else:
                    worksheet.set_column('O:O', 20, format2)
                    worksheet.set_column('P:P', 30, format2)

                worksheet.write('A1:A1', 'Type du colis', format1)
                worksheet.write('B1:B1', 'Adresse d\'expédition', format1)
                worksheet.write('C1:C1', 'Nom du client final', format1)
                worksheet.write('D1:D1', 'Email du client final', format1)
                worksheet.write('E1:E1', 'Téléphone du client final', format1)
                worksheet.write('F1:F1', 'Ville du client final', format1)
                worksheet.write('G1:G1', 'Code Postal du client final', format1)
                worksheet.write('H1:H1', 'Adresse du Client Final', format1)
                worksheet.write('I1:I1', 'Modèle du colis', format1)
                worksheet.write('J1:J1', 'Poids Colis en KG', format1)
                worksheet.write('K1:K1', 'Valeur du produit à assurer en DH', format1)
                worksheet.write('L1:L1', 'Méthode contre remboursement', format1)
                worksheet.write('M1:M1', 'Montant contre remboursement en DH', format1)
                worksheet.write('N1:N1', 'Référence Externe', format1)
                if rec.client_type == 'b2c':
                    worksheet.write('O1:O1', 'Type du retour documentaire N°1', format1)
                    worksheet.write('P1:P1', 'Référence du retour documentaire N°1', format1)
                    worksheet.write('Q1:Q1', 'Type du retour documentaire N°2', format1)
                    worksheet.write('R1:R1', 'Référence du retour documentaire N°2', format1)
                    worksheet.write('S1:S1', 'Type du retour documentaire N°3', format1)
                    worksheet.write('T1:T1', 'Référence du retour documentaire N°3', format1)
                    worksheet.write('U1:U1', 'Type du retour documentaire N°4', format1)
                    worksheet.write('V1:V1', 'Référence du retour documentaire N°4', format1)
                    worksheet.write('W1:W1', 'Type du retour documentaire N°5', format1)
                    worksheet.write('X1:X1', 'Référence du retour documentaire N°5', format1)
                    worksheet.write('Y1:Y1', 'Nature', format1)
                    worksheet.write('Z1:Z1', 'Commentaires', format1)
                else:
                    worksheet.write('O1:O1', 'Nature', format1)
                    worksheet.write('P1:P1', 'Commentaires', format1)

                worksheet2.set_row(0, 16)

                worksheet2.set_column('A:A', 20, format2)
                worksheet2.set_column('B:B', 20, format2)
                worksheet2.set_column('C:C', 40, format2)
                worksheet2.set_column('D:D', 30, format2)
                worksheet2.set_column('E:E', 30, format2)
                if rec.client_type == 'b2c':
                    worksheet2.set_column('F:F', 40, format2)
                    worksheet2.set_column('G:G', 40, format2)
                else:
                    worksheet2.set_column('F:F', 40, format2)

                worksheet2.write('A1:A1', 'Villes du client final', format1)
                worksheet2.write('B1:B1', 'Adresse d\'expédition', format1)
                worksheet2.write('C1:C1', 'Modèle du colis', format1)
                worksheet2.write('D1:D1', 'Type de colis', format1)
                worksheet2.write('E1:E1', 'Retours de fonds', format1)
                if rec.client_type == 'b2c':
                    worksheet2.write('F1:F1', 'Type de documents', format1)
                    worksheet2.write('G1:G1', 'Natures', format1)
                else:
                    worksheet2.write('F1:F1', 'Natures', format1)
                # worksheet2.write('F0:F0', 'Type de documents', format1)

                destinators = [type.display_name for type in values['products']]
                j = 1
                for exp in destinators:
                    if exp:
                        worksheet2.write(j, 3, exp, format2)
                        j += 1

                destinators = [type.name for type in values['return_of_funds']]
                j = 1
                for exp in destinators:
                    if exp:
                        worksheet2.write(j, 4, exp, format2)
                        j += 1

                if rec.client_type == 'b2c':
                    types_docs = [type.display_name for type in values['document_types']]
                    j = 1
                    for exp in types_docs:
                        if exp:
                            worksheet2.write(j, 5, exp, format2)
                            j += 1

                    nature_marchandises = [nature.name for nature in values['nature_marchandises']]
                    j = 1
                    for exp in nature_marchandises:
                        if exp:
                            worksheet2.write(j, 6, exp, format2)
                            j += 1
                else:
                    nature_marchandises = [nature.name for nature in values['nature_marchandises']]
                    j = 1
                    for exp in nature_marchandises:
                        if exp:
                            worksheet2.write(j, 5, exp, format2)
                            j += 1

                worksheet.set_row(1, 13)

                worksheet.write(1, 0, 'Petite palette', format2)
                worksheet.data_validation('A1:A1000',
                                          {'validate': 'list',
                                           'source': [type.display_name for type in values['products']]})
                worksheet.write(1, 2, '', format2)
                # worksheet.data_validation('C1:C1000',
                #                           {'validate': 'list',
                #                            'source': [type.name for type in values['destinators']]})
                worksheet.write(1, 3, '', format2)
                # worksheet.conditional_format('D1:D1000', {'type': 'text',
                #                                        'criteria': 'not containing',
                #                                        'value': '@',
                #                                        'format': format_red})
                phone_format = workbook.add_format({'font_size': 12, 'align': 'center', 'valign': 'vcenter',
                                                    'font_color': 'black', 'border': 1, 'num_format': '0#########'})
                phone_format.set_text_wrap()
                worksheet.set_column('E:E', 20, phone_format)
                worksheet.write(1, 4, '0601020304', phone_format)

                # worksheet.data_validation('E1:E1000',
                #                           {'validate': 'length',
                #                            'criteria': '=',
                #                            'value': 13})
                worksheet.write(1, 5, '', format2)
                worksheet.write(1, 6, '70000', format2)
                worksheet.data_validation('I1:I1000',
                                          {'validate': 'list',
                                           'source': [type.name for type in values['modeles_colis']]})
                worksheet.write(1, 7, '16 Lotissement Assaada', format2)
                worksheet.write(1, 8, '', format2)
                worksheet.write(1, 9, '5', format2)
                worksheet.write(1, 10, '7800', format2)
                worksheet.write(1, 11, '', format2)
                worksheet.data_validation('L1:L1000',
                                          {'validate': 'list',
                                           'source': [type.name for type in values['return_of_funds']]})
                worksheet.write(1, 12, '6000', format2)
                worksheet.write(1, 13, '', format2)

                cities_list = [type.name for type in values['destinations']]
                i = 1
                for city in cities_list:
                    worksheet2.write(i, 0, city, format2)
                    i += 1
                worksheet.data_validation('F1:F1000',
                                          {'validate': 'list',
                                           'error_type': 'information',
                                           'source': 'Paramétrages!A$2:A$%s' % (len(cities_list) + 1)})
                expeditions = [type.name for type in values['expeditions']]
                j = 1
                for exp in expeditions:
                    worksheet2.write(j, 1, exp, format2)
                    j += 1

                worksheet.write(1, 1, '', format2)
                worksheet.data_validation('B1:B1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!B$2:B$%s' % (len(expeditions) + 1)})
                j = 1
                colix = [type.name for type in values['modeles_colis']]
                for exp in colix:
                    worksheet2.write(j, 2, exp, format2)
                    j += 1

                worksheet.data_validation('I1:I1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!C$2:C$%s' % (len(colix) + 1)})
                if rec.client_type == 'b2c':
                    worksheet.data_validation('O1:O10000',
                                              {'validate': 'list',
                                               'source': 'Paramétrages!F$2:F$%s' % (len(values['document_types']) + 1)})
                    worksheet.data_validation('Q1:Q10000',
                                              {'validate': 'list',
                                               'source': 'Paramétrages!F$2:F$%s' % (len(values['document_types']) + 1)})
                    worksheet.data_validation('S1:S10000',
                                              {'validate': 'list',
                                               'source': 'Paramétrages!F$2:F$%s' % (len(values['document_types']) + 1)})
                    worksheet.data_validation('U1:U10000',
                                              {'validate': 'list',
                                               'source': 'Paramétrages!F$2:F$%s' % (len(values['document_types']) + 1)})
                    worksheet.data_validation('W1:W10000',
                                              {'validate': 'list',
                                               'source': 'Paramétrages!F$2:F$%s' % (len(values['document_types']) + 1)})
                    worksheet.data_validation('Y1:Y10000',
                                              {'validate': 'list',
                                               'source': 'Paramétrages!G$2:G$%s' % (
                                                       len(values['nature_marchandises']) + 1)})
                else:
                    worksheet.data_validation('O1:O10000',
                                              {'validate': 'list',
                                               'source': 'Paramétrages!F$2:F$%s' % (
                                                       len(values['nature_marchandises']) + 1)})
            else:
                partner = rec.id
                products = self.env['sochepress.type.colis'].sudo().search([])
                expeditions = self.env['res.partner'].sudo().search(
                    [('parent_id', '=', partner), ('type', '=', 'other')])
                contracts = self.env['sochepress.contract'].sudo().search([
                    ('stage_id', '=', self.env.ref('sochepress_base.sochepress_contract_stage_in_progress').id),
                    ('partner_id', '=', partner)], limit=1)
                child = ('id', 'in', rec.child_ids.ids if partner else [])
                if rec.client_type == 'ecommercant':
                    destinations = self.env['sochepress.destination'].sudo().search([('type', '=', 'client_final')])
                else:
                    destinations = self.env['sochepress.destination'].sudo().search(
                        [('id', 'in', contracts.destination_ids.ids)])
                return_of_funds = self.env['sls.return.method'].sudo().search([], order='sequence')

                partners = self.env['res.partner'].sudo().search(
                    [('destination_id', 'in', contracts.destination_ids.ids), child])
                destinators = self.env['res.partner'].sudo().search(
                    [('parent_id', '=', partner), ('type', '=', 'delivery'), ('hidden', '=', False)])
                modeles_colis = self.env['product.template'].sudo().search([(
                    'client_id', 'in', [rec.id]), ('hidden', '=', False)])
                document_types = self.env['sochepress.document.type'].sudo().search([])
                nature_marchandises = self.env['sochepress.merchandise'].sudo().search([])
                values = {
                    'partners': partners,
                    'expeditions': expeditions,
                    'destinators': destinators,
                    'products': products,
                    'destinations': destinations,
                    'return_of_funds': return_of_funds,
                    'modeles_colis': modeles_colis,
                    'document_types': document_types,
                    'nature_marchandises': nature_marchandises,
                }
                report_name = 'Template B2B'
                worksheet = workbook.add_worksheet(report_name)
                worksheet2 = workbook.add_worksheet('Paramétrages')

                format1 = workbook.add_format(
                    {'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                     'font_color': 'black', 'bold': True, 'border': 1})
                format1.set_text_wrap()
                format2 = workbook.add_format(
                    {'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                     'font_color': 'black', 'border': 1})
                format2.set_text_wrap()

                worksheet.set_row(0, 20)

                worksheet.set_column('A:A', 20, format2)
                worksheet.set_column('B:B', 20, format2)
                worksheet.set_column('C:C', 20, format2)
                worksheet.set_column('D:D', 20, format2)
                worksheet.set_column('E:E', 20, format2)
                worksheet.set_column('F:F', 20, format2)
                worksheet.set_column('G:G', 20, format2)
                worksheet.set_column('H:H', 20, format2)
                worksheet.set_column('I:I', 20, format2)
                worksheet.set_column('J:J', 20, format2)
                worksheet.set_column('K:K', 20, format2)
                worksheet.set_column('L:L', 20, format2)
                worksheet.set_column('M:M', 20, format2)
                worksheet.set_column('N:N', 20, format2)  # modif
                worksheet.set_column('O:O', 20, format2)  # modif
                worksheet.set_column('P:P', 20, format2)  # modif
                worksheet.set_column('Q:Q', 20, format2)
                worksheet.set_column('R:R', 20, format2)
                worksheet.set_column('S:S', 30, format2)
                worksheet.set_column('T:T', 30, format2)
                worksheet.set_column('U:U', 30, format2)
                worksheet.set_column('V:V', 30, format2)

                worksheet.write('A1:A1', 'Type du colis', format1)
                worksheet.write('B1:B1', 'Adresse d\'expédition', format1)
                worksheet.write('C1:C1', 'Adresse de livraison', format1)
                # worksheet.write('D1:D1', 'Horaires souhaités ', format1)
                worksheet.write('D1:D1', 'Modèle du colis', format1)
                worksheet.write('E1:E1', 'Poids colis en KG', format1)
                worksheet.write('F1:F1', 'Valeur du produit à assurer en DH', format1)
                worksheet.write('G1:G1', 'Méthode contre remboursement', format1)
                worksheet.write('H1:H1', 'Montant contre remboursement en DH', format1)
                worksheet.write('I1:I1', 'Type du retour documentaire N°1', format1)
                worksheet.write('J1:J1', 'Référence du retour documentaire N°1', format1)
                worksheet.write('K1:K1', 'Type du retour documentaire N°2', format1)
                worksheet.write('L1:L1', 'Référence du retour documentaire N°2', format1)
                worksheet.write('M1:M1', 'Type du retour documentaire N°3', format1)
                worksheet.write('N1:N1', 'Référence du retour documentaire N°3', format1)
                worksheet.write('O1:O1', 'Type du retour documentaire N°4', format1)
                worksheet.write('P1:P1', 'Référence du retour documentaire N°4', format1)
                worksheet.write('Q1:Q1', 'Type du retour documentaire N°5', format1)
                worksheet.write('R1:R1', 'Référence du retour documentaire N°5', format1)
                worksheet.write('S1:S1', 'Référence Externe', format1)
                worksheet.write('T1:T1', 'Code Barre', format1)  # modif
                worksheet.write('U1:U1', 'Nature', format1) # modif
                worksheet.write('V1:V1', 'Commentaires', format1)  # modif

                worksheet.set_row(1, 14)

                worksheet2.set_row(0, 15)
                worksheet2.set_row(1, 13)
                worksheet2.set_column('A:A', 20, format2)
                worksheet2.set_column('B:B', 40, format2)
                worksheet2.set_column('C:C', 35, format2)
                worksheet2.set_column('D:D', 40, format2)
                worksheet2.set_column('E:E', 35, format2)
                worksheet2.set_column('F:F', 35, format2)
                worksheet2.set_column('G:G', 35, format2)

                # worksheet2.write('A1:A1', 'Villes du client final', format1)
                worksheet2.write('A1:A1', 'Adresse d\'expédition', format1)
                worksheet2.write('B1:B1', 'Modèle du colis', format1)
                worksheet2.write('C1:C1', 'Adresse de livraison', format1)
                worksheet2.write('D1:D1', 'Type de colis', format1)
                worksheet2.write('E1:E1', 'Retours de fonds', format1)
                worksheet2.write('F1:F1', 'Type de documents', format1)
                worksheet2.write('G1:G1', 'Natures', format1)

                expeditions = [type.name for type in values['expeditions']]
                j = 1
                for exp in expeditions:
                    worksheet2.write(j, 0, exp, format2)
                    j += 1
                j = 1
                colix = [type.name for type in values['modeles_colis']]
                for exp in colix:
                    if exp:
                        worksheet2.write(j, 1, exp, format2)
                        j += 1
                destinators = [type.name for type in values['destinators']]
                j = 1
                for exp in destinators:
                    if exp:
                        worksheet2.write(j, 2, exp, format2)
                        j += 1
                products = [type.display_name for type in values['products']]
                j = 1
                for exp in products:
                    if exp:
                        worksheet2.write(j, 3, exp, format2)
                        j += 1

                funds = [type.name for type in values['return_of_funds']]
                j = 1
                for exp in funds:
                    if exp:
                        worksheet2.write(j, 4, exp, format2)
                        j += 1

                types_docs = [type.display_name for type in values['document_types']]
                j = 1
                for exp in types_docs:
                    if exp:
                        worksheet2.write(j, 5, exp, format2)
                        j += 1
                nature_marchandises = [nature.name for nature in values['nature_marchandises']]
                j = 1
                for exp in nature_marchandises:
                    if exp:
                        worksheet2.write(j, 6, exp, format2)
                        j += 1

                # worksheet.write(1, 0, 'Petite palette', format2)
                worksheet.data_validation('A1:A1000',
                                          {'validate': 'list',
                                           'source': [type.display_name for type in values['products']]})
                # worksheet.write(1, 1, '', format2)
                worksheet.data_validation('B1:B1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!A$2:A$%s' % (len(expeditions) + 1)})
                # worksheet.write(1, 2, '', format2)
                # worksheet.write(1, 3, '', format2)
                worksheet.data_validation('D1:D1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!B$2:B$%s' % (len(colix) + 1)})

                worksheet.data_validation('C1:C1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!C$2:C$%s' % (len(destinators) + 1)})

                # worksheet.write(1, 5, '7', format2)
                # worksheet.write(1, 6, '7800', format2)
                # worksheet.write(1, 7, '', format2)
                worksheet.data_validation('G1:G1000',
                                          {'validate': 'list',
                                           'source': [type.name for type in values['return_of_funds']]})

                # worksheet.write(1, 8, '6000', format2)
                # worksheet.write(1, 9, '', format2)
                worksheet.data_validation('I1:I1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!F$2:F$%s' % (len(types_docs) + 1)})
                # worksheet.write(1, 10, '', format2)
                # worksheet.write(1, 11, '', format2)
                worksheet.data_validation('K1:K1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!F$2:F$%s' % (len(types_docs) + 1)})
                worksheet.data_validation('M1:M1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!F$2:F$%s' % (len(types_docs) + 1)})
                worksheet.data_validation('O1:O1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!F$2:F$%s' % (len(types_docs) + 1)})
                worksheet.data_validation('Q1:Q1000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!F$2:F$%s' % (len(types_docs) + 1)})                           
                # worksheet.write(1, 12, '', format2)
                worksheet.data_validation('T1:T1000', {'validate': 'length', 'criteria': '>=', 'value': 10,
                                                       'error_title': 'Longueur du code-barre incorrect',
                                                       'error_message': 'Le code-barre doit être sur 10 positions'})  # modif

                worksheet.data_validation('U1:U10000',
                                          {'validate': 'list',
                                           'source': 'Paramétrages!G$2:G$%s' % (
                                               len(values['nature_marchandises']) + 1)})


class TransportOrderReport(models.AbstractModel):
    _name = 'report.sochepress_base.transport_order_report_xslx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report.sochepress_base.transport_order_report_xslx'

    def generate_xlsx_report(self, workbook, data, datas):
        l = []
        i = 1
        for rec in datas:

            report_name = 'Import Rendez Vous %s' % (
                rec.name)
            if report_name in l:
                report_name = report_name + "(" + str(i) + ")"
                worksheet = workbook.add_worksheet(report_name)
                i = i + 1
            else:
                worksheet = workbook.add_worksheet(report_name)
            l.append(report_name)

            format1 = workbook.add_format(
                {'font_size': 8, 'align': 'center', 'valign': 'vcenter',
                 'font_color': 'black', 'bold': True, 'border': 1})
            format2 = workbook.add_format(
                {'font_size': 8, 'align': 'center', 'valign': 'vcenter',
                 'font_color': 'black', 'border': 1})

            worksheet.set_row(0, 15)

            worksheet.set_column('A:A', 10)
            worksheet.set_column('B:B', 10)
            worksheet.set_column('C:C', 20)
            worksheet.set_column('D:D', 30)
            worksheet.set_column('E:E', 10)
            worksheet.set_column('F:F', 10)
            worksheet.set_column('G:G', 10)
            worksheet.set_column('H:H', 10)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('J:J', 10)
            worksheet.set_column('K:K', 10)
            worksheet.set_column('L:L', 10)
            worksheet.set_column('M:M', 10)
            worksheet.set_column('N:N', 20)
            worksheet.set_column('O:O', 20)
            worksheet.set_column('P:P', 20)
            worksheet.set_column('Q:Q', 10)
            worksheet.set_column('R:R', 10)
            worksheet.set_column('S:S', 20)
            worksheet.set_column('T:T', 30)

            worksheet.write('A1:A1', 'Id', format1)
            worksheet.write('B1:B1', 'Date-visite', format1)
            worksheet.write('C1:C1', 'Identifiant externe client', format1)
            worksheet.write('D1:D1', 'Nom', format1)
            # worksheet.write('E1:E1', 'Nom', format1)
            worksheet.write('E1:E1', 'Telephone', format1)
            worksheet.write('F1:F1', 'Mobile', format1)
            worksheet.write('G1:G1', 'Courriel', format1)
            worksheet.write('H1:H1', 'Adresse', format1)
            worksheet.write('I1:I1', 'Code postal', format1)
            worksheet.write('J1:J1', 'Ville', format1)
            worksheet.write('K1:K1', 'Latitude', format1)
            worksheet.write('L1:L1', 'Longitude', format1)
            worksheet.write('M1:M1', 'Type', format1)
            worksheet.write('N1:N1', 'Duree maximale de transport', format1)
            worksheet.write('O1:O1', 'Duree', format1)
            worksheet.write('P1:P1', 'Creneau horaire de passage', format1)
            worksheet.write('Q1:Q1', 'Commentaires', format1)
            worksheet.write('R1:R1', 'Cap_Poids', format1)
            worksheet.write('S1:S1', 'Cap_Volume', format1)
            worksheet.write('T1:T1', 'Référence de commande', format1)

            j = 1

            for col in rec.colis:
                worksheet.set_row(j, 15)

                worksheet.write(j, 0, col.name, format2)
                if rec.create_date:
                    worksheet.write(j, 1, rec.create_date.strftime("%d/%m/%Y"), format2)
                else:
                    worksheet.write(j, 1, '', format2)
                # if col.customer_id.code_portail:
                #     worksheet.write(j, 2, col.customer_id.code_portail, format2)
                # else:
                worksheet.write(j, 2, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.name:
                        worksheet.write(j, 3, col.destinator_id.name, format2)
                    else:
                        worksheet.write(j, 3, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.name:
                        worksheet.write(j, 3, col.expeditor_id.name, format2)
                    else:
                        worksheet.write(j, 3, '', format2)
                # if worksheet.write(j, 4, col.destinator_id.lastname, format2):
                #     worksheet.write(j, 4, col.destinator_id.lastname, format2)
                # else:
                #     worksheet.write(j, 4, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.phone:
                        phone_stripped = col.destinator_id.phone.replace(" ", "")
                        if phone_stripped[0] == '+':
                            phone = phone_stripped.ljust(13)[:13]
                        else:
                            if phone_stripped[0] == '0':
                                phone_212 = '+212' + phone_stripped[1:]
                                phone = phone_212.ljust(13)[:13]
                            else:
                                phone_212 = '+212' + phone_stripped[0:]
                                phone = phone_212.ljust(13)[:13]
                        worksheet.write(j, 4, phone, format2)
                    else:
                        worksheet.write(j, 4, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.phone:
                        phone_stripped = col.expeditor_id.phone.replace(" ", "")
                        if phone_stripped[0] == '+':
                            phone = phone_stripped.ljust(13)[:13]
                        else:
                            if phone_stripped[0] == '0':
                                phone_212 = '+212' + phone_stripped[1:]
                                phone = phone_212.ljust(13)[:13]
                            else:
                                phone_212 = '+212' + phone_stripped[0:]
                                phone = phone_212.ljust(13)[:13]
                        worksheet.write(j, 4, phone, format2)
                    else:
                        worksheet.write(j, 4, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.mobile:
                        mobile_stripped = col.destinator_id.mobile.replace(" ", "")
                        if mobile_stripped[0] == '+':
                            mobile = mobile_stripped.ljust(13)[:13]
                        else:
                            if mobile_stripped[0] == '0':
                                mobile_212 = '+212' + mobile_stripped[1:]
                                mobile = mobile_212.ljust(13)[:13]
                            else:
                                mobile_212 = '+212' + mobile_stripped[0:]
                                mobile = mobile_212.ljust(13)[:13]
                        worksheet.write(j, 5, mobile, format2)
                    else:
                        worksheet.write(j, 5, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.mobile:
                        mobile_stripped = col.expeditor_id.mobile.replace(" ", "")
                        if mobile_stripped[0] == '+':
                            mobile = mobile_stripped.ljust(13)[:13]
                        else:
                            if mobile_stripped[0] == '0':
                                mobile_212 = '+212' + mobile_stripped[1:]
                                mobile = mobile_212.ljust(13)[:13]
                            else:
                                mobile_212 = '+212' + mobile_stripped[0:]
                                mobile = mobile_212.ljust(13)[:13]
                        worksheet.write(j, 5, mobile, format2)
                    else:
                        worksheet.write(j, 5, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.email:
                        worksheet.write(j, 6, col.destinator_id.email, format2)
                    else:
                        worksheet.write(j, 6, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.email:
                        worksheet.write(j, 6, col.expeditor_id.email, format2)
                    else:
                        worksheet.write(j, 6, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.contact_address:
                        worksheet.write(j, 7, col.destinator_id.street, format2)
                    else:
                        worksheet.write(j, 7, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.contact_address:
                        worksheet.write(j, 7, col.expeditor_id.street, format2)
                    else:
                        worksheet.write(j, 7, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.zip:
                        worksheet.write(j, 8, col.destinator_id.zip, format2)
                    else:
                        worksheet.write(j, 8, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.zip:
                        worksheet.write(j, 8, col.expeditor_id.zip, format2)
                    else:
                        worksheet.write(j, 8, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.city:
                        worksheet.write(j, 9, col.destinator_id.city, format2)
                    else:
                        worksheet.write(j, 9, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.city:
                        worksheet.write(j, 9, col.expeditor_id.city, format2)
                    else:
                        worksheet.write(j, 9, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.partner_latitude:
                        worksheet.write(j, 10, col.destinator_id.partner_latitude, format2)
                    else:
                        worksheet.write(j, 10, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.partner_latitude:
                        worksheet.write(j, 10, col.expeditor_id.partner_latitude, format2)
                    else:
                        worksheet.write(j, 10, '', format2)
                if rec.type_ot == 'delivery':
                    if col.destinator_id.partner_longitude:
                        worksheet.write(j, 11, col.destinator_id.partner_longitude, format2)
                    else:
                        worksheet.write(j, 11, '', format2)
                if rec.type_ot == 'collecting':
                    if col.expeditor_id.partner_longitude:
                        worksheet.write(j, 11, col.expeditor_id.partner_longitude, format2)
                    else:
                        worksheet.write(j, 11, '', format2)
                if rec.type_ot == 'collecting':
                    worksheet.write(j, 12, 'Collecte', format2)
                elif rec.type_ot == 'delivery':
                    worksheet.write(j, 12, 'Livraison', format2)
                else:
                    worksheet.write(j, 12, '', format2)
                worksheet.write(j, 13, '', format2)
                worksheet.write(j, 14, 10, format2)
                worksheet.write(j, 15, '', format2)
                if col.delivery_delay_reason_id:
                    worksheet.write(j, 16, col.delivery_delay_reason_id.name, format2)
                else:
                    worksheet.write(j, 16, '', format2)
                worksheet.write(j, 17, floor(col.weight), format2)
                worksheet.write(j, 18, floor(col.volume), format2)
                if col.request_id.name:
                    worksheet.write(j, 19, col.request_id.name, format2)
                else:
                    worksheet.write(j, 19, '', format2)

                j = j + 1
