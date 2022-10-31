import logging

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler,
                          CallbackQueryHandler, Filters, MessageHandler,
                          Updater)

from tlgm_logger import TlgmLogsHandler
from motlin_api import get_products, get_token, get_product

HANDLE_MENU, HANDLE_PRODUCT = (1, 2)

logger = logging.getLogger(__file__)


def handle_menu(update, context):
    user = update.effective_user
    motlin_access_token = context.bot_data['motlin_access_token']
    keyboard = []
    products = get_products(motlin_access_token)
    for product in products:
        keyboard.append(
                        [
                            InlineKeyboardButton(
                                product['attributes']['name'],
                                callback_data=product['id']
                            )
                        ]
                        )
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        query = update.callback_query
        query.answer()
        query.edit_message_text('Please choose:',
                                reply_markup=reply_markup)
    else:
        update.message.reply_text(
                                'Please choose:',
                                reply_markup=reply_markup)
    return HANDLE_PRODUCT


def handle_product(update, context):
    query = update.callback_query
    query.answer()
    motlin_access_token = context.bot_data['motlin_access_token']
    product = get_product(motlin_access_token, query['data'])
    reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Назад', callback_data='back')]])
    query.edit_message_text(
                            text=product['attributes']['description'],
                            reply_markup=reply_markup
    )
    return HANDLE_MENU


def handle_echo(update, context):
    redis = context.bot_data['redis']
    update.message.reply_text(update.message.text)
    return HANDLE_MENU


def cancel(update, context):
    update.message.reply_text('До следующих встреч!')
    return ConversationHandler.END


def error_handler(update, context):
    logger.exception('Exception', exc_info=context.error)


def main():
    logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.INFO
    )

    env = Env()
    env.read_env()
    tlgm_bot_token = env('TLGM_BOT_TOKEN')
    motlin_client_id = env('MOTLIN_CLIENT_ID')
    motline_client_secret_key = env('MOTLIN_CLIENT_SECRET_KEY')
    redis_db_id = env('REDIS_DB_ID', default=0)
    redis_port = env('REDIS_PORT', default=6379)
    redis_host = env('REDIS_HOST', default='localhost')
    redis_db = redis.Redis(
                           host=redis_host,
                           port=redis_port,
                           db=redis_db_id,
                           charset="utf-8",
                           decode_responses=True
    )

    updater = Updater(tlgm_bot_token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['redis'] = redis_db
    # Fix me Проверить есть ли необходимость в их хранении
    dispatcher.bot_data['motlin_client_id'] = motlin_client_id
    dispatcher.bot_data['motlin_client_secret_key'] = motline_client_secret_key
    # Fix me end
    dispatcher.bot_data['motlin_access_token'] = get_token(
                                                    motlin_client_id,
                                                    motline_client_secret_key
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', handle_menu)],

        states={
            HANDLE_MENU: [
                       MessageHandler(Filters.text & ~Filters.command,
                                      handle_menu),
                       CallbackQueryHandler(handle_menu),
                      ],
            HANDLE_PRODUCT: [CallbackQueryHandler(handle_product)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%H:%M:%S',
    )
    logger.setLevel(logging.INFO)
    logger.addHandler(TlgmLogsHandler(
                                      updater.bot,
                                      env('ADMIN_TLGM_CHAT_ID'),
                                      formatter
                                     )
                      )
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
