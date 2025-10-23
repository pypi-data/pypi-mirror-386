from odoo import models, fields


class ResPartnerFriend(models.Model):
    _name = 'res.partner.friend'

    inviter_id = fields.Many2one('res.partner', domain=[('participant', '=', True)])
    friend_id = fields.Many2one('res.partner', domain=[('participant', '=', True)])
    used = fields.Boolean(default=False)
