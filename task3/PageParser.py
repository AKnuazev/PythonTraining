import json
import requests
from os import getcwd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread, Lock
from multiprocessing import Pool
from time import time, sleep
from math import ceil


# ======================= MULTITHREADING =======================

# Locker
threadLock = Lock()


class AppParsingThread(Thread):
    """ Class for own threads """
    def __init__(self, apps, keyword, pageData):
        Thread.__init__(self)
        self.apps = apps
        self.keyword = keyword
        self.pageData = pageData

    def run(self):
        appData = []
        for appBlock in self.apps:
            data = get_app_data(appBlock, self.keyword)
            if data is not None:
                appData.append(data)    # Parse page

        threadLock.acquire()            # Lock
        self.pageData.extend(appData)   # Save to global
        threadLock.release()            # Unlock


# ======================= PAGES PARSING =======================
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
        or None if smth is wrong
    """
    baseURL = "https://play.google.com"  # Base part of URL
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
        return None  # Unavailable url -> return None

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
    pageData = []  # List for apps data

    startTime = time()                                  # Getting apps list starts
    soup = BeautifulSoup(html, features='lxml')         # Object for parsing the page code
    apps = soup.find_all('div', class_='Q9MA7b')        # Getting a list of found application blocks
    print("• Getting apps list:\t", time() - startTime) # Getting apps list ends

    startTime = time()  # App parsing starts

    # Calculations for threads creation
    THREADS_NUMBER = 8  # Based on a small research - gives best efficiency (about 30 apps on thread on popular words)
    step = ceil(len(apps)/THREADS_NUMBER)

    # Threads creation
    pool = []   # Pool of threads
    for i in range(THREADS_NUMBER):
        start = step*i
        end = step*(i+1) if step*(i+1) < len(apps) else len(apps)
        newThread = AppParsingThread(apps[start:end], keyword, pageData)     # Create
        newThread.start()                                                    # Start
        pool.append(newThread)                                               # Save to list

    # Wait for threads to end
    for thread in pool:
        thread.join()

    print("• Parsing apps pages:\t", time() - startTime)  # App parsing ends

    print("\n============ SEARCH STATISTIC ============")
    print("• Total apps found:\t", len(apps))
    print("• Relevant apps:\t", len(pageData))
    return pageData


def get_page_html(URL):
    """ Returns HTML code of page with apps, that were found by keyword (using Chrome driver)

        Arguments:
        --------------------
        URL -- page with found apps URL

        Output:
        --------------------
        <html>...</html>
    """
    print("\n============= TIME STATISTIC =============")
    SCROLL_PAUSE_TIME = 1  # Time to wait for page to load new apps

    # Set up browser
    startTime = time()
    options = Options()
    options.headless = True  # Disable opening window
    browser = webdriver.Chrome(executable_path=getcwd() + "/chromedriver", options=options)

    browser.get(URL)  # Load page by URL

    lastHeight = None
    newHeight = browser.execute_script("return document.body.scrollHeight")  # Get scroll height
    while not lastHeight == newHeight:
        lastHeight = newHeight
        script = "window.scrollTo(0, document.body.scrollHeight);"  # Script to scroll down
        browser.execute_script(script)  # Execute script

        sleep(SCROLL_PAUSE_TIME)  # Wait for page to load new apps

        newHeight = browser.execute_script("return document.body.scrollHeight")  # Get new height

    print("• Getting page code:\t", time()-startTime)
    return browser.page_source


# ======================= CONTROL =======================
def main():
    print("Welcome to Google Play Store parsing app")
    print("-------------------------------------------\n")
    print("Enter a keyword to search for applications:")
    keyword = input()

    URL = "https://play.google.com/store/search?q=" + keyword + "&c=apps"
    html = get_page_html(URL)

    pageData = get_page_data(html, keyword)

    print("\n=============== APPS DATA: ===============")
    print(json.dumps(pageData, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
