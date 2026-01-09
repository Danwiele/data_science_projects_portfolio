import pandas as pd
import time
import json
import random
from datetime import datetime
import os
import csv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pathlib import Path

#path for chrome drivers (to check on your computer), put it inside the ''
chromedriver_path = r''

#month variable to organize scraping results from different months
month = datetime.now().strftime('%Y-%m')

#here input your directory to folder you want to save the file 
base_dir = Path(r'')

#name of the file
filename = f'otodom_scraped_{month}.csv'

#connecting paths
output_dir = base_dir / filename

#splitting scraping into districts to make it more efficient and error proof
districts = [
    'bemowo', 
    'bialoleka', 
    'bielany', 
    'mokotow', 
    'ochota', 
    'praga--poludnie', 
    'praga--polnoc', 
    'rembertow', 
    'srodmiescie', 
    'targowek', 
    'ursus', 
    'ursynow', 
    'wawer', 
    'wesola', 
    'wilanow', 
    'wlochy', 
    'wola', 
    'zoliborz'
 ]


#setting up requests to download data quicker
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.otodom.pl/'
})

def setup_driver():
    '''Setting up driver and chrome options'''
    chrome_options = Options()
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    cService = Service(chromedriver_path)
    return webdriver.Chrome(service=cService, options=chrome_options)

def close_cookies(driver):
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
        )
        accept_button.click()
    except TimeoutException: 
        print('No cookies popup')

def select_max_pages(driver):
    try:
        #waiting for pagination rendering
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(5) 

        #getting the pagination elements
        wait = WebDriverWait(driver, 5)
        pagination_container = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'ul[data-cy="nexus-pagination-component"]')
        ))

        #making sure that both buttons and anchors are taken into account while looking for max page button
        all_elements = pagination_container.find_elements(By.CSS_SELECTOR, 'li button, li a')

        page_numbers = []
        for el in all_elements:
            txt = el.text.strip()
            if txt.isdigit():
                page_numbers.append(int(txt))
        
        if page_numbers:
            max_p = max(page_numbers)
            print(f'Pages found: {max_p}')
            return max_p
        else:
            return 1

    except TimeoutException:
        print('No pagination, only one page')
        return 1
    
    except Exception as e:
        print(f"Other pagination error: {e}")
        return 1

def collect_offer_links(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    base_url = 'https://www.otodom.pl'
    urls = set()
    
    for a in soup.select('a[data-cy="listing-item-link"]'):
        href = a.get('href')
        if href:
            full_url = base_url + href if href.startswith('/') else href
            urls.add(full_url)
    return list(urls)

def get_offer_details_fast(url, district_name):
   
    try:
        #getting html
        response = session.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Status code error: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        if script_tag:
            data_json = json.loads(script_tag.string)
            
           #setting correct logic to pull the desired data
            ad = data_json['props']['pageProps']['ad']
            target = ad.get('target', {})
            add_info = {c['label']: c['values'] for c in ad.get('additionalInformation', [])}
            chars = {c['key']: c['value'] for c in ad.get('characteristics', [])}
            loc = ad.get('location', {})
            cords = loc.get('coordinates', {})
            
            lat = cords.get('latitude')
            long = cords.get('longitude')

            row = {
                'price': chars.get('price'),
                'rent': chars.get('rent'),
                'area': chars.get('m'),
                'extras': ", ".join(target.get('Extras_types', [])) if target and target.get('Extras_types') else None, #extras are represented in a list of values, so we put them into comma separated value so we can save it to csv
                'price_per_sq_m': chars.get('price_per_m'),
                'no_rooms': chars.get('rooms_num'),
                'market_type': chars.get('market'),
                'building_type': chars.get('building_type'),
                'no_floor': chars.get('floor_no'),
                'building_floors_num': chars.get('building_floors_num'),
                'windows_type': chars.get('windows_type'),
                'construction_status': chars.get('construction_status'),
                'building_ownership': chars.get('building_ownership'),
                'lat': lat,
                'long': long,
                'district': district_name,
                'built_year': add_info.get('build_year')[0] if add_info.get('build_year') else None,
                'url': url
            }
            return row
            
    except Exception as e:
        print(f'Error while scraping details {url}: {e}')
        return None

def scrape_district(district_name):
    print(f'\n Starting scraping: {district_name}')
    
    #core url for scraping different districts
    base_url = f'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa/{district_name}'
    
    driver = setup_driver()
    
    try:
        driver.get(base_url)
        close_cookies(driver)
        time.sleep(2)
        
        max_pages = select_max_pages(driver)
        print(f'District {district_name}: {max_pages} found to download.')
        
        for page in range(1, max_pages + 1):
            separator = '&' if '?' in base_url else '?'
            current_page_url = f"{base_url}{separator}page={page}"
            
            print(f'Downloading page: {page}/{max_pages}')
            driver.get(current_page_url)
            
            
            time.sleep(random.uniform(3, 5))
            
            links = collect_offer_links(driver)
            
            if not links:
                print('No links on the page')
                continue
            
            page_data = []
            for link in links:
                details = get_offer_details_fast(link, district_name)
                if details:
                    page_data.append(details)
                time.sleep(random.uniform(0.8, 1.5))
            
            #saving data after each page
            if page_data:
                df = pd.DataFrame(page_data)
                header_mode = not os.path.exists(output_dir)
                df.to_csv(
                    output_dir, 
                    mode='a', 
                    index=False, 
                    header=header_mode, 
                    encoding='utf-8-sig',
                    sep=';',                  
                    quoting=csv.QUOTE_ALL, 
                    lineterminator='\n'      
                )
                print(f'Saved {len(page_data)} offers to the file.')
                
    except Exception as e:
        print(f'Error while scraping {district_name}: {e}')
    finally:
        driver.quit()
        print(f'Succesfully scraped {district_name}')

def main():
    print('Starting scraping')
    
    for district in districts:
        try:
            scrape_district(district)

            time.sleep(random.uniform(10, 20))
            
        except KeyboardInterrupt:
            print('\nStopped by the user')
            break
        except Exception as e:
            print(f'Error while scraping {e}')

    print('\n Scraping finished')

if __name__ == '__main__':
    main()