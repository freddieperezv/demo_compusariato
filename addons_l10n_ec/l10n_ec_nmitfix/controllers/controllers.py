# -*- coding: utf-8 -*-
# from odoo import http


# class L10nEcNmitfix(http.Controller):
#     @http.route('/l10n_ec_nmitfix/l10n_ec_nmitfix/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ec_nmitfix/l10n_ec_nmitfix/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ec_nmitfix.listing', {
#             'root': '/l10n_ec_nmitfix/l10n_ec_nmitfix',
#             'objects': http.request.env['l10n_ec_nmitfix.l10n_ec_nmitfix'].search([]),
#         })

#     @http.route('/l10n_ec_nmitfix/l10n_ec_nmitfix/objects/<model("l10n_ec_nmitfix.l10n_ec_nmitfix"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ec_nmitfix.object', {
#             'object': obj
#         })
