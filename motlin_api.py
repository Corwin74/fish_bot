import requests
from environs import Env


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


def get_products(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
                            'https://api.moltin.com/catalog/products',
                            headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


def get_product_stock(access_token, product_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
                        f'https://api.moltin.com/v2/inventories/{product_id}',
                        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


def get_cart(access_token, cart_id='abc'):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def add_product_to_cart(access_token, product_sku, quantity, cart_id='abc'):
    headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
    }
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    json_data = {
                    "data": {
                        "sku": product_sku,
                        "type": "cart_item",
                        "quantity": quantity,
                    }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.text


def get_product(access_token, product_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
                    f'https://api.moltin.com/pcm/products/{product_id}',
                    headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


def get_first_pricebook(access_token):
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


def get_product_price(access_token, product_sku):
    for product in get_first_pricebook(access_token):
        if product_sku == product['attributes']['sku']:
            return product['attributes']['currencies']


if __name__ == "__main__":
    access_token = None
    env = Env()
    env.read_env()
    motlin_client_id = env('MOTLIN_CLIENT_ID')
    motline_client_secret_key = env('MOTLIN_CLIENT_SECRET_KEY')
    if not access_token:
        access_token = get_token(motlin_client_id, motline_client_secret_key)
    print(get_product_stock(access_token, '35b6d123-9d11-4d76-9561-057c1595fcab'))
