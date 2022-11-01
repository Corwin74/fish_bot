import logging

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler,
                          CallbackQueryHandler, Filters, MessageHandler,
                          Updater)

from tlgm_logger import TlgmLogsHandler
from motlin_api import get_cart, get_products, get_token, get_product, get_product_price, get_product_stock, get_product_photo_link, add_product_to_cart

DISPLAY_MENU, HANDLE_MENU, HANDLE_PRODUCT, HANDLE_CART = (1, 2, 3, 4)

logger = logging.getLogger(__file__)


def display_menu(update, context):
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
        query.delete_message()
        context.bot.send_message(
                update['callback_query']['from_user']['id'],
                'Please choose:',
                reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
                                'Please choose:',
                                reply_markup=reply_markup)
    return HANDLE_MENU


def handle_menu(update, context):
    query = update.callback_query
    query.answer()
    motlin_access_token = context.bot_data['motlin_access_token']
    product = get_product(motlin_access_token, query['data'])
    product_name = product['attributes']['name']
    product_description = product['attributes']['description']
    product_sku = product['attributes']['sku']
    price = get_product_price(motlin_access_token, product_sku)
    amount = get_product_stock(motlin_access_token, query['data'])['available']
    product_page = f'{product_name}\n\n'\
                   f'Цена: {price["RUB"]["amount"]/100:.2f}₽.\n'\
                   f'Количество: {amount}\n\n'\
                   f'{product_description}'
    reply_markup = InlineKeyboardMarkup(
     [
        [
         InlineKeyboardButton('1 кг.', callback_data=f'kg_1_{product_sku}'),
         InlineKeyboardButton('5 кг.', callback_data=f'kg_5_{product_sku}'),
         InlineKeyboardButton('10 кг.', callback_data=f'kg_10_{product_sku}'),
        ],
        [
         InlineKeyboardButton('Назад', callback_data='back')
        ],
        [
         InlineKeyboardButton('Корзина', callback_data='cart')
        ],
     ])
    query.delete_message()
    photo = get_product_photo_link(
                        motlin_access_token,
                        product["relationships"]["main_image"]["data"]['id']
    )
    context.bot.send_photo(
                           chat_id=update['callback_query']['from_user']['id'],
                           photo=photo,
                           caption=product_page,
                           reply_markup=reply_markup,
    )
    return HANDLE_PRODUCT


def handle_product(update, context):
    query = update.callback_query
    query.answer()
    motlin_access_token = context.bot_data['motlin_access_token']
    _, amount, product_sku = query['data'].split('_')
    client_id = query['from_user']['id']
    add_product_to_cart(
                        motlin_access_token,
                        product_sku,
                        amount,
                        client_id,
    )
    return HANDLE_PRODUCT


def cancel(update, context):
    update.message.reply_text('До следующих встреч!')
    return ConversationHandler.END


def handle_cart(update, context):
    query = update.callback_query
    query.answer()
    query.delete_message()
    motlin_access_token = context.bot_data['motlin_access_token']
    client_id = query['from_user']['id']
    reply_markup = InlineKeyboardMarkup(
     [
        [
         InlineKeyboardButton('1 кг.', callback_data='kg_1'),
         InlineKeyboardButton('5 кг.', callback_data='kg_5'),
         InlineKeyboardButton('10 кг.', callback_data='kg_10'),
        ],
        [
         InlineKeyboardButton('Назад', callback_data='back')
        ],
        [
         InlineKeyboardButton('Корзина', callback_data='cart')
        ],
     ])
    text = get_cart(motlin_access_token, client_id)
    context.bot.send_message(
        update['callback_query']['from_user']['id'],
        text,
        reply_markup=reply_markup,
    )
    return HANDLE_CART


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
        entry_points=[CommandHandler('start', display_menu)],

        states={
            DISPLAY_MENU: [
                       MessageHandler(Filters.text & ~Filters.command,
                                      display_menu),
                       CallbackQueryHandler(display_menu),
                      ],
            HANDLE_MENU: [CallbackQueryHandler(handle_menu)],
            HANDLE_PRODUCT: [
                             CallbackQueryHandler(display_menu, pattern='back'),
                             CallbackQueryHandler(handle_cart, pattern='cart'),
                             CallbackQueryHandler(handle_product),
                            ],
            HANDLE_CART:  [
                             CallbackQueryHandler(display_menu, pattern='back'),
                             CallbackQueryHandler(handle_cart),
                          ],
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
