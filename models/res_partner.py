# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    telegram_username = fields.Char(string="Telegram Username")
    telegram_chat_id = fields.Char(string="Telegram Chat ID")
