
import sys
sys.path.insert(0, 'Module')
import processordb
import json
import urllib.request
import urllib.parse
import bcrypt
import pybase64
import time
import requests
import math
from io import BytesIO
from PIL import Image
import traceback
import smarteditorgen

session = requests.Session()

def upload_from_pil(image, cookie):
    image = image.convert("RGB")
    url = "https://sell.smartstore.naver.com/api/v2/product-photos/uploads?acceptedPatterns=image%2Fjpeg,image%2Fgif,image%2Fpng,image%2Fbmp"
    image_bytes = BytesIO()
    image.save(image_bytes, format='JPEG')
    image_bytes.seek(0)  # Reset the file pointer to the beginning
    files = {
        f"files{[0]}":("image1.JPG",image_bytes,'image/jpeg')
    }
    headers = {
    'authority': 'sell.smartstore.naver.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,ko;q=0.8',
    'cache-control': 'no-cache',
    'cookie': cookie,
    'origin': 'https://sell.smartstore.naver.com',
    'pragma': 'no-cache',
    'referer': 'https://sell.smartstore.naver.com/',
    'sec-ch-ua': '"Brave";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'x-current-state': 'https://sell.smartstore.naver.com/#/products/create',
    'x-current-statename': 'main.product.create',
    'x-to-statename': 'main.product.create'
    }

    response = requests.request("POST", url, headers=headers, files=files)
    
    return response.json()[0]["imageUrl"]


def changeurlownership(url, navercookie):
    tempheaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=tempheaders)
    image = Image.open(BytesIO(response.content))
    return upload_from_pil(image, navercookie)

def check_tag(tag):
    tag_availability = session.get("https://sell.smartstore.naver.com/api/product/shared/is-restrict-tag",
                params={
                    "_action": "isRestrictTag",
                    "tag" : tag
                }).json()
    return not tag_availability["restricted"]

def product_upload(pi_item_dup, navercookie):
    try:
        pi_item = pi_item_dup
        session.headers.update({"cookie": navercookie})
        accountdefault = session.get("https://sell.smartstore.naver.com/api/products?_action=create").json()
        
        customerbenefit = {
                    "immediateDiscountPolicy": {
                        "discountMethod": {
                            "value": pi_item.ProductOriginPrice - pi_item.ProductPrice,
                            "discountUnitType": "WON"
                        },
                        "mobileDiscountMethod": {
                            "value": pi_item.ProductOriginPrice - pi_item.ProductPrice,
                            "discountUnitType": "WON"
                        }
                    },
                    "specialDiscountPolicies": []
                }
        
        if pi_item.ProductOriginPrice - pi_item.ProductPrice == 0:
            customerbenefit = {
                "specialDiscountPolicies": []
            }
        
        optionalImages = []
        for subimage in pi_item.ProductSubImages.split(','):
            if subimage != '':
                optionalImages.append({"url": changeurlownership(subimage, navercookie)})

        sellerTags = []
        for ProductTag in pi_item.ProductTags.split(','):
            if ProductTag.strip() != '':
                if check_tag(ProductTag):
                    sellerTags.append({"text": ProductTag})

        def search_value(ls, key_to_find):
            desired_value = None
            for key, value in ls:
                if key == key_to_find:
                    desired_value = value
                    return desired_value
            return desired_value  

        pid_ls = []
        for skuprops in pi_item.ProductOptions["sku_props"]:
            pid = skuprops["pid"]
            for value in skuprops["values"]:
                pid_ls.append((pid + ":" + value["vid"], value["optioncode"]))

        optionInfo_options = []
        for option in pi_item.ProductOptions["sku_props"]:
            optionInfo_options.append({
                                    "groupName": option["prop_name"],
                                    "usable": True,
                                    "optionType": "COMBINATION",
                                    "sortType": "CREATE"
                                })

        optionCombinations = []
        optionorder = 1
        for num, sku_price in enumerate(pi_item.ProductOptions["sku_price"]):
            props_ids = sku_price["props_ids"].split(';')
            optioncombi = {}
            for i, props_id in enumerate(props_ids):
                optionname = str(search_value(pid_ls, props_id))
                optioncombi.update({"optionName" + str(i+1): optionname})
            optioncombi.update({"stockQuantity": sku_price["stock"]*10})
            optioncombi.update({"price": (sku_price["sale_price"] - pi_item.ProductPrice)})
            optioncombi.update({"sellerManagerCode": sku_price["skuid"]})
            optioncombi.update({"usable": True})
            optioncombi.update({"logisticsCenterOptionStocks": []})
            optioncombi.update({"regOrder": num + 1})
            
            optionCombinations.append(optioncombi)

        if len(pi_item.ProductOptions["sku_props"]) == 0:
            optionCombinations = []
            optionInfo_options.append({
                                    "groupName": "선택",
                                    "usable": True,
                                    "optionType": "COMBINATION",
                                    "sortType": "CREATE"
                                })
            optionCombinations.append({
                "optionName1": "상품 담기",
                "stockQuantity": 9999,
                "logisticsCenterOptionStocks": [],
                "price": 0,
                "sellerManagerCode": str(pi_item.TaobaoID),
                "usable": True,
                "regOrder": 1
                })


        image_json = []
        imageorder = 2
        image_json.append({
                        "imageType": "REPRESENTATIVE",
                        "order": 1,
                        "imageUrl": changeurlownership(pi_item.ProductMainImage, navercookie),
                        "width": 0,
                        "height": 0,
                        "fileSize": 0
                    })
        for imageurl in pi_item.ProductSubImages.split(','):
            if imageurl != '':
                image_json.append({
                        "imageType": "OPTIONAL",
                        "order": imageorder,
                        "imageUrl": changeurlownership(imageurl, navercookie),
                        "width": 0,
                        "height": 0,
                        "fileSize": 0
                    })
                imageorder += 1

        #카테고리가 int가 아닌 경우 str -> int로 전환시켜줌.
        if type(pi_item.ProductCategory) == str:
            try:
                pi_item.ProductCategory = int(pi_item.ProductCategory)
            except:
                pass

        upload_json = {
            "product": {
                "accountNo": accountdefault["product"]["accountNo"],
                "name": pi_item.ProductName,
                "salePrice": pi_item.ProductOriginPrice,
                "stockQuantity": 999,
                "logisticsCenterStocks": [],
                "saleType": "NEW",
                "excludeAdminDiscount": False,
                "excludeGivePresent": False,
                "excludeGiftValidPeriodExtension": False,
                "payExposure": True,
                "category": {
                    "id": pi_item.ProductCategory,
                    "wholeCategoryName": "",
                    "lastLevel": True,
                    "deleted": False,
                    "sellBlogUse": True,
                    "sortOrder": 0,
                    "juvenileHarmful": False,
                    "$order": 21,
                    "exceptionalCategoryTypes": [
                        "REGULAR_SUBSCRIPTION",
                        "FREE_RETURN_INSURANCE"
                    ],
                    "exceptionalCategoryAttributes": [
                        {
                            "id": "REGULAR_SUBSCRIPTION",
                            "content": {
                                "certificationIds": []
                            }
                        }
                    ]
                },
                "images": image_json,
                "videos": [],
                "videoRegisterYn": False,
                "detailAttribute": {
                    "naverShoppingSearchInfo": {
                        "modelName": pi_item.ProductName,
                        },
                    "afterServiceInfo": accountdefault["product"]["detailAttribute"]["afterServiceInfo"],
                    "originAreaInfo": {
                        "type": "IMPORT",
                        "originArea": {
                            "code": "0200037"
                        },
                        "plural": False,
                        "importer": "굿초이스그룹"
                    },
                    "sellerCodeInfo": {
                        "sellerManagementCode": pi_item.TaobaoID,
                        "sellerBarcode": pi_item.TaobaoID,
                        "sellerCustomCode1": pi_item.TaobaoID,
                        "sellerCustomCode2": pi_item.TaobaoID
                    },
                    "seoInfo": {
                        "pageTitle": pi_item.ProductName,
                        "metaDescription": pi_item.ProductName,
                        "sellerTags": sellerTags
                    },
                    "optionInfo": {
                        "optionUsable": True,
                        "useStockManagement": True,
                        "options": optionInfo_options,
                        "optionCombinations": optionCombinations,
                        "optionStandards": [],
                        "optionDeliveryAttributes": []
                    },
                    "supplementProductInfo": accountdefault["product"]["detailAttribute"]["supplementProductInfo"],
                    "purchaseReviewInfo": accountdefault["product"]["detailAttribute"]["purchaseReviewInfo"],
                    "customMadeInfo": accountdefault["product"]["detailAttribute"]["customMadeInfo"],
                    "taxType": accountdefault["product"]["detailAttribute"]["taxType"],
                    "certification": False,
                    "productCertificationInfos": [],
                    "certificationTargetExcludeContent": {
                        "kcExemption": "OVERSEAS",
                        "kcYn": "KC_EXEMPTION_OBJECT",
                        "childYn": True
                    },
                    "minorPurchasable": True,
                    "productInfoProvidedNotice": accountdefault["product"]["detailAttribute"]["productInfoProvidedNotice"],
                    "productAttributes": [],
                    "consumptionTax": "TEN",
                    "useReturnCancelNotification": False,
                    "releaseDate": None
                },
                "detailContent": {
                    "productDetailInfoContent": smarteditorgen.smarteditorgenerator(pi_item.ProductOptions, pi_item.ProductDescData),
                    "editorType": "SEONE",
                    "editorTypeForEditor": "SEONE",
                    "existsRemoveTags": False
                },
                "deliveryInfo": accountdefault["deliveryBaseInfoVO"]["templateList"][0]["templateContent"],
                "customerBenefit": customerbenefit,
                "productStats": {},
                "shopManagementYn": False,
                "representImageUrl": pi_item.ProductMainImage,
                "useSalePeriod": False,
                "product3dImageConfig": {}
            },
            "tempSaveId": 0,
            "savedTemplate": {
                "EVENT_PHRASE": False
            },
            "singleChannelProductMap": {
                "STOREFARM": {
                    "id": "",
                    "selfProductNameUsable": False,
                    "channelProductName": "",
                    "channelServiceType": "STOREFARM",
                    "channelProductType": "SINGLE",
                    "channel": None,
                    "epInfo": {
                        "naverShoppingRegistration": True,
                        "enuriRegistration": False,
                        "danawaRegistration": False,
                        "naverDisabled": False,
                        "enuriDisabled": False,
                        "danawaDisabled": False,
                        "disabledAll": False
                    },
                    "channelProductDisplayStatusType": "ON",
                    "channelProductStatusType": "NORMAL",
                    "storeKeepExclusiveProduct": False,
                    "orderRequestUsable": False,
                    "best": False,
                    "bbsConfig": False,
                    "materialImages": [],
                    "tagImages": [],
                    "barcodeImage": None,
                    "affiliateInfo": {
                        "affiliateYn": False
                    },
                    "loungeProductType": None,
                    "channelNo": accountdefault["simpleAccountInfo"]["defaultChannelNo"]
                }
            },
            "representNo": accountdefault["simpleAccountInfo"]["representNo"],
            "representName": accountdefault["simpleAccountInfo"]["representName"],
            "representativeBirthDay": accountdefault["simpleAccountInfo"]["representativeBirthDay"],
            "representType": accountdefault["simpleAccountInfo"]["representType"],
            "productRegistAuthCategories": accountdefault["simpleAccountInfo"]["representType"],
            "accountNo": accountdefault["product"]["accountNo"],
            "accountId": accountdefault["simpleAccountInfo"]["accountId"],
            "advertiser": accountdefault["simpleAccountInfo"]["advertiser"],
            "mallSeq": accountdefault["simpleAccountInfo"]["mallSeq"],
            "defaultChannelNo": accountdefault["simpleAccountInfo"]["defaultChannelNo"],
            "accountExternalStatusType": accountdefault["simpleAccountInfo"]["accountExternalStatusType"],
            "npayRefKey": accountdefault["simpleAccountInfo"]["npayRefKey"],
            "payUseYn": accountdefault["simpleAccountInfo"]["payUseYn"],
            "actionGrade": accountdefault["simpleAccountInfo"]["actionGrade"],
            "branchUseYn": accountdefault["simpleAccountInfo"]["branchUseYn"],
            "sellerNo": accountdefault["simpleAccountInfo"]["sellerNo"],
            "ownerChannelInfoList": accountdefault["simpleAccountInfo"]["ownerChannelInfoList"],
            "enforcedPermitPreOrderConfig": accountdefault["simpleAccountInfo"]["enforcedPermitPreOrderConfig"],
            "subscriptionUseYn": accountdefault["simpleAccountInfo"]["subscriptionUseYn"],
            "businessType": accountdefault["simpleAccountInfo"]["businessType"],
            "blogExposureYn": accountdefault["simpleAccountInfo"]["blogExposureYn"],
            "freeReturnInsuranceYn": accountdefault["simpleAccountInfo"]["freeReturnInsuranceYn"],
            "nextEngineUseYn": accountdefault["simpleAccountInfo"]["nextEngineUseYn"],
            "secondHandYn": accountdefault["simpleAccountInfo"]["secondHandYn"],
            "rentalUseYn": accountdefault["simpleAccountInfo"]["rentalUseYn"],
            "rentalCreditCheckRequiredYn": accountdefault["simpleAccountInfo"]["rentalCreditCheckRequiredYn"],
            "brandStoreExhibitionYn": accountdefault["simpleAccountInfo"]["brandStoreExhibitionYn"],
            "searchableChannelInfoListMap": accountdefault["simpleAccountInfo"]["searchableChannelInfoListMap"],
            "hasTalkTalkChannel": accountdefault["simpleAccountInfo"]["hasTalkTalkChannel"],
            "brandPackageCatalogType": accountdefault["simpleAccountInfo"]["brandPackageCatalogType"],
            "epNaverShoppingOperable": accountdefault["simpleAccountInfo"]["epNaverShoppingOperable"],
            "epOperable": accountdefault["simpleAccountInfo"]["epOperable"],
            "overseas": accountdefault["simpleAccountInfo"]["overseas"],
            "creatableChannelInfoListMap": accountdefault["simpleAccountInfo"]["creatableChannelInfoListMap"],
            "updatableChannelInfoListMap": accountdefault["simpleAccountInfo"]["updatableChannelInfoListMap"],
            "epEnuriOperable": accountdefault["simpleAccountInfo"]["epEnuriOperable"],
            "epDanawaOperable": accountdefault["simpleAccountInfo"]["epDanawaOperable"],
            "adult": accountdefault["simpleAccountInfo"]["adult"]
        }

        product_upload = session.post("https://sell.smartstore.naver.com/api/products", json=upload_json).json()
        if "code" in product_upload:
            #pi_item.change_smartstoreid(1)
            print(product_upload)
            processordb.Commit()
            return 1
        else:
            #pi_item.change_smartstoreid(product_upload["singleChannelProductMap"]["STOREFARM"]["id"])
            processordb.Commit()
            return product_upload["singleChannelProductMap"]["STOREFARM"]["id"]
    except Exception as e:
        print(traceback.format_exc())
        return 1

def delete_product(pi_item, navercookie):
    session.headers.update({"cookie": navercookie})
    #상품 검색하기
    json_data = {
        'searchKeywordType': 'CHANNEL_PRODUCT_NO',
        'searchKeyword': str(pi_item.SmartStoreID),
        'productName': '',
        'modelName': '',
        'manufacturerName': '',
        'brandName': '',
        'searchPaymentType': 'ALL',
        'searchPeriodType': 'PROD_REG_DAY',
        'deliveryAttributeType': '',
        'productKindType': '',
        'etcCondition': '',
        'subscriptionType': '',
        'logisticsCompanyNo': '',
        'useProductLogistics': True,
        'deliveryCompanyId': '',
        'useDeliveryCompany': True,
        'viewData': {
            'productStatusTypes': [
                'SALE',
            ],
            'channelServiceTypes': [
                'STOREFARM',
                'WINDOW',
                'AFFILIATE',
                '',
            ],
            'pageSize': 100,
        },
        'searchOrderType': 'REG_DATE',
        'productStatusTypes': [
            'SALE',
        ],
        'channelServiceTypes': [
            'STOREFARM',
            'WINDOW',
            'AFFILIATE',
        ],
        'page': 0,
        'size': 100,
        'sort': [],
    }

    search_result = session.post(
        'https://sell.smartstore.naver.com/api/products/list/search',
        json = json_data
    ).json()
    
    productid = search_result["content"][0]["id"]
    
    #상품 삭제하기
    params = {
        '_action': 'updateProductStatusType',
    }

    json_data = {
        'productNos': [
            productid,
        ],
        'productStatusType': 'DELETE',
        'productBulkUpdateType': 'DELETE',
    }
    resp = session.patch('https://sell.smartstore.naver.com/api/products/bulk-update', params=params, json = json_data).json()
    
    return resp