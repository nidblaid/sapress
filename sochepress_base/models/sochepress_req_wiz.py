# -*- coding: utf-8 -*-

try:
    import xlrd
except ImportError:
    xlrd = xlsx = None
import base64
# import tempfile
# import xlsxwriter
import logging
# import contextlib
# import io
import re
from Levenshtein import distance
from difflib import SequenceMatcher
from fastDamerauLevenshtein import damerauLevenshtein
from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from operator import itemgetter

_logger = logging.getLogger(__name__)


# from pprint import pprint
# import dask.dataframe


class SochepressReqWiz(models.TransientModel):
    _name = 'sochepress.req.wiz'
    _description = "Sochepress Req Wizard"

    customer_id = fields.Many2one('res.partner', string="Customer", required=True)
    type = fields.Selection([('normal', "Normal"), ('transport', "Dedicted transport"),
                             ('course', "Urgent course")],
                            string="Type")
    cavenas = fields.Binary(string='Canevas')
    data = fields.Binary(attachment=False, string='Canevas datas')
    name = fields.Char('Name')
    canevas_name = fields.Char(string='Filename')
    errors = fields.Text(string='Errors')
    warning = fields.Text(string='Warnings')
    tested = fields.Integer(default=0)

    def remove_accent(self, chaine):
        accent = ['é', 'è', 'ê', 'à', 'ù', 'û', 'ç', 'ô', 'î', 'ï', 'â']
        sans_accent = ['e', 'e', 'e', 'a', 'u', 'u', 'c', 'o', 'i', 'i', 'a']

        for i in range(0, len(accent)):
            chaine = chaine.replace(accent[i], sans_accent[i])

        return chaine

    # @api.onchange('customer_id')
    def generate_canevas(self):
        if self.customer_id:
            return self.env.ref('sochepress_base.'
                                'report_customer_excel'). \
                report_action([self.customer_id.id])

    def existing_partner(self, name, phone=False):
        domain = [('name', '!=', False), ('parent_id', '=', self.customer_id.id)]
        for partner in self.env['res.partner'].sudo().search(domain):
            cond = partner.name.lower().replace(" ", "") == name.lower().replace(" ", "")
            if phone and partner.phone:
                cond = cond and partner.phone.lower().replace(" ", "") == phone.lower().replace(" ", "")
            if cond:
                return partner
        return False

    def existing_colis_modele(self, name):
        return self.env['product.template'].sudo().search(
            [('client_id', 'in', [self.customer_id.parent_id.id, self.customer_id.id]),('name', '=', name)],limit=1)
        """for partner in self.env['product.template'].sudo().search(
            [('client_id', 'in', [self.customer_id.parent_id.id, self.customer_id.id])]):
            if partner.name.lower().replace(" ", "") == name.lower().replace(" ", ""):
                return partner
        return False"""

    def existing_fund(self, name):
        for partner in self.env['sls.return.method'].sudo().search([], order='sequence'):
            if partner.name.lower().replace(" ", "") == name.lower().replace(" ", ""):
                return partner
        return False

    def existing_nature(self, name):
        for nature in self.env['sochepress.merchandise'].sudo().search([]):
            if nature.name.lower().replace(" ", "") == name.lower().replace(" ", ""):
                return nature
        return False

    def existing_doc_type(self, name):
        for partner in self.env['sochepress.document.type'].sudo().search([]):
            if partner.display_name.lower().replace(" ", "") == name.lower().replace(" ", ""):
                return partner
        return False

    def existing_location(self, name):
        corrected_name = " ".join(name.split())
        allin_one = corrected_name.lower().replace(" ", "")
        mots = corrected_name.split(" ")
        destinations = []
        exacts = []
        starts = []
        ends = []
        dists = []
        senconds = []
        motsss = mots
        leven = []
        if len(mots) > 1:
            motsss += [allin_one]
        space_replace = allin_one.lower().replace(" ", "")
        unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
        unaccented_string_name = self.remove_accent(unscane_replace)
        search = [('type', '=', 'client_final')]
        for partner in self.env['sochepress.destination'].sudo().search(search):
            space_replace = partner.name.lower().replace(" ", "")
            unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
            unaccented_string_partner = self.remove_accent(unscane_replace)
            cond1 = (unaccented_string_partner in unaccented_string_name)
            cond2 = (unaccented_string_name in unaccented_string_partner)
            cond3 = (unaccented_string_name == unaccented_string_partner)
            cond4 = unaccented_string_partner.startswith(unaccented_string_name)
            cond5 = unaccented_string_partner.endswith(unaccented_string_name)
            if cond3:
                exacts.append(partner)
            if cond1 or cond2:
                if partner not in destinations:
                    destinations.append(partner)
            if cond4:
                starts.append(partner)
            if cond5:
                ends.append(partner)

            senconds.append(
                (partner, SequenceMatcher(None, unaccented_string_name,
                                          unaccented_string_partner).ratio()))
            leven.append((partner, distance(unaccented_string_partner,
                                            unaccented_string_name)))
            dists.append(
                (partner, damerauLevenshtein(unaccented_string_name,
                                             unaccented_string_partner, similarity=False)))
        #             # if cond3:
        # for m in motsss:
        #     if len(m) > 3:
        #         space_replace = m.lower().replace(" ", "")
        #         unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
        #         unaccented_string_name = self.remove_accent(unscane_replace)
        #         for partner in self.env['sochepress.destination'].sudo().search([('type', '=', 'client_final')]):
        #             space_replace = partner.name.lower().replace(" ", "")
        #             unscane_replace = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", space_replace)
        #             unaccented_string_partner = self.remove_accent(unscane_replace)
        #             cond1 = (unaccented_string_partner in unaccented_string_name)
        #             cond2 = (unaccented_string_name in unaccented_string_partner)
        #             cond3 = (unaccented_string_name == unaccented_string_partner)
        #             cond4 = unaccented_string_partner.startswith(unaccented_string_name)
        #             cond5 = unaccented_string_partner.endswith(unaccented_string_name)
        #             if cond3:
        #                 exacts.append(partner)
        #             if cond1 or cond2:
        #                 if partner not in destinations:
        #                     destinations.append(partner)
        #             if cond4:
        #                 starts.append(partner)
        #             if cond5:
        #                 ends.append(partner)
        # #             # if cond3:
        # #             #     for p in self.env['sochepress.destination'].sudo().search([('type', '=', 'client_final'), ('id', '!=', partner.id)]):
        # #             # return partner
        # # # print([d.name for d in destinations])
        # # # print([d.name for d in exacts])
        # # # return [d.name for d in destinations], exacts
        # print('====>', [d.name for d in exacts])
        # print('====>', [d.name for d in destinations])
        # print('====>', [d.name for d in starts])
        # print('====>', [d.name for d in ends])
        senconds.sort(key=itemgetter(1))
        leven.sort(key=itemgetter(1))
        # # print('=====>', dists)
        # print('=====>', [(x[0].name, x[1]) for x in senconds[-3:]])
        # print('=====>', [(x[0].name, x[1]) for x in leven[:3]])
        # # max = dists[0][1]
        # # init = False
        # # for x in senconds:
        # #     print("=====>", x[0], x[1])
        # #     if max < x[1]:
        # #         init = x
        # #         max = x[1]
        # # print("====> ", init)
        regle_1 = senconds[-1] if senconds else False
        regle_2 = leven[0] if leven else False

        if regle_1 and regle_2:
            if regle_2[1] <= 1 or regle_1[1] >= 0.7:
                if regle_2[0] == regle_1[0]:
                    return regle_1[0]

        if len(starts) == 1:
            return starts[0]

        if len(ends) == 1:
            return ends[0]
            # else:
            #     return False

        return False
        # if exacts and len(destinations) <= 1:
        #     return exacts[0]
        # if len(destinations) == 1:
        #     return destinations[0]
        # return False

    def test_import(self):
        Attachment = self.env['ir.attachment'].sudo()
        partner = self.customer_id.id
        contract = self.env['sochepress.contract'].sudo().search(
            [('stage_id', '=', self.env.ref(
                'sochepress_base.sochepress_contract_stage_in_progress').id),
             ('partner_id', '=', partner)], limit=1)
        vals = {
            'customer_id': partner,
            'contract_id': contract.id,
            'creation_type': 'importation',
            'state': 'waiting'
        }
        colis = []
        error_line = []
        warning_line = []
        created_deliveries = 0
        nb_colis = 0
        correct_colis = 0
        rejected_colis = 0
        address = []
        filename = self.canevas_name
        if not self.cavenas:
            raise UserError("Please add the canevas")
        if filename.split('.')[-1] not in ['xls', 'csv', 'xlsx']:
            raise UserError(
                "L'extension du fichier chargé n'est pas correct.")
        # datas = base64.decodestring(self.cavenas)
        # print("DATAS", datas)
        # attachment = Attachment.create({
        #     'name': filename,
        #     'datas': datas,
        #     'type': 'binary'
        # })
        wb = xlrd.open_workbook(
            file_contents=base64.decodebytes(self.cavenas))
        sheet = wb.sheets()[0]
        # file_path = tempfile.gettempdir() + '/file.csv'
        # data = self.cavenas
        # f = open(file_path, 'wb')
        # f.write(base64.decodebytes(data))
        # f.close()
        # # d = pd.read_csv(file_path)
        # data = dask.dataframe.read_csv(file_path)
        # print(data)
        for row in range(1, sheet.nrows):
            type_colis = str(sheet.cell(row, 0).value)
            expeditor = str(sheet.cell(row, 1).value)
            if self.customer_id.client_type in ['ecommercant', 'b2c']:
                """# if float(sheet.cell(row, 9).value) < 1:
                #     raise ValidationError("Le poids de colis Invalide!")
                # if int(float(sheet.cell(row, 10).value)) < 0:
                #     raise ValidationError("La Valeur du produit à assurer en DH Invalide!")"""
                destinator = str(sheet.cell(row, 2).value)
                d_email = str(sheet.cell(row, 3).value)
                d_tel = str(sheet.cell(row, 4).value)
                destination = str(sheet.cell(row, 5).value)
                d_zip = str(sheet.cell(row, 6).value)
                d_street = str(sheet.cell(row, 7).value)
                colis_modele = str(sheet.cell(row, 8).value)
                weight = str(sheet.cell(row, 9).value)
                p_value = str(sheet.cell(row, 10).value)
                return_of_fund = str(sheet.cell(row, 11).value)
                return_amount = str(sheet.cell(row, 12).value)
                ref_ext = str(sheet.cell(row, 13).value)
                doc_type1 = ''
                doc_ref1 = ''
                doc_type2 = ''
                doc_ref2 = ''
                doc_type3 = ''
                doc_ref3 = ''
                doc_type4 = ''
                doc_ref4 = ''
                doc_type5 = ''
                doc_ref5 = ''
                notes = ''

                if self.customer_id.client_type == 'b2c':
                    doc_type1 = str(sheet.cell(row, 14).value)
                    doc_ref1 = str(sheet.cell(row, 15).value)
                    doc_type2 = str(sheet.cell(row, 16).value)
                    doc_ref2 = str(sheet.cell(row, 17).value)
                    doc_type3 = str(sheet.cell(row, 18).value)
                    doc_ref3 = str(sheet.cell(row, 19).value)
                    doc_type4 = str(sheet.cell(row, 20).value)
                    doc_ref4 = str(sheet.cell(row, 21).value)
                    doc_type5 = str(sheet.cell(row, 22).value)
                    doc_ref5 = str(sheet.cell(row, 23).value)
                    #notes = str(sheet.cell(row, 24).value)
                    nature_marchandise = str(sheet.cell(row, 24).value)
                    notes = str(sheet.cell(row, 25).value)
                else:
                    notes = str(sheet.cell(row, 15).value)
                    nature_marchandise = str(sheet.cell(row, 14).value)
                    notes = str(sheet.cell(row, 15).value)

                if expeditor == '' and d_zip == '' and destinator == '' and destination == '' and d_email == '' \
                    and d_tel == '' and d_street == '' and weight == '' and colis_modele == '' and p_value == '' \
                    and return_of_fund == '' and return_amount == '' and ref_ext == '' and nature_marchandise == '' \
                    and notes == '':
                    # error_line.append("La ligne %s n'a pas d'informations définie, elle sera ignorée" % row)
                    warning_line.append(
                        "La ligne %s n'a pas d'informations définie, elle est considérée comme fin du canevas." % row)
                    break
                nb_colis += 1
                error = False
                if weight == '':
                    error = True
                    error_line.append(
                        "La ligne %s a une valeur de poids non définie." % (
                            row + 1))
                elif weight == '0':
                    error = True
                    error_line.append(
                        "La ligne %s a 0 comme valeur de poids." % (
                            row + 1))
                elif float(weight) < 1:
                    error = True
                    error_line.append(
                        "La ligne %s a 0 Le poids de colis Invalide!." % (
                            row + 1)) 
                else:
                    try:
                        weight = float(weight)
                        if weight > contract.max_weight:
                            error = True
                            error_line.append(
                                "Le poids du colis de la ligne %s excède le poids maximal autorisé. Veuillez mettre un poids inférieur à %s kg" % (
                                    (row + 1), contract.max_weight))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a le poids de colis invalide!" % (
                                row + 1))
                if p_value != '':
                    if float(p_value) < 0:
                        error = True
                        error_line.append(
                        "La ligne %s a une Valeur du produit à assurer en DH Invalide!." % (
                            row + 1))

                d_tel = "0%s" % str(d_tel.split('.')[0]) if \
                    d_tel.split('.')[0] and str(
                        d_tel.split('.')[0][0]) != '0' else str(
                    d_tel.split('.')[0])

                if d_tel == '':
                    error = True
                    d_check_ok = False
                    warning_line.append(
                        "La ligne %s n'a pas de téléphone de client final." % (
                            row + 1))
                else:
                    pattern = r"(08|07|06|05|04)\d{8}"
                    test_string = d_tel
                    result = re.match(pattern, test_string)
                    if result:
                        # The value match the pattern
                        pass
                    else:
                        error = True
                        d_check_ok = True
                        error_line.append(
                            "La ligne %s a un format de telephone incorrect, le format correct est : 06xxxxxxxxx." % (
                                row + 1))

                    # TODO ajouter le code de check de formal du téléphone ici si non okay ajouter le code error_line.append("La ligne %s a un format de telephone incorrect, le format correct est+212xxxxxx")
                    # TODO mettre error = True et d_check_ok = True

                if expeditor == '':
                    expeditor = self.customer_id.id
                    source = self.customer_id.destination_id
                    if not source:
                        error = True
                        error_line.append(
                            "L'adresse d'expédition %s n'a pas de ville associée, merci de la préciser." % expeditor)
                else:
                    the_name = expeditor
                    expeditor_partner = self.existing_partner(expeditor, d_tel)
                    if not expeditor_partner:
                        source = self.customer_id.destination_id
                        if source:
                            warning_line.append(
                                "L'adresse d'expédition %s de la ligne %s sera nouvellement crée, vous pouvez le voire sur la liste de vos expéditeurs." % (
                                    the_name, (row + 1)))
                        else:
                            error = True
                            error_line.append(
                                "L'adresse d'expédition ne peut être ajouter car le client de la demande n'a pas de ville associée.")
                    else:
                        # pass
                        if not expeditor_partner.destination_id:
                            error = True
                            error_line.append(
                                "L'addresse d'expédition %s n'a pas de ville associée, merci de la préciser sur votre carnet d'expédition ." % expeditor)

                d_check_ok = True
                if destinator == '':
                    error = True
                    d_check_ok = False
                    error_line.append(
                        "La ligne %s n'a pas de nom de client final." % (
                            row + 1))

                if d_email == '':
                    # error = True
                    # d_check_ok = False
                    warning_line.append(
                        "La ligne %s n'a pas d'email de client final." % (
                            row + 1))
                else:
                    pattern = r'[^@]+@[^@]+\.[^@]+'
                    test_string = d_email
                    result = re.match(pattern, test_string)
                    if result:
                        # The value match the pattern
                        pass
                    else:
                        # error = True
                        # d_check_ok = True
                        warning_line.append(
                            "La ligne %s a un format d'email incorrect, le format correct est : monemail@test.com." % (
                                row + 1))
                    # TODO ajouter le code de check de formal de l'email ici
                    # TODO meme chose que les checks sur le telephone
                    pass

                if destination == '':
                    error = True
                    d_check_ok = False
                    error_line.append(
                        "La ligne %s n'a pas de ville du client final défini." % (
                            row + 1))

                if d_zip == '':
                    warning_line.append(
                        "La ligne %s n'a pas de code postal de client final." % (
                            row + 1))
                else:
                    pattern = r"\b\d{5}\b"
                    test_string = d_zip
                    result = re.match(pattern, test_string)
                    if result:
                        pass
                        # The value match the pattern
                    else:
                        # error = True
                        # d_check_ok = True
                        warning_line.append(
                            "La ligne %s a un format de code zip incorrect, le format correct se compose de 5 chiffres : par ex. 72000." % (
                                row + 1))
                    # TODO ajouter le code de check du code zip ici
                    # TODO meme chose que le telephone

                if d_street == '':
                    error = True
                    d_check_ok = False
                    error_line.append(
                        "La ligne %s n'a pas d'adresse de client final." % (
                            row + 1))
                else:
                    pattern = r'(?=.*?\b[0-9]{1,3}\b)((?:[^a-zA-Z]*[a-zA-Z])){3,}.*'
                    test_string = d_street
                    result = re.match(pattern, test_string)
                    if result:
                        # The value match the pattern
                        pass
                    else:
                        error = True
                        d_check_ok = True

                        error_line.append(
                            "La ligne %s a un format d'adresse incorrect, Merci de saisir une adresse détaillée (Un minimum de 2 mots et un chiffre), les symboles (:,-,_,°,...) ne sont pas acceptés." % (
                                row + 1))
                    # TODO ajouter le code de check de formal des addresses ici
                    pass
                if d_check_ok:
                    created_deliveries += 1
                    if destinator not in address:
                        # created_deliveries += 1
                        address.append(destinator)

                if colis_modele == '':
                    error = True
                    error_line.append(
                        "La ligne %s n'a pas de modèle de colis défini." % (
                            row + 1))
                else:
                    colis_modele_id = self.existing_colis_modele(
                        colis_modele)
                    if not colis_modele_id:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de modèle de colis incorrecte. Les valeurs correctes sont indiquées sur la feuille 'Paramétrages' du canevas." % (
                                row + 1))
                if p_value != '':
                    try:
                        p_value = float(p_value)
                        if p_value == 0:
                            e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                            r = ""
                            warning_line.append(
                                "La ligne %s a  une valeur du produit à assurer en DH nulle. %s %s" % (
                                    (row + 1), e, r))

                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de produit en DH incorrecte" % (
                                row + 1))
                else:
                    e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                    r = ""
                    warning_line.append(
                        "La ligne %s a  une valeur du produit à assurer en DH nulle. %s %s" % (
                            (row + 1), e, r))
                if return_of_fund != '':
                    return_of_fund = self.existing_fund(return_of_fund)
                    if not return_of_fund:
                        error = True
                        return_of_fund = False
                        error_line.append(
                            "La ligne %s a une méthode contre remboursement incorrecte. Les valeurs correctes sont indiquées sur la feuille 'Paramétrages' du canevas." % (
                                row + 1))
                    else:
                        return_of_fund = return_of_fund.id
                else:
                    # error = True
                    return_of_fund = False
                    warning_line.append(
                        "La ligne %s n'a pas de méthode contre remboursementtt" % (
                            row + 1))

                if return_amount != '':
                    try:
                        return_amount = float(return_amount)
                        return_f = self.env['sls.return.method'].sudo().browse(
                            return_of_fund) if return_of_fund else False
                        if return_f:
                            if return_f.montant_obligatoire and return_amount <= 0:
                                error = True
                                error_line.append(
                                    "La ligne %s a une valeur de montant contre remboursement en DH égale à 0 bien qu'une méthode contre remboursement aie été spécifié." % (
                                        row + 1))
                        else:
                            error = True
                            error_line.append(
                                "La ligne %s n'a pas de méthode contre remboursement" % (
                                        row + 1))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de montant contre remboursement en DH incorrecte" % (
                                row + 1))
                else:
                    return_f = self.env['sls.return.method'].sudo().browse(
                        return_of_fund) if return_of_fund else False
                    if return_f and return_f.montant_obligatoire:
                        error = True
                        error_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))
                if self.customer_id.client_type == 'b2c':
                    if doc_type1 != '':
                        doc1 = self.existing_doc_type(doc_type1)
                        if not doc1:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 1 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref1:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 1 précisé." % (
                                row + 1))

                    if doc_type2 != '':
                        doc2 = self.existing_doc_type(doc_type2)
                        if not doc2:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 2 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref2:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 2 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 2 précisé." % (
                                row + 1))

                    if doc_type3 != '':
                        doc3 = self.existing_doc_type(doc_type3)
                        if not doc3:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 3 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref3:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 3 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 3 précisé." % (
                                row + 1))

                    if doc_type4 != '':
                        doc4 = self.existing_doc_type(doc_type4)
                        if not doc4:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 4 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref4:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 4 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 4 précisé." % (
                                row + 1))
                    if doc_type5 != '':
                        doc5 = self.existing_doc_type(doc_type5)
                        if not doc5:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 5 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref5:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 5 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 5 précisé." % (
                                row + 1))
                if ref_ext == '':
                    warning_line.append(
                        "La ligne %s n'a pas de référence externe de colis renseigné." % (
                            row + 1))
                if nature_marchandise != '':
                    nature_marchandise = self.existing_nature(nature_marchandise)
                    if not nature_marchandise:
                        warning_line.append(
                            "La ligne %s a une nature de marchandise inexistante, elle ne sera pas ajoutée" % (row + 1))
                else:
                    nature_marchandise = False
                    warning_line.append(
                        "La ligne %s n'a pas de nature de marchandise" % (row + 1))

                if notes == '':
                    warning_line.append(
                        "La ligne %s n'a pas de commentaires renseignés sur le colis." % (
                            row + 1))

                if not error:
                    correct_colis += 1
                else:
                    rejected_colis += 1
            elif self.customer_id.client_type == 'b2b':
                """# if float(sheet.cell(row, 4).value) < 1:
                #     raise ValidationError("Le poids de colis Invalide!")
                # if int(float(sheet.cell(row, 5).value)) < 0:
                #     raise ValidationError("La Valeur du produit à assurer en DH Invalide!")"""
                destinator = str(sheet.cell(row, 2).value)
                # horaires = str(sheet.cell(row, 3).value)
                colis_modele = str(sheet.cell(row, 3).value)
                weight = str(sheet.cell(row, 4).value)
                p_value = str(sheet.cell(row, 5).value)
                return_of_fund = str(sheet.cell(row, 6).value)
                return_amount = str(sheet.cell(row, 7).value)
                doc_type1 = str(sheet.cell(row, 8).value)
                doc_ref1 = str(sheet.cell(row, 9).value)
                doc_type2 = str(sheet.cell(row, 10).value)
                doc_ref2 = str(sheet.cell(row, 11).value)
                doc_type3 = str(sheet.cell(row, 12).value)
                doc_ref3 = str(sheet.cell(row, 13).value)
                doc_type4 = str(sheet.cell(row, 14).value)
                doc_ref4 = str(sheet.cell(row, 15).value)
                doc_type5 = str(sheet.cell(row, 16).value)
                doc_ref5 = str(sheet.cell(row, 17).value)
                ref_ext = str(sheet.cell(row, 18).value)
                code_barre = str(sheet.cell(row, 19).value)  # modif
                nature_marchandise = str(sheet.cell(row, 20).value)
                notes = str(sheet.cell(row, 21).value)  # modif

                if expeditor == '' and doc_type1 == '' and destinator == '' and doc_ref1 == '' and doc_type2 == '' and doc_ref2 == '' and doc_type3 == '' and doc_ref3 == '' and doc_type4 == '' and doc_ref4 == '' and doc_type5 == '' and doc_ref5 == '' and weight == '' and colis_modele == '' and p_value == '' and return_of_fund == '' and return_amount == '' and ref_ext == '' and code_barre == '' and nature_marchandise == '' and notes == '':
                    # error_line.append("La ligne %s n'a pas d'informations définie, elle sera ignorée" % row)
                    warning_line.append(
                        "La ligne %s n'a pas d'informations définie, elle est considérée comme fin du canevas." % (
                            row + 1))
                    break
                nb_colis += 1
                error = False
                try:
                    if code_barre != '':
                        if code_barre[0] != '0':
                            code_barre = int(float(code_barre))  # modif
                except Exception as e:
                    _logger.error(str(e))

                if weight == '':
                    error = True
                    error_line.append(
                        "La ligne %s a une valeur de poids non définie." % (
                            row + 1))
                elif weight == '0':
                    error = True
                    error_line.append(
                        "La ligne %s a 0 comme valeur de poids." % (
                            row + 1))
                elif float(weight) < 1:
                    error = True
                    error_line.append(
                        "La ligne %s a 0 Le poids de colis Invalide!." % (
                            row + 1))              
                else:
                    try:
                        weight = float(weight)
                        if weight > contract.max_weight:
                            error = True
                            error_line.append(
                                "Le poids du colis de la ligne %s excède le poids maximal autorisé. Veuillez mettre un poids inférieur à %s kg" % (
                                    (row + 1), contract.max_weight))

                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a le poids de colis invalide!" % (
                                row + 1))
                if p_value != '':
                    if float(p_value) < 0:
                        error = True
                        error_line.append(
                        "La ligne %s a une Valeur du produit à assurer en DH Invalide!." % (
                            row + 1))                

                if expeditor == '':
                    expeditor = self.customer_id.id
                    source = self.customer_id.destination_id
                    if not source:
                        error = True
                        error_line.append(
                            "L'adresse d'expédition %s n'a pas de ville associée, merci de la préciser." % expeditor)
                else:
                    the_name = expeditor
                    expeditor_partner = self.existing_partner(expeditor)
                    if not expeditor_partner:
                        error = True
                        error_line.append(
                            "L'adresse d'expédition ne peut être ajouter car le client de la demande n'a pas de ville associée.")
                    else:
                        if not expeditor_partner.destination_id:
                            error = True
                            error_line.append(
                                "L'adresse d'expédition %s n'a pas de ville associée, merci de la préciser." % expeditor)

                if destinator == '':
                    error = True
                    error_line.append(
                        "La ligne %s n'a pas d'adresse de livraison définie." % (
                            row + 1))
                else:
                    the_name = destinator
                    destinator_partner = self.existing_partner(the_name)
                    if not destinator_partner:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur d'adresse de livraison incorrecte." % (
                                row + 1))
                    else:
                        destinator = destinator_partner
                        if not destinator.destination_id:
                            error = True
                            error_line.append(
                                "L'addresse de livraison %s n'a pas de ville associée, merci de la préciser sur votre carnet de livraison." % destinator_partner.name)

                if colis_modele == '':
                    error = True
                    error_line.append(
                        "La ligne %s n'a pas de modèle de colis défini." % (
                            row + 1))
                else:
                    colis_modele_id = self.existing_colis_modele(
                        colis_modele)
                    if not colis_modele_id:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de modèle de colis incorrecte." % (
                                row + 1))
                if p_value != '':
                    try:
                        p_value = float(p_value)
                        if p_value == 0:
                            e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                            r = ""
                            warning_line.append(
                                "La ligne %s a  une valeur du produit à assurer en DH nulle. %s %s" % (
                                    (row + 1), e, r))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de produit en DH incorrecte" % (
                                row + 1))
                else:
                    e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                    r = ""
                    warning_line.append(
                        "La ligne %s a  une valeur du produit à assurer en DH nulle. %s %s" % (
                            (row + 1), e, r))
                if return_of_fund != '':
                    return_of_fund = self.existing_fund(
                        return_of_fund)
                    if not return_of_fund:
                        error = True
                        return_of_fund = False
                        error_line.append(
                            "La ligne %s a une méthode contre remboursement incorrecte" % (
                                row + 1))
                    else:
                        return_of_fund = return_of_fund.id
                else:
                    # error = True
                    return_of_fund = False
                    warning_line.append(
                        "La ligne %s n'a pas de méthode contre remboursement" % (
                            row + 1))

                if return_amount != '':
                    try:
                        return_amount = float(return_amount)
                        return_f = self.env['sls.return.method'].sudo().browse(
                            return_of_fund) if return_of_fund else False
                        if return_f:
                            if return_f.montant_obligatoire and return_amount <= 0:
                                error = True
                                error_line.append(
                                    "La ligne %s a une valeur de montant contre remboursement en DH égale à 0 bien qu'une méthode contre remboursement aie été spécifié." % (
                                        row + 1))
                        else:
                            error = True
                            error_line.append(
                                "La ligne %s n'a pas de méthode contre remboursement" % (
                                        row + 1))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de montant contre remboursement en DH incorrecte" % (
                                row + 1))
                else:
                    return_f = self.env['sls.return.method'].sudo().browse(
                        return_of_fund) if return_of_fund else False
                    if return_f and return_f.montant_obligatoire:
                        error = True
                        error_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))

                # if horaires == '':
                #     error = True
                #     error_line.append("La ligne %s n'a pas de valeur d'horaires de livraisons" % (row + 1))

                if doc_type1 != '':
                    doc1 = self.existing_doc_type(doc_type1)
                    if not doc1:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 1 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref1:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 1 précisé." % (
                            row + 1))

                if doc_type2 != '':
                    doc2 = self.existing_doc_type(doc_type2)
                    if not doc2:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 2 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref2:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 2 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 2 précisé." % (
                            row + 1))

                if doc_type3 != '':
                    doc3 = self.existing_doc_type(doc_type3)
                    if not doc3:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 3 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref3:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 3 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 3 précisé." % (
                            row + 1))

                if doc_type4 != '':
                    doc4 = self.existing_doc_type(doc_type4)
                    if not doc4:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 4 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref4:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 4 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 4 précisé." % (
                            row + 1))

                if doc_type5 != '':
                    doc5 = self.existing_doc_type(doc_type5)
                    if not doc5:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 5 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref5:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 5 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 5 précisé." % (
                            row + 1))

                if ref_ext == '':
                    warning_line.append(
                        "La ligne %s n'a pas de référence externe de colis renseigné." % (
                            row + 1))

                if notes == '':
                    warning_line.append(
                        "La ligne %s n'a pas de commentaires renseignés sur le colis." % (
                            row + 1))

                if code_barre == '':
                    warning_line.append(
                        "Aucun code barre n'a été indiqué ur la ligne %s, vous pouvez en renseigner sur la colonne Code Barre avant importation" % (
                            row + 1))
                else:
                    _partner = self.customer_id
                    prefix = _partner.prefix and _partner.prefix or ''
                    code_barre_concat = "%s%s" % (prefix, code_barre)
                    code_barre_exist_or_not = self.env['sochepress.customer.request.line'].code_barre_exist(
                        code_barre_concat)
                    if code_barre_exist_or_not:
                        error = True
                        error_line.append(
                            "La ligne %s a un code barre déjà existant, veuillez en renseigner un autre." % (row + 1))

                if nature_marchandise != '':
                    nature_marchandise = self.existing_nature(nature_marchandise)
                    if not nature_marchandise:
                        warning_line.append(
                            "La ligne %s a une nature de marchandise inexistante, elle ne sera pas ajoutée" % (row + 1))
                else:
                    nature_marchandise = False
                    warning_line.append(
                        "La ligne %s n'a pas de nature de marchandise" % (row + 1))

                if notes == '':
                    warning_line.append(
                        "La ligne %s n'a pas de commentaires renseignés sur le colis." % (
                            row + 1))

                if not error:
                    correct_colis += 1
                else:
                    rejected_colis += 1
            else:
                error_line.append(
                    "Vous n'avez pas de type de client autorisant une importation de commande, merci de contacter l'équipe SLS.")
                break

        listToStr_errors = '\n'.join(map(str, error_line))
        listToStr_warnings = '\n'.join(map(str, warning_line))
        if len(listToStr_errors) > 0:
            self.errors = listToStr_errors
        else:
            self.errors = False
        if len(listToStr_warnings) > 0:
            self.warning = listToStr_warnings
        else:
            self.warning = False
        self.tested += 1
        if not self.type:
            self.type = 'normal'
        new_wizard = self.env['sochepress.req.wiz'].create(
            {'customer_id': self.customer_id.id, 'type': self.type, 'cavenas': self.cavenas,
             'canevas_name': self.canevas_name, 'errors': self.errors, 'warning': self.warning})
        view_id = self.env.ref('sochepress_base.sochepress_req_wizard_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sochepress.req.wiz',
            'view_mode': 'form',
            'res_id': new_wizard.id,
            'views': [(view_id, 'form')],
            'target': 'new',
        }

    def import_request(self):
        # Attachment = self.env['ir.attachment'].sudo()
        partner = self.customer_id.id
        contract = self.env['sochepress.contract'].sudo().search(
            [('stage_id', '=', self.env.ref(
                'sochepress_base.sochepress_contract_stage_in_progress').id),
             ('partner_id', '=', partner)], limit=1)
        vals = {
            'customer_id': partner,
            'contract_id': contract.id,
            'creation_type': 'importation',
            'state': 'waiting'
        }
        colis = []
        error_line = []
        warning_line = []
        created_deliveries = 0
        nb_colis = 0
        correct_colis = 0
        rejected_colis = 0
        if not self.cavenas:
            raise ValidationError('You must add a canevas')

        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.cavenas))
        sheet = wb.sheets()[0]
        # row_index = 1
        # print("========>", row_index)
        # while row_index < sheet.nrows:
        #     limit = sheet.nrows if (row_index + 40) > sheet.nrows else (row_index + 40)
        #     print("========>", row_index)
        #
        #     row_index += 40
        for row in range(1, sheet.nrows):
            expeditor = str(sheet.cell(row, 1).value)
            volume = 0
            colis_type_id = False
            product_id = False
            doc1 = False
            doc2 = False
            doc3 = False
            doc4 = False
            doc5 = False
            if self.customer_id.client_type in ['ecommercant', 'b2c']:
                """if int(sheet.cell(row, 9).value) < 1:
                    raise ValidationError("Le poids de colis Invalide!")
                if int(sheet.cell(row, 10).value) < 0:
                    raise ValidationError("La Valeur du produit à assurer en DH Invalide!")"""
                destinator = str(sheet.cell(row, 2).value)
                d_email = str(sheet.cell(row, 3).value)
                d_tel = str(sheet.cell(row, 4).value)
                destination = str(sheet.cell(row, 5).value)
                d_zip = str(sheet.cell(row, 6).value)
                d_street = str(sheet.cell(row, 7).value)
                colis_modele = str(sheet.cell(row, 8).value)
                weight = str(sheet.cell(row, 9).value)
                p_value = str(sheet.cell(row, 10).value)
                return_of_fund = str(sheet.cell(row, 11).value)
                return_amount = str(sheet.cell(row, 12).value)
                ref_ext = str(sheet.cell(row, 13).value)
                nature_marchandise = ''
                doc_type1 = ''
                doc_ref1 = ''
                doc_type2 = ''
                doc_ref2 = ''
                doc_type3 = ''
                doc_ref3 = ''
                doc_type4 = ''
                doc_ref4 = ''
                doc_type5 = ''
                doc_ref5 = ''
                notes = ''

                if self.customer_id.client_type == 'b2c':
                    doc_type1 = str(sheet.cell(row, 14).value)
                    doc_ref1 = str(sheet.cell(row, 15).value)
                    doc_type2 = str(sheet.cell(row, 16).value)
                    doc_ref2 = str(sheet.cell(row, 17).value)
                    doc_type3 = str(sheet.cell(row, 18).value)
                    doc_ref3 = str(sheet.cell(row, 19).value)
                    doc_type4 = str(sheet.cell(row, 20).value)
                    doc_ref4 = str(sheet.cell(row, 21).value)
                    doc_type5 = str(sheet.cell(row, 22).value)
                    doc_ref5 = str(sheet.cell(row, 23).value)
                    nature_marchandise = str(sheet.cell(row, 24).value)
                    notes = str(sheet.cell(row, 25).value)
                else:
                    nature_marchandise = str(sheet.cell(row, 14).value)
                    notes = str(sheet.cell(row, 15).value)

                custom_destination = False

                if expeditor == '' and d_zip == '' and destinator == '' and destination == '' and d_email == '' and d_tel == '' and d_street == '' and weight == '' and colis_modele == '' and p_value == '' and return_of_fund == '' and return_amount == '' and ref_ext == '' and nature_marchandise == '' and notes == '':
                    # error_line.append("La ligne %s n'a pas d'informations définie, elle sera ignorée" % row)
                    warning_line.append(
                        "La ligne %s n'a pas d'informations définie, elle est considérée comme fin du canevas." % (
                            row + 1))
                    break
                nb_colis += 1
                colis_type_id = False
                error = False
                if weight == '':
                    error = True
                    error_line.append(
                        "La ligne %s a une valeur de poids non définie." % (
                            row + 1))
                elif weight == '0':
                    error = True
                    error_line.append(
                        "La ligne %s a 0 comme valeur de poids." % (
                            row + 1))
                elif float(weight) < 1:
                    error = True
                    error_line.append(
                        "La ligne %s a 0 Le poids de colis Invalide!." % (
                            row + 1))              
                else:
                    try:
                        weight = float(weight)
                        if 1 <= weight <= 30:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_colis').id
                        if 31 <= weight <= 100:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_petite_palette').id
                        if 101 <= weight <= 300:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_moyenne_palette').id
                        if weight >= 301:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_grande_palette').id
                        if weight > contract.max_weight:
                            error = True
                            error_line.append(
                                "Le poids du colis de la ligne %s excède le poids maximal autorisé. Veuillez mettre un poids inférieur à %s kg" % (
                                    (row + 1), contract.max_weight))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a le poids de colis invalide!" % (
                                row + 1))
                if p_value != '':                
                    if float(p_value) < 0:
                            error = True
                            error_line.append(
                            "La ligne %s a une Valeur du produit à assurer en DH Invalide!." % (
                                row + 1))                

                # print("==============<<>>==============")
                if expeditor == '':
                    expeditor = self.customer_id
                    source = expeditor.destination_id
                    if not source:
                        error = True
                        error_line.append(
                            "L'adresse d'expédition %s n'a pas de ville associée, merci de la préciser." % expeditor)
                else:
                    the_name = expeditor
                    expeditor_partner = self.existing_partner(expeditor)
                    if not expeditor_partner:
                        source = self.customer_id.destination_id
                        if source:
                            warning_line.append(
                                "L'adresse d'expédition %s de la ligne %s sera nouvellement crée, vous pouvez le voire sur la liste de vos expéditeurs." % (
                                    the_name, (row + 1)))
                            expeditor_partner = self.env[
                                'res.partner'].sudo().create({
                                'type': 'other',
                                'name': expeditor,
                                'destination_id': source.id if source else False,
                                'city': source.name,
                                'parent_id': self.customer_id.id
                            })
                            expeditor = expeditor_partner
                        else:
                            error = True
                            error_line.append(
                                "L'adresse d'expédition ne peut être ajouter car le client de la demande n'a pas de ville associée.")
                    else:
                        source = expeditor_partner.destination_id
                        if not source:
                            error = True
                            error_line.append(
                                "L'addresse d'expédition %s n'a pas de ville associée, merci de la préciser sur votre carnet d'expédition ." % expeditor)
                        expeditor = expeditor_partner

                d_check_ok = True
                if destinator == '':
                    error = True
                    d_check_ok = False
                    error_line.append(
                        "La ligne %s n'a pas de nom de client final." % (
                            row + 1))

                d_tel = "0%s" % str(d_tel.split('.')[0]) if \
                    d_tel.split('.')[0] and str(
                        d_tel.split('.')[0][0]) != '0' else str(
                    d_tel.split('.')[0])

                if d_tel == '':
                    error = True
                    d_check_ok = False
                    error_line.append(
                        "La ligne %s n'a pas de téléphone de client final." % (
                            row + 1))
                else:
                    pattern = r"(08|07|06|05|04)\d{8}"
                    test_string = d_tel
                    result = re.match(pattern, test_string)
                    if result:
                        # The value match the pattern
                        pass
                    else:
                        error = True
                        d_check_ok = True
                        error_line.append(
                            "La ligne %s a un format de telephone incorrect, le format correct est : 06xxxxxxxxx." % (
                                row + 1))

                    # TODO ajouter le code de check de formal du téléphone ici si non okay ajouter le code error_line.append("La ligne %s a un format de telephone incorrect, le format correct est+212xxxxxx")
                    # TODO mettre error = True et d_check_ok = True

                if d_email == '':
                    # error = True
                    # d_check_ok = False
                    warning_line.append(
                        "La ligne %s n'a pas d'email de client final." % (
                            row + 1))
                else:
                    pattern = r'[^@]+@[^@]+\.[^@]+'
                    test_string = d_email
                    result = re.match(pattern, test_string)
                    if result:
                        # The value match the pattern
                        pass
                    else:
                        # error = True
                        # d_check_ok = True
                        warning_line.append(
                            "La ligne %s a un format d'email incorrect, le format correct est : monemail@test.com." % (
                                row + 1))
                    # TODO ajouter le code de check de formal de l'email ici
                    # TODO meme chose que les checks sur le telephone
                    pass

                if destination == '':
                    error = True
                    d_check_ok = False
                    error_line.append(
                        "La ligne %s n'a pas de ville du client final défini." % (
                            row + 1))
                else:
                    destination_id = self.existing_location(destination)
                    custom_destination = destination
                    destination = destination_id

                if d_zip == '':
                    # error = True
                    # d_check_ok = False
                    warning_line.append(
                        "La ligne %s n'a pas de code postal de client final." % (
                            row + 1))
                else:
                    pattern = r"\b\d{5}\b"
                    test_string = d_zip
                    result = re.match(pattern, test_string)
                    if result:
                        pass
                        # The value match the pattern
                    else:
                        # error = True
                        # d_check_ok = True
                        warning_line.append(
                            "La ligne %s a un format de code zip incorrect, le format correct se compose de 5 chiffres : par ex. 72000." % (
                                row + 1))
                    # TODO ajouter le code de check du code zip ici
                    # TODO meme chose que le telephone

                if d_street == '':
                    error = True
                    d_check_ok = False
                    error_line.append(
                        "La ligne %s n'a pas d'adresse de client final." % (
                            row + 1))
                else:
                    pattern = r'(?=.*?\b[0-9]{1,3}\b)((?:[^a-zA-Z]*[a-zA-Z])){3,}.*'
                    test_string = d_street
                    result = re.match(pattern, test_string)
                    if result:
                        # The value match the pattern
                        pass
                    else:
                        error = True
                        d_check_ok = True
                        error_line.append(
                            "La ligne %s a un format d'adresse incorrect, Merci de saisir une adresse détaillée (Un minimum de 2 mots et un chiffre), les symboles (:,-,_,°,...) ne sont pas acceptés." % (
                                row + 1))
                    # TODO ajouter le code de check de formal des addresses ici
                    pass

                if d_check_ok:
                    name = destinator
                    destinator_partner = self.existing_partner(name, d_tel)
                    created_deliveries += 1
                    if not destinator_partner:
                        destinator_partner = self.env[
                            'res.partner'].sudo().create({
                            'type': 'delivery',
                            'name': name,
                            'email': d_email,
                            'mobile': d_tel,
                            'phone': d_tel,
                            'destination_id': destination.id if destination else False,
                            'zip': d_zip,
                            'city': custom_destination,
                            'street': d_street,
                            'parent_id': self.customer_id.id
                        })

                    destinator = destinator_partner
                    # else:
                    #     destinator.write({
                    #         'type': 'delivery',
                    #         'name': name,
                    #         'email': d_email,
                    #         'mobile': d_tel,
                    #         'phone': d_tel,
                    #         'destination_id': destination.id if destination else False,
                    #         'zip': d_zip,
                    #         'city': custom_destination,
                    #         'street': d_street,
                    #         'parent_id': req.env.user.partner_id.id
                    #     })

                if colis_modele == '':
                    error = True
                    error_line.append(
                        "La ligne %s n'a pas de modèle de colis défini." % (
                            row + 1))
                else:
                    colis_modele_id = self.existing_colis_modele(
                        colis_modele)
                    if not colis_modele_id:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de modèle de colis incorrecte." % (
                                row + 1))
                    else:
                        product_id = colis_modele_id

                if p_value != '':
                    try:
                        p_value = float(p_value)
                        if p_value == 0:
                            e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                            r = ""
                            warning_line.append(
                                "La ligne %s a  une valeur du produit à assurer en DH nulle. %s" % (
                                    (row + 1), e))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de produit en DH incorrecte" % (
                                row + 1))
                else:
                    e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                    r = ""
                    warning_line.append(
                        "La ligne %s a  une valeur du produit à assurer en DH nulle. %s" % (
                            (row + 1), e))
                if return_of_fund != '':
                    return_of_fund = self.existing_fund(return_of_fund)
                    if not return_of_fund:
                        error = True
                        return_of_fund = False
                        error_line.append(
                            "La ligne %s a une méthode contre remboursement incorrecte" % (
                                row + 1))
                    else:
                        return_of_fund = return_of_fund
                else:
                    # error = True
                    return_of_fund = False
                    warning_line.append(
                        "La ligne %s n'a pas de méthode contre remboursement" % (
                            row + 1))

                if return_amount != '':
                    try:
                        return_amount = float(return_amount)
                        return_f = self.env['sls.return.method'].sudo().browse(
                            return_of_fund.id) if return_of_fund else False
                        if return_f:
                            if return_f.montant_obligatoire and return_amount <= 0:
                                error = True
                                error_line.append(
                                    "La ligne %s a une valeur de montant contre remboursement en DH égale à 0 bien qu'une méthode contre remboursement aie été spécifié." % (
                                        row + 1))
                        else:
                            error = True
                            error_line.append(
                                "La ligne %s n'a pas de méthode contre remboursement" % (
                                        row + 1))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de montant contre remboursement en DH incorrecte" % (
                                row + 1))
                else:
                    return_f = self.env['sls.return.method'].sudo().browse(
                        return_of_fund.id) if return_of_fund else False
                    if return_f and return_f.montant_obligatoire:
                        error = True
                        error_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))

                if ref_ext == '':
                    warning_line.append(
                        "La ligne %s n'a pas de référence externe de colis renseigné." % (
                            row + 1))
                if notes == '':
                    warning_line.append(
                        "La ligne %s n'a pas de commentaires renseignés sur le colis." % (
                            row + 1))

                if self.customer_id.client_type == 'b2c':
                    if doc_type1 != '':
                        doc1 = self.existing_doc_type(doc_type1)
                        if not doc1:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 1 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref1:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 1 précisé." % (
                                row + 1))

                    if doc_type2 != '':
                        doc2 = self.existing_doc_type(doc_type2)
                        if not doc2:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 2 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref2:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 2 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 2 précisé." % (
                                row + 1))

                    if doc_type3 != '':
                        doc3 = self.existing_doc_type(doc_type3)
                        if not doc3:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 3 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref3:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 3 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 3 précisé." % (
                                row + 1))

                    if doc_type4 != '':
                        doc4 = self.existing_doc_type(doc_type4)
                        if not doc4:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 4 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref4:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 4 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 4 précisé." % (
                                row + 1))

                    if doc_type5 != '':
                        doc5 = self.existing_doc_type(doc_type5)
                        if not doc5:
                            error = True
                            error_line.append(
                                "La ligne %s a une valeur de type de document 5 incorrecte" % (
                                    row + 1))
                        else:
                            if not doc_ref5:
                                warning_line.append(
                                    "La ligne %s n'a pas de référence de document 5 bien qu'un type de document ait été précisé." % (
                                        row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de type de document 5 précisé." % (
                                row + 1))
                if nature_marchandise != '':
                    nature_marchandise = self.existing_nature(nature_marchandise)
                    if not nature_marchandise:
                        warning_line.append(
                            "La ligne %s a une nature de marchandise inexistante, elle ne sera pas ajoutée" % (
                                row + 1))
                else:
                    nature_marchandise = False
                    warning_line.append(
                        "La ligne %s n'a pas de nature de marchandise" % (row + 1))
                if not error:
                    correct_colis += 1
                    colis_vals = {
                        'weight': weight,
                        'type_colis_id': colis_type_id,
                        'expeditor_id': expeditor.id if expeditor else False,
                        'source_id': source.id if source else False,
                        'destinator_id': destinator.id if destinator else False,
                        'destination_id': destination.id if destination else False,
                        'volume': product_id.volume if product_id else 0,
                        'product_id': product_id.id if product_id else False,
                        'declared_value': p_value,
                        'return_method_id': return_of_fund.id if return_of_fund else False,
                        'return_amount': return_amount,
                        'custom_destination': custom_destination,
                        'ref_ext': ref_ext,
                        'notes': notes,
                        'nature_marchandise': nature_marchandise.id if nature_marchandise else False,
                        'notes': notes,
                    }
                    docs = []
                    if doc1:
                        docs.append((0, 0, {'ref_doc': doc_ref1 and  doc_ref1 or '',
                                            'document_type_id': doc1.id}))

                    if doc2:
                        docs.append((0, 0, {'ref_doc': doc_ref2 and  doc_ref2 or '',
                                            'document_type_id': doc2.id}))
                    if doc3:
                        docs.append((0, 0, {'ref_doc': doc_ref3 and  doc_ref3 or '',
                                            'document_type_id': doc3.id}))
                    if doc4:
                        docs.append((0, 0, {'ref_doc': doc_ref4 and  doc_ref4 or '',
                                            'document_type_id': doc4.id}))
                    if doc5:
                        docs.append((0, 0, {'ref_doc': doc_ref5 and  doc_ref5 or '',
                                            'document_type_id': doc5.id}))


                    if docs:
                        colis_vals['document_ids'] = docs
                    colis.append(colis_vals)
                else:
                    rejected_colis += 1
            elif self.customer_id.client_type == 'b2b':
                # if int(sheet.cell(row, 4).value) < 1:
                #     raise ValidationError("Le poids de colis Invalide!")
                # if int(sheet.cell(row, 5).value) < 0:
                #     raise ValidationError("La Valeur du produit à assurer en DH Invalide!")
                destinator = str(sheet.cell(row, 2).value)
                # horaires = str(sheet.cell(row, 3).value)
                colis_modele = str(sheet.cell(row, 3).value)
                weight = str(sheet.cell(row, 4).value)
                p_value = str(sheet.cell(row, 5).value)
                return_of_fund = str(sheet.cell(row, 6).value)
                return_amount = str(sheet.cell(row, 7).value)
                doc_type1 = str(sheet.cell(row, 8).value)
                doc_ref1 = str(sheet.cell(row, 9).value)
                doc_type2 = str(sheet.cell(row, 10).value)
                doc_ref2 = str(sheet.cell(row, 11).value)
                doc_type3 = str(sheet.cell(row, 12).value)
                doc_ref3 = str(sheet.cell(row, 13).value)
                doc_type4 = str(sheet.cell(row, 14).value)
                doc_ref4 = str(sheet.cell(row, 15).value)
                doc_type5 = str(sheet.cell(row, 16).value)
                doc_ref5 = str(sheet.cell(row, 17).value)
                ref_ext = str(sheet.cell(row, 18).value)
                code_barre = str(sheet.cell(row, 19).value)  # modif
                nature_marchandise = str(sheet.cell(row, 20).value)  # modif
                notes = str(sheet.cell(row, 21).value)  # modif
                if expeditor == '' and doc_type1 == '' and destinator == '' and doc_ref1 == '' and doc_type2 == '' and doc_ref2 == '' and doc_type3 == '' and doc_ref3 == '' and doc_type4 == '' and doc_ref4 == '' and doc_type5 == '' and doc_ref5 == '' and weight == '' and colis_modele == '' and p_value == '' and return_of_fund == '' and return_amount == '' and ref_ext == '' and code_barre == '' and nature_marchandise == '' and notes == '':
                    warning_line.append(
                        "La ligne %s n'a pas d'informations définie, elle est considérée comme fin du canevas." % (
                            row + 1))
                    break
                nb_colis += 1
                error = False
                try:
                    if code_barre != '':
                        if code_barre[0] != '0':
                            code_barre = int(float(code_barre))  # modif
                except Exception as e:
                    _logger.error(str(e))

                if weight == '':
                    error = True
                    error_line.append(
                        "La ligne %s a une valeur de poids non définie." % (
                            row + 1))
                elif weight == '0':
                    error = True
                    error_line.append(
                        "La ligne %s a 0 comme valeur de poids." % (
                            row + 1))
                elif float(weight) < 1:
                    error = True
                    error_line.append(
                        "La ligne %s a 0 Le poids de colis Invalide!." % (
                            row + 1))              
                else:
                    try:
                        weight = float(weight)
                        if 1 <= weight <= 30:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_colis').id
                        if 31 <= weight <= 100:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_petite_palette').id
                        if 101 <= weight <= 300:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_moyenne_palette').id
                        if weight >= 301:
                            colis_type_id = self.env.ref(
                                'sochepress_base.colis_type_grande_palette').id
                        if weight > contract.max_weight:
                            error = True
                            error_line.append(
                                "Le poids du colis de la ligne %s excède le poids maximal autorisé. Veuillez mettre un poids inférieur à %s kg" % (
                                    (row + 1), contract.max_weight))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a le poids de colis invalide!" % (
                                row + 1))

                if p_value != '':
                    if float(p_value) < 0:
                        error = True
                        error_line.append(
                        "La ligne %s a une Valeur du produit à assurer en DH Invalide!." % (
                            row + 1))                

                if expeditor == '':
                    expeditor = self.customer_id.id
                    source = self.customer_id.destination_id
                    # if not source:
                    #     error = True
                    #     error_line.append(
                    #         "L'addresse d'expédition %s n'a pas de ville associée, merci de la préciser." % expeditor)
                else:
                    the_name = expeditor
                    expeditor_partner = self.existing_partner(the_name)
                    if not expeditor_partner:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur d'addresse d'expéditeur incorrecte." % (
                                row + 1))
                    else:
                        # if not expeditor_partner.destination_id:
                        #     error = True
                        #     error_line.append(
                        #         "L'addresse d'expédition %s n'a pas de ville associée, merci de la préciser sur votre carnet d'expéditions" % expeditor)
                        expeditor = expeditor_partner
                # if horaires == '':
                #     error = True
                #     error_line.append("La ligne %s n'a pas de valeur d'horaires de livraisons" % (row + 1))

                if destinator == '':
                    error = True
                    error_line.append(
                        "La ligne %s n'a pas d'addresse de livraison définie." % (
                            row + 1))
                else:
                    the_name = destinator
                    destinator_partner = self.existing_partner(the_name)
                    if not destinator_partner:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur d'addresse de livraison incorrecte." % (
                                row + 1))
                    else:
                        destinator = destinator_partner
                        # if not destinator.destination_id:
                        #     error = True
                        #     error_line.append(
                        #         "L'addresse de livraison %s n'a pas de ville associée, merci de la préciser sur votre carnet de livraison." % expeditor)

                if colis_modele == '':
                    error = True
                    error_line.append(
                        "La ligne %s n'a pas de modèle de colis défini." % (
                            row + 1))
                else:
                    colis_modele_id = self.existing_colis_modele(
                        colis_modele)
                    if not colis_modele_id:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de modèle de colis incorrecte. %s" % (
                                row + 1,colis_modele))

                    else:
                        product_id = colis_modele_id

                if p_value != '':
                    try:
                        p_value = float(p_value)
                        if p_value == 0:
                            e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                            r = ""
                            warning_line.append(
                                "La ligne %s a  une valeur du produit à assurer en DH nulle. %s" % (
                                    (row + 1), e))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de produit en DH incorrecte" % (
                                row + 1))
                else:
                    e = "Pour protéger votre colis, nous vous recommandons de contracter notre assurance et déclarer la valeur du produit, Cette garantie vous permet d'être indemnisé du montant de l'<strong>assurance</strong> souscrite si vous subissez une perte ou une <strong>détérioration</strong> de votre <strong>colis</strong>."
                    r = "<br /><strong t-if='len(error)<=0''>Si vous souhaitez continuer sans indiquer la valeur du produit, Merci de cliquer sur <i>Continuer l'importation</i></strong>"
                    warning_line.append(
                        "La ligne %s a  une valeur du produit à assurer en DH nulle. %s" % (
                            (row + 1), e))

                if return_of_fund != '':
                    return_of_fund = self.existing_fund(
                        return_of_fund)
                    if not return_of_fund:
                        error = True
                        return_of_fund = False
                        error_line.append(
                            "La ligne %s a une méthode contre remboursement incorrecte" % (
                                row + 1))
                    else:
                        return_of_fund = return_of_fund.id
                else:
                    # error = True
                    return_of_fund = False
                    warning_line.append(
                        "La ligne %s n'a pas de méthode contre remboursement" % (
                            row + 1))

                if return_amount != '':
                    try:
                        return_amount = float(return_amount)
                        return_f = self.env['sls.return.method'].sudo().browse(
                            return_of_fund) if return_of_fund else False
                        if return_f:
                            if return_f.montant_obligatoire and return_amount <= 0:
                                error = True
                                error_line.append(
                                    "La ligne %s a une valeur de montant contre remboursement en DH égale à 0 bien qu'une méthode contre remboursement aie été spécifié." % (
                                        row + 1))
                        else:
                            error = True
                            error_line.append(
                                "La ligne %s n'a pas de méthode contre remboursement" % (
                                        row + 1))
                    except ValueError:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de montant contre remboursement en DH incorrecte" % (
                                row + 1))
                else:
                    return_f = self.env['sls.return.method'].sudo().browse(
                        return_of_fund) if return_of_fund else False
                    if return_f and return_f.montant_obligatoire:
                        error = True
                        error_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))
                    else:
                        warning_line.append(
                            "La ligne %s n'a pas de valeur de montant contre remboursement définie." % (
                                row + 1))

                if doc_type1 != '':
                    doc1 = self.existing_doc_type(doc_type1)
                    if not doc1:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 1 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref1:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 1 précisé." % (
                            row + 1))

                if doc_type2 != '':
                    doc2 = self.existing_doc_type(doc_type2)
                    if not doc2:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 2 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref2:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 2 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 2 précisé." % (
                            row + 1))

                if doc_type3 != '':
                    doc3 = self.existing_doc_type(doc_type3)
                    if not doc3:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 3 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref3:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 3 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 3 précisé." % (
                            row + 1))

                if doc_type4 != '':
                    doc4 = self.existing_doc_type(doc_type4)
                    if not doc4:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 4 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref4:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 4 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 4 précisé." % (
                            row + 1))

                if doc_type5 != '':
                    doc5 = self.existing_doc_type(doc_type5)
                    if not doc5:
                        error = True
                        error_line.append(
                            "La ligne %s a une valeur de type de document 5 incorrecte" % (
                                row + 1))
                    else:
                        if not doc_ref5:
                            warning_line.append(
                                "La ligne %s n'a pas de référence de document 5 bien qu'un type de document ait été précisé." % (
                                    row + 1))
                else:
                    warning_line.append(
                        "La ligne %s n'a pas de valeur de type de document 5 précisé." % (
                            row + 1))

                if ref_ext == '':
                    warning_line.append(
                        "La ligne %s n'a pas de référence externe de colis renseigné." % (
                            row + 1))

                if notes == '':
                    warning_line.append(
                        "La ligne %s n'a pas de commentaires renseignés sur le colis." % (
                            row + 1))

                if nature_marchandise != '':
                    nature_marchandise = self.existing_nature(nature_marchandise)
                    if not nature_marchandise:
                        warning_line.append(
                            "La ligne %s a une nature de marchandise inexistante, elle ne sera pas ajoutée" % (
                                row + 1))
                else:
                    nature_marchandise = False
                    warning_line.append(
                        "La ligne %s n'a pas de nature de marchandise" % (row + 1))
                # modif
                if notes == '':
                    warning_line.append(
                        "La ligne %s n'a pas de commentaires renseignés sur le colis." % (
                            row + 1))

                code_barre_concat = ''
                if code_barre == '':
                    warning_line.append(
                        "Aucun code barre n'a été indiqué pour la ligne %s, vous pouvez en renseigner sur la colonne Code barre avant importation" % (
                            row + 1))
                else:
                    _partner = self.customer_id
                    prefix = _partner.prefix and _partner.prefix or ''
                    # if not prefix:
                    #     error = True
                    #     error_line.append(
                    #         "Le préfixe du client %s n'a pas été renseigné." % (row + 1))

                    code_barre_concat = "%s%s" % (prefix, code_barre)
                    code_barre_exist_or_not = self.env[
                        'sochepress.customer.request.line'].code_barre_exist(code_barre_concat)
                    if code_barre_exist_or_not:
                        error = True
                        error_line.append(
                            "La ligne %s a un code barre déjà existant, veuillez en renseigner un autre." % (row + 1))

                if not error:

                    colis_vals = {
                        'type_colis_id': colis_type_id,
                        'expeditor_id': expeditor.id,
                        'source_id': expeditor.destination_id.id if expeditor.destination_id else False,
                        'destinator_id': destinator.id,
                        'horaires': destinator.horaires,
                        'destination_id': destinator.destination_id.id if destinator.destination_id else False,
                        'volume': product_id.volume,
                        'product_id': product_id.id,
                        'declared_value': p_value,
                        'return_method_id': return_of_fund,
                        'return_amount': return_amount,
                        'weight': weight,
                        'ref_ext': ref_ext,
                        'barcode': code_barre_concat,
                        'notes': notes,
                        'nature_marchandise': nature_marchandise.id if nature_marchandise else False,
                        'notes': notes,
                        # 'portal': 1,
                    }
                    docs = []
                    if doc1:
                        docs.append((0, 0, {'ref_doc': doc_ref1 and  doc_ref1 or '',
                                            'document_type_id': doc1.id}))

                    if doc2:
                        docs.append((0, 0, {'ref_doc': doc_ref2 and  doc_ref2 or '',
                                            'document_type_id': doc2.id}))
                    if doc3:
                        docs.append((0, 0, {'ref_doc': doc_ref3 and  doc_ref3 or '',
                                            'document_type_id': doc3.id}))
                    if doc4:
                        docs.append((0, 0, {'ref_doc': doc_ref4 and  doc_ref4 or '',
                                            'document_type_id': doc4.id}))
                    if doc5:
                        docs.append((0, 0, {'ref_doc': doc_ref5 and  doc_ref5 or '',
                                            'document_type_id': doc5.id}))

                    if docs:
                        colis_vals['document_ids'] = docs
                    colis.append(colis_vals)
                    correct_colis += 1

                else:
                    rejected_colis += 1
            else:
                error_line.append(
                    "Vous n'avez pas de type de client autorisant une importation de commande, merci de contacter l'équipe SLS.")
                break
            # attachment.unlink()

        # vals['request_line_ids'] = colis
        vals['error_line'] = '<br />'.join(error_line)
        vals['warning_line'] = '<br />'.join(warning_line)
        vals['rejected_colis'] = rejected_colis
        vals['correct_colis'] = correct_colis
        vals['nb_colis'] = nb_colis
        vals['created_deliveries'] = created_deliveries
        vals['type'] = self.type
        vals['portal'] = 0

        # pprint(vals)
        # print('================================++>')
        if len(error_line) == 0:
            request_id = False
            if len(colis) > 0:
                request_id = self.env['sochepress.customer.request'].sudo().create(vals)
            index = 0
            colis_list = []
            while index < len(colis):
                colis_datas = colis[index:index + 30]
                colis_list.append(colis_datas)
                index = index + 30
            ind = 0
            for colis_data in colis_list:
                for col in colis_data:
                    col['portal'] = 0
                    colis_id = self.env['sochepress.customer.request.line'].sudo().create(
                        col)
                    colis_id.request_id = request_id.id
                    ind += 1
            if request_id.customer_id.auto_accept_demand:
                val = request_id.verified_action()
                if val:
                    return val
                request_id.accepted_action()
            # self.flush()
            # request_id.generate_expedition()
            # request_id.generate_request_services()
            # request_id.generate_expeditions_services()
            # request_id.generate_colis_services()
            # print("==================> creating")
            # request_id = self.env['sochepress.customer.request'].sudo().create(
            #     vals)
        else:
            raise ValidationError(
                _('You must correct the errors before importing the canvas!'+str(vals['error_line'])))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sochepress.customer.request',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'sochepress_base.customer_request_form_view').id,
            'res_id': request_id.id,
            # 'views': [(False, 'form')],
        }
