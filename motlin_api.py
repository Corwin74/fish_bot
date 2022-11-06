import requests


def renew_access_token(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                args = list(args)
                access_token = get_token(
                    args[0].bot_data['motlin_client_id'],
                    args[0].bot_data['motlin_client_secret_key']
                )
                args[0].bot_data['motlin_access_token'] = access_token
                return func(*args, **kwargs)
            else:
                raise e
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
    return response.json().get('access_token')


@renew_access_token
def get_products(context):
    access_token = context.bot_data['motlin_access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        'https://api.moltin.com/catalog/products',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


@renew_access_token
def get_product_photo_link(context, image_id):
    access_token = context.bot_data['motlin_access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/v2/files/{image_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']['link']['href']


@renew_access_token
def get_product_stock(context, product_id):
    access_token = context.bot_data['motlin_access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/v2/inventories/{product_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


@renew_access_token
def get_cart_cost(context, cart_id):
    access_token = context.bot_data['motlin_access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    display_price = response.json()['data']['meta']['display_price']
    return display_price["with_tax"]["formatted"]


@renew_access_token
def get_cart_items(context, cart_id):
    access_token = context.bot_data['motlin_access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


@renew_access_token
def add_product_to_cart(context, product_sku, quantity, cart_id):
    access_token = context.bot_data['motlin_access_token']
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


@renew_access_token
def remove_product_from_cart(context, cart_id, product_id):
    access_token = context.bot_data['motlin_access_token']
    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()['data']


@renew_access_token
def get_product(context, product_id):
    access_token = context.bot_data['motlin_access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/pcm/products/{product_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


def _get_first_pricebook(context):
    access_token = context.bot_data['motlin_access_token']
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


@renew_access_token
def get_product_price(context, product_sku):
    for product in _get_first_pricebook(context):
        if product_sku == product['attributes']['sku']:
            return product['attributes']['currencies']


@renew_access_token
def create_customer(context, email, name):
    access_token = context.bot_data['motlin_access_token']
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


@renew_access_token
def get_customer(context, customer_id):
    access_token = context.bot_data['motlin_access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f'https://api.moltin.com/v2/customers/{customer_id}',
        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']
