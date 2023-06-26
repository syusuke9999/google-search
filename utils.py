import os
import requests
import urllib.parse
import re
import datetime
import logging
import math
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
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
    
def create_encoded_url(input_url,member_id):
    encoded_url = urllib.parse.quote_plus(input_url)
    final_url = "https://l.keymate.ai?member_id="+member_id+"&url=" + encoded_url
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

    url = "https://api.short.io/links"

    payload = {
        "domain": "ln.keymate.ai",
        "originalURL": input_url,
        "allowDuplicates": True
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "sk_q01svLvu0ZuLP7Il"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()

        if response.status_code == 200:
            return response_json['secureShortURL']
        else:
            print(f"Error: {response_json}")
            return input_url

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {input_url}")
        return input_url
    except Exception as err:
        print(f"An error occurred: {input_url}")
        return input_url

def fetch_content(url, numofpages, responseTooLarge, member_id, timeout, summary=False):
    """
    Fetches the content of the given URL.
    Returns a summary if the summary parameter is set to True.
    """
    totReqSecs = 30
    idealTimeoutFirst = 7
    idealTimeoutSecond = 3
    if numofpages < 6:
        idealTimeoutFirst = timeout
        idealTimeoutSecond = math.floor(timeout/4)
    else:
        idealTimeoutFirst = timeout
        idealTimeoutSecond =  math.floor(timeout/4)
    try:
        if url.lower().endswith(('.pdf', '.doc', '.ppt')):
            print(f"Error fetching content: {url}")
            return 'Add a pdf doc or ppt reader plugin for this link'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        options = Options()
        options = webdriver.ChromeOptions() 
        options.add_argument("start-maximized")
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = uc.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=options)
        # Use Selenium to fetch conten
        #options = Options()
        #options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        #options.add_argument('--headless')
        #options.add_argument('--disable-gpu')
        #options.add_argument('--no-sandbox')
        #options.add_argument('--disable-dev-shm-usage')
        #driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=options)
        driver.set_page_load_timeout(idealTimeoutFirst)

        try:
            driver.get(url)
            WebDriverWait(driver, idealTimeoutFirst).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            html_content = driver.page_source
        except Exception:
            print("Timed out waiting for page to load")
            html_content = "This url is giving page fetch timeout change the query."
            response = requests.get(url, timeout=idealTimeoutSecond)
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
                print(f"not giving content: {url}")
                return 'this site is not giving us the content'
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
        print(f"Error fetching content 6: {url}")
        response = requests.get(url, timeout=idealTimeoutSecond)
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
        print(f"not giving content 2: {url}")
        return 'this site is not giving the content'

def get_timeout(page_number, total_pages, tot_req_secs=30):
    if total_pages < 2:
        tot_req_secs = tot_req_secs - 2 
            
    if total_pages < 6:
        budgetPerCall = math.floor(tot_req_secs/total_pages)
        budgetPageImportance = math.floor( (tot_req_secs * 0.8) / 3)+1
        if page_number <= 3:
            # These are the important pages, allocate more time
            if page_number is 1:
                return math.floor(budgetPerCall*0.8)+1
            if page_number is 2:
                return math.floor(budgetPerCall*0.8)
            if page_number is 3:
                return math.floor(budgetPerCall*0.8)-1
        else:
            spentAbove = math.floor(budgetPerCall*0.8)+1+math.floor(budgetPerCall*0.8)+math.floor(budgetPerCall*0.8)-1
            leftBudget = (tot_req_secs - math.floor((budgetPerCall*0.2)*3))-spentAbove
            leftNumberPages = (10 - total_pages) - 3
            return round((leftBudget/leftNumberPages)*0.8)
        
    if total_pages >= 6:
        budgetPerCall = math.floor(tot_req_secs/total_pages)
        budgetPageImportance = math.floor( (tot_req_secs * 0.8) / 3)+1
        if page_number <= 3:
            # These are the important pages, allocate more time
            if page_number is 1:
                return math.floor(budgetPerCall*0.8)+1
            if page_number is 2:
                return math.floor(budgetPerCall*0.8)
            if page_number is 3:
                return math.floor(budgetPerCall*0.8)-1
        else:
            spentAbove = math.floor(budgetPerCall*0.8)+1+math.floor(budgetPerCall*0.8)+math.floor(budgetPerCall*0.8)-1
            leftBudget = (tot_req_secs - math.floor((budgetPerCall*0.2)*3))-spentAbove
            leftNumberPages = (10 - total_pages) - 3
            return round((leftBudget/leftNumberPages)*0.8)
    else:
        return 7


def process_results(results, numofpages, responseTooLarge, member_id):
    formatted_results = [SearchResult(res['title'], res['link']) for res in results]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {}
        for i, result in enumerate(formatted_results[:numofpages]):
            timeout = get_timeout(i + 1, numofpages)
            future = executor.submit(fetch_content, result.link, numofpages, responseTooLarge, member_id, timeout, summary=False)
            futures[future] = result

        for future in concurrent.futures.as_completed(futures):
            result = futures[future]
            try:
                result.link = shorten_url(create_encoded_url(result.link,member_id))
                result.full_content = future.result() or "Error fetching content"
                if result.full_content is "Error fetching content":
                    result.summary = "Redirect user to links if Error fetching content occurs on full_content"
            except Exception as e:
                print(f"Error in fetch_content:")
                result.link = shorten_url(create_encoded_url(result.link,member_id))
                result.full_content = "Error fetching content"
                result.summary = "Redirect user to links if Error fetching content occurs on full_content"


    return [res.to_dict() for res in formatted_results]
