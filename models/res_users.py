# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

TELEGRAM_BOT_USER_FIELDS = [
    "telegram_bot_receive",
    "telegram_bot_receive_deadline",
    "telegram_bot_receive_deadline_1_day",
    "telegram_bot_receive_deadline_overdue",
    "telegram_bot_receive_reached_stage",
    "telegram_bot_receive_new_assignees"
]


class Users(models.Model):
    _inherit = "res.users"

    telegram_bot_receive = fields.Boolean(string="Receive Telegram Notifications")
    telegram_bot_receive_deadline = fields.Boolean(string="Deadlines Of Tasks",
                                                   help="Receive notifications about deadlines of tasks")
    telegram_bot_receive_deadline_1_day = fields.Boolean(string="1 Day Away From Deadline",
                                                         help="Receive notifications about tasks that are 1 day away "
                                                              "from deadline")
    telegram_bot_receive_deadline_overdue = fields.Boolean(string="Overdue",
                                                           help="Receive notifications about tasks that are overdue")
    telegram_bot_receive_reached_stage = fields.Boolean(string="Reached Stage",
                                                        help="Receive notifications as task creator about tasks that "
                                                             "reach certain stage")
    telegram_bot_receive_new_assignees = fields.Boolean(string="New Tasks",
                                                        help="Receive notifications about new tasks")

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + TELEGRAM_BOT_USER_FIELDS

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + TELEGRAM_BOT_USER_FIELDS
