from odoo import models, api
from odoo.tools import email_split
import logging

_logger = logging.getLogger(__name__)

class ParticipantActivities(models.Model):
    _inherit = "participant.activities"

    @api.model
    def message_new(self, msg, custom_values=None):

        return super().message_new(self.__filter_mails_of_incoming_servers(msg), custom_values=custom_values)

    def message_update(self, msg, update_vals=None):
        return super().message_update(self.__filter_mails_of_incoming_servers(msg), update_vals=update_vals)

    def __filter_mails_of_incoming_servers(self, msg):
        recipient_mails_str = msg.get('to')
        icoming_mail_servers = self.env['fetchmail.server'].search([])
        
        incoming_mail_addresses = []
        for incoming_mail_server in icoming_mail_servers:
            incoming_mail_addresses.append(incoming_mail_server.user)
        copied_msg = msg.copy()
        
        
        # Get the string of emails filter out the mails configured in incoming mails and turn back into string
        recipient_mails = email_split(recipient_mails_str)
        filtered_recipient_mails = []
        for mail in recipient_mails:
            if mail not in incoming_mail_addresses:
                filtered_recipient_mails.append(mail)
        copied_msg['to'] = ','.join(filtered_recipient_mails)
        
        # This can be done in one line but might not be very legible
        # copied_msg['to'] = ','.join([mail for mail in email_split(recipient_mails_str) if mail not in incoming_mail_addresses])
        return copied_msg