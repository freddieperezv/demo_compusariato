from odoo import fields, models, api

DEFAULT_BLOCKING_LEVEL = 'error'

class AccountEdiDocument(models.Model):
    _inherit = 'account.edi.document'

    def _prepare_jobs(self):
        to_process = {}
        documents = self.filtered(lambda d: d.state in ('to_send', 'to_cancel') and d.blocking_level != 'error')
        for edi_doc in documents:
            move = edi_doc.move_id
            edi_format = edi_doc.edi_format_id
            if move.is_invoice(include_receipts=True):
                doc_type = 'invoice'
            elif move.payment_id or move.statement_line_id:
                doc_type = 'payment'
            elif move.wh_id:
                doc_type = 'wh'
            else: continue
            custom_key = edi_format._get_batch_key(edi_doc.move_id, edi_doc.state)
            key = (edi_format, edi_doc.state, doc_type, move.company_id, custom_key)
            to_process.setdefault(key, self.env['account.edi.document'])
            to_process[key] |= edi_doc
        invoices = []
        payments = []
        for key, documents in to_process.items():
            edi_format, state, doc_type, company_id, custom_key = key
            target = invoices if doc_type == 'invoice' else payments
            batch = self.env['account.edi.document']
            for doc in documents:
                if edi_format._support_batching(move=doc.move_id, state=state, company=company_id):
                    batch |= doc
                else:
                    target.append((doc, doc_type))
            if batch:
                target.append((batch, doc_type))
        return invoices + payments

    @api.model
    def _process_job(self, documents, doc_type):
        def _postprocess_post_edi_results(documents, edi_result):
            attachments_to_unlink = self.env['ir.attachment']
            for document in documents:
                move = document.move_id
                move_result = edi_result.get(move, {})
                if move_result.get('attachment'):
                    old_attachment = document.attachment_id
                    document.attachment_id = move_result['attachment']
                    if not old_attachment.res_model or not old_attachment.res_id:
                        attachments_to_unlink |= old_attachment
                if move_result.get('success') is True:
                    document.state = 'sent'
                else:
                    document.write({
                        'error': move_result.get('error', False),
                        'blocking_level': move_result.get('blocking_level', DEFAULT_BLOCKING_LEVEL) if 'error' in move_result else False,
                    })
            attachments_to_unlink.unlink()
        def _postprocess_cancel_edi_results(documents, edi_result):
            invoice_ids_to_cancel = set()  # Avoid duplicates
            attachments_to_unlink = self.env['ir.attachment']
            for document in documents:
                move = document.move_id
                move_result = edi_result.get(move, {})
                if move_result.get('success') is True:
                    old_attachment = document.attachment_id
                    document.write({
                        'state': 'cancelled',
                        'error': False,
                        'attachment_id': False,
                        'blocking_level': False,
                    })
                    if move.is_invoice(include_receipts=True) and move.state == 'posted':
                        invoice_ids_to_cancel.add(move.id)
                    if not old_attachment.res_model or not old_attachment.res_id:
                        attachments_to_unlink |= old_attachment
                else:
                    document.write({
                        'error': move_result.get('error', False),
                        'blocking_level': move_result.get('blocking_level', DEFAULT_BLOCKING_LEVEL) if move_result.get('error') else False,
                    })
            if invoice_ids_to_cancel:
                invoices = self.env['account.move'].browse(list(invoice_ids_to_cancel))
                invoices.button_draft()
                invoices.button_cancel()
            attachments_to_unlink.unlink()
        documents.edi_format_id.ensure_one()  # All account.edi.document of a job should have the same edi_format_id
        documents.move_id.company_id.ensure_one()  # All account.edi.document of a job should be from the same company
        if len(set(doc.state for doc in documents)) != 1:
            raise ValueError('All account.edi.document of a job should have the same state')
        edi_format = documents.edi_format_id
        state = documents[0].state
        if doc_type == 'invoice' or doc_type == 'wh':
            if state == 'to_send':
                edi_result = edi_format._post_invoice_edi(documents.move_id)
                _postprocess_post_edi_results(documents, edi_result)
            elif state == 'to_cancel':
                edi_result = edi_format._cancel_invoice_edi(documents.move_id)
                _postprocess_cancel_edi_results(documents, edi_result)
        elif doc_type == 'payment':
            if state == 'to_send':
                edi_result = edi_format._post_payment_edi(documents.move_id)
                _postprocess_post_edi_results(documents, edi_result)
            elif state == 'to_cancel':
                edi_result = edi_format._cancel_payment_edi(documents.move_id)
                _postprocess_cancel_edi_results(documents, edi_result)

    wh_id = fields.Many2one('account.wh')

