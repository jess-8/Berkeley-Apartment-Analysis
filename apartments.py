import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from  webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import itertools
import sys
import re
import statistics
import json

apartment_names = []
apartment_prices = []
apartment_type = []
apartment_dates = []
diff_pages = []
temp = []

# combine sub-lists into a large list
def combine_lsts(lst):
    return [inner for details in lst for inner in details]

# convert lists to strings
def convert_to_string(lst):
    if lst:
        return json.dumps(lst).replace('[', '').replace(']', '').replace('"', '')
    return

# get all links for each apartment in a page of Apartments.com
def retrieve_links(website_url):
    global apart_name

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get(f"{website_url}")

    actions = ActionChains(driver)

    try:
        items = driver.find_element(By.ID, "placardContainer")
        all_li = items.find_elements(By.TAG_NAME, "li")
    except selenium.common.exceptions.TimeoutException:
        print(f'taking too long!')
        sys.exit()
    except selenium.common.exceptions.InvalidSelectorException:
        print(f'Check')
        sys.exit()
    else:
        for i in all_li:
            link = i.find_element(By.TAG_NAME, 'a').get_attribute('href')
            # filter for correct link
            if link and 'tour' not in link and 'video' not in link and 'javascript' not in link and '/berkeley-ca/' not in link:
                get_details(link)

    # after storing all info for each apartment in dict, make all entries strings
    to_excel(apartment_names, apartment_prices, apartment_type, apartment_dates)

# extract information within each apartment's webpage
def get_details(link):
    global apartment_prices
    global apartment_names
    global apartment_type
    global apartment_dates
    global number_bed

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get(f"{link}")

    actions = ActionChains(driver)

    try:
        # get apartment name and address (filter for only Berkeley apartments)
        apart_name, address = driver.find_element(By.CSS_SELECTOR, "div[class*=propertyNameRow]"), driver.find_element(By.CSS_SELECTOR, "div[class*=propertyAddressRow]")
        if 'berkeley' not in address.text.lower():
            return
        else:
            items = driver.find_elements(By.CSS_SELECTOR, "div[class*=pricingGridItem]")
    except selenium.common.exceptions.TimeoutException:
        print(f'taking too long!')
        sys.exit()
    except selenium.common.exceptions.InvalidSelectorException:
        print(f'Check')
        sys.exit()
    except selenium.common.exceptions.NoSuchElementException:
        print(f'no such element')
        sys.exit()
    else:
        apart_name, address = apart_name.text, [address.text.splitlines()[0]]

        # clean apartment details (exclude unnecessary info)
        stopwords = ['Tour This Floor Plan', 'Show Floor Plan Details', 'Unit', 'Price', 'price', 'square feet', 'Apply Now', 'Availability', 'Floor Plan', 'Virtual Tour', 'Photos', 'Floor Plans']
        for i in items:
            details = list(filter(lambda w: w not in stopwords and not re.search('^View', w), i.text.splitlines()))
            if details:
                # get availability date
                get_date(apart_name, details)
            else:
                print(apart_name)
                return

# get availability dates for all rooms for each apartment
def get_date(apart_name, details):
    global apartment_prices
    global apartment_names
    global apartment_type
    global number_bed
    global apartment_dates

    # normlaly, date follows after 'availability'
    for i in range(len(details)):   
        if details[i] == "availibility":
            date_available = details[i+1]

    try:
        if date_available.lower() == 'available now':
            date_available = 'Now'
    except (UnboundLocalError, NameError) as e:
        # if no 'availablity' in apartment details, date is last (clean and filter)
        date_available = details[-1]
        if ', ' in date_available:
            date_available = date_available.split(', ')
            date_words = ['Available', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Now']
            func = lambda w: any([re.sub(r'[^\w\s]', '', i) in date_words for i in w.split(' ') if i])
            check = list(map(func, date_available))
            date_available = convert_to_string([date_available[check.index(listed_date)] for listed_date in check if listed_date])
    
    get_price(apart_name, details, date_available)


# get prices for each room type
def get_price(apart_name, details, date_available):
    global apartment_prices
    global apartment_names
    global apartment_type
    global number_bed
    global apartment_dates
    # filter for prices
    for info_piece in details:
        if '$' in info_piece and 'deposit' not in info_piece:
            split_prices = info_piece.replace(' / Person', '').split('$')
            if '–' not in info_piece:
                prices = int(split_prices[1].replace(',', ''))
            else:
                # if there is a price range listed, find the mean of that price range
                prices = [int(j.replace(' – ', '').replace(',', '')) if '–' in j else int(j.replace(',', '')) if j else None for j in split_prices]
                prices.remove(None)
                prices = sum(prices) / len(prices)
    # if no prices listed, return ['NA'] for that value
    if not prices:
        prices = 'NA'

    # get all possible matching strings (into lists) that can be room types
    test = [info.split(', ')[:-1] for info in details if ('bed' in info or 'beds' in info or 'Studio' in info) and ('bath' in info or 'baths' in info)]
    
    if details:
        number_bed = test[0][0].split(', ')[0]
        apartment_names.append(apart_name)
        apartment_type.append(number_bed)
        apartment_prices.append(prices)
        apartment_dates.append(date_available)

# transfer to excel spreadsheet
def to_excel(apartment_names, apartment_prices, apartment_type, apartment_dates):
    df = pd.DataFrame(
        {'Apartment Names': apartment_names,
         'Room Type': apartment_type,
         'Prices': apartment_prices, 
         'Date Available': apartment_dates}
    )

    df.to_excel('four_col.xlsx', index=False)
    print('done')
    sys.exit()

retrieve_links('https://www.apartments.com/apartments/berkeley-ca')
