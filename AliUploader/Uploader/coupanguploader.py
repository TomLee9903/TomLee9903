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
import coupanghtmlgen
import traceback
import time

globalcookie = ""

def search_value(ls, key_to_find):
        desired_value = None
        for key, value in ls:
            if key == key_to_find:
                desired_value = value
                return desired_value
        return desired_value  
        
def imageupload(url):
    img_headers = {
        'authority': 'wing.coupang.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie': globalcookie,
        'origin': 'https://wing.coupang.com',
        'referer': 'https://wing.coupang.com/tenants/seller-web/vendor-inventory/formV2',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {
        'imageType': 'REPRESENTATION',
        'externalUrl': url,
        'vendorInventoryId': '',
    }
    response = requests.post(
        'https://wing.coupang.com/tenants/seller-web/file/image/upload/from-external-url-v2',
        headers=img_headers,
        data=data,
    )
    return response.json()["message"]

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


def product_upload(pi_item_dup, coupangcookie):
    global globalcookie
    try:
        globalcookie = coupangcookie
        pi_item = pi_item_dup
        
        coupanghtml = coupanghtmlgen.htmlgenerator(pi_item.ProductOptions, pi_item.ProductDescData, pi_item.ProductVideo)
        
        #이미지 서버에 업로드
        for prop in pi_item.ProductOptions["sku_props"]:
            for value in prop["values"]:
                if value["imageUrl"] != "":
                    value["imageUrl"] = coupanghtmlgen.uploadimgurl(value["imageUrl"])
        for option in pi_item.ProductOptions["sku_price"]:
            option["imageUrl"] = find_image_url(pi_item.ProductOptions, option["skuid"])
        
        headers = {
            'authority': 'wing.coupang.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.8',
            'content-type': 'application/json',
            'cookie': coupangcookie,
            'origin': 'https://wing.coupang.com',
            'referer': 'https://wing.coupang.com/tenants/seller-web/vendor-inventory/formV2',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        #모든 가격 데이터를 15% 증가시킴
        pi_item.ProductOriginPrice = math.ceil(pi_item.ProductOriginPrice * 1.05 / 100) * 100
        pi_item.ProductPrice = math.ceil(pi_item.ProductPrice * 1.05 / 100) * 100
        for option in pi_item.ProductOptions["sku_price"]:
            option["sale_price"] = math.ceil(option["sale_price"] * 1.05 / 100) * 100
        
        option_prices = [float(item["sale_price"]) for item in pi_item.ProductOptions["sku_price"]]
        option_minprice = min(option_prices)
        pi_item.ProductOriginPrice = option_minprice
        
        #태그를 넣어줌
        sellerTags = []
        for ProductTag in pi_item.ProductTags.split(','):
            if ProductTag.strip() != '':
                sellerTags.append(ProductTag)

        pid_ls = []
        if len(pi_item.ProductOptions["sku_props"]) > 2:
            return 1
        
        for skuprops in pi_item.ProductOptions["sku_props"]:
            pid = skuprops["pid"]
            for value in skuprops["values"]:
                pid_ls.append((pid + ":" + value["vid"], value["optioncode"]))
        
        
        item_ls = []
        for option in pi_item.ProductOptions["sku_price"]:
            props_ids = option["props_ids"].split(';')
            attrib_ls = []
            option_title = ""
            for i, props_id in enumerate(props_ids):
                optionname = str(search_value(pid_ls, props_id))
                option_title += optionname + " "
                
                
                attrib = {
                    'editable': False,
                    'attributeTypeId': 2439,
                    'attributeTypeName': '색상',
                    'attributeValueName': optionname,
                    'exposed': 'EXPOSED',
                }
                
                if i == 0:
                    attrib["attributeTypeId"] = 2439
                    attrib["attributeTypeName"] = "색상"
                elif i == 1:
                    attrib["attributeTypeId"] = None
                    if pi_item.ProductOptions["sku_props"][i]["prop_name"] == "색상":
                        pi_item.ProductOptions["sku_props"][i]["prop_name"] = "색상2"
                    attrib["attributeTypeName"] = pi_item.ProductOptions["sku_props"][i]["prop_name"]
                else:
                    continue
                
                attrib_ls.append(attrib)
                
                if i == 0:
                    attrib_ls.append({
                        "editable": False,
                        "attributeTypeId": 7652,
                        "attributeTypeName": "수량",
                        "attributeValueName": "1개",
                        "exposed": "EXPOSED"
                    })

            option_title = option_title.strip()
            images = []
            if option["imageUrl"] != "":
                coupang_image_url = imageupload(option["imageUrl"])
                images.append({
                            'imageOrder': 0,
                            'imageType': 'REPRESENTATION',
                            'cdnPath': coupang_image_url,
                            'vendorPath': coupang_image_url,
                        })
            item = {
                    'id': 'e9c1cfb7-7e73-4ad5-a656-64eeeab70c4b',
                    'salePrice': option["sale_price"],
                    'originalPrice': 0,
                    'maximumBuyCount': 999,
                    'isModelNoEmpty': False,
                    'images': images,
                    'offerDescription': '',
                    'contents': [
                        {
                            'contentsType': 'HTML',
                            'contentDetails': [
                                {
                                    'content': coupanghtml,
                                    'detailType': 'TEXT',
                                },
                            ],
                        },
                    ],
                    'registrationType': 'NORMAL',
                    'skuInfo': {
                        'fragile': False,
                    },
                    'skuChecked': False,
                    'externalVendorSku' : pi_item.TaobaoID,
                    'globalInfo': {
                        'material': {},
                        'importHsCode': None,
                    },
                    'autoPricingInfo': None,
                    'itemName': option_title,
                    'attributes': attrib_ls,
                    'saleAgentCommission': 10.8,
                    'notices': [
                        {
                            'noticeCategoryName': '기타 재화',
                            'noticeCategoryDetailName': '품명 및 모델명',
                            'content': '상품 상세페이지 참조',
                        },
                        {
                            'noticeCategoryName': '기타 재화',
                            'noticeCategoryDetailName': '인증/허가 사항',
                            'content': '상품 상세페이지 참조',
                        },
                        {
                            'noticeCategoryName': '기타 재화',
                            'noticeCategoryDetailName': '제조국(원산지)',
                            'content': '상품 상세페이지 참조',
                        },
                        {
                            'noticeCategoryName': '기타 재화',
                            'noticeCategoryDetailName': '제조자(수입자)',
                            'content': '상품 상세페이지 참조',
                        },
                        {
                            'noticeCategoryName': '기타 재화',
                            'noticeCategoryDetailName': '소비자상담 관련 전화번호',
                            'content': '상품 상세페이지 참조',
                        },
                    ],
                    'maximumBuyForPerson': 0,
                    'maximumBuyForPersonPeriod': 1,
                    'certifications': [
                        {
                            'certificationType': 'NOT_REQUIRED',
                            'certificationCode': '',
                        },
                    ],
                    'taxType': 'TAX',
                    'adultOnly': 'EVERYONE',
                    'parallelImported': 'NOT_PARALLEL_IMPORTED',
                    'pccNeeded': True,
                    'outboundShippingTimeDay': 7,
                    'searchTags': sellerTags,
                    'overseasPurchased': 'OVERSEAS_PURCHASED',
                    'unitCount': 1,
                    'modelNo': option["skuid"]
                }
            item_ls.append(item)
        
        returnjson = requests.get(
                        'https://wing.coupang.com/tenants/seller-web/vendor/my/return-address',
                        headers=headers,
                    ).json()["content"][0]
        outboundjsons = requests.get(
                        'https://wing.coupang.com/tenants/seller-web/vendor/my/outbound-address',
                        headers=headers,
                    ).json()["content"]
        
        outboundjson = None
        for outboundjson_ in outboundjsons:
            if outboundjson_["addressType"] == "OVERSEA":
                outboundjson = outboundjson_
                break
                
        #
        json_data = {
            'locale': 'ko_KR',
            'sellerProductId': None,
            'displayCategoryCode': 64681,
            'categoryId': 1937,
            'saleAgentCommissionType': 'FIXED_RATE',
            'brand': None,
            'bundleInfo': {
                'bundleType': 'SINGLE',
                'discountDisabled': 'false',
            },
            'manufacture': None,
            'giveawayType': None,
            'productId': None,
            'productOrigin': None,
            'copiedFrom': None,
            'contributorType': 'COUPANG',
            'sellerProductName': pi_item.ProductName,
            'displayProductName': pi_item.ProductName,
            'generalProductName': pi_item.ProductName,
            'saleStartedAt': '2023-12-17T11:11:46',
            'saleEndedAt': '2099-12-31T00:00:00',
            'items': item_ls,
            'requiredDocuments': [],
            'deliveryMethod': 'AGENT_BUY',
            'deliveryCompanyCode': 'CJGLS',
            'deliveryChargeType': 'FREE',
            'deliveryCharge': 0,
            'freeShipOverAmount': 0,
            'remoteAreaDeliverable': 'Y',
            'unionDeliveryType': 'NOT_UNION_DELIVERY',
            'outboundShippingPlaceCode': outboundjson["outboundShippingPlaceId"],
            'extraInfoMessage': '',
            'returnCenterCode': str(returnjson["centerCode"]),
            'returnChargeName': str(returnjson["centerName"]),
            'companyContactNumber': str(returnjson["mallUserTel1"]),
            'returnZipCode': str(returnjson["centerPost"]),
            'returnAddress': str(returnjson["centerAddr1"]),
            'returnAddressDetail': str(returnjson["centerAddr2"]),
            'returnCharge': 5000,
            'deliveryChargeOnReturn': 5000,
            'metaData': {
                'VERSION': '2',
                'IMAGE_UI_REGISTRATION_TYPE': 'ITEM',
                'CONTENT_UI_REGISTRATION_TYPE': 'HTML',
                'CONTENT_UI_REGISTRATION_LEVEL_TYPE': 'INVENTORY',
                'SALE_PERIOD_SELECTION_TYPE': 'NOT_SET',
                'MAXIMUM_PURCHASE_SELECTION_TYPE': 'NOT_SET',
                'USED_PRODUCT_SELECTION_TYPE': 'NONE',
                'SKU_INFO_UI_REGISTRATION_TYPE': 'PRODUCT',
                'OUTBOUND_SHIPPING_TIME_SELECTION_TYPE': 'NOT_SET',
                'CATEGORY_USE_TYPE': 'RECENT',
                'IS_SINGLE_OPTION_PRODUCT': 'FALSE',
                'UP_BUNDLING_OPT_STATUS': 'true',
            },
            'inspectionData': None,
            'registrationType': 'NORMAL',
            'progressiveDiscountRuleDtos': [
                {
                    'discountType': 1,
                    'id': 0,
                    'conditionAmount': 2,
                    'discountAmount': 5,
                },
                {
                    'discountType': 1,
                    'id': 1,
                    'conditionAmount': 3,
                    'discountAmount': 6,
                },
                {
                    'discountType': 1,
                    'id': 2,
                    'conditionAmount': 4,
                    'discountAmount': 7,
                },
                {
                    'discountType': 1,
                    'id': 3,
                    'conditionAmount': 5,
                    'discountAmount': 8,
                },
                {
                    'discountType': 1,
                    'id': 4,
                    'conditionAmount': 6,
                    'discountAmount': 9,
                },
            ],
            'requested': True,
            'roleCode': 2,
        }

        response = requests.post(
            'https://wing.coupang.com/tenants/seller-web/vendor-inventory/saveV2',
            headers=headers,
            json=json_data,
        )
        
        return response.json()["message"]
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return 1

