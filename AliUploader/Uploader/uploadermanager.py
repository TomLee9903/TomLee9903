
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import sys
sys.path.insert(0, 'Module')
import processordb
import naveruploader
import esmuploader
import interparkuploader
import elevenuploader
import coupanguploader
import coupanghtmlgen
import htmlgen
import os
import json
import copy
import subprocess
import time
import pyautogui

userinfo = json.load(open("accinfo.json"))["userinfo"]

# 디버거 크롬 구동
try:
    subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9225 --user-data-dir="C:\chrometemp"') # 디버거 크롬 구동
except:
    subprocess.Popen(r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe --remote-debugging-port=9225 --user-data-dir="C:\chrometemp"') # 디버거 크롬 구동
options = webdriver.ChromeOptions()
user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.83 Safari/537.36"
options.add_argument('user-agent=' + user_agent)
options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")

# 크롬 버전을 확인하여 버전이 안맞으면 자동으로 업데이트 하여 설치해주는 옵션       
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.implicitly_wait(10)
print("Please select google Chrome user and press enter")
input()

# 속도 향상을 위한 옵션 해제
options.add_argument('disable-notifications')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
options.add_experimental_option("useAutomationExtension", False) 
options.add_argument("disable-gpu") 
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
prefs = {'profile.default_content_setting_values': {'cookies' : 2, 'images': 2, 'plugins' : 2, 'popups': 2, 'geolocation': 2, 'notifications' : 2, 'auto_select_certificate': 2, 'fullscreen' : 2, 'mouselock' : 2, 'mixed_script': 2, 'media_stream' : 2, 'media_stream_mic' : 2, 'media_stream_camera': 2, 'protocol_handlers' : 2, 'ppapi_broker' : 2, 'automatic_downloads': 2, 'midi_sysex' : 2, 'push_messaging' : 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop' : 2, 'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement' : 2, 'durable_storage' : 2}}   
#self.options.add_experimental_option('prefs', prefs)
# 크롬 브라우저와 셀레니움을 사용하면서 발생되는 '시스템에 부착된 장치가 작동하지 않습니다.' 라는 크롬 브라우저의 버그를 조치하기 위한 코드. 
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# 윈도우 사이즈 맥스로 키우기
driver.maximize_window()
driver.get("https://best.aliexpress.com/")
time.sleep(1)
pyautogui.press('f12')
time.sleep(2)
pyautogui.press('f12')

def get_cookies_string(driver):
    cookiels = []
    for cookie in driver.get_cookies():
        if cookie["name"] == "wing-locale" or cookie["name"] == "locale":
            cookie["value"] = "ko"
        cookiels.append(cookie["name"] + "=" + cookie["value"])
    return "; ".join(cookiels)

#11번가 로그인
def eleven_login():
    driver.get("https://login.11st.co.kr/auth/front/selleroffice/login.tmall")
    sleep(1)
    if "view" in driver.current_url:
        pass
    else:
        id = userinfo["elevenauth"].split(":")[0]
        pw = userinfo["elevenauth"].split(":")[1]

        driver.find_element(By.CSS_SELECTOR, "#loginName").clear()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#loginName").clear()
        time.sleep(1)

        driver.find_element(By.CSS_SELECTOR, "#loginName").send_keys(id)
        time.sleep(1)
        print(userinfo["elevenauth"].split(":")[0])
        driver.find_element(By.CSS_SELECTOR, "#passWord").clear()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#passWord").send_keys(pw)
        time.sleep(1)
        print(userinfo["elevenauth"].split(":")[1])
        driver.find_element(By.CSS_SELECTOR, "#loginbutton").send_keys(Keys.ENTER)
        time.sleep(5)
        print('Success to log-in at 11st seller office!')
        
    return get_cookies_string(driver)

#Smartstore 로그인
def smartstore_login():
    driver.get('https://sell.smartstore.naver.com/#/home/dashboard')
    sleep(2)
    if "dashboard" in driver.current_url:
        pass
    else:
        driver.get("https://accounts.commerce.naver.com/login?url=https%3A%2F%2Fsell.smartstore.naver.com%2F%23%2Flogin-callback")
        sleep(2)
        driver.find_element(By.XPATH, "//input[@type='text']").clear()
        driver.find_element(By.XPATH, "//input[@type='password']").clear()
        driver.find_element(By.XPATH, "//input[@type='text']").send_keys(userinfo["smartstoreauth"].split(":")[0])
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(userinfo["smartstoreauth"].split(":")[1])
        driver.find_element(By.XPATH, "//button[@type='button' and contains(@class, 'Button_btn')]").click()
        sleep(3)
        if "dashboard" not in driver.current_url:
            print("수동 로그인을 진행해주세요. 완료 후 Enter 를 눌러주세요")
            input()
    navercookie = get_cookies_string(driver)
    return navercookie
def esm_login():
    driver.get("https://www.esmplus.com/")
    sleep(2)
    if "signin" not in driver.current_url:
        pass
    else:
        #driver.find_element(By.ID, "checkbox-true-default").click()
        driver.find_element(By.ID, "typeMemberInputId01").clear()
        driver.find_element(By.ID, "typeMemberInputPassword01").clear()
        if driver.find_element(By.ID, "typeMemberInputId01").get_attribute("value") == "":
            driver.find_element(By.ID, "typeMemberInputId01").send_keys(userinfo["gmarketauth"].split(":")[0])
        if driver.find_element(By.ID, "typeMemberInputPassword01").get_attribute("value") == "":
            driver.find_element(By.ID, "typeMemberInputPassword01").send_keys(userinfo["gmarketauth"].split(":")[1])
        driver.find_element(By.CLASS_NAME, "box__submit").find_element(By.TAG_NAME, "button").click()

        sleep(3)
        if "home" not in driver.current_url.lower():
            print("수동 로그인을 진행해주세요. 완료 후 Enter 를 눌러주세요")
            input()
    esmcookie = get_cookies_string(driver)
    return esmcookie

def interpark_login():
    driver.get("https://seller.interpark.com/main")
    sleep(1)
    if "login" in driver.current_url:
        driver.find_element(By.ID, "memId").clear()
        driver.find_element(By.ID, "memPwd").clear()
        if driver.find_element(By.ID, "memId").get_attribute("value") == "": 
            driver.find_element(By.ID, "memId").send_keys(userinfo["interparkauth"].split(":")[0])
        if driver.find_element(By.ID, "memPwd").get_attribute("value") == "":
            driver.find_element(By.ID, "memPwd").send_keys(userinfo["interparkauth"].split(":")[1])
        
        driver.find_element(By.CLASS_NAME, "saveID").find_element(By.TAG_NAME, "label").click()
        #driver.find_element(By.ID, "frmMemberLogin").find_element(By.TAG_NAME, "button").send_keys(Keys.ENTER)
        driver.execute_script("fncLoginCheck.valid('00');")
        sleep(2)
    interparkcookie = get_cookies_string(driver)
    return interparkcookie

def coupanglogin():
    driver.get("https://wing.coupang.com/")
    if "xauth" in driver.current_url:
        driver.find_element(By.ID, "username").send_keys(userinfo["coupangauth"].split(":")[0])
        driver.find_element(By.ID, "password").send_keys(userinfo["coupangauth"].split(":")[1])
        driver.find_element(By.ID, "kc-login").click()
        sleep(2)
        
        if "xauth" in driver.current_url:
            print("수동 로그인을 진행해주세요. 완료 후 Enter 를 눌러주세요")
            input()

    coupangcookie = get_cookies_string(driver)
    return coupangcookie


def delete_popups():
    curr=driver.current_window_handle
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if handle != curr:
            driver.close()
    driver.switch_to.window(curr)

def changetoint(s):
    try:
        return int(s)
    except ValueError:
        return 1


def uploaditem(pi_items_dup):
    pi_items = []
    for pi_item in pi_items_dup:
        try:
            if pi_item.ProductVideo == "":
                pi_item.ProductVideo = None
            pi_item.ProductHtmlDescription = htmlgen.htmlgenerator(pi_item.ProductOptions, pi_item.ProductDescData, pi_item.ProductVideo)
            pi_items.append(pi_item)
        except:
            pass
    
    if userinfo["smartstoreauth"] != "":
        smartstorecookie = smartstore_login()
        for pi_item in copy.deepcopy(pi_items):
            navercode = naveruploader.product_upload(pi_item,smartstorecookie)
            print("Naver Uploaded: ",navercode)
    

    if userinfo["coupangauth"] != "":
        coupangcookie = coupanglogin()
        for pi_item in copy.deepcopy(pi_items):
            coupangcode = coupanguploader.product_upload(pi_item, coupangcookie)
            print("Coupang Uploaded: ",coupangcode)
            
    if userinfo["gmarketauth"] != "":
        esmcookie = esm_login()
        for pi_item in copy.deepcopy(pi_items):
            auctioncode, gmarketcode = esmuploader.product_upload(pi_item,esmcookie)
            print("Auction Uploaded: ",auctioncode)
            print("Gmarket Uploaded: ",gmarketcode)
    
    
    if userinfo["interparkauth"] != "":
        interparkcookie = interpark_login()
        for pi_item in copy.deepcopy(pi_items):
            interparkcode = interparkuploader.product_upload(pi_item,interparkcookie)
            print("Interpark Uploaded: ",interparkcode)
        
    if userinfo["elevenauth"] != "":
        elevencookie = eleven_login()
        for pi_item in copy.deepcopy(pi_items):
            elevencode = elevenuploader.product_upload(pi_item,elevencookie)
            print("11번가 Uploaded: ",elevencode)
    
def GetDriver():
    return driver