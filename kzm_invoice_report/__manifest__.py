# -*- coding: utf-8 -*-
{
    'name': "Invoice Report",
    'summary': """Invoice Report """,
    'description': """
        * Personnaliser l'adresse
        * Code / Designation
        * Désactiver la colone taxe
        * Ajouter le montant totale en lettre
        * Ajouter totale remise
        * Ajouter les information de la banque """,
    'author': "KARIZMA CONSEIL",
    'website': 'http://www.karizma.ma',
    'category': 'Tools',
    'version': '13.0',
    'depends': ['base',
                'account',
                'kzm_base',
                'l10n_ma'
                ],
    'data': [
        'security/security.xml',
        'views/res_config_setting_view.xml',
        'reports/invoice_report.xml',
        'reports/invoice_report_without_header_footer.xml',
    ],
}
