import logging

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler,
                          CallbackQueryHandler, Filters, MessageHandler,
                          Updater)

from tlgm_logger import TlgmLogsHandler

ECHO = (1,)

logger = logging.getLogger(__file__)


def start(update, context):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'),
                 InlineKeyboardButton("Option 2", callback_data='2')],

                [InlineKeyboardButton("Option 3", callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
                              'Please choose:',
                              reply_markup=reply_markup)
    return ECHO


def button(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Selected option: {query.data}")


def handle_echo(update, context):
    redis = context.bot_data['redis']
    update.message.reply_text(update.message.text)
    return ECHO


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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            ECHO: [
                       MessageHandler(Filters.text & ~Filters.command,
                                      handle_echo),
                      ],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(button))

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
