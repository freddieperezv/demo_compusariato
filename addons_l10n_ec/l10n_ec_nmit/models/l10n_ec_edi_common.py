from odoo import fields, models, api


class AccountL10nEcCommon(models.AbstractModel):
    _name = 'account.l10n.ec.common'
    _description = 'Common account edi'


    def action_process_edi_web_services(self):
        return self.move_id.action_process_edi_web_services()

    def action_retry_edi_documents_error(self):
        self.ensure_one()
        return self.move_id.action_retry_edi_documents_error()

    move_id = fields.Many2one("account.move", readonly=True)
    edi_blocking_level = fields.Selection(selection=[
        ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error')
    ])
    edi_error_count = fields.Integer()
    edi_error_message = fields.Html()
    edi_state = fields.Selection(selection=[
        ('to_send', 'To Send'), ('sent', 'Sent'), 
        ('to_cancel', 'To Cancel'), ('cancelled', 'Cancelled')
    ])
    edi_web_services_to_process = fields.Text()
