from email.policy import default
from odoo import api, fields,models


class BatchEdiWebService(models.AbstractModel):
    _name = 'batch.edi.web.service'
    _description = 'batch.edi.web.service'
    document_model = 'account.move'
    document_date = 'date'
    document_types = ('move_type', 'in',('out_invoice',))
    document_state = ('edi_state', '=', 'to_send')

    date = fields.Date(default=fields.Date.today())
    document_ids =  fields.Many2many(
        document_model,
        domain=lambda s: f'[{s.document_state}, {s.document_types}]',
        default=lambda s: s.env.context.get('active_ids')
    )


    @api.onchange('date')
    def onchange_date(self):
        self.document_ids = [(5, )]
        self.document_ids = [(6, 0, self._get_record_by_date().ids)]

    def _get_record_by_date(self):
        return self.env[self.document_model].search([
            (self.document_date, '=', self.date),
            self.document_state,
            self.document_types
        ])
    
    def _get_record_ids(self):
        if self.document_ids:
            return self.document_ids
        return self._get_record_by_date()

    def action_process_edi_web_services(self):
        records = self._get_record_ids()
        if not records: return
        [
            doc.action_process_edi_web_services()
            for doc in records
        ]
        action = self.env.ref('l10n_ec_nmit.batch_move_edi_web_service_action').read()
        return {
            **action[0],
            'res_id': self.id,
        }


class BatchMoveEdiWebService(models.Model):
    _name = 'batch.move.edi.web.service'
    _inherit = 'batch.edi.web.service'


class BatchWhEdiWebService(models.Model):
    _name = 'batch.wh.edi.web.service'
    _inherit = 'batch.edi.web.service'
    document_model = 'account.wh'
    document_date = 'date'
    document_types = ('move_type', '=','in_invoice')
    document_state = ('move_id.edi_state', '=', 'to_send')

    document_ids =  fields.Many2many(
        document_model,
        domain=lambda s: f'[{s.document_state}, {s.document_types}]',
        default=lambda s: s.env.context.get('active_ids')
    )