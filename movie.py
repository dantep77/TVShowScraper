from bs4 import BeautifulSoup
from selenium import webdriver
import sqlite3
import datetime
from selenium.webdriver import ChromeOptions

#set up sqlite database
con  = sqlite3.connect('showDatabase.db')
cursor = con.cursor()


def scrape_and_insert():
    # create a table containing data about each of the top 250 imdb shows
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d')
    cursor.execute("CREATE TABLE IF NOT EXISTS shows(ID INTEGER PRIMARY KEY, title, score, rating, timestamp)")

    # Set up selenium web driver
    options = ChromeOptions()
    options.add_argument("--headless=new") #run in headless mode
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36") #user agent must be set or page doesn't load?
    driver = webdriver.Chrome(options=options)
    url = "https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250"
    driver.get(url)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #scroll to bottom of page to load all items

    page_source = driver.page_source #beautiful soup page source after loading full page
    soup = BeautifulSoup(page_source, "lxml") #create Beautiful Soup object

    # Get ul item containing all shows
    showList = soup.findAll('ul', attrs={'class': 'ipc-metadata-list ipc-metadata-list--dividers-between sc-a1e81754-0 dHaCOW compact-list-view ipc-metadata-list--base'})

    # Create result set containing all show 'li' itemsdbdb
    li_items = showList[0].findAll('li', attrs={'class':'ipc-metadata-list-summary-item sc-10233bc-0 TwzGn cli-parent'})

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
        params = (title, score, rating, timestamp)
        cursor.execute("INSERT INTO shows(title, score, rating, timestamp) VALUES (?, ?, ?, ?)", params)
        con.commit()
    driver.quit()

def compare_data():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    cursor.execute('SELECT id, title, score, rating FROM shows WHERE timestamp = ?', (today,))
    today_data = cursor.fetchall()

    cursor.execute('SELECT id, title, score, rating FROM shows WHERE timestamp = ?', (yesterday,))
    yesterday_data = cursor.fetchall()

    today_set = {(title, score, rating) for _, title, score, rating in today_data}
    yesterday_set = {(title, score, rating) for _, title, score, rating in yesterday_data}

    newShows = list(today_set - yesterday_set)

    for today_show in today_data:
        id, title, score, rating = today_show
        if (title, score, rating) not in newShows:
            cursor.execute('SELECT id, title, score, rating FROM shows WHERE timestamp = ? AND title = ?', (yesterday, title))
            yesterday_show = cursor.fetchone()
            if yesterday_show:
                if (title, score, rating) != (yesterday_show[1], yesterday_show[2], yesterday_show[3]):
                    rank_difference = (id) - (yesterday_show[0]+500)
                    print(f"{title} (ID: {id}) moved {rank_difference} positions")
    
    print(newShows)
def remove_duplicates():
    cursor.execute('''
        DELETE FROM shows
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM shows
            GROUP BY title, score, rating, timestamp
        )
    ''')

    con.commit()

con.close()