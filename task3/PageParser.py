import json
import requests
from os import getcwd
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread, Lock
from time import time, sleep
from math import ceil

# Locker
thread_lock = Lock()


class AppParsingThread(Thread):
    """ Class for own threads """
    def __init__(self, apps: list, keyword: str, page_data: list):
        Thread.__init__(self)

        self.apps = apps
        self.keyword = keyword
        self.page_data = page_data

    def run(self):
        app_data = []
        for app_block in self.apps:
            data = get_app_data(app_block, self.keyword)
            if data is not None:
                app_data.append(data)    # Parse page

        thread_lock.acquire()            # Lock
        self.page_data.extend(app_data)  # Save to global
        thread_lock.release()            # Unlock


def get_app_data(app_block: Tag, keyword: str) -> dict:
    """Returns dictionary with app data by its URL

        Arguments:
        --------------------
        title   -- app title
        app_URL  -- app URL

        Output:
        --------------------
        {
            "title": str,
            "url": str
            "author": str,
            "category": str,
            "description": str
            "marks_number": int,
            "mean_mark": float,
            "lastUpdate": str,
        }
        or None if smth is wrong
    """
    base_URL = "https://play.google.com"  # Base part of URL
    try:
        title = app_block.text                              # Get title
        app_URL = app_block.next_element.attrs['href']      # Get URL
        # Check if the keyword is present in title
        if keyword.lower() not in title.lower():
            return None
    except:
        return None  # If for some reason got app with no title -> return None

    app_data = {"title": title, "url": base_URL + app_URL}      # Dict for app data
    try:
        html = requests.get(base_URL + app_URL).text            # HTML code of app page
    except:
        return None  # Unavailable url -> return None

    soup = BeautifulSoup(html, 'lxml')  # Object for parsing the page code

    # Parse page blocks one by one
    # DATA: author, category
    try:
        infoBlock = soup.find('div', class_="qQKdcc")
        app_data["author"] = infoBlock.next.text
        app_data["category"] = infoBlock.text[len(app_data["author"]):]

    except:
        app_data["author"] = None
        app_data["category"] = None

    # DATA: description
    try:
        infoBlock = soup.find('div', class_="DWPxHb")
        app_data["description"] = infoBlock.next.next.text
    except:
        app_data["description"] = None

    # DATA: mean_mark, marks_number
    try:
        infoBlock = soup.find('div', class_="K9wGie")
        app_data["mean_mark"] = float(infoBlock.next.text)
        marksNumberText = infoBlock.next.next_sibling.next_sibling.text
        app_data["marks_number"] = int(marksNumberText.replace(",", "")[:-5])
    except:
        app_data["mean_mark"] = None
        app_data["marks_number"] = None

    # DATA: lastUpdate
    try:
        infoBlock = soup.find('div', class_="IxB2fe")
        app_data["lastUpdate"] = infoBlock.next.text.replace("Updated", "")
    except:
        app_data["lastUpdate"] = None

    return app_data


def get_page_data(html: str, keyword: str) -> list:
    """ Returns a list of dictionaries with data about applications on the page

        Arguments:
        --------------------
        html    -- page html code
        keyword -- word by which we are looking for apps

        Output:
        --------------------
        [ app1Data, app2Data, ... ]
    """
    page_data = []  # List for apps data

    start_time = time()                                     # Getting apps list starts
    soup = BeautifulSoup(html, features='lxml')             # Object for parsing the page code
    apps = soup.find_all('div', class_='Q9MA7b')            # Getting a list of found application blocks
    print("• Getting apps list:\t", time() - start_time)    # Getting apps list ends

    start_time = time()  # App parsing starts

    # Calculations for threads creation
    THREADS_NUMBER = 8  # Based on a small research - gives best efficiency (about 30 apps per thread on popular words)
    step = ceil(len(apps)/THREADS_NUMBER)

    # Threads creation
    pool = []   # Pool of threads
    for i in range(THREADS_NUMBER):
        start = step*i
        end = step*(i+1) if step*(i+1) < len(apps) else len(apps)
        new_thread = AppParsingThread(apps[start:end], keyword, page_data)   # Create
        new_thread.start()                                                   # Start
        pool.append(new_thread)                                              # Save to list

    # Wait for threads to end
    for thread in pool:
        thread.join()

    print("• Parsing apps pages:\t", time() - start_time)  # App parsing ends

    print("\nSEARCH STATISTIC:")
    print("• Total apps found:\t", len(apps))
    print("• Relevant apps:\t", len(page_data))

    return page_data


def get_page_html(URL: str) -> str:
    """ Returns HTML code of page with apps, that were found by keyword (using Chrome driver)

        Arguments:
        --------------------
        URL -- page with found apps URL

        Output:
        --------------------
        <html>...</html>
    """
    print("\nTIME STATISTIC:")
    SCROLL_PAUSE_TIME = 1  # Time to wait for page to load new apps

    # Set up browser
    start_time = time()
    options = Options()
    options.headless = True  # Disable opening window
    browser = webdriver.Chrome(executable_path=getcwd() + "/chromedriver", options=options)

    browser.get(URL)  # Load page by URL

    last_height = None
    new_height = browser.execute_script("return document.body.scrollHeight")     # Get scroll height
    while not last_height == new_height:
        last_height = new_height
        script = "window.scrollTo(0, document.body.scrollHeight);"  # Script to scroll down
        browser.execute_script(script)                              # Execute script

        sleep(SCROLL_PAUSE_TIME)                                    # Wait for page to load new apps

        new_height = browser.execute_script("return document.body.scrollHeight")  # Get new height

    print("• Getting page code:\t", time()-start_time)
    return browser.page_source


def main():
    print("Welcome to Google Play Store parsing app")
    print("-------------------------------------------\n")
    print("Enter a keyword to search for applications:")
    keyword = input()

    URL = "https://play.google.com/store/search?q=" + keyword + "&c=apps"
    html = get_page_html(URL)

    page_data = get_page_data(html, keyword)

    print("\nAPPS DATA:")
    print(json.dumps(page_data, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
