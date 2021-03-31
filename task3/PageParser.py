import time
import json
import requests
from os import getcwd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread

def get_app_data(appBlock, keyword):
    """Returns dictionary with app data by its URL

        Arguments:
        --------------------
        title   -- app title
        appURL  -- app URL

        Output:
        --------------------
        {
            "title": str,
            "url": str
            "author": str,
            "category": str,
            "description": str
            "marksNumber": int,
            "meanMark": float,
            "lastUpdate": str,
        }
    """
    baseURL = "https://play.google.com"                 # Base part of URL
    try:
        title = appBlock.text                           # Get title
        appURL = appBlock.next_element.attrs['href']    # Get URL
        # Check if the keyword is present in title
        if keyword.lower() not in title.lower():
            return None
    except:
        return None  # If for some reason got app with no title -> return None

    appData = {"title": title, "url": baseURL + appURL}     # Dict for app data
    try:
        html = requests.get(baseURL + appURL).text          # HTML code of app page
    except:
        return None  # Unavailable url

    soup = BeautifulSoup(html, 'lxml')  # Object for parsing the page code

    # Parse page blocks one by one
    # DATA: author, category
    try:
        infoBlock = soup.find('div', class_="qQKdcc")
        appData["author"] = infoBlock.next.text
        appData["category"] = infoBlock.text[len(appData["author"]):]

    except:
        appData["author"] = None
        appData["category"] = None

    # DATA: description
    try:
        infoBlock = soup.find('div', class_="DWPxHb")
        appData["description"] = infoBlock.next.next.text
    except:
        appData["description"] = None

    # DATA: meanMark, marksNumber
    try:
        infoBlock = soup.find('div', class_="K9wGie")
        appData["meanMark"] = float(infoBlock.next.text)
        marksNumberText = infoBlock.next.next_sibling.next_sibling.text
        appData["marksNumber"] = int(marksNumberText.replace(",", "")[:-5])
    except:
        appData["meanMark"] = None
        appData["marksNumber"] = None

    # DATA: lastUpdate
    try:
        infoBlock = soup.find('div', class_="IxB2fe")
        appData["lastUpdate"] = infoBlock.next.text.replace("Updated", "")
    except:
        appData["lastUpdate"] = None

    return appData


def get_page_data(html, keyword):
    """ Returns a list of dictionaries with data about applications on the page

        Arguments:
        --------------------
        html    -- page html code
        keyword -- word by which we are looking for apps

        Output:
        --------------------
        [ app1Data, app2Data, ... ]
    """
    pageData = []                                   # List for apps data
    soup = BeautifulSoup(html, features='lxml')     # Object for parsing the page code

    # STEP 1: Parse first type of app blocks on page
    apps = soup.find_all('div', class_='Q9MA7b')    # Getting a list of found application blocks

    ''' NOTE: In plan was to make it using multiprocessing, but got some recursion troubles, had to skip
    Not working prototype:
    
    # Iterate over apps
    with Pool(processes=10) as pool:
        print(pool.map(partial(get_app_data), apps))
    '''
    # THREADS_NUMBER = 10
    # step = len(apps)/THREADS_NUMBER
    # pool = []
    # for i in range(THREADS_NUMBER):
    #     pool.append()

    for app in apps:
        data = get_app_data(app, keyword)

        # Check if the keyword is present in title
        if data is not None:
            pageData.append(data)                # Add app data to list
        else:
            continue    # If keyword was not found -> continue

    return pageData


def get_page_html(URL):
    """ Returns HTML code of page with apps, that were found by keyword (using Chrome driver)

        Arguments:
        --------------------
        URL -- page with found apps URL

        Output:
        --------------------
        <html>...<!html>
    """
    SCROLL_PAUSE_TIME = 1       # Time to wait for page to load new apps

    # Set up browser
    options = Options()
    options.headless = True    # Disable opening window
    browser = webdriver.Chrome(executable_path=getcwd() + "/chromedriver", options=options)

    browser.get(URL)            # Load page by URL

    lastHeight = None
    newHeight = browser.execute_script("return document.body.scrollHeight")   # Get scroll height
    while not lastHeight == newHeight:
        lastHeight = newHeight
        script = "window.scrollTo(0, document.body.scrollHeight);"  # Script to scroll down
        browser.execute_script(script)                              # Execute script

        time.sleep(SCROLL_PAUSE_TIME)   # Wait for page to load new apps

        newHeight = browser.execute_script("return document.body.scrollHeight")  # Get new height

    return browser.page_source


def main():
    print("Welcome to Google Play Store parsing app")
    print("-------------------------------------------")
    print("Enter a keyword to search for applications:")
    keyword = input()

    URL = "https://play.google.com/store/search?q="+keyword+"&c=apps"
    html = get_page_html(URL)

    pageData = get_page_data(html, keyword)

    print("\nResult:")
    print("-------------------------------------------")
    print(json.dumps(pageData, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
