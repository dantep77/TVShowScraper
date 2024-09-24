from bs4 import BeautifulSoup
from selenium import webdriver
import sqlite3

#set up sqlite database
con  = sqlite3.connect('showDatabase.db')
cursor = con.cursor()

# create a table containing data about each of the top 250 imdb shows
cursor.execute("CREATE TABLE IF NOT EXISTS shows(ID INTEGER PRIMARY KEY, title, score, rating, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
res = cursor.execute("SELECT name FROM sqlite_master")

# Set up selenium web driver
driver = webdriver.Chrome()
url = "https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250"
driver.get(url)

driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #scroll to bottom of page to load all items

page_source = driver.page_source #beautiful soup page source after loading full page
soup = BeautifulSoup(page_source, "lxml") #create Beautiful Soup object

# Get ul item containing all shows
showList = soup.findAll('ul', attrs={'class': 'ipc-metadata-list ipc-metadata-list--dividers-between sc-a1e81754-0 dHaCOW compact-list-view ipc-metadata-list--base'})

    # Create result set containing all show 'li' itemsdbdb
li_items = showList[0].findAll('li', attrs={'class':'ipc-metadata-list-summary-item sc-10233bc-0 TwzGn cli-parent'})

key = 1 #id for each show entry
for li in li_items:  # Iterate over each 'li'
    title = li.findChildren('h3', attrs={'class': 'ipc-title__text'})[0].contents[0].encode('utf-8').decode('ascii', 'ignore')
    score = li.findChildren('span', attrs={'ipc-rating-star--rating'})[0].contents[0].encode('utf-8').decode('ascii', 'ignore')
    #some ratings don't exist, so use try & except
    try:
        rating = li.findChildren('span', attrs=['sc-b189961a-8 hCbzGp cli-title-metadata-item'])[2].contents[0].encode('utf-8').decode('ascii', 'ignore')
    except:
        rating = "NA"
    
    #format title (remove leading numbers & space)
    title = title[title.index(' ')+1:]

    #insert into table
    params = (key, title, score, rating)
    cursor.execute("INSERT OR REPLACE INTO shows(ID, title, score, rating) VALUES (?, ?, ?, ?)", params)
    con.commit()
    key += 1
print(res.fetchall())
driver.quit()
