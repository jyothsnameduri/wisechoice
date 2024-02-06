from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from amazoncaptcha import AmazonCaptcha
from googletrans import Translator,LANGUAGES
import re
import pandas as pd
import csv
from time import sleep

class Amazon_Review_Extract:
    def __init__(self):
        chrome_options = Options()
#         Uncommenting below 2 lines can disable the browser pop up
#         chrome_options.add_argument('--headless')
#         chrome_options.add_argument('--disable-gpu')
        

        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.data = []
        self.trans = Translator()
        
        
    def link(self,url):
        asin_pattern = r'/[A-Z0-9]{10}(?=/|$)'
        match = re.search(asin_pattern, url)
        if match:
            asin =  match.group(0)[1:]
            domain = url.split('ww.amazon.')[1][:3]
            return "https://www.amazon."+domain+"/product-reviews/"+asin+"/ref=cm_cr_arp_d_paging_btm_next_2?ie=UTF8&reviewerType=all_reviews&pageNumber="
        else:
            quit()
        
    def bypass(self):
        try:
            self.link = self.driver.find_element(By.XPATH,"//div[@class = 'a-row a-text-center']//img").get_attribute('src')
            captcha = AmazonCaptcha.fromlink(self.link)
            captcha_v = AmazonCaptcha.solve(captcha)
            ip = self.driver.find_element(By.ID,'captchacharacters').send_keys(captcha_v)
            butt = self.driver.find_element(By.CLASS_NAME,"a-button-text")
            butt.click()
        except :
            return 
        
    def extract(self,url):
        self.driver.get(url)
        self.bypass()
        html = BeautifulSoup(self.driver.page_source,'lxml')
        data_dicts = []
    
        # Select all Reviews BOX html using css selector
        boxes = html.select('div[data-hook="review"]')
        
        # Iterate all Reviews BOX 
        for box in boxes:
            
            # Select Name using css selector and cleaning text using strip()
            # If Value is empty define value with 'N/A' for all.
            try:
                name = box.select_one('[class="a-profile-name"]').text.strip()
            except Exception as e:
                name = 'N/A'

            try:
                stars = box.select_one('[data-hook="review-star-rating"]').text.strip().split(' out')[0]
            except Exception as e:
                stars = 'N/A'   

            try:
                title = box.select_one('[data-hook="review-title"]').text
                title = re.sub(r"\d.\d out of 5 stars", " ", title)
            except Exception as e:
                title = 'N/A'

            try:
                # Convert date str to dd/mm/yyy format
                datetime_str = box.select_one('[data-hook="review-date"]').text.strip().split(' on ')[-1]
                date = datetime.strptime(datetime_str, '%B %d, %Y').strftime("%d/%m/%Y")
            except Exception as e:
                date = 'N/A'

            try:
                description = box.select_one('[data-hook="review-body"]').text.strip()
                lan = self.trans.detect(description[:5]).lang
                if lan != 'en':
                    description = self.trans.translate(description,src=lan,dest='en').text
            except Exception as e:
                description = 'N/A'

            # create Dictionary with al review data 
            data_dict = {
                'Name' : name,
                'Stars' : stars,
                'Title' : title,
                'Date' : date,
                'Description' : description
            }

            # Add Dictionary in master empty List
            data_dicts.append(data_dict)
        
        return data_dicts
    
    def price_cal(self,url):
        try:
            self.driver.get("https://pricehistoryapp.com/")
            element = self.driver.find_element(By.CSS_SELECTOR, "input.w-full")
            element.send_keys(url)
            element.send_keys(Keys.ENTER)
            sleep(10)
            html = BeautifulSoup(self.driver.page_source,'lxml')
            text = html.find('div',class_="content-width mx-auto px-3").text
            for i in range(len(text)):
                if text[i:i+5] == '. Thi':
                    text = text[i+1:]
                    break
            
            price_pattern = re.compile(r'(\d+(\.\d+)?)')
            prices = [match[0] for match in price_pattern.findall(text)]
            self.prices = {'Current':float(prices[0]),'Lowest':float(prices[1]),'Average':float(prices[2]),'Highest':float(prices[3])}
            self.fairness = self.fairness_score(self.prices['Lowest'],self.prices['Highest'],self.prices['Average'],self.prices['Current'])
            return True
        except:
            return False
    
    def fairness_score(self,Pmin, Pmax, Pavg, Pcur):
        if Pmax == Pmin:
            return 50 if Pcur == Pavg else (100 if Pcur == Pmin else 0)
        else:
            return (abs(Pcur-Pavg)/(Pmax - Pmin))*100

    def start(self,p_url):
        reviews = []
        url = self.link(p_url)
        self.driver.get(url+'1')
        self.bypass()
        html = BeautifulSoup(self.driver.page_source,'lxml')
        self.product_name = html.find('a',class_='a-link-normal')
        i = 1
        while True:
            review = self.extract(url+str(i))
            if review == []:
                break 
            # add review data in reviews empty list
            reviews += review
            i += 1
        try:
            df_reviews = pd.DataFrame(reviews)
            df_reviews["Review"] = df_reviews["Title"]+ df_reviews["Description"]
            df_reviews = df_reviews["Review"]
            return pd.DataFrame(df_reviews)
        except :
            return pd.DataFrame()
#         df_reviews.to_csv('scrapedReviews.csv', index=False)
    def finish(self):
        self.driver.quit()
        
        

class Flipkart_Review_Extract:
    def __init__(self):
        chrome_options = Options()
#         Uncommenting below 2 lines can disable the browser pop up
#         chrome_options.add_argument('--headless')
#         chrome_options.add_argument('--disable-gpu')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.data = []
        self.trans = Translator()
        
    def review_link_extract(self,link):
        self.driver.get(link)
        try:
            a = self.driver.find_element(By.XPATH,"//div[@class='col JOpGWq']//a")
            self.driver.get(a.get_attribute('href'))
        except :
            print('MEE')
        sleep(1)
        try:
            a = self.driver.find_element(By.XPATH,"//div[@class='col-9-12']//a")
            self.driver.get(a.get_attribute('href'))
        except :
            print('YOUUU')
        sleep(1)
        a = self.driver.find_element(By.XPATH,"//nav[@class='yFHi8N']//a")
        page_count = self.driver.find_element(By.XPATH,"//div[@class='_2MImiq _1Qnn1K']//span").text
        return a.get_attribute('href')[:-1],int(page_count.split()[-1])
    
    def extract(self,link):
        self.driver.get(link)
        reviews = self.driver.find_elements(By.XPATH,"//div[@class='_1YokD2 _3Mn1Gg col-9-12']//div[@class='_1AtVbE col-12-12']")
        review_list = []
        reviews.pop()
        reviews.pop(0)
        for i in reviews:

            try:
                rm_btn = i.find_element(By.XPATH,"//span[@class='_1BWGvX']//span")
                while True :
                    try:
                        rm_btn.click()
                    except :
                        break
            except:
                pass
            try:
                review_list.append(i.find_element(By.CLASS_NAME,"t-ZTKy").text)
            except :
                review_list.append('')
        return review_list
        
    def start(self,link):
        link,page_count = self.review_link_extract(link)
        l = []
        for i in range(1,page_count+1):
            l.extend(self.extract(link+str(i)))
        return pd.DataFrame(l)
    
    def price_cal(self,url):
        try:
            self.driver.get("https://pricehistoryapp.com/")
            element = self.driver.find_element(By.CSS_SELECTOR, "input.w-full")
            element.send_keys(url)
            element.send_keys(Keys.ENTER)
            sleep(10)
            html = BeautifulSoup(self.driver.page_source,'lxml')
            text = html.find('div',class_="content-width mx-auto px-3").text
            for i in range(len(text)):
                if text[i:i+5] == '. Thi':
                    text = text[i+1:]
                    break
            
            price_pattern = re.compile(r'(\d+(\.\d+)?)')
            prices = [match[0] for match in price_pattern.findall(text)]
            self.prices = {'Current':float(prices[0]),'Lowest':float(prices[1]),'Average':float(prices[2]),'Highest':float(prices[3])}
            self.fairness = self.fairness_score(self.prices['Lowest'],self.prices['Highest'],self.prices['Average'],self.prices['Current'])
            return True
        except:
            return False
    
    def fairness_score(self,Pmin, Pmax, Pavg, Pcur):
        if Pmax == Pmin:
            return 50 if Pcur == Pavg else (100 if Pcur == Pmin else 0)
        else:
            return (abs(Pcur-Pavg)/(Pmax - Pmin))*100
        
    def finish(self):
        self.driver.quit()

# 
# 
# obj.bypass()
# print(obj.start(input()))

# obj = Flipkart_Review_Extract()
# obj.start("https://www.flipkart.com/sony-alpha-full-frame-ilce-7m2k-bq-in5-mirrorless-camera-body-28-70-mm-lens/p/itm92df94dc68fff?pid=DLLF6QZPNKTQMS8J&fm=organic&ppt=dynamic&ppn=dynamic&ssid=fnewy5pmbk0000001706938474552")
# 
# 