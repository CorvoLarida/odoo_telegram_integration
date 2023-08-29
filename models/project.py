# -*- coding: utf-8 -*-
from urllib import parse

import requests
from odoo import models, fields, api, _


def return_if_exists(value):
    if value:
        return parse.quote(value)
    else:
        return "N/A"


class Task(models.Model):
    _inherit = "project.task"

    notification_date_deadline_1_day_send = fields.Boolean(default=False)
    notification_date_deadline_overdue_send = fields.Boolean(default=False)

    def _get_text_new_assignees(self, telegram_data):
        text = f"На вас была создана задача \"{telegram_data['task_name']}\".\n" \
               f"Срок до {telegram_data['task_deadline']}.\n" \
               f"Создатель {telegram_data['task_creator_name']} @{telegram_data['task_creator_telegram'][0]}.\n" \
               f"Проект \"{telegram_data['project_name']}\".\n" \
               f"{telegram_data['task_url']}\n"
        return text

    def _get_text_in_stage(self, telegram_data, stage):
        text = f"Задача \"{telegram_data['task_name']}\" находится в статусе \"{stage.name}\". " \
               f"Пожалуйста проверьте.\n" \
               f"{telegram_data['task_url']}"
        return text

    def _get_text_deadline(self, telegram_data, delta):
        if "N/A" in telegram_data["task_creator_telegram"]:
            per_to_contact = telegram_data["task_creator_name"]
        else:
            per_to_contact = "@" + telegram_data["task_creator_telegram"][0]
        text = ""
        if delta == 1:
            text = f"Остался день до окончания срока задачи \"{telegram_data['task_name']}\"! Пожалуйста поторопитесь " \
                   f"или обратитесь к {per_to_contact} для переноса срока.\n{telegram_data['task_url']}"
        if delta < 0:
            text = f"Вы просрочили срок сдачи задачи \"{telegram_data['task_name']}\"! Пожалуйста обратитесь к {per_to_contact}.\n{telegram_data['task_url']}"
        return text

    def _check_users_settings(self, initial_tg_ids, notification_type, **kwargs):
        receivers_list = []
        users = self.env["res.users"].search([("telegram_bot_receive", "=", True),
                                              ("telegram_chat_id", "in", initial_tg_ids)])
        if users:
            search_query = []
            if notification_type == "stage":
                search_query.append(("telegram_bot_receive_reached_stage", "=", True))
            elif notification_type == "new_assignees":
                search_query.append(("telegram_bot_receive_new_assignees", "=", True))
            elif notification_type == "deadline":
                if kwargs.get("delta"):
                    delta = kwargs.get("delta")
                    search_query.append(("telegram_bot_receive_deadline", "=", True))
                    if delta == 1:
                        search_query.append(("telegram_bot_receive_deadline_1_day", "=", True))
                    elif delta < 0:
                        search_query.append(("telegram_bot_receive_deadline_overdue", "=", True))
                    else:
                        search_query.clear()
            if search_query:
                receivers = users.search(search_query)
                for receiver in receivers:
                    receivers_list.append(receiver.telegram_chat_id)

        return receivers_list

    @api.constrains("stage_id")
    def _moved_to_stage(self):
        to_send_reached_stage = self.env["ir.config_parameter"].sudo().get_param("telegram_bot.to_send_reached_stage")
        if to_send_reached_stage:
            reached_stage_id = self.env["ir.config_parameter"].sudo().get_param("telegram_bot.reached_stage_id")
            if self.stage_id.id == int(reached_stage_id):
                telegram_data = self._get_data_for_telegram()
                text = self._get_text_in_stage(telegram_data=telegram_data, stage=self.stage_id)
                receivers_telegram_ids = self._check_users_settings(
                    initial_tg_ids=telegram_data["task_creator_telegram_id"],
                    notification_type="stage")
                self._send_notification(receivers_telegram_ids=receivers_telegram_ids,
                                        text=text)
                del telegram_data
                del text
            del reached_stage_id
        del to_send_reached_stage

    @api.model
    def _scheduled_in_stage(self):
        reached_stage = self.env["ir.config_parameter"].get_param("telegram_bot.reached_stage_id")
        records_in_stage = self.env['project.task'].search([("stage_id.id", "=", int(reached_stage))])
        for rec in records_in_stage:
            telegram_data = rec._get_data_for_telegram()
            receivers_telegram_ids = self._check_users_settings(
                initial_tg_ids=telegram_data["task_creator_telegram_id"],
                notification_type="stage")
            text = rec._get_text_in_stage(telegram_data=telegram_data, stage=rec.stage_id)
            rec._send_notification(receivers_telegram_ids=receivers_telegram_ids,
                                   text=text)
            del telegram_data
            del text
        del reached_stage
        del records_in_stage

    @api.model
    def _scheduled_deadline(self):
        to_send_deadline = self.env["ir.config_parameter"].get_param("telegram_bot.to_send_deadline")
        if to_send_deadline:
            today = fields.Date.today()
            records = self.env["project.task"].search(['&', ("date_deadline", "!=", False),
                                                       '|', ("notification_date_deadline_1_day_send", "=", False),
                                                       ("notification_date_deadline_overdue_send", "=", False)])
            to_send_deadline_1_day = self.env["ir.config_parameter"].get_param("telegram_bot.to_send_deadline_1_day")
            to_send_deadline_overdue = self.env["ir.config_parameter"].get_param(
                "telegram_bot.to_send_deadline_overdue")
            for rec in records:
                delta = int((rec.date_deadline - today).days)
                telegram_data = rec._get_data_for_telegram()
                receivers_telegram_ids = rec._check_users_settings(
                    initial_tg_ids=telegram_data["assignees_telegram_ids"],
                    notification_type="deadline", delta=delta)
                text = rec._get_text_deadline(telegram_data, delta)
                if delta == 1:
                    if to_send_deadline_1_day:
                        if not rec.notification_date_deadline_1_day_send:
                            rec._send_notification(receivers_telegram_ids=receivers_telegram_ids,
                                                   text=text)
                            rec.notification_date_deadline_1_day_send = True
                elif delta == -1:
                    if to_send_deadline_overdue:
                        if not rec.notification_date_deadline_overdue_send:
                            rec._send_notification(receivers_telegram_ids=receivers_telegram_ids,
                                                   text=text)
                            rec.notification_date_deadline_overdue_send = True

            del today
            del records
            del to_send_deadline_1_day
            del to_send_deadline_overdue
        del to_send_deadline

    def _send_to_new_assignees(self, new_assignees_ids):
        to_send_new_assignees = self.env["ir.config_parameter"].sudo().get_param("telegram_bot.to_send_new_assignees")
        if to_send_new_assignees:
            telegram_data = self._get_data_for_telegram()
            new_assignees = self.env["res.users"].search([("id", "in", new_assignees_ids)])
            self._get_assignees(dict_to_update=telegram_data,
                                list_of_users=new_assignees)
            receivers_telegram_ids = self._check_users_settings(initial_tg_ids=telegram_data["assignees_telegram_ids"],
                                                                notification_type="new_assignees")
            text = self._get_text_new_assignees(telegram_data)
            self._send_notification(receivers_telegram_ids=receivers_telegram_ids,
                                    text=text)
            del telegram_data
            del new_assignees
            del text
        del to_send_new_assignees

    def write(self, vals):
        old_assignees_ids = [user.id for user in self.user_ids]
        if "user_ids" in vals:
            all_assignees_ids = vals.get("user_ids")[0][2]
            new_assignees_ids = []
            for assignee in all_assignees_ids:
                if assignee not in old_assignees_ids:
                    new_assignees_ids.append(assignee)
            if new_assignees_ids:
                self._send_to_new_assignees(new_assignees_ids)
        if "date_deadline" in vals:
            vals["notification_date_deadline_1_day_send"] = False
            vals["notification_date_deadline_overdue_send"] = False
        res = super(Task, self).write(vals)
        return res

    def _send_notification(self, receivers_telegram_ids, text):
        bot_enable = self.env["ir.config_parameter"].sudo().get_param("telegram_bot.enable_bot")
        if bot_enable:
            bot_api_key = self.env["ir.config_parameter"].sudo().get_param("telegram_bot.bot_api_key")
            if bot_api_key:
                base = f"https://api.telegram.org/bot{bot_api_key}/sendMessage?"
                if receivers_telegram_ids:
                    for chat_id in receivers_telegram_ids:
                        if chat_id and len(chat_id) == 10:
                            url = f"{base}chat_id={chat_id}&text={text}"
                            requests.get(url)
                            print("Message sent successfully")
                        else:
                            print("Tough Luck")
                            continue

    def _get_assignees(self, dict_to_update, list_of_users):
        assignees = list_of_users
        assignees_names = []
        assignees_telegram_usernames = []
        assignees_telegram_ids = []
        for assignee in assignees:
            assignees_names.append(return_if_exists(assignee.name))
            assignees_telegram_usernames.append(return_if_exists(assignee.telegram_username))
            if assignee.telegram_username:
                assignees_telegram_ids.append(assignee.telegram_chat_id)
            else:
                assignees_telegram_ids.append(False)
        dict_to_update.update({
            "assignees_names": assignees_names,
            "assignees_telegram_usernames": assignees_telegram_usernames,
            "assignees_telegram_ids": assignees_telegram_ids,
        })

    def _get_data_for_telegram(self):
        data_for_telegram = {
            "task_name": return_if_exists(self.name),
            "task_creator_name": return_if_exists(self.create_uid.name),
            "task_creator_telegram": [return_if_exists(self.create_uid.telegram_username)],
            "task_creator_telegram_id": [self.create_uid.telegram_chat_id],
            "task_deadline": self.date_deadline,
            "project_name": return_if_exists(self.project_id.name)
        }

        url_id = self.id
        url_action = self.env.ref("project.action_view_all_task").id
        url_model = self._name
        url_menu_id = self.env["ir.ui.menu"].search([("name", "=", "Project")]).id
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url = f"{base_url}/web#id={url_id}&menu_id={url_menu_id}&action={url_action}&model={url_model}&view_type=form"
        data_for_telegram.update({
            "task_url": parse.quote(url)
        })
        self._get_assignees(dict_to_update=data_for_telegram,
                            list_of_users=self.user_ids)
        if not data_for_telegram["task_deadline"]:
            data_for_telegram["task_deadline"] = "N/A"
        else:
            data_for_telegram["task_deadline"] = self.date_deadline.strftime("%d-%m-%Y")
        if data_for_telegram["project_name"] == "N/A":
            data_for_telegram["project_name"] = "Private"

        return data_for_telegram

    # @api.constrains('date_deadline')
    # def _test_send_telegram_notification(self):
    #     # print(self.name, "  BEFORE:      ", self.notification_date_deadline_send)
    #     print("And Task Creator:    ", self.create_uid.name)
    #     print("And Their Telegram:    ", self.create_uid.telegram_username)
    #
    #     telegram_data = self._get_data_for_telegram()
    #     text = f"DEADLINE DATE This is a test text *******d:\n" \
    #            f"task name: {telegram_data['task_name']}\n" \
    #            f"task creator: {telegram_data['task_creator_name']}\n" \
    #            f"their telegram: @{telegram_data['task_creator_telegram'][0]}\n" \
    #            f"deadline: {telegram_data['task_deadline']}\n" \
    #            f"project name: {telegram_data['project_name']}\n" \
    #            f"assignees names: {telegram_data['assignees_names']}\n" \
    #            f"assignees telegram usernames: {telegram_data['assignees_telegram_usernames']}\n" \
    #            f"task url: {telegram_data['task_url']}\n"
    #     self._send_notification(receivers_telegram_ids=telegram_data["assignees_telegram_ids"],
    #                             text=text)
