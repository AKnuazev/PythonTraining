![Google Play Logo](images/Google_Play-Logo.wine.png)
# Google Play Store parsing app
## Logic
### Step 1. Getting page code
```python 
def get_page_html(URL: str) -> str:
```
1. Create a browser object (based on the Chrome driver in this case, but any other can be used)
2. We transfer the URL to it and thereby load the page
3. Since the applications page uses dynamic loading, its needed to scroll down to access all applications. The algorithm following: as long as the current height of the page does not coincide with the latter, scroll down to the end and wait 1 second to load next applications

### Step 2. Getting apps list from the page
```python
apps = soup.find_all('div', class_='Q9MA7b')
```
Using tag ```div``` with class ```Q9MA7b``` we find all HTML app blocks

### Step 3. Getting app data from app html block
#### Multithreading
```python
class AppParsingThread(Thread):
```
To optimize the parsing was used multithreading
Thread accepts as input
- ```apps: list``` - part of the general list of HTML application blocks
- ```keyword: str``` - the word that apps were searched by
- ```page_data: list``` - a shared resource for writing received application data to

And then, at startup, sequentially transfers HTML blocks to the ```get_app_date``` function and adds the received information to ```page_data``` (to avoid data races, the addition is protected by locker)

#### Getting app data from HTML block
```python
def get_app_data(app_block: Tag, keyword: str) -> dict:
```
1. The function checks if the name contains a keyword. If not - returns ```None```
2. Then it makes a request to the application page. If the request failed, it returns ```None```
3. And at the end function sequentially iterates over the necessary tags and classes, obtaining the necessary data from the html blocks. If some data not found - writes ```None``` instead.

### Step 4. Returning the result
At the end found data is converted to JSON and printed in console with some extra statistics about parsing process.

## Required:
- json
- requests
- os
- bs4
- selenium
- threading
- time
- math

## Apps information displayed:
- name
- url of the application page
- author
- category
- description
- average rating
- number of ratings
- Last update

## Implementation features:
- Accessing a page using a browser
- Special tools for parsing pages
- Multithreading