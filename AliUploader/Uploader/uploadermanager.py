
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
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

userinfo = json.load(open("accinfo.json"))["userinfo"]

options = webdriver.ChromeOptions() 
options.add_argument('disable-notifications')

current_script_directory = os.path.dirname(os.path.abspath(__file__))
chromedriver_path = os.path.join(current_script_directory, "chromedriver.exe")

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

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
        driver.find_element(By.ID, "loginName").send_keys(userinfo["elevenauth"].split(":")[0])
        driver.find_element(By.ID, "passWord").send_keys(userinfo["elevenauth"].split(":")[1])
        driver.find_element(By.ID, "loginbutton").click()
    
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
    
    