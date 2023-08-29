# -*- coding: utf-8 -*-
{
    'name': "Telegram Bot Integration",

    'summary': """
        Telegram Bot Integration For Odoo
    """,

    'description': """
        Telegram Bot Integration For Odoo
        Current Modules Integration:
        - Project
    """,

    'author': "",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'project', 'contacts'],

    'data': [
        'data/ir_cron_data.xml',
        'data/ir_module_category_data.xml',
        'security/telegram_bot_security.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
    ],

}
