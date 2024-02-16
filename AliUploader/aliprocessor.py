
#공통 모듈
import sys
sys.path.append('Module')
sys.path.insert(1, '/Module')
import scrapedb
import processordb
import defaultvar
#기본 모듈
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import math
import json
import urllib.request
import urllib.parse
import time
import random
import string
import warnings
from multiprocessing import Pool
import traceback
#특수 모듈
import bcrypt
import pybase64


warnings.filterwarnings("ignore")

#번역 API
accinfo = json.load(open("accinfo.json"))
PAPAGO_CLIENTID = accinfo["papagoauth"]["PAPAGO_CLIENTID"]
PAPAGO_CLIENTSECRET = accinfo["papagoauth"]["PAPAGO_CLIENTSECRET"]
fontpath = "Module\\fonts\\TheJamsil4Medium.ttf"


def find_image_url(products_data, sku):
    try:
        for product in products_data['sku_price']:
            if product['skuid'] == sku:
                props_id_ls = product['props_ids'].split(';')
                for props_ids in props_id_ls:
                    prop_ids = props_ids.split(':')
                    pid = prop_ids[0]
                    vid = prop_ids[1]
                    for sku_prop in products_data['sku_props']:
                        if sku_prop['pid'] == pid:
                            for value in sku_prop['values']:
                                if value['vid'] == vid:
                                    if value['imageUrl'] == '':
                                        continue
                                    return value['imageUrl']
        return ''  # Return None if no match is found
    except:
        #상품 옵션이 존재하지 않는 경우
        return ''


# English text confirmation module
def is_english(text):
    english_ranges = [
        (0x0041, 0x005A),   # Basic Latin Uppercase
        (0x0061, 0x007A),   # Basic Latin Lowercase
        (0x0080, 0x00FF),   # Latin-1 Supplement
        # Add more ranges if needed for extended Latin characters, numbers, etc.
    ]

    for char in text:
        char_code = ord(char)
        for start, end in english_ranges:
            if start <= char_code <= end:
                return True
    return False


#파파고 번역 모듈
def translate_chinese(text):
    if not is_english(text):
        return text
    
    translate_request = requests.post("https://naveropenapi.apigw.ntruss.com/nmt/v1/translation",
              headers={
                  "X-NCP-APIGW-API-KEY-ID": PAPAGO_CLIENTID,
                  "X-NCP-APIGW-API-KEY" : PAPAGO_CLIENTSECRET,
                  "Content-Type": "application/json"
                  },
              json={
                  "source" : "en",
                  "target" : "ko",
                  "text": text
                })
    translated_text = translate_request.json()["message"]["result"]["translatedText"]
    
    return translated_text.replace('"','')



#네이버 인증 코드 발급 모듈
def get_bearer_token(client_id, clientSecret, type_="SELF"):
    # 3초전 timestamp
    timestamp = str(int((time.time()-100) * 1000))
    # 밑줄로 연결하여 password 생성
    password = client_id + "_" + timestamp
    # bcrypt 해싱
    hashed = bcrypt.hashpw(password.encode('utf-8'), clientSecret.encode('utf-8'))
    # base64 인코딩
    client_secret_sign = pybase64.standard_b64encode(hashed).decode('utf-8')
    headers = {"content-type": "application/x-www-form-urlencoded" }

    data_ = {
        "client_id": client_id,
        "timestamp": timestamp,
        "client_secret_sign": client_secret_sign,
        "grant_type": "client_credentials",
        "type": type_
    }
    query = urllib.parse.urlencode(data_)
    oauth_url = 'https://api.commerce.naver.com/external/v1/oauth2/token?' + query

    response = requests.post(url=oauth_url, headers=headers)
    response_data = response.json()

    if 'access_token' in response_data:
        return response_data['access_token']
        
    else:
        print(response_data)
        print("토큰 요청 실패, 재시도")
        time.sleep(1)
        return get_bearer_token(client_id, clientSecret, type_)

###이미지 번역 처리 모듈 모음
#HTML 상의 모든 이미지를 추출하는 함수
def html_image_extractor(html):
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = []
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src:
            if "http" not in src[:6]:
                src = "https:" + src
            image_urls.append(src)
    return image_urls

#JSON 번역 처리 모듈
def json_extractor(json_string):
    json_data = json.loads(json_string)
    result = []

    def extract(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                extract(key)
                extract(value)
        elif isinstance(obj, list):
            for item in obj:
                extract(item)
        elif isinstance(obj, str):
            if is_english(obj):
                result.append(obj)

    extract(json_data)
    return result


def is_url(url):
    if "http" in url[:6]:
        return True
    else:
        return False

def is_numeric(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def json_extractor(json_string):
    json_data = json.loads(json_string)
    result = []

    def extract(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                extract(value)
        elif isinstance(obj, list):
            for item in obj:
                extract(item)
        elif isinstance(obj, str):
            # Check if the string is in English, not a URL, and not numeric
            if is_english(obj) and not is_url(obj) and not is_numeric(obj):
                result.append(obj)

    extract(json_data)
    return result

def json_restore(json_string, translated_texts):
    before_translation = json_extractor(json_string)
    manipulated_json = json_string
    for original,transed in zip(before_translation, translated_texts):
        manipulated_json = manipulated_json.replace(original.strip(), transed.strip())
        
    translated_json = json.loads(manipulated_json)
    return translated_json

def processali(scrapeditem):
    try:
        ###상세페이지 이미지 추출 및 번역
        description_imageurls = [] #번역된 이미지 URL
        i = 0
        for imageurl in html_image_extractor(scrapeditem.TaobaoDescription):
            description_imageurls.append(imageurl)

        

        ###옵션값의 번역
        #옵션값의 이미지 추출
        option_image_list = []
        for item in scrapeditem.TaobaoOptions["sku_props"]:
            for value in item["values"]:
                if "imageUrl" in value:
                    if value["imageUrl"] != "" and value["imageUrl"] != None:
                        option_image_list.append(value["imageUrl"])
        #옵션 이미지 텍스트 추출
        option_image_urls = []
        if len(option_image_list) > 0:
            for imageurl in option_image_list:
                if "http" not in imageurl[:6]:
                    imageurl = "https:" + imageurl
                option_image_urls.append(imageurl)

        #옵션 전처리
        processed_options = scrapeditem.TaobaoOptions

        for item in processed_options["sku_props"]:
            for value in item["values"]:
                if "imageUrl" in value:
                    if value["imageUrl"] != "":
                        if value["imageUrl"] != "" and value["imageUrl"] != None:
                            new_img_url = option_image_urls.pop(0)
                            value["imageUrl"] = new_img_url

        #옵션값 번역      
        option_text_ls = json_extractor(json.dumps(processed_options))
        translated_option = [translate_chinese(text) for text in option_text_ls]
        processed_options = json_restore(json.dumps(processed_options, ensure_ascii=False), translated_option)



        for option in processed_options["sku_price"]:
            #판매가 설정해주는 작업
            option["sale_price"] = defaultvar.alipricecalculation_withmargin(float(option["sale_price"]), accinfo["margin"])
            
            #가격 상향 작업
            if option["sale_price"] < 900:
                option["sale_price"] = 900
            elif option["sale_price"] < 3900:
                option["sale_price"] = 3900
            elif option["sale_price"] < 6900:
                option["sale_price"] = 6900
            elif option["sale_price"] < 9900:
                option["sale_price"] = 9900
                
            #옵션 이미지 설정해주는 작업
            option["imageUrl"] = find_image_url(processed_options, option["skuid"])

        option_char = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
            '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38',
            '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50'],
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
            'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'BB', 'CC', 'DD', 'EE', 'FF', 'GG', 'HH', 'II', 'JJ', 'KK', 'LL',
            'MM', 'NN', 'OO', 'PP', 'QQ', 'RR', 'SS', 'TT', 'UU', 'VV', 'WW', 'XX', 'YY', 'ZZ'],
            ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ', 'ㄲ', 'ㄸ', 'ㅃ', 'ㅆ', 'ㅉ',
            'ㄱㄱ', 'ㄴㄴ', 'ㄷㄷ', 'ㄹㄹ', 'ㅁㅁ', 'ㅂㅂ', 'ㅅㅅ', 'ㅇㅇ', 'ㅈㅈ', 'ㅊㅊ', 'ㅋㅋ', 'ㅌㅌ', 'ㅍㅍ', 'ㅎㅎ', 'ㄲㄲ',
            'ㄸㄸ', 'ㅃㅃ', 'ㅆㅆ', 'ㅉㅉ']
        ]

        for props in processed_options["sku_props"]:
            selected_option_char = option_char.pop(0)
            for value in props["values"]:
                optionstr = selected_option_char.pop(0) + "." + value["name"]
                if len(optionstr) > 20:
                    optionstr = optionstr[:18] + ".."
                else:
                    optionstr = optionstr[:20]
                value["optioncode"] = optionstr


        #처리된 옵션값을 기반으로 가격 계산
        option_prices = [float(item["sale_price"]) for item in processed_options["sku_price"]]
        option_maxprice = max(option_prices)
        option_minprice = min(option_prices)
        origin_price = option_minprice
        sale_price = option_minprice
        if option_maxprice >= 1.5 * option_minprice:
            origin_price = 2 * (option_maxprice - option_minprice)


        pi = processordb.ProcessedItem()
        pi.ProductID = scrapeditem.ProductID
        pi.TaobaoID = scrapeditem.TaobaoID
        pi.ProductOriginPrice = origin_price
        pi.ProductPrice = sale_price
        pi.ProductDeliveryFee = 0
        pi.ProductCategory = scrapeditem.searchsimilarcategory(scrapeditem.ProductName)
        pi.ProductVideo = scrapeditem.TaobaoVideoUrl
        pi.ProductDescData = description_imageurls
        pi.ProductProperties = json.dumps(scrapeditem.TaobaoProperties)
        pi.ProductOptions = json.dumps(processed_options)
        pi.ProductTags = scrapeditem.ProductTags
        pi.Owner = defaultvar.store_owner

        pi.ProductName = scrapeditem.ProductName
        pi.ProductMainImage = scrapeditem.ProductSubImages.split(',')[0]
        pi.ProductSubImages = ','.join(scrapeditem.ProductSubImages.split(',')[1:])
        pi.Type = 2
        print(f"Completed Processing for {scrapeditem.ProductID}")
        return pi

    except:
        print(f"Failed Processing for {scrapeditem.ProductID}")
        traceback.print_exc()
        return None    
