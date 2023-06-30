import os
import requests

app_name = 'keymategooglesearchgpt'
heroku_api_key = os.environ["HEROKU_API_KEY"]

# Get the current config vars
response = requests.get(
    f'https://api.vercel.com/v1/integrations/deploy/prj_3T3hjTU4PoltpYHkdPYW6QyUqMmV/qSBJZSsfob'
)
print(response.status_code)
print(response.text)
