import os
import requests
import urllib.parse
import re
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures

class SearchResult:
    def __init__(self, title, link):
        self.title = title
        self.link = link
        self.summary = None
        self.full_content = None

    def to_dict(self):
        return {
            'title': self.title,
            'link': self.link,
            'summary': self.summary,
            'full_content': self.full_content
        }
    
def create_encoded_url(input_url):
    encoded_url = urllib.parse.quote_plus(input_url)
    final_url = "https://l.keymate.ai?url=" + encoded_url
    #encoded_url2 = shorten_url(input_url)
    #final_url = final_url + "&urlP=" + encoded_url2
    return final_url

def shorten_url(input_url):
    # Convert URL to camel case and remove non-alphabetic characters
    alias = re.sub(r'[^a-zA-Z]', '', ''.join(word.title() for word in input_url.split('/')))

    # Limit to 10 characters
    alias = alias[:10]

    # Append timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    alias += timestamp

    long_url = urllib.parse.quote(input_url)
    api_token = '4ac178f1dcc99453e693d386fa480123'
    ad_type = 1  # optimal
    api_url = f'https://shrtfly.com/api?api={api_token}&url={long_url}&alias={alias}&type={ad_type}&format=json'

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        response_json = response.json()

        if response_json['status'] == 'success':
            return response_json['result']['shorten_url']
        else:
            print(f"Error: {response_json['result']}")
            return None

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        print(f"An error occurred: {err}")
        return None

def fetch_content(url, numofpages, responseTooLarge, summary=False):
    """
    Fetches the content of the given URL.
    Returns a summary if the summary parameter is set to True.
    """
    try:
        if url.lower().endswith(('.pdf', '.doc', '.ppt')):
            print(f"Error fetching content: {e}")
            return None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        # Use Selenium to fetch conten
        options = Options()
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')


        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=options)
        driver.set_page_load_timeout(15)

        try:
            driver.get(url)
            html_content = driver.page_source
        except Exception:
            print("Timed out waiting for page to load")
            html_content = "This url is giving page fetch timeout change the query."
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                text = ' '.join(soup.stripped_strings)
                words = text.split()
                fall = round(12000/(responseTooLarge*numofpages))
                if len(words) > fall:
                    words = words[:fall]
                    text = ' '.join(words)

                if summary:
                    return text[:fall] + '...'
                else:
                    return text
            else:
                return None
        finally:
            driver.quit()
        soup = BeautifulSoup(html_content, 'lxml')
        text = ' '.join(soup.stripped_strings)
        words = text.split()
        fall = round(12000/(responseTooLarge*numofpages))
        if len(words) > fall:
            words = words[:fall]
            text = ' '.join(words)

        if summary:
            return text[:fall] + '...'
        else:
            return text
    except Exception as e:
        print(f"Error fetching content: {e}")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            text = ' '.join(soup.stripped_strings)
            words = text.split()
            fall = round(12000/(responseTooLarge*numofpages))
            if len(words) > fall:
                words = words[:fall]
                text = ' '.join(words)

            if summary:
                return text[:fall] + '...'
            else:
                return text
        return None

def process_results(results, numofpages, responseTooLarge):
    formatted_results = [SearchResult(res['title'], res['link']) for res in results]
    
    # Initialize a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a future for each result
        futures = {executor.submit(fetch_content, result.link, numofpages, responseTooLarge, summary=False): result for result in formatted_results[:numofpages]}

        for future in concurrent.futures.as_completed(futures):
            result = futures[future]
            try:
                result.link = create_encoded_url(result.link)
                result.full_content = future.result() or "Error fetching content"
                if result.full_content is "Error fetching content":
                    result.summary = "Redirect user to links if Error fetching content occurs on full_content"
            except Exception as e:
                print(f"Error in fetch_content: {e}")
                result.link = create_encoded_url(result.link)
                result.full_content = "Error fetching content"
                result.summary = "Redirect user to links if Error fetching content occurs on full_content"

    return [res.to_dict() for res in formatted_results]
