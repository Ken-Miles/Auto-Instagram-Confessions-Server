# instagram account details (username and password)
import yaml

with open('credentials.yml') as f:
    credentials = dict(yaml.safe_load(f))
    username = credentials['username']
    password = credentials['password']
    sheet_url = credentials['sheet_url']
