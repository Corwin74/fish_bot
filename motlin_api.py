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


def get_product_photo_link(access_token, image_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
                            f'https://api.moltin.com/v2/files/{image_id}',
                            headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']['link']['href']


def get_product_stock(access_token, product_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
                        f'https://api.moltin.com/v2/inventories/{product_id}',
                        headers=headers,
    )
    response.raise_for_status()
    return response.json()['data']


def get_cart_cost(access_token, cart_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['meta']['display_price']["with_tax"]["formatted"]


def get_cart_items(access_token, cart_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def add_product_to_cart(access_token, product_sku, quantity, cart_id):
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
    return response.text


def remove_product_from_cart(access_token, cart_id, product_id):
    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


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


def create_customer(access_token, email, name):
    headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
    }
    json_data = {
                    "data": {
                              "type": "customer",
                              "name": name,
                              "email": email,
                            }
                }
    response = requests.post(
        "https://api.moltin.com/v2/customers",
        headers=headers,
        data=json_data,
    )
    response.raise_for_status()


if __name__ == "__main__":
    access_token = '70e71dae51137df5bce6c46395830091e443afb9'
    env = Env()
    env.read_env()
    motlin_client_id = env('MOTLIN_CLIENT_ID')
    motline_client_secret_key = env('MOTLIN_CLIENT_SECRET_KEY')
    if not access_token:
        access_token = get_token(motlin_client_id, motline_client_secret_key)
    print(access_token)
    resp = get_cart_items(access_token, '213999118')
    for product in resp:
        print(product['name'])
        print(product["quantity"])
        print(product['meta']['display_price']["with_tax"]['unit']["formatted"])
        print(product['meta']['display_price']["with_tax"]['value']["formatted"])
