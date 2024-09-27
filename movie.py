from bs4 import BeautifulSoup
from selenium import webdriver
import sqlite3
import datetime
from selenium.webdriver import ChromeOptions

#Connect to sqlite 3 database containing shows table
con  = sqlite3.connect('showDatabase.db')
cursor = con.cursor()

def scrape_and_insert():
    #*Scrapes the top 250 shows from IMDB and inserts them into a table in showDatabase
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d') #Timestamp used to mark each entry
    cursor.execute("CREATE TABLE IF NOT EXISTS shows(ID INTEGER PRIMARY KEY, title, score, rating, timestamp)") # Create a sqlite3 table with an id, title, imdb rating, maturity rating, and a timestamp

    #Selenium webdriver setup
    options = ChromeOptions() #Needed to set headless mode
    options.add_argument("--headless=new") #Run webdriver in headless mode
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36") #User agent needed when running in headless mode
    driver = webdriver.Chrome(options=options) #apply options
    url = "https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250" #imdb url
    driver.get(url) #set url

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #scroll to bottom of page to load all items

    page_source = driver.page_source #beautiful soup page source after loading full page
    soup = BeautifulSoup(page_source, "lxml") #create Beautiful Soup object

    # Get ul item containing all shows
    showList = soup.findAll('ul', attrs={'class': 'ipc-metadata-list ipc-metadata-list--dividers-between sc-a1e81754-0 dHaCOW compact-list-view ipc-metadata-list--base'})

    # Create result set containing all show 'li' itemsdbdb
    li_items = showList[0].findAll('li', attrs={'class':'ipc-metadata-list-summary-item sc-10233bc-0 TwzGn cli-parent'})

    for li in li_items:  # Iterate over each 'li'
        title = li.findChildren('h3', attrs={'class': 'ipc-title__text'})[0].contents[0].encode('utf-8').decode('ascii', 'ignore') #set title value, this needs editing later
        score = li.findChildren('span', attrs={'ipc-rating-star--rating'})[0].contents[0].encode('utf-8').decode('ascii', 'ignore') #set imdb rating (score)
        #some ratings don't exist, so use try & except
        try:
            rating = li.findChildren('span', attrs=['sc-b189961a-8 hCbzGp cli-title-metadata-item'])[2].contents[0].encode('utf-8').decode('ascii', 'ignore')
        except:
            rating = "NA" #for all shows where the maturity rating is blank
        
        #format title (remove leading numbers & space)
        title = title[title.index(' ')+1:]

        #insert into table
        params = (title, score, rating, timestamp)
        cursor.execute("INSERT INTO shows(title, score, rating, timestamp) VALUES (?, ?, ?, ?)", params)
        con.commit()
    driver.quit() #quit webdriver

def compare_data():
    '''
    Compares imdb tv show rankings from yesterday to today

    Returns
    -------
    2d list containing the name of a show and ranking increase (0 for a new show)
    '''

    today = datetime.datetime.now().strftime('%Y-%m-%d') #Set the value for today in the same format as the table
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d') #Set the value for yesterday in the same format as the table

    cursor.execute('SELECT id, title, score, rating FROM shows WHERE timestamp = ?', (today,)) #Get all tv shows from today
    today_data = cursor.fetchall() #Store in a variable

    cursor.execute('SELECT id, title, score, rating FROM shows WHERE timestamp = ?', (yesterday,)) #Get all tv shows from yesterday
    yesterday_data = cursor.fetchall() #Store in a variable

    #*Create sets from today and yesterday data without IDs or IMDB ratings to find all new shows on the top 250 list
    today_set = {(title, rating) for _, title, rating in today_data}
    yesterday_set = {(title, rating) for _, title, rating in yesterday_data}

    newShows = list(today_set - yesterday_set) # ? does this add shows that were added and removed to the newShows list?

    changes = []
    #*Iterate through today_data and determine if a show moved positions
    for today_show in today_data:
        id, title, rating = today_show #
        if (title, rating) not in newShows:

            #find the equivalent show from yesterday
            cursor.execute('SELECT id, title, rating FROM shows WHERE timestamp = ? AND title = ?', (yesterday, title))
            yesterday_show = cursor.fetchone()

            if yesterday_show: #if there is an equivalent show for yesterday #? is this necessary
                if (title, rating) != (yesterday_show[1], yesterday_show[3]):
                    rank_difference = (id) - (yesterday_show[0]+500)
                    changes += [title, rank_difference]
    
    return changes + newShows

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

scrape_and_insert()
con.close()