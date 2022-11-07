from datetime import datetime
import requests

FORCE_TO_EXPIRE_SEC = 200


def check_and_renew_access_token(func):
    def wrapper(*args, **kwargs):
        if (datetime.now() - args[0].bot_data['motlin_access_token'][2]) \
            .seconds > args[0].bot_data['motlin_access_token'][1] - \
                FORCE_TO_EXPIRE_SEC:
            args = list(args)
            access_token = get_token(
                args[0].bot_data['motlin_client_id'],
                args[0].bot_data['motlin_client_secret_key']
            )
            args[0].bot_data['motlin_access_token'] = access_token
        return func(*args, **kwargs)
    return wrapper


def get_token(client_id, client_secret_key):
    request_body = {
        "client_id": client_id,
        "client_secret": client_secret_key,
        "grant_type": "client_credentials",
    }
    response = requests.post(
        'https://api.moltin.com/oauth/access_token',
        data=request_body,
        timeout=10,
    )
    response.raise_for_status()
    return (
        response.json().get('access_token'),
        response.json().get('expires_in'),
        datetime.now(),
    )


@check_and_renew_access_token
def get_products(context):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        'https://api.moltin.com/catalog/products',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


@check_and_renew_access_token
def get_product_photo_link(context, image_id):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/v2/files/{image_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']['link']['href']


@check_and_renew_access_token
def get_product_stock(context, product_id):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/v2/inventories/{product_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


@check_and_renew_access_token
def get_cart_cost(context, cart_id):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    display_price = response.json()['data']['meta']['display_price']
    return display_price["with_tax"]["formatted"]


@check_and_renew_access_token
def get_cart_items(context, cart_id):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


@check_and_renew_access_token
def add_product_to_cart(context, product_sku, quantity, cart_id):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    json_data = {
        "data": {
            "sku": product_sku,
            "type": "cart_item",
            "quantity": int(quantity),
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()['data']


@check_and_renew_access_token
def remove_product_from_cart(context, cart_id, product_id):
    access_token = context.bot_data['motlin_access_token'][0]
    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()['data']


@check_and_renew_access_token
def get_product(context, product_id):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/pcm/products/{product_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


@check_and_renew_access_token
def get_first_pricebook(context):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        'https://api.moltin.com/pcm/catalogs',
        headers=headers,
    )
    response.raise_for_status()
    pricebook_id = response.json()['data'][0]['attributes']['pricebook_id']
    response = requests.get(
        f'https://api.moltin.com/pcm/pricebooks/{pricebook_id}/prices',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


def get_product_price(context, product_sku):
    for product in get_first_pricebook(context):
        if product_sku == product['attributes']['sku']:
            return product['attributes']['currencies']


@check_and_renew_access_token
def create_customer(context, email, name):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    json_data = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
        }
    }
    response = requests.post(
        "https://api.moltin.com/v2/customers",
        headers=headers,
        json=json_data,
    )
    response.raise_for_status()
    return response.json()['data']


@check_and_renew_access_token
def get_customer(context, customer_id):
    access_token = context.bot_data['motlin_access_token'][0]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/v2/customers/{customer_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']
