
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
import os
from webdriver_manager.chrome import ChromeDriverManager

def cleanInstagramNumber(followers):
    if ',' in followers:
        followers=followers.replace(',','.')
        return int(float(followers)*1000)
    if 'k' in followers:
        followers=followers[:-1]
        return int(float(followers)*1000)
    else:
        return int(followers)

def scrape_Instagram(folder,baseURL=r'https://www.instagram.com//'):
    """
    Function that scapes Instagram followers 
    """
    url=os.path.join(baseURL,folder)
    print(url)
    rows = BeautifulSoup(urlRQ.urlopen(url).read(),'lxml').findAll('meta')#[0].tbody.findAll('tr')
    for row in rows:
        content=str(row.get('content'))
        if 'Followers' in content or 'volgers' in content:
            followers=content.split()[0]
            return cleanInstagramNumber(followers)

    #driver = webdriver.Chrome()
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    time.sleep(10)#wait some time to allow the script to load all javascript
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    #print(soup.prettify())#print all the html fetched
    
    spans=soup.findAll("span",attrs={'class': 'g47SY'})
    for span in spans:
        try:
            return cleanInstagramNumber(span.attrs['title'])
        except:
            pass

def scrape_Weibo(folder,baseURL=r'https://www.weibo.com//'):
    #driver = webdriver.Chrome()
    driver = webdriver.Chrome(ChromeDriverManager().install())
    url = baseURL+folder#"https://www.weibo.com/canadagooseofficial"
    driver.get(url)
    time.sleep(20)#wait some time to allow the script to load all javascript
    driver.get(url)#redoing it to get away from the default page is required, somethimes
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

def scrape_Pinterest(folder,baseURL=r'https://www.pinterest.com/'):
    """
    Function that scapes Pinterest followers 
    """
    url=baseURL+folder+'/_community/'
    print(url)
    try:
        soup = BeautifulSoup(urlRQ.urlopen(url).read(),'lxml')
    except:
        time.sleep(1)
        soup = BeautifulSoup(urlRQ.urlopen(url).read(),'lxml')
    text=soup.get_text()
    #print(text)
    followers=int(text[text.index('followers')+11:text.index('pinterestapp:following')-2])
    print(followers)
    return followers

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

#GET PINTEREST FOLLOWERS
SmartPhoto_followers_Pinterest_Belgium=scrape_Pinterest(folder='smartphotobe',baseURL=r'https://www.pinterest.com/')
SmartPhoto_followers_Pinterest_Netherlands=scrape_Pinterest(folder='smartphotonl',baseURL=r'https://www.pinterest.com/')
SmartPhoto_followers_Pinterest_France=scrape_Pinterest(folder='smartphotofr',baseURL=r'https://www.pinterest.com/')
SmartPhoto_followers_Pinterest_Suisse=scrape_Pinterest(folder='smartphoto',baseURL=r'https://www.pinterest.com/')
SmartPhoto_followers_Pinterest_UK=scrape_Pinterest(folder='smartphotocouk',baseURL=r'https://www.pinterest.com/')
SmartPhoto_followers_Pinterest_Sweden=scrape_Pinterest(folder='smartphotonord',baseURL=r'https://www.pinterest.com/')
SmartPhoto_followers_Pinterest_Germany=scrape_Pinterest(folder='smartphotodeu',baseURL=r'https://www.pinterest.com/')
SmartPhoto_followers_Pinterest_CanadaGoose=scrape_Pinterest(folder='canadagooseinc',baseURL=r'https://www.pinterest.com/')
   
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
        SmartPhoto_followers_Instagram_UK,SmartPhoto_followers_Pinterest_Belgium,SmartPhoto_followers_Pinterest_Netherlands,
        SmartPhoto_followers_Pinterest_France,SmartPhoto_followers_Pinterest_Suisse,SmartPhoto_followers_Pinterest_UK,
        SmartPhoto_followers_Pinterest_Sweden,SmartPhoto_followers_Pinterest_Germany,SmartPhoto_followers_Pinterest_CanadaGoose]
print(fields)
with open(r'C:\Users\joris\.spyder-py3\good code\scraping\scraping.csv', 'a',newline='') as f:
    writer = csv.writer(f)
    writer.writerow(fields)
 
print('new scrapings saved with success.')
    
