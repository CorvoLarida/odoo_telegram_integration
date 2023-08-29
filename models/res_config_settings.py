import base64
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    telegram_bot_enable = fields.Boolean(config_parameter="telegram_bot.enable_bot")
    telegram_bot_api_key = fields.Char(string="Telegram Bot API Key")
    telegram_bot_to_send_deadline = fields.Boolean(config_parameter="telegram_bot.to_send_deadline")
    telegram_bot_to_send_deadline_1_day = fields.Boolean(config_parameter="telegram_bot.to_send_deadline_1_day")
    telegram_bot_to_send_deadline_overdue = fields.Boolean(config_parameter="telegram_bot.to_send_deadline_overdue")
    telegram_bot_to_send_reached_stage = fields.Boolean(config_parameter="telegram_bot.to_send_reached_stage")
    telegram_bot_to_send_new_assignees = fields.Boolean(config_parameter="telegram_bot.to_send_new_assignees")
    telegram_bot_reached_stage_id = fields.Many2one(comodel_name="project.task.type",
                                                    config_parameter="telegram_bot.reached_stage_id")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.telegram_bot_api_key:
            self.env["ir.config_parameter"].set_param("telegram_bot.bot_api_key", self.telegram_bot_api_key)
