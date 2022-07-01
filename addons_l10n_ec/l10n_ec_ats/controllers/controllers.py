from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import osutil


class FileExporter(http.Controller):
    @http.route("""/web/export/<model('account.ats'):ats_id>""",
                type='http', auth="user")
    def index(self, ats_id):
        return request.make_response(
            ats_id._get_data, 
            headers=[('Content-Disposition',
                        content_disposition(osutil.clean_filename(f'{ats_id.name.strftime("%Y%m%d")}_ats.xml' ))
                     ), 
                     ('Content-Type', 'application/atom+xml')
                    ],
        )