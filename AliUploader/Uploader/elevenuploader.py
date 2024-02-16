import sys
sys.path.insert(0, 'Module')
import processordb
from datetime import datetime, timedelta
import urllib.parse
import json
from time import sleep
import math
from PIL import Image
import io
import requests
from bs4 import BeautifulSoup
import traceback
import string
import random

tbheaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

def generate_time_strings():
    # Get the current date
    current_date = datetime.now().strftime('%Y%m%d')

    # Calculate the date after 3years days
    future_date = (datetime.now() + timedelta(days=365*3)).strftime('%Y%m%d')

    return current_date, future_date

def search_value(ls, key_to_find):
        desired_value = None
        for key, value in ls:
            if key == key_to_find:
                desired_value = value
                return desired_value
        return desired_value  
        

def upload_img(imgurl, headers):
    filecontent = requests.get(imgurl, headers=headers).content
    image = Image.open(io.BytesIO(filecontent))
    #Image resize
    # resize the image
    image = image.convert("RGB")
    width, height = image.size
    if width < 600 or height < 600:
        ratio = max(700/width, 700/height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height))

    image_bytes_io = io.BytesIO()
    image.save(image_bytes_io, format='JPEG')
    image_bytes = image_bytes_io.getvalue()
    files=[
    ('file',(''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=15))+'.jpg',image_bytes,'image/jpeg'))
    ]
    
    
    url = "https://apis.11st.co.kr/product/hulk/v2/preprocess/po-image/B"
    response = requests.post(url, headers=headers, files=files)
    print(response.text)
    return response.json()["data"]

def product_upload(pi_item_dup, elevencookie):
    try:
        pi_item = pi_item_dup
        current_time, future_time = generate_time_strings()
        
        #모든 가격 데이터를 15% 증가시킴
        pi_item.ProductOriginPrice = math.ceil(pi_item.ProductOriginPrice * 1.05 / 100) * 100
        pi_item.ProductPrice = math.ceil(pi_item.ProductPrice * 1.05 / 100) * 100
        for option in pi_item.ProductOptions["sku_price"]:
            option["sale_price"] = math.ceil(option["sale_price"] * 1.05 / 100) * 100
        
        option_prices = [float(item["sale_price"]) for item in pi_item.ProductOptions["sku_price"]]
        option_minprice = min(option_prices)
        pi_item.ProductOriginPrice = option_minprice
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.7',
            'Connection': 'keep-alive',
            'Cookie': elevencookie,
            'Origin': 'https://soffice.11st.co.kr',
            'Referer': 'https://soffice.11st.co.kr/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Sec-GPC': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        #AccountDetail
        response = requests.get('https://apis.11st.co.kr/product/bruce/selleroffice/v1/seller', headers=headers)
        nicknameseq = response.json()["storeNicknames"][0]["nicknameSequence"]
        
        pid_ls = []
        for skuprops in pi_item.ProductOptions["sku_props"]:
            pid = skuprops["pid"]
            for value in skuprops["values"]:
                pid_ls.append((pid + ":" + value["vid"], value["optioncode"]))
                
        optionexist = True
        optionobj = None
        #가능 옵션이 여러개인 경우
        if len(pi_item.ProductOptions["sku_props"]) > 0:
            #옵션 종류 설정
            names = []
            for item in pi_item.ProductOptions["sku_props"]:
                propname = {}
                propname["name"] = item["prop_name"]
                values = []
                for value in item["values"]:
                    values.append(value["optioncode"])
                propname["values"] = values
                names.append(propname)
            
            #옵션 상세 정보 설정
            items = []
            
            for option in pi_item.ProductOptions["sku_price"]:
                item = {}
                item["price"] = option["sale_price"] - pi_item.ProductPrice
                item["quantity"] = option["stock"]
                item["sellerStockCode"] = str(option["skuid"])
                item["values"] = []
                props_ids = option["props_ids"].split(';')
                for props_id in props_ids:
                    optionname = str(search_value(pid_ls, props_id))
                    item["values"].append(optionname)
                item["weight"] = 0
                item["optionProductImage"] = None
                item["stockStatusCode"] = "01"
                item["catalogMatching"] = None
                item["attributeJson"] = None
                items.append(item)
            
            optionobj = {
                "addWeight": 0,
                "calculated": None,
                "combination": {
                    "names": names,
                    "items": items
                },
                "custom": None,
                "optionPrice": 0,
                "quantity": 999,
                "sortCode": "00"
            }
        #옵션이 없는 경우
        else:
            optionexist = False
        
        #Auth
        authcode = requests.get('https://apis.11st.co.kr/product/bruce/seller/auth', headers=headers).json()[0]["authObjectNo"]
        prdInfoTmpltNo = requests.get(
                    'https://apis.11st.co.kr/product/bruce/selleroffice/v1/delivery/send-close',
                    headers=headers,
                ).json()[0]["prdInfoTmpltNo"]
        defaultaddress = requests.get(
                    'https://apis.11st.co.kr/product/bruce/selleroffice/v1/delivery/default-address',
                    headers=headers,
                ).json()
        print(prdInfoTmpltNo)
        print(nicknameseq)
        elevenjson = {
            "productStatusCode": "01",
            "displayCategoryNo": 939966,
            "productName": pi_item.ProductName[:50],
            "productEnglishName": "",
            "advertisementPhrase": "",
            "abroad": {
                "purchasingAgentServiceCode": "02",
                "hsCode": "55",
                "importFeeCode": "03",
                "placeCode": "D",
                "abroadInCode": None,
                "sizeTableDisplayYn": ""
            },
            "brand": None,
            "sellPrice": pi_item.ProductPrice,
            "option": optionobj,
            "parent": optionexist,
            "pkgCtlgNo": 0,
            "stockQuantity": 999,
            "standardProductYn": "Y",
            "sellerManagementCode": str(pi_item.TaobaoID),
            "selling": {
                "methodCode": "01",
                "startDate": current_time,
                "endDate": future_time,
                "periodCode": "110"
            },
            "origin": {
                "code": "02",
                "detailCode": "1287",
                "name": "",
                "differentYn": "N"
            },
            "rawMaterial": None,
            "bookAndAlbum": None,
            "medical": None,
            "beefTraceTypeCode": "01",
            "beefTraceContent": "",
            "image": {
                "primaryImage": "/imagetemp_nfs"+ upload_img(pi_item.ProductMainImage, headers = headers),
                "additionalImages": [],
                "cardViewImage": ""
            },
            "luxuryComponent": None,
            "detailContent": {
                "afterService": "카카오톡 굿초이스그룹으로 문의주세요",
                "returnOrExchange": "카카오톡 굿초이스그룹으로 문의주세요",
                "detail": pi_item.ProductHtmlDescription,
                "detailTypeCode": "13"
            },
            "notification": {
                "type": 891045,
                "items": [
                    {
                        "code": "11800",
                        "name": "상품상세설명 참조"
                    },
                    {
                        "code": "23760413",
                        "name": "상품상세설명 참조"
                    },
                    {
                        "code": "11905",
                        "name": "상품상세설명 참조"
                    },
                    {
                        "code": "23756033",
                        "name": "상품상세설명 참조"
                    },
                    {
                        "code": "23759100",
                        "name": "상품상세설명 참조"
                    }
                ]
            },
            "certification": {
                "groups": [
                    {
                        "code": "01",
                        "objectCode": "03",
                        "exclusionTypeCode": None,
                        "items": []
                    },
                    {
                        "code": "02",
                        "objectCode": "03",
                        "exclusionTypeCode": None,
                        "items": []
                    },
                    {
                        "code": "03",
                        "objectCode": "03",
                        "exclusionTypeCode": None,
                        "items": []
                    },
                    {
                        "code": "04",
                        "objectCode": "05",
                        "exclusionTypeCode": None,
                        "items": []
                    }
                ]
            },
            "taxCode": "01",
            "priceComparisonYn": "Y",
            "delivery": {
                "availableAreaCode": "01",
                "wayCode": "01",
                "companyCode": "00034", #CJ
                "sendCloseTemplateNo": prdInfoTmpltNo,
                "availableBundleYn": "Y",
                "payTypeCode": "",
                "returnChargeCode": defaultaddress["inAddressLocationCode"],
                "deliveryClassificationCode": "02",
                "visitYn": "N",
                "visitAddressSeq":defaultaddress["visitAddressSequence"],
                "returnAddressAbroadYn": "N",
                "sendAddressAbroadYn": "Y",
                "sendAddressSeq": defaultaddress["outAddressSequence"],
                "returnAddressSeq": defaultaddress["inAddressSequence"],
                "globalSendAddressSeq": defaultaddress["visitAddressSequence"],
                "globalReturnAddressSeq": 0,
                "integrationReturnAddressMemNo": None,
                "integrationSendAddressMemNo": authcode,
                "sellerAbroadReturnAddressCode": None,
                "sellerAbroadSendAddressCode": None,
                "todaySendCanQty": None,
                "global": None,
                "charge": {
                    "chargeTypeCode": "01",
                    "charge": None,
                    "additionalChargeTypeCode": None,
                    "jejuCharge": None,
                    "islandCharge": None,
                    "returnCharge": 10000,
                    "exchangeCharge": 20000,
                    "freeBasisAmount": None,
                    "range": []
                }
            },
            "todaySend": {
                "todaySendCanQty": None,
                "todaySendCanQtyOverOrderPeriod": 1
            },
            "movieObjNo": 0,
            "sellerDiscount": None,
            "purchaseLimit": {
                "minimumTypeCode": "00",
                "maximumTypeCode": "00",
                "maximumQuantity": None,
                "minorPurchaseYn": "Y",
                "purchaseUnit": None,
                "shoppingCartRestrictionYn": "N"
            },
            "multiPurchaseDiscount": None,
            "point": None,
            "hopeSupport": None,
            "gift": None,
            "giftWrappingCode": "01",
            "catalogAttribute": None,
            "sellerNickNameSeq": nicknameseq,
            "groupBidAmount": 200
        }

        response = requests.post("https://apis.11st.co.kr/product/hulk/v2/product/save?createCd=1201",
                    headers=headers, json=elevenjson).json()
        print(response)
        if response["status"] == 400:
            return 1
        return response["data"]
    except:
        print(traceback.print_exc())
        return 1


        
        
    