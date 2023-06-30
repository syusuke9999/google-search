import os
import requests

app_name = 'keymategooglesearchgpt'
heroku_api_key = os.environ["HEROKU_API_KEY"]

# Get the current config vars
response = requests.get(
    f'https://api.heroku.com/apps/{app_name}/config-vars',
    headers={
        'Accept': 'application/vnd.heroku+json; version=3',
        'Authorization': f'Bearer {heroku_api_key}',
    },
)
config_vars = response.json()

# Get the current values of APIKEYS, SEARCHIDS, and CURRENTID
api_keys = config_vars['APIKEYS'].split(';')
search_ids = config_vars['SEARCHIDS'].split(';')
current_id = int(config_vars['CURRENTID'])

# Increment CURRENTID
current_id = (current_id + 1) % len(api_keys)

# Set GOOGLE_API_KEY and CUSTOM_SEARCH_ENGINE_ID to the new values
new_values = {
    'GOOGLE_API_KEY': api_keys[current_id],
    'CUSTOM_SEARCH_ENGINE_ID': search_ids[current_id],
    'CURRENTID': str(current_id),
}

# Update the config vars
response = requests.patch(
    f'https://api.heroku.com/apps/{app_name}/config-vars',
    headers={
        'Accept': 'application/vnd.heroku+json; version=3',
        'Authorization': f'Bearer {heroku_api_key}',
    },
    json=new_values,
)

if response.status_code == 200:
    print(f'Successfully updated config vars.')
    response = requests.get(
        f'https://api.vercel.com/v1/integrations/deploy/prj_3T3hjTU4PoltpYHkdPYW6QyUqMmV/qSBJZSsfob'
    )
    
else:
    print(f'Failed to update config vars.')
