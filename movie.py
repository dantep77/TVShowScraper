from bs4 import BeautifulSoup
from selenium import webdriver
import time
import csv
import os
print(os.getcwd())

# Set up selenium web driver
driver = webdriver.Chrome()
url = "https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250"
driver.get(url)

#csv file set up
file = open("tv_show.csv", "w", newline='')
writer = csv.writer(file)
writer.writerow(["TITLE", "SCORE", "RATING"])
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #scroll to bottom of page to load all items

page_source = driver.page_source
soup = BeautifulSoup(page_source, "lxml") #create Beautiful Soup object

# Get ul item containing all shows
showList = soup.findAll('ul', attrs={'class': 'ipc-metadata-list ipc-metadata-list--dividers-between sc-a1e81754-0 dHaCOW compact-list-view ipc-metadata-list--base'})

    # Create result set containing all show 'li' items
li_items = showList[0].findAll('li', attrs={'class':'ipc-metadata-list-summary-item sc-10233bc-0 TwzGn cli-parent'})

for li in li_items:  # Iterate over each 'li'
    title = li.findChildren('h3', attrs={'class': 'ipc-title__text'})[0].contents[0].encode('utf-8').decode('ascii', 'ignore')
    score = li.findChildren('span', attrs={'ipc-rating-star--rating'})[0].contents[0].encode('utf-8').decode('ascii', 'ignore')
    try:
        rating = li.findChildren('span', attrs=['sc-b189961a-8 hCbzGp cli-title-metadata-item'])[2].contents[0].encode('utf-8').decode('ascii', 'ignore')
    except:
        rating = "NA"
    
    #format output
    print(title)
    title = title[title.index(' ')+1:]

    #write to csv file
    writer.writerow([title,score,rating])
file.close()
driver.quit()