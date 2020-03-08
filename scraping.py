
# =============================================================================
# from weibo_scraper import get_weibo_profile
# #weibo_profile = get_weibo_profile(name='来去之间',)
# weibo_profile = get_weibo_profile(name='来去之间',)
# print(weibo_profile)
# =============================================================================

from bs4 import BeautifulSoup
from selenium import webdriver
import time
from datetime import datetime
import csv
import urllib.request as urlRQ

print(bs4.__version__)

def scrape_Instagram(folder,baseURL=r'https://www.instagram.com//'):
    """
    Function that scapes Instagram followers 
    """
    url=baseURL+folder
    rows = BeautifulSoup(urlRQ.urlopen(url).read(),'lxml').findAll('meta')#[0].tbody.findAll('tr')
    for row in rows:
        content=str(row.get('content'))
        if 'Followers' in content:
            followers=content.split()[0]
            if ',' in followers:
                followers=followers.replace(',','.')
                return int(float(followers)*1000)
            if 'k' in followers:
                followers=followers[:-1]
                return int(float(followers)*1000)
            else:
                return int(followers)

def scrape_Weibo(folder,baseURL=r'https://www.weibo.com//'):
    driver = webdriver.Chrome()
    url = baseURL+folder#"https://www.weibo.com/canadagooseofficial"
    driver.get(url)
    time.sleep(30)#wait so,e time to allow the script to load all javascript
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    #print(soup.prettify())#print all the html fetched
    
    tableCounter=soup.findAll("table", {"class": "tb_counter"})[0].tbody.findAll('tr')
    for each_row in tableCounter:
        divs = each_row.findAll('td')
        #print(divs)
        if divs[1].span.text=='粉丝': #use only the row from the table with followers info
            CanadaGoose_followers_Weibo=int(divs[1].strong.text)
            return CanadaGoose_followers_Weibo

#GET INSTAGRAM FOLLOWERS
SmartPhoto_followers_Instagram_Belgium=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphotobe/')
SmartPhoto_followers_Instagram_France=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto_fr/')
SmartPhoto_followers_Instagram_Netherlands=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto.nl/')
SmartPhoto_followers_Instagram_Germany=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto.de/')
SmartPhoto_followers_Instagram_Denmark=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto.dk/')
SmartPhoto_followers_Instagram_Suisse=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto_ch/')
SmartPhoto_followers_Instagram_Sweden=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphotose/')
SmartPhoto_followers_Instagram_Norway=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto.no/')
SmartPhoto_followers_Instagram_Finland=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto.fi/')
SmartPhoto_followers_Instagram_UK=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'smartphoto.co.uk/')
CanadaGoose_followers_Instagram=scrape_Instagram(baseURL=r'https://www.instagram.com/',folder=r'canadagoose/')
           
#GET WEIBO FOLLOWERS
attempts=0
while attempts<3:
    try:
        CanadaGoose_followers_Weibo=scrape_Weibo(r'canadagooseofficial',baseURL=r'https://www.weibo.com//')
        break
    except Exception as e:
        print(e)
        attempts+=1

#write results to csv  
fields=[datetime.today().date(),CanadaGoose_followers_Weibo,SmartPhoto_followers_Instagram_Belgium,CanadaGoose_followers_Instagram,
        SmartPhoto_followers_Instagram_France,SmartPhoto_followers_Instagram_Netherlands,SmartPhoto_followers_Instagram_Germany,SmartPhoto_followers_Instagram_Denmark,
        SmartPhoto_followers_Instagram_Suisse,SmartPhoto_followers_Instagram_Sweden,SmartPhoto_followers_Instagram_Norway,SmartPhoto_followers_Instagram_Finland,
        SmartPhoto_followers_Instagram_UK]
print(fields)
with open(r'E:\financieel\beleggingen\scraping.csv', 'a',newline='') as f:
    writer = csv.writer(f)
    writer.writerow(fields)
 
print('new scrapings saved with success.')