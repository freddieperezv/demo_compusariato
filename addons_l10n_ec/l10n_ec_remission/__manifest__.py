# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Remisiones para Ecuador",
    "version": "15.0.1",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": ["l10n_ec_nmit", "stock"],
    "author": "NMIT",
    "website": "www.newmind-it.com",
    "data": [
        "security/ir.model.access.csv",
	    "data/remission.guide.reason.csv",
	    "data/l10n_latam.document.type.csv",
	    "data/eremission.xml",
	    "reports/report_eremission_guide.xml",
	    "views/account_move_view.xml",
	    "views/account_remission_guide_line_view.xml",
	    "views/account_remission_guide_view.xml",
	    "views/res_partner_view.xml",
    ]
}
