import requests

data = {
    "username": "matias",
    "password": "asdf"
}

response = requests.post("https://splus.cloud/adss/v1/auth/login", data=data)

token = response.json()["access_token"]

import requests 

data = {
    "query": """SELECT top 100 * from dr3.all_dr3""",
    "mode": "adql",
    "format": "csv"
}

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.post("https://splus.cloud/adss/v1/query", json=data, headers=headers)
response = requests.post("https://splus.cloud/adss/sync", data=data, headers=headers)

# content has the bytes of the CSV file