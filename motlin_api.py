import requests


def get_token(client_id):
    request_body = {
                "client_id": client_id,
                "grant_type": "implicit",
    }

    response = requests.post(
                    'https://api.moltin.com/oauth/access_token',
                    data=request_body,
                    timeout=30,
    )
    response.raise_for_status()
    return response.json().get('access_token')


if __name__ == "__main__":
    print(get_token("659175c46f466a17552820f18bb9199b8876154946"))
