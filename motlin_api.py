import requests
from environs import Env


def get_token(client_id):
    request_body = {
                "client_id": client_id,
                "grant_type": "implicit",
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
    return response.text


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


if __name__ == "__main__":
    env = Env()
    env.read_env()
    motlin_client_id = env('MOTLIN_CLIENT_ID')
    print(add_product_to_cart(get_token(motlin_client_id), "4", 3))
