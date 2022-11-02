import requests
import logging

from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler,
                          CallbackQueryHandler, Filters, MessageHandler,
                          Updater)

from tlgm_logger import TlgmLogsHandler
from motlin_api import (
                        create_customer, get_cart_cost, get_cart_items,
                        get_products, get_token, get_product,
                        get_product_price, get_product_stock,
                        get_product_photo_link, add_product_to_cart,
                        remove_product_from_cart,
)

DISPLAY_MENU, HANDLE_MENU, HANDLE_PRODUCT, \
        HANDLE_CART, WAITING_EMAIL = (1, 2, 3, 4, 5)

logger = logging.getLogger(__file__)


def display_menu(update, context):
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
                                'Сегодня в ассортименте:',
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
    if query['data'] == 'email':
        context.bot.send_message(
            client_id,
            'Для оформления заказа укажите адрес электронной почты:',
        )
        return WAITING_EMAIL
    if not query['data'] == 'cart':
        _, item_id = query['data'].split('_')
        remove_product_from_cart(
                                 motlin_access_token,
                                 client_id,
                                 item_id
        )
    menu_buttons = []
    message_text = ""
    for item in get_cart_items(motlin_access_token, client_id):
        menu_buttons.append(
                    [
                        InlineKeyboardButton(
                            f'{item["name"]} - удалить из корзины',
                            callback_data=f'delete_{item["id"]}',
                        )
                    ]
        )
        display_price = item["meta"]["display_price"]["with_tax"]
        message_text += f'{item["name"]}\n'\
            f'{display_price["unit"]["formatted"]} за кг.\n'\
            f'В корзине {item["quantity"]} кг.'\
            f'на сумму: {display_price["value"]["formatted"]}\n\n'
    menu_buttons.append(
        [InlineKeyboardButton('В меню', callback_data='back')]
    )
    if len(message_text):
        cart_cost = get_cart_cost(motlin_access_token, client_id)
        message_text += f'Общая сумма заказа: {cart_cost}\n'
        menu_buttons.append(
            [InlineKeyboardButton('Оформить заказ', callback_data='email')]
        )
    else:
        message_text = "Корзина пуста"
    reply_markup = InlineKeyboardMarkup(menu_buttons)
    context.bot.send_message(
                             client_id,
                             message_text,
                             reply_markup=reply_markup,
    )
    return HANDLE_CART


def handle_email(update, context):
    motlin_access_token = context.bot_data['motlin_access_token']
    message = update.message.to_dict()
    create_customer(
                    motlin_access_token,
                    message['text'],
                    message['from']['username'],
    )
    update.message.reply_text(
        f'Спасибо за заказ! Вы указали электронный адрес: {message["text"]}'
    )
    return ConversationHandler.END


def wrong_email(update, context):
    update.message.reply_text(
            'Неправильный формат email адреса. Попробуйте еще раз')
    return WAITING_EMAIL


def error_handler(update, context):
    logger.exception('Exception', exc_info=context.error)
    if isinstance(context.error, requests.exceptions.HTTPError):
        if context.error.response.status_code == 401:
            motlin_client_id = context.bot_data['motlin_client_id']
            motline_client_secret_key = \
                context.bot_data['motlin_client_secret_key']
            context.bot_data['motlin_access_token'] = get_token(
                                                    motlin_client_id,
                                                    motline_client_secret_key
                                                               )


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

    updater = Updater(tlgm_bot_token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['motlin_access_token'] = get_token(
                                                    motlin_client_id,
                                                    motline_client_secret_key
                                                          )
    dispatcher.bot_data['motlin_client_id'] = motlin_client_id
    dispatcher.bot_data['motlin_client_secret_key'] = motline_client_secret_key

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
            WAITING_EMAIL:  [
                        MessageHandler(Filters.entity('email'), handle_email),
                        MessageHandler(Filters.text & ~Filters.command,
                                       wrong_email),
                            ]
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
