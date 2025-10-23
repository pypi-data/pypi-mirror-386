from odoo import models, api, fields, tools, _
import random
import string
import logging

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = "res.partner"

    interest_ids = fields.Many2many('res.partner.interest', column1='partner_id',
                                    column2='category_id', string='Interests')

    def _generate_promotional_code(self):
        code = ''.join([random.choice(string.ascii_letters) for _ in range(6)]).upper()

        if self.env['res.partner'].search_count([('promotional_code', '=', code)], limit=1):
            return self._generate_promotional_code()

        return code

    promotional_code = fields.Char(default=_generate_promotional_code)

    friend_ids = fields.One2many('res.partner.friend', 'inviter_id')
    inviter_id = fields.Many2one('res.partner', compute='_compute_inviter_id')
    active_contracts_count = fields.Integer(compute='_compute_active_contracts', store=True)

    def _compute_inviter_id(self):
        for record in self:
            record.inviter_id = self.env['res.partner.friend'].search([
                ('friend_id', '=', record.id)
            ]).inviter_id

    @api.depends('contract_ids.stage_id')
    def _compute_active_contracts(self):
        for record in self:
            record.active_contracts_count = self.env['contract.participation'].search_count([
                ('partner_id.vat', '=', record.vat),
                ('stage_id', '=', self.env['contract.participation.stage'].search([('valid', '=', 'True')]).id)
            ])

    @tools.ormcache()
    def _compute_plant_participants(self):
        participants = self.env['res.partner'].sudo().search([('participant', '=', True)])
        return len(participants)
