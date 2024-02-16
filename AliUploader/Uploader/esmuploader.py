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

tbheaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

def generate_time_strings():
    # Get the current date
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Calculate the date after 90 days
    future_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

    return current_date, future_date

def search_value(ls, key_to_find):
        desired_value = None
        for key, value in ls:
            if key == key_to_find:
                desired_value = value
                return desired_value
        return desired_value  
        

def upload_img(imgurl, headers):
    print(imgurl)
    filecontent = requests.get(imgurl, headers=tbheaders).content
    image = Image.open(io.BytesIO(filecontent))
    #Image resize
    # resize the image
    width, height = image.size
    if width < 600 or height < 600:
        ratio = max(600/width, 600/height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height))
    image = image.convert('RGB')
    image_bytes_io = io.BytesIO()
    image.save(image_bytes_io, format='JPEG')
    image_bytes = image_bytes_io.getvalue()
    
    url = "https://www.esmplus.com/Sell/ImageUpload/ImageUpload?actionType=U&goodsRegVer=2&imageType=additional"
    files=[
    ('btnSelectFile',(imgurl.split('/')[-1],image_bytes,'image/jpeg'))
    ]

    response = requests.request("POST", url, headers=headers, files=files)
    response2 = requests.post("https://www.esmplus.com/Sell/ImageUpload/ImageUpload?actionType=C", headers=headers, params={
        "tempImageUrls" : f"primary:{response.json()['UploadImageUrl']}:0:false"
    })
    
    primary_imgurl = urllib.parse.unquote(response2.json()["UploadImageUrls"].split(':')[1])

    return primary_imgurl

def product_upload(pi_item_dup, esmcookie):
    try:
        pi_item = pi_item_dup
        current_time, future_time = generate_time_strings()
        headers1 = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': esmcookie,
            'Origin': 'https://www.esmplus.com',
            'Referer': 'https://www.esmplus.com/Sell/SingleGoods?cmd=2&goodsNo=2690663472&menuCode=TDM398',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Brave";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
            }
        #모든 가격 데이터를 15% 증가시킴
        pi_item.ProductOriginPrice = math.ceil(pi_item.ProductOriginPrice * 1.05 / 100) * 100
        pi_item.ProductPrice = math.ceil(pi_item.ProductPrice * 1.05 / 100) * 100
        for option in pi_item.ProductOptions["sku_price"]:
            option["sale_price"] = math.ceil(option["sale_price"] * 1.05 / 100) * 100
        
        
        option_prices = [float(item["sale_price"]) for item in pi_item.ProductOptions["sku_price"]]
        option_maxprice = max(option_prices)
        option_minprice = min(option_prices)

        if option_minprice * 3 /2 < option_maxprice: #업로드 조건을 만족하지 않는 경우 이를 만족하게 옵션의 가격을 조정
            alpha = ((option_maxprice * 2 / 3) - option_minprice)/(option_maxprice - option_minprice)
            for option in pi_item.ProductOptions["sku_price"]:
                option["sale_price"] = (float(option_maxprice - option["sale_price"]) * alpha) + option["sale_price"]
                option["sale_price"] = math.ceil(option["sale_price"] / 100) * 100
        else:
            pass

        option_prices = [float(item["sale_price"]) for item in pi_item.ProductOptions["sku_price"]]
        pi_item.ProductOriginPrice = min(option_prices)

        mainimage = upload_img(pi_item.ProductMainImage, headers1)

        AdditionalImages = []
        for imgurl in pi_item.ProductSubImages.split(',')[1:]:
            AdditionalImages.append({
                                "Operation": "1",
                                "Url": upload_img(imgurl, headers1),
                                "BigImage": "false",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": ""
                            })

        #옵션 정보 정렬
        pid_ls = []
        for skuprops in pi_item.ProductOptions["sku_props"]:
            pid = skuprops["pid"]
            for value in skuprops["values"]:
                pid_ls.append((pid + ":" + value["vid"], value["optioncode"]))
        
        optionCombinations = []
        optionorder = 1
        orderoption = None
        #가능 옵션이 여러개인 경우
        if len(pi_item.ProductOptions["sku_props"]) > 0:
            for num, sku_price in enumerate(pi_item.ProductOptions["sku_price"]):
                props_ids = sku_price["props_ids"].split(';')
                optioncombi = {}
                optioncombi.update({"OptType": str(len(pi_item.ProductOptions["sku_props"]))})
                
                optioncombi.update({"OptValue1": "",
                "RcmdOptValueNo1": "0",
                "OptName1": "",
                "RcmdOptNo1": "0",
                "OptValue2": "",
                "RcmdOptValueNo2": "0",
                "OptName2": "",
                "RcmdOptNo2": "0",
                "OptValue3": "",
                "RcmdOptValueNo3": "0",
                "OptName3": "",
                "RcmdOptNo3": "0"})
                optls = []
                for i, props_id in enumerate(props_ids):
                    optionname = str(search_value(pid_ls, props_id))
                    optioncombi.update({"OptValue" + str(i+1): optionname})
                    optioncombi.update({"RcmdOptValueNo"+ str(i+1): "0"})
                    optioncombi.update({"OptName"+ str(i+1): pi_item.ProductOptions["sku_props"][i]["prop_name"]})
                    optioncombi.update({"RcmdOptNo"+ str(i+1): "0"})
                    optls.append(optionname)
                optls.extend([None] * 10)
                optioncombi.update({"SellerStockCode": str(sku_price["skuid"]),
                "SkuMatchingVerNo": None,
                "AddAmnt": str(sku_price["sale_price"] - pi_item.ProductOriginPrice),
                "OptRepImageLevel": "0",
                "OptRepImageUrl": "",
                "OptionInfoCalculation": None,
                "SkuList": None,
                "OptionNameLangList": []})
                
                
                optioncombi.update({"OptionValueLangList": [
                    {
                        "LangCode": "ENG",
                        "Opt1": optls[0],
                        "Opt2": optls[1],
                        "Opt3": optls[2]
                    },
                    {
                        "LangCode": "JPN",
                        "Opt1": optls[0],
                        "Opt2": optls[1],
                        "Opt3": optls[2]
                    },
                    {
                        "LangCode": "CHN",
                        "Opt1": optls[0],
                        "Opt2": optls[1],
                        "Opt3": optls[2]
                    }
                ]})
                
                optioncombi.update({"SiteOptionInfo": [
                    {
                        "SiteId": "1",
                        "ExposeYn": "Y",
                        "SoldOutYn": "N",
                        "StockQty": None
                    },
                    {
                        "SiteId": "2",
                        "ExposeYn": "Y",
                        "SoldOutYn": "N",
                        "StockQty": None
                    }
                ]})
                
                optionCombinations.append(optioncombi)
                orderoption = {
                        "OptType": "2",
                        "StockMngIs": False,
                        "UnifyStockIs": False,
                        "OptionInfoList": optionCombinations
                    }
        
        #가능 옵션이 하나인 경우
        else:
            pass

        pi_item.ProductHtmlDescription = pi_item.ProductHtmlDescription.replace("naver", "google")

        ShipmentPlaceNo = requests.get("https://www.esmplus.com/SELL/SYI/GetShipmentPlaces",
                    headers=headers1).json()[0]["ShipmentPlaceNo"]

        #DeliveryFeeTemplate = {"DeliveryFeeType":1, "DeliveryFeeSubType":0, "FeeAmnt":0, "PrepayIs":False, "CodIs":False, "JejuAddDeliveryFee":0, "BackwoodsAddDeliveryFee":0, "ShipmentPlaceNo":ShipmentPlaceNo, "DetailList":[]}

        memberinfo = requests.get("https://www.esmplus.com/SELL/SYI/GetDefaultReturnMemberAddress",
                                            headers=headers1).json()
        ReturnExchangeAddress = memberinfo["MembAddrNo"]
        masterid = memberinfo["MasterId"]
        accountid = memberinfo["InsOprt"]

        #IacTransPolicyNo = requests.get(f"https://www.esmplus.com/SELL/SYI/GetTransPolicyList?siteId=1&sellerId={accountid}&categoryCode=",
        #                                headers=headers1).json()[0]["TransPolicyNo"]
        #GmktTransPolicyNo  = requests.get(f"https://www.esmplus.com/SELL/SYI/GetTransPolicyList?siteId=2&sellerId={accountid}&categoryCode=",
        #                                headers=headers1).json()[0]["TransPolicyNo"]
        IacTransPolicyNo = "-200"
        GmktTransPolicyNo = "-200"


        requests.get("https://www.esmplus.com/SELL/SYI/GetDeliveryFeeTemplatesWithDetail",
                    data={"shipmentPlaceNo": ShipmentPlaceNo},headers=headers1).json()

        productjson = {
            "model": {
                "GoodsNo": None,
                "SiteGoodsNo": None,
                "IsIacSellingStatus": "0",
                "IsIacSellingStatusSpecified": False,
                "CommandType": "1",
                "IsLeaseAllowedInIac": False,
                "CallFrom": "0",
                "SYIStep1": {
                    "PurchaseBenefits": [],
                    "RegMarketType": "0",
                    "SiteSellerId": [
                        {
                            "key": "1",
                            "value": str(accountid)
                        },
                        {
                            "key": "2",
                            "value": str(accountid)
                        }
                    ],
                    "HasCatalog": False,
                    "CatalogId": "0",
                    "CatalogName": "",
                    "CatalogLowestPrice": "0",
                    "SellType": "1",
                    "GoodsType": "1",
                    "GoodsName": {
                        "InputType": "1",
                        "GoodsName": pi_item.ProductName[:50],
                        "GoodsNameSearch": pi_item.ProductName[:50],
                        "GoodsNamePrmt": "",
                        "SiteGoodsName": [],
                        "SiteGoodsNameEng": [
                            {
                                "key": "1",
                                "value": ""
                            },
                            {
                                "key": "2",
                                "value": ""
                            }
                        ],
                        "SiteGoodsNameChn": [
                            {
                                "key": "1",
                                "value": ""
                            },
                            {
                                "key": "2",
                                "value": ""
                            }
                        ],
                        "SiteGoodsNameJpn": [
                            {
                                "key": "1",
                                "value": ""
                            },
                            {
                                "key": "2",
                                "value": ""
                            }
                        ],
                        "UseSellerNicknameIac": False,
                        "AdMessageIac": ""
                    },
                    "SiteCategoryCode": [
                        {
                            "key": "1",
                            "value": "28141100"
                        },
                        {
                            "key": "2",
                            "value": "100000014200000123300024445"
                        }
                    ],
                    "SiteGoodsClassList": [
                        {
                            "key": "1",
                            "value": ""
                        },
                        {
                            "key": "2",
                            "value": ""
                        }
                    ],
                    "Book": {
                        "Author": "",
                        "BrandName": "",
                        "BrandNo": "",
                        "ISBNCode": "",
                        "ImgSmall": "",
                        "IsSTCodeImage": False,
                        "IsbnCodeAllowYn": "N",
                        "MakerName": "",
                        "MakerNo": "",
                        "Name": "",
                        "Price": "",
                        "PublishDate": None,
                        "Publisher": "",
                        "STCode": "",
                        "Title": "",
                        "Translater": ""
                    },
                    "MakerId": "0",
                    "MakerName": "",
                    "UserDefineMakerName": "",
                    "BrandId": "0",
                    "BrandName": "",
                    "UserDefineBrandName": "",
                    "GmktShopKind1": "-1",
                    "GmktShopKind2": "-1",
                    "GmktShopKind3": "-1",
                    "StatusCode": "",
                    "StoreShopCategoryGoods": {
                        "CategoryLevel": "0",
                        "ShopLCategoryCode": "00000000",
                        "ShopMCategoryCode": "00000000",
                        "ShopSCategoryCode": "00000000"
                    },
                    "MiniShopCategoryGoods": {
                        "CategoryLevel": "0",
                        "ShopLCategoryCode": "00000000",
                        "ShopMCategoryCode": "00000000",
                        "ShopSCategoryCode": "00000000"
                    },
                    "IsTPLGoods": False,
                    "AdminRestrict": "",
                    "SiteSellerAdjustCommissionPrice": {
                        "IacOpenAdjustCommissionPrice": "0",
                        "IacSpecialAdjustCommissionPrice": "0",
                        "GmktOpenAdjustCommissionPrice": "0",
                        "GmktSpecialAdjustCommissionPrice": "0"
                    },
                    "CatalogInfo": {
                        "CatalogId": "0",
                        "CatalogIdSpecified": False,
                        "CatalogName": None,
                        "LowestPrice": "0",
                        "LowestPriceSpecified": False,
                        "ImageUrl": None,
                        "MakerId": "0",
                        "MakerIdSpecified": False,
                        "MakerName": None,
                        "BrandId": "0",
                        "BrandIdSpecified": False,
                        "BrandName": None,
                        "ModelName": None,
                        "MainDescription": None,
                        "MatchingItemCount": "0",
                        "MatchingItemCountSpecified": False,
                        "ProductionDate": None,
                        "ProductionDateSpecified": False,
                        "ProductionDateType": "0",
                        "ProductionDateTypeSpecified": False,
                        "PriceRenovationDate": None,
                        "PriceRenovationDateSpecified": False,
                        "IsAdult": False,
                        "IsAdultSpecified": False,
                        "IsBook": False,
                        "IsBookSpecified": False
                    },
                    "IsItemNameChangeAllowed": False
                },
                "SYIStep2": {
                    "SellingStatus": "0",
                    "GoodsStatus": "1",
                    "UsedMonths": None,
                    "IsGMKTEnvironmentFriendlyCertType": False,
                    "IsIACEnvironmentFriendlyCertType": False,
                    "Price": {
                        "InputType": "1",
                        "GoodsPrice": pi_item.ProductOriginPrice,
                        "GoodsPriceIAC": "0",
                        "GoodsPriceGMKT": "0",
                        "IsSeparate": False,
                        "IsUserCustomSettlementGMKT": False,
                        "GoodsPriceSettlementGMKT": "0",
                        "BookPrice": "0",
                        "OrgGoodsPrice": "0"
                    },
                    "PricePerUnit": {
                        "Unit": None,
                        "UnitPrice": "0"
                    },
                    "WirelessCallingPlan": {
                        "PhoneFeeType": "0",
                        "PhoneFeeUrl": "",
                        "Plans": [],
                        "MobilePhoneFeeUrl": ""
                    },
                    "MobileDevicePrice": {
                        "PhoneDevicePrice": "",
                        "PhoneSupportDiscount": "",
                        "MakerSupportDiscount": "",
                        "TeleComSupportDiscount": "",
                        "PhoneAddDiscount": "",
                        "PhoneInstallmentPrice": ""
                    },
                    "Stock": {
                        "InputType": "1",
                        "SiteGoodsCountNo": "0",
                        "BuyableQuantityType": "0",
                        "BuyableQuantity": "",
                        "BuyableQuantityDay": "",
                        "GoodsCount": "99999",
                        "GoodsCountIAC": "99999",
                        "GoodsCountGMKT": "99999",
                        "OldGoodsCount": "0",
                        "OldGoodsCountIAC": "0",
                        "OldGoodsCountGMKT": "0"
                    },
                    "Options": {
                        "InputType": "1",
                        "OptVerType": "0",
                        "OptVerTypeIAC": "0",
                        "OptVerTypeGMKT": "0",
                        "JsonData": None,
                        "JsonDataIAC": None,
                        "JsonDataGMKT": None,
                        "JsonDataLegacy": None
                    },
                    "OrderOption": orderoption,
                    "Additions": {
                        "InputType": "1",
                        "JsonData": None,
                        "JsonDataIAC": None,
                        "JsonDataGMKT": None,
                        "JsonDataLegacy": None,
                        "CommonGoodsNo": None,
                        "IsUseCommonGoods": False
                    },
                    "AddonService": {
                        "AddonServiceUseType": "0",
                        "AddonServiceList": []
                    },
                    "SellingPeriod": {
                        "IAC": {
                            "StartDate": f"{current_time} 00:00:00",
                            "EndDate": f"{future_time} 23:59:59"
                        },
                        "GMKT": {
                            "StartDate": f"{current_time} 00:00:00",
                            "EndDate": f"{future_time} 23:59:59"
                        },
                        "History": []
                    },
                    "PreSale": {
                        "UseSettingIAC": False,
                        "SaleStartDateIAC": current_time
                    },
                    "GoodsImage": {
                        "AdditionalImages": AdditionalImages,
                        "PrimaryImage": {
                            "Operation": "1",
                            "Url": mainimage,
                            "BigImage": "False",
                            "ImageSourceCode": "0",
                            "ImageSourceOriginId": ""
                        },
                        "FixedImage": {
                            "Operation": "1",
                            "Url": mainimage,
                            "BigImage": "False",
                            "ImageSourceCode": "0",
                            "ImageSourceOriginId": ""
                        },
                        "AdditionalImagesSite": "0",
                        "AdditionalImagesStr": "[]"
                    },
                    "DescriptionType": "2",
                    "DescriptionTypeSpecified": False,
                    "Description": {
                        "InputType": "1",
                        "Text": None,
                        "TextIAC": None,
                        "TextGMKT": None
                    },
                    "NewDescription": {
                        "InputType": "1",
                        "Text": urllib.parse.quote(pi_item.ProductHtmlDescription),
                        "IsEditor": False,
                        "TextEng": None,
                        "IsEditorEng": False,
                        "TextChn": None,
                        "IsEditorChn": False,
                        "TextJpn": None,
                        "IsEditorJpn": False,
                        "TextIAC": None,
                        "TextGMKT": None,
                        "TextAdd": None,
                        "TextAddEng": None,
                        "TextAddChn": None,
                        "TextAddJpn": None,
                        "TextAddIAC": None,
                        "TextAddGMKT": None,
                        "TextPrmt": None,
                        "TextPrmtIAC": None,
                        "TextPrmtGMKT": None,
                        "OuterShareYn": None,
                        "OuterShareUrl": None,
                        "OuterShareNew": False,
                        "Height": "9212"
                    },
                    "ItemCode": str(pi_item.TaobaoID),
                    "CustCategoryNo": "0",
                    "CustCategory": None,
                    "ExpiryDate": "0-0-0",
                    "ExpiryDateSpecified": True,
                    "LaunchingDate": None,
                    "LaunchingDateSpecified": False,
                    "ManufacturedDate": "0-0-0",
                    "ManufacturedDateSpecified": True,
                    "Origin": {
                        "ProductType": "",
                        "Type": "2",
                        "Name": "아시아 중국",
                        "Code": "174",
                        "IsMultipleOrigin": "False"
                    },
                    "LegacyRawMaterials": None,
                    "RawMaterials": None,
                    "Capacity": {
                        "Volume": None,
                        "Unit": "0",
                        "IsMultipleVolume": False
                    },
                    "Manual": None,
                    "ECoupon": {
                        "Period": "0",
                        "Price": "0",
                        "Ratio": "0",
                        "CouponName": "",
                        "ExpireType": "0",
                        "Expire1StartDate": "",
                        "Expire1EndDate": "",
                        "Expire2Duration": "0",
                        "Expire2Start": "0",
                        "UseTermType": "0",
                        "UseTerm1StartDate": "",
                        "UseTerm1EndDate": "",
                        "UseTerm2Start": "0",
                        "UseTerm2Duration": "0",
                        "CouponTemplate": "0",
                        "CouponImageUrl": "",
                        "DownloadTemplate": "0",
                        "DownloadImageUrl": "",
                        "ApplyPlace": "",
                        "IsInformByAddress": False,
                        "Address": "",
                        "AddressNo": "",
                        "IsInformByURL": False,
                        "URL": "",
                        "ApplyPlacePriority": "0",
                        "MoneyType": "0",
                        "MobileUseInfo": "",
                        "MobileHelpDeskphoneNo": "",
                        "TelephoneNo": "",
                        "AdditionalBenefit": "",
                        "HasRestrictCondition": False,
                        "RestrictCondition": "",
                        "Guide": "",
                        "PublicationCorp": "",
                        "PublicationCorpURL": "",
                        "IsCustomerNameView": False
                    },
                    "DeliveryInfo": {
                        "CommonDeliveryUseYn": True,
                        "InvalidDeliveryInfo": False,
                        "CommonDeliveryWayOPTSEL": "1",
                        "GmktDeliveryWayOPTSEL": "0",
                        "IsCommonGmktUnifyDelivery": False,
                        "GmktDeliveryCOMP": "100000012",
                        "IacDeliveryCOMP": "10013",
                        "IsCommonVisitTake": False,
                        "IsCommonQuickService": False,
                        "IsCommonIACPost": False,
                        "CommonIACPostType": "0",
                        "CommonIACPostPaidPrice": "0",
                        "IsGmktVisitTake": False,
                        "IsGmktQuickService": False,
                        "IsGmktTodayDEPAR": False,
                        "IsGmktTodayDEPARAgree": False,
                        "IsGmktVisitReceiptTier": False,
                        "MountBranchGroupSeq": "0",
                        "CommonVisitTakeType": "0",
                        "CommonVisitTakePriceDcAmnt": "0",
                        "CommonVisitTakeFreeGiftName": None,
                        "CommonVisitTakeADDRNo": None,
                        "CommonQuickServiceCOMPName": None,
                        "CommonQuickServicePhone": None,
                        "CommonQuickServiceDeliveryEnableRegionNo": None,
                        "ShipmentPlaceNo": str(ShipmentPlaceNo),
                        "DeliveryFeeType": "2",
                        "BundleDeliveryYNType": None,
                        "BundleDeliveryTempNo": None,
                        "EachDeliveryFeeType": "1",
                        "EachDeliveryFeeQTYEachGradeType": None,
                        "DeliveryFeeTemplateJSON": "{\"DeliveryFeeType\":1, \"DeliveryFeeSubType\":0, \"FeeAmnt\":0, \"PrepayIs\":false, \"CodIs\":false, \"JejuAddDeliveryFee\":0, \"BackwoodsAddDeliveryFee\":0, \"ShipmentPlaceNo\":"+str(ShipmentPlaceNo)+", \"DetailList\":[]}",
                        "EachDeliveryFeePayYn": "2",
                        "IsCommonGmktEachADDR": False,
                        "ReturnExchangeADDRNo": str(ReturnExchangeAddress),
                        "OldReturnExchangeADDR": None,
                        "OldReturnExchangeADDRTel": None,
                        "OldReturnExchangeSetupDeliveryCOMPName": None,
                        "OldReturnExchangeDeliveryFeeStr": None,
                        "ExchangeADDRNo": "",
                        "ReturnExchangeSetupDeliveryCOMP": None,
                        "ReturnExchangeSetupDeliveryCOMPName": None,
                        "ReturnExchangeDeliveryFee": "0",
                        "ReturnExchangeDeliveryFeeStr": "",
                        "IacTransPolicyNo": str(IacTransPolicyNo),
                        "GmktTransPolicyNo": str(GmktTransPolicyNo),
                        "BackwoodsDeliveryYn": "Y",
                        "IsTplConvertible": False,
                        "IsGmktIACPost": False
                    },
                    "IsAdultProduct": "False",
                    "IsVATFree": "False",
                    "ASInfo": None,
                    "CertIAC": {
                        "HasIACCertType": False,
                        "MedicalInstrumentCert": {
                            "ItemLicenseNo": None,
                            "AdDeliberationNo": None,
                            "IsUse": False,
                            "CertificationOfficeName": None,
                            "CertificationNo": None,
                            "Operation": "1"
                        },
                        "BroadcastEquipmentCert": {
                            "BroadcastEquipmentIs": False,
                            "AddtionalConditionIs": False,
                            "IsUse": False,
                            "CertificationOfficeName": None,
                            "CertificationNo": "",
                            "Operation": "1"
                        },
                        "FoodCert": {
                            "IsUse": False,
                            "CertificationOfficeName": None,
                            "CertificationNo": None,
                            "Operation": "1"
                        },
                        "HealthFoodCert": {
                            "AdDeliberationNo": None,
                            "IsUse": False,
                            "CertificationOfficeName": None,
                            "CertificationNo": None,
                            "Operation": "1"
                        },
                        "EnvironmentFriendlyCert": {
                            "CertificationType": "ENV_DTL",
                            "isIACEnvironmentFriendlyCertType": False,
                            "isGMKTEnvironmentFriendlyCertType": False,
                            "CertBizType": "ENV_DTL",
                            "ProducerName": None,
                            "PresidentInfoNA": None,
                            "RepItemName": None,
                            "InfoHT": None,
                            "CertGroupType": None,
                            "InfoEM": None,
                            "CertStartDate": None,
                            "CertEndDate": None,
                            "InfoAD": None,
                            "CertificationOfficeName": None,
                            "CertificationExpiration": None,
                            "IsUse": False,
                            "CertificationNo": None,
                            "Operation": "1"
                        },
                        "SafeCert": {
                            "SafeCertType": "0",
                            "AuthItemType": "0",
                            "CertificationNo": None,
                            "IsUse": False,
                            "CertificationOfficeName": None,
                            "Operation": "1"
                        },
                        "ChildProductSafeCert": {
                            "SafeCertType": "0",
                            "ChangeType": "0",
                            "SafeCertDetailInfoList": []
                        },
                        "IntegrateSafeCert": {
                            "ItemNo": None,
                            "IntegrateSafeCertGroupList": [
                                {
                                    "SafeCertGroupNo": "1",
                                    "CertificationType": "1"
                                },
                                {
                                    "SafeCertGroupNo": "2",
                                    "CertificationType": "1"
                                },
                                {
                                    "SafeCertGroupNo": "3",
                                    "CertificationType": "1"
                                },
                                {
                                    "SafeCertGroupNo": "4",
                                    "CertificationType": "1"
                                }
                            ]
                        }
                    },
                    "CertificationNoGMKT": "",
                    "LicenseSeqGMKT": None,
                    "OfficialNotice": {
                        "NoticeItemGroupNo": "35",
                        "NoticeItemCodes": [
                            {
                                "NoticeItemCode": "35-1",
                                "NoticeItemValue": "상세정보 참조"
                            },
                            {
                                "NoticeItemCode": "35-2",
                                "NoticeItemValue": "상세정보 참조"
                            },
                            {
                                "NoticeItemCode": "35-3",
                                "NoticeItemValue": "상세정보 참조"
                            },
                            {
                                "NoticeItemCode": "35-4",
                                "NoticeItemValue": "상세정보 참조"
                            },
                            {
                                "NoticeItemCode": "35-5",
                                "NoticeItemValue": "상세정보 참조"
                            },
                            {
                                "NoticeItemCode": "35-6",
                                "NoticeItemValue": "상세정보 참조"
                            },
                            {
                                "NoticeItemCode": "999-5",
                                "NoticeItemValue": "상세정보 참조"
                            }
                        ]
                    },
                    "ItemWeight": "0",
                    "SkuList": [],
                    "SkuMatchingVerNo": "0",
                    "RentalAddInfo": None,
                    "CertificationTextGMKT": "",
                    "LicenseTextGMKT": None,
                    "InventoryNo": None,
                    "SingleSellerShop": None,
                    "IsUseSellerFunding": None,
                    "IsGift": True,
                    "ConsultingDetailList": [],
                    "Install": {
                        "IsInstall": False,
                        "InstallMakerId": "0",
                        "InstallModelCode": pi_item.TaobaoID
                    }
                },
                "SYIStep3": {
                    "G9RegisterCommand": "0",
                    "IsG9Goods": False,
                    "IsOnlyG9Goods": False,
                    "SellerDiscount": {
                        "DiscountAmtIac1": "0",
                        "DiscountAmtIac2": None,
                        "DiscountAmtGmkt1": "0",
                        "DiscountAmtGmkt2": None,
                        "IsSellerDCExceptionIacItem": False,
                        "IsSellerDCExceptionGmktItem": False,
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "DiscountType": "1",
                        "DiscountTypeSpecified": False,
                        "DiscountAmt": "0",
                        "DiscountAmtSpecified": False,
                        "DiscountAmt1": "0",
                        "DiscountAmt1Specified": False,
                        "DiscountAmt2": None,
                        "DiscountAmt2Specified": False,
                        "StartDate": f"{current_time}",
                        "StartDateSpecified": False,
                        "EndDate": "9999-12-31",
                        "EndDateSpecified": False,
                        "DiscountTypeIac": "1",
                        "DiscountTypeSpecifiedIac": False,
                        "StartDateIac": f"{current_time}",
                        "StartDateSpecifiedIac": False,
                        "EndDateIac": "9999-12-31",
                        "IacEndDateSpecified": False,
                        "DiscountAmtIac": "0",
                        "DiscountAmtSpecifiedIac": False,
                        "DiscountTypeGmkt": "1",
                        "DiscountTypeSpecifiedGmkt": False,
                        "StartDateGmkt": f"{current_time}",
                        "StartDateSpecifiedGmkt": False,
                        "EndDateGmkt": "9999-12-31",
                        "EndDateSpecifiedGmkt": False,
                        "DiscountAmtGmkt": "0",
                        "DiscountAmtSpecifiedGmkt": False
                    },
                    "FreeGift": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "IsOnly": "1",
                        "IsOnlySpecified": False,
                        "IacFreeGiftName": "",
                        "GmkFreeGiftName": ""
                    },
                    "IsPcs": True,
                    "IsPcsSpecified": True,
                    "IacPcsCoupon": True,
                    "IacPcsCouponSpecified": False,
                    "GmkPcsCoupon": True,
                    "GmkPcsCouponSpecified": False,
                    "GmkBargain": False,
                    "GmkBargainSpecified": False,
                    "IacFreeWishKeyword": [],
                    "IacDiscountAgreement": True,
                    "IacDiscountAgreementSpecified": False,
                    "GmkDiscountAgreement": True,
                    "GmkDiscountAgreementSpecified": False,
                    "GmkOverseaAgreementSeller": True,
                    "GmkOverseaAgreementSellerSpecified": False,
                    "IacBuyerBenefit": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.651Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.651Z",
                        "EndDateSpecified": False,
                        "IsMemberDiscount": False,
                        "IsMemberDiscountSpecified": False,
                        "MemberDiscountPrice": "0",
                        "MemberDiscountPriceSpecified": False,
                        "IsBulkDiscount": False,
                        "IsBulkDiscountSpecified": False,
                        "BulkDiscountQty": "0",
                        "BulkDiscountQtySpecified": False,
                        "BulkDiscountPrice": "0",
                        "BulkDiscountPriceSpecified": False
                    },
                    "GmkBuyerBenefit": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "Type": "",
                        "StartDate": f"{current_time}T02:33:33.651Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.651Z",
                        "EndDateSpecified": False,
                        "ConditionType": "",
                        "ConditionValue": "0",
                        "ConditionValueSpecified": False,
                        "Unit": "",
                        "UnitValue": "0",
                        "UnitValueSpecified": False,
                        "WhoFee": ""
                    },
                    "IacDonation": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.651Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.651Z",
                        "EndDateSpecified": False,
                        "DonationPrice": "0",
                        "DonationPriceSpecified": False,
                        "DonationMaxPrice": "0",
                        "DonationMaxPriceSpecified": False,
                        "DonationType": ""
                    },
                    "GmkDonation": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.651Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.651Z",
                        "EndDateSpecified": False,
                        "DonationPrice": "0",
                        "DonationPriceSpecified": False,
                        "DonationMaxPrice": "0",
                        "DonationMaxPriceSpecified": False,
                        "DonationType": ""
                    },
                    "IacSellerPoint": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "PointType": "1",
                        "PointTypeSpecified": False,
                        "Point": "0",
                        "PointSpecified": True
                    },
                    "GmkSellerMileage": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "PointType": "1",
                        "PointTypeSpecified": False,
                        "Point": "0",
                        "PointSpecified": True
                    },
                    "IacChance": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.651Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.651Z",
                        "EndDateSpecified": False,
                        "ChanceQty": "0"
                    },
                    "IacBrandShop": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "LCategoryCode": "",
                        "MCategoryCode": "",
                        "SCategoryCode": "",
                        "BrandCode": "",
                        "BrandName": "",
                        "BrandImage": []
                    },
                    "GmkBizOn": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "LCategoryCode": "",
                        "MCategoryCode": "",
                        "SCategoryCode": ""
                    },
                    "IacAdditional": [],
                    "GmkAdditional": [],
                    "IacPayWishKeyword": [],
                    "IacAdPromotion": {
                        "CategorySmart": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "CategoryPower": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "Best100Smart": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "Chance": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "AccessMode": "1",
                        "AccessModeSpecified": False
                    },
                    "GmkAdPromotion": {
                        "LargePlus": "0",
                        "LargePlusSpecified": False,
                        "LargePowerMini": "0",
                        "LargePowerMiniSpecified": False,
                        "LargeBestPower": "0",
                        "LargeBestPowerSpecified": False,
                        "MiddlePlus": "0",
                        "MiddlePlusSpecified": False,
                        "MiddlePower": "0",
                        "MiddlePowerSpecified": False,
                        "MiddleDetailPower": "0",
                        "MiddleDetailPowerSpecified": False,
                        "MiddleBestPower": "0",
                        "MiddleBestPowerSpecified": False,
                        "SmallPlus": "0",
                        "SmallPlusSpecified": False,
                        "SmallPower": "0",
                        "SmallPowerSpecified": False
                    },
                    "OverseaAgree": {
                        "RegType": None,
                        "Gubun": "0",
                        "GubunSpecified": False,
                        "OverseaDisAgreeIs": True
                    },
                    "IsLeaseAvailableInIac": False,
                    "GmktShopGroupCd": "0",
                    "IsIacFreeWishKeyword": False,
                    "IacFreeWishKeywordEndDate": False,
                    "IacCommissionRate": "0",
                    "IacCommissionRateOpenMarket": "0",
                    "IacCommissionRateGroupBy": "0",
                    "IsIacFeeDiscountItem": False,
                    "IsDispExclude": True,
                    "IsDispExcludeSpecified": False
                },
                "IsSingleGoods": False,
                "SiteGoodsNoIac": None,
                "SiteGoodsNoGmkt": None,
                "GoodsKind": "1",
                "BarCode": None,
                "IsSiteDisplayIac": False,
                "IsSiteDisplayGmkt": False,
                "SellingStatusIac": None,
                "SellingStatusGmkt": None,
                "MasterId": str(masterid),
                "LoginId": str(accountid),
                "IsDeleteGroup": False,
                "EditorUseYn": "N",
                "SdInfo": {
                    "SdCategoryCode": "00070007000600100000",
                    "SdBrandName": None,
                    "SdMakerId": "0",
                    "SdMakerName": None,
                    "SdBrandId": "0",
                    "SdProductBrandId": "0",
                    "SdProductBrandName": None,
                    "EpinCodeList": [
                        None
                    ],
                    "SdAttrMatchingList": [],
                    "SdBasicAttrMatching": {},
                    "EpinCreateReqBarcode": "",
                    "EpinCreateReqModelName": "",
                    "EpinCreateReqModelNo": ""
                },
                "BuyableQuantityMappingType": "1",
                "IsIacConvertToSingleGoods": False,
                "IsGmktConvertToSingleGoods": False,
                "AdminId": None
            },
            "orgModel": {
                "GoodsNo": None,
                "SiteGoodsNo": None,
                "IsIacSellingStatus": "0",
                "IsIacSellingStatusSpecified": False,
                "CommandType": "1",
                "IsLeaseAllowedInIac": False,
                "CallFrom": "0",
                "SYIStep1": {
                    "PurchaseBenefits": [],
                    "RegMarketType": "0",
                    "SiteSellerId": [
                        {
                            "key": "1",
                            "value": str(accountid)
                        },
                        {
                            "key": "2",
                            "value": str(accountid)
                        }
                    ],
                    "HasCatalog": False,
                    "CatalogId": "0",
                    "CatalogName": "",
                    "CatalogLowestPrice": "0",
                    "SellType": "1",
                    "GoodsType": "1",
                    "GoodsName": {
                        "InputType": "1",
                        "GoodsName": "",
                        "SiteGoodsName": [],
                        "SiteGoodsNameEng": [],
                        "SiteGoodsNameChn": [],
                        "SiteGoodsNameJpn": [],
                        "UseSellerNicknameIac": False,
                        "AdMessageIac": "",
                        "GoodsNameSearch": "",
                        "GoodsNamePrmt": "",
                        "ManagerTag": {}
                    },
                    "SiteCategoryCode": [],
                    "SiteGoodsClassList": [],
                    "Book": {
                        "STCode": "",
                        "IsSTCodeImage": False,
                        "ISBNCode": "",
                        "IsbnCodeAllowYn": "",
                        "Name": "",
                        "Author": "",
                        "Publisher": "",
                        "Price": "0",
                        "PublishDate": None,
                        "MakerName": "",
                        "MakerNo": "",
                        "BrandName": "",
                        "BrandNo": "0",
                        "ImgSmall": "",
                        "Title": "",
                        "Translater": ""
                    },
                    "MakerId": "0",
                    "MakerName": "",
                    "UserDefineMakerName": "",
                    "BrandId": "0",
                    "BrandName": "",
                    "UserDefineBrandName": "",
                    "GmktShopKind1": "-1",
                    "GmktShopKind2": "-1",
                    "GmktShopKind3": "-1",
                    "StatusCode": "",
                    "StoreShopCategoryGoods": {
                        "SiteId": "0",
                        "SiteGoodsNo": "",
                        "ShopLCategoryCode": "",
                        "ShopMCategoryCode": "",
                        "ShopSCategoryCode": "",
                        "SellerCustNo": "",
                        "CategoryLevel": "0"
                    },
                    "MiniShopCategoryGoods": {
                        "SiteId": "0",
                        "SiteGoodsNo": "",
                        "ShopLCategoryCode": "",
                        "ShopMCategoryCode": "",
                        "ShopSCategoryCode": "",
                        "SellerCustNo": "",
                        "CategoryLevel": "0"
                    },
                    "IsTPLGoods": False,
                    "AdminRestrict": "",
                    "SiteSellerAdjustCommissionPrice": {
                        "IacOpenAdjustCommissionPrice": "0",
                        "IacSpecialAdjustCommissionPrice": "0",
                        "GmktOpenAdjustCommissionPrice": "0",
                        "GmktSpecialAdjustCommissionPrice": "0"
                    },
                    "CatalogInfo": {
                        "CatalogId": "0",
                        "CatalogIdSpecified": False,
                        "CatalogName": None,
                        "LowestPrice": "0",
                        "LowestPriceSpecified": False,
                        "ImageUrl": None,
                        "MakerId": "0",
                        "MakerIdSpecified": False,
                        "MakerName": None,
                        "BrandId": "0",
                        "BrandIdSpecified": False,
                        "BrandName": None,
                        "ModelName": None,
                        "MainDescription": None,
                        "MatchingItemCount": "0",
                        "MatchingItemCountSpecified": False,
                        "ProductionDate": None,
                        "ProductionDateSpecified": False,
                        "ProductionDateType": "0",
                        "ProductionDateTypeSpecified": False,
                        "PriceRenovationDate": None,
                        "PriceRenovationDateSpecified": False,
                        "IsAdult": False,
                        "IsAdultSpecified": False,
                        "IsBook": False,
                        "IsBookSpecified": False
                    },
                    "IsItemNameChangeAllowed": False
                },
                "SYIStep2": {
                    "SellingStatus": "0",
                    "GoodsStatus": "1",
                    "UsedMonths": None,
                    "IsGMKTEnvironmentFriendlyCertType": False,
                    "IsIACEnvironmentFriendlyCertType": False,
                    "Price": {
                        "InputType": "1",
                        "GoodsPrice": "0",
                        "GoodsPriceIAC": "0",
                        "GoodsPriceGMKT": "0",
                        "IsUserCustomSettlementGMKT": False,
                        "GoodsPriceSettlementGMKT": "0",
                        "BookPrice": "0"
                    },
                    "PricePerUnit": {
                        "Unit": None,
                        "UnitPrice": "0"
                    },
                    "WirelessCallingPlan": {
                        "PhoneFeeType": "0",
                        "PhoneFeeUrl": None,
                        "Plans": [],
                        "MobilePhoneFeeUrl": None
                    },
                    "MobileDevicePrice": {
                        "PhoneDevicePrice": "0",
                        "PhoneSupportDiscount": "0",
                        "MakerSupportDiscount": "0",
                        "TeleComSupportDiscount": "0",
                        "PhoneAddDiscount": "0",
                        "PhoneInstallmentPrice": "0"
                    },
                    "Stock": {
                        "InputType": "1",
                        "GoodsCount": "0",
                        "SiteGoodsCountNo": "0",
                        "BuyableQuantityType": "0",
                        "BuyableQuantity": "0",
                        "BuyableQuantityDay": "0",
                        "GoodsCountIAC": "0",
                        "GoodsCountGMKT": "0",
                        "RemainCountIAC": "0",
                        "RemainCountGMKT": "0",
                        "OldGoodsCount": "0",
                        "OldGoodsCountIAC": "0",
                        "OldGoodsCountGMKT": "0"
                    },
                    "Options": {
                        "InputType": "1",
                        "OptVerType": "0",
                        "OptVerTypeIAC": "0",
                        "OptVerTypeGMKT": "0",
                        "JsonData": None,
                        "JsonDataIAC": None,
                        "JsonDataGMKT": None,
                        "JsonDataLegacy": None
                    },
                    "OrderOption": {
                        "GoodsNo": None,
                        "OptType": "0",
                        "StockMngIs": None,
                        "UnifyStockIs": None,
                        "OptionNameInfo": {
                            "OptName1": None,
                            "RcmdOptNo1": None,
                            "OptName2": None,
                            "RcmdOptNo2": None,
                            "OptName3": None,
                            "RcmdOptNo3": None,
                            "OptName4": None,
                            "RcmdOptNo4": None,
                            "OptName5": None,
                            "RcmdOptNo5": None,
                            "OptionNameLangList": None
                        },
                        "OptionInfoList": []
                    },
                    "Additions": {
                        "InputType": "1",
                        "JsonData": None,
                        "JsonDataIAC": None,
                        "JsonDataGMKT": None,
                        "JsonDataLegacy": None,
                        "CommonGoodsNo": None,
                        "IsUseCommonGoods": False
                    },
                    "AddonService": {
                        "AddonServiceUseType": "0",
                        "AddonServiceList": []
                    },
                    "SellingPeriod": {
                        "InputType": "1",
                        "IAC": {
                            "StartDate": f"{current_time}T02:33:33.667Z",
                            "StartDateSpecified": False,
                            "EndDate": f"{current_time}T02:33:33.667Z",
                            "EndDateSpecified": False
                        },
                        "GMKT": {
                            "StartDate": f"{current_time}T02:33:33.667Z",
                            "StartDateSpecified": False,
                            "EndDate": f"{current_time}T02:33:33.667Z",
                            "EndDateSpecified": False
                        },
                        "History": []
                    },
                    "PreSale": {
                        "UseSettingIAC": False,
                        "SaleStartDateIAC": f"{current_time}T02:33:33.667Z"
                    },
                    "GoodsImage": {
                        "AdditionalImagesStr": None,
                        "PrimaryImage": {
                            "Operation": "0",
                            "Url": None,
                            "BigImage": False,
                            "Seq": "0",
                            "ImageSourceCode": "0",
                            "ImageSourceOriginId": None
                        },
                        "ListImage": {
                            "Operation": "0",
                            "Url": None,
                            "BigImage": False,
                            "Seq": "0",
                            "ImageSourceCode": "0",
                            "ImageSourceOriginId": None
                        },
                        "ExpandedImage": {
                            "Operation": "0",
                            "Url": None,
                            "BigImage": False,
                            "Seq": "0",
                            "ImageSourceCode": "0",
                            "ImageSourceOriginId": None
                        },
                        "FixedImage": {
                            "Operation": "0",
                            "Url": None,
                            "BigImage": False,
                            "Seq": "0",
                            "ImageSourceCode": "0",
                            "ImageSourceOriginId": None
                        },
                        "AdditionalImages": [
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            },
                            {
                                "Operation": "0",
                                "Url": None,
                                "BigImage": False,
                                "Seq": "0",
                                "ImageSourceCode": "0",
                                "ImageSourceOriginId": None
                            }
                        ],
                        "AdditionalImagesSite": "0"
                    },
                    "DescriptionType": "2",
                    "DescriptionTypeSpecified": False,
                    "Description": {
                        "InputType": "1",
                        "Text": None,
                        "TextIAC": None,
                        "TextGMKT": None
                    },
                    "NewDescription": {
                        "InputType": "1",
                        "Text": None,
                        "IsEditor": False,
                        "TextEng": None,
                        "IsEditorEng": False,
                        "TextChn": None,
                        "IsEditorChn": False,
                        "TextJpn": None,
                        "IsEditorJpn": False,
                        "TextIAC": None,
                        "TextGMKT": None,
                        "TextAdd": None,
                        "TextAddEng": None,
                        "TextAddChn": None,
                        "TextAddJpn": None,
                        "TextAddIAC": None,
                        "TextAddGMKT": None,
                        "TextPrmt": None,
                        "TextPrmtIAC": None,
                        "TextPrmtGMKT": None,
                        "OuterShareYn": None,
                        "OuterShareUrl": None,
                        "OuterShareNew": False,
                        "Height": "0"
                    },
                    "ItemCode": str(pi_item.TaobaoID),
                    "CustCategoryNo": "0",
                    "CustCategory": None,
                    "ExpiryDate": None,
                    "ExpiryDateSpecified": False,
                    "LaunchingDate": None,
                    "LaunchingDateSpecified": False,
                    "ManufacturedDate": None,
                    "ManufacturedDateSpecified": False,
                    "Origin": {
                        "ProductType": "",
                        "Type": "0",
                        "Name": None,
                        "Code": None,
                        "IsMultipleOrigin": False
                    },
                    "LegacyRawMaterials": None,
                    "RawMaterials": None,
                    "Capacity": {
                        "Volume": None,
                        "Unit": "0",
                        "IsMultipleVolume": False
                    },
                    "Manual": None,
                    "ECoupon": {
                        "MoneyType": "0",
                        "Price": "0",
                        "Ratio": "0",
                        "CouponName": None,
                        "ExpireType": "0",
                        "Expire1StartDate": f"{current_time}T02:33:33.667Z",
                        "Expire1EndDate": f"{current_time}T02:33:33.667Z",
                        "Expire2Start": "0",
                        "Expire2Duration": "0",
                        "UseTermType": "0",
                        "UseTerm1StartDate": f"{current_time}T02:33:33.667Z",
                        "UseTerm1EndDate": f"{current_time}T02:33:33.667Z",
                        "UseTerm2Start": "0",
                        "UseTerm2Duration": "0",
                        "isDiffDate": False,
                        "CouponTemplate": "0",
                        "CouponImageUrl": None,
                        "DownloadTemplate": "0",
                        "DownloadImageUrl": None,
                        "ApplyPlace": None,
                        "ApplyPlaceKind": "BranchAddress",
                        "AddressNo": None,
                        "IsInformByAddress": False,
                        "Address": None,
                        "IsInformByURL": False,
                        "URL": None,
                        "ApplyPlacePriority": "0",
                        "MobileUseInfo": None,
                        "MobileHelpDeskphoneNo": None,
                        "TelephoneNo": None,
                        "AdditionalBenefit": None,
                        "HasRestrictCondition": False,
                        "RestrictCondition": None,
                        "Guide": None,
                        "PublicationCorp": None,
                        "PublicationCorpURL": None,
                        "IsCustomerNameView": False,
                        "Period": "0"
                    },
                    "DeliveryInfo": {
                        "CommonDeliveryUseYn": False,
                        "InvalidDeliveryInfo": False,
                        "CommonDeliveryWayOPTSEL": "0",
                        "GmktDeliveryWayOPTSEL": "0",
                        "IsCommonGmktUnifyDelivery": False,
                        "GmktDeliveryCOMP": None,
                        "IacDeliveryCOMP": None,
                        "IsCommonVisitTake": False,
                        "IsCommonQuickService": False,
                        "IsCommonIACPost": False,
                        "CommonIACPostType": "0",
                        "CommonIACPostPaidPrice": "0",
                        "IsGmktVisitTake": False,
                        "IsGmktQuickService": False,
                        "IsGmktTodayDEPAR": False,
                        "IsGmktTodayDEPARAgree": False,
                        "IsGmktVisitReceiptTier": False,
                        "MountBranchGroupSeq": "0",
                        "CommonVisitTakeType": "0",
                        "CommonVisitTakePriceDcAmnt": "0",
                        "CommonVisitTakeFreeGiftName": None,
                        "CommonVisitTakeADDRNo": None,
                        "CommonQuickServiceCOMPName": None,
                        "CommonQuickServicePhone": None,
                        "CommonQuickServiceDeliveryEnableRegionNo": None,
                        "ShipmentPlaceNo": None,
                        "DeliveryFeeType": "0",
                        "BundleDeliveryYNType": None,
                        "BundleDeliveryTempNo": None,
                        "EachDeliveryFeeType": "0",
                        "EachDeliveryFeeQTYEachGradeType": "0",
                        "DeliveryFeeTemplateJSON": None,
                        "EachDeliveryFeePayYn": "0",
                        "IsCommonGmktEachADDR": False,
                        "ReturnExchangeADDRNo": None,
                        "OldReturnExchangeADDR": None,
                        "OldReturnExchangeADDRTel": None,
                        "OldReturnExchangeSetupDeliveryCOMPName": None,
                        "OldReturnExchangeDeliveryFeeStr": None,
                        "ExchangeADDRNo": None,
                        "ReturnExchangeSetupDeliveryCOMP": None,
                        "ReturnExchangeSetupDeliveryCOMPName": None,
                        "ReturnExchangeDeliveryFee": "0",
                        "ReturnExchangeDeliveryFeeStr": None,
                        "IacTransPolicyNo": "0",
                        "GmktTransPolicyNo": "0",
                        "BackwoodsDeliveryYn": None,
                        "IsTplConvertible": False
                    },
                    "IsAdultProduct": False,
                    "IsVATFree": False,
                    "ASInfo": None,
                    "CertIAC": {
                        "HasIACCertType": False,
                        "MedicalInstrumentCert": {
                            "ItemLicenseNo": None,
                            "AdDeliberationNo": None,
                            "IsUse": None,
                            "CertificationOfficeName": None,
                            "CertificationNo": None,
                            "Operation": "0"
                        },
                        "BroadcastEquipmentCert": {
                            "BroadcastEquipmentIs": False,
                            "AddtionalConditionIs": False,
                            "IsUse": None,
                            "CertificationOfficeName": None,
                            "CertificationNo": None,
                            "Operation": "0"
                        },
                        "FoodCert": {
                            "IsUse": None,
                            "CertificationOfficeName": None,
                            "CertificationNo": None,
                            "Operation": "0"
                        },
                        "HealthFoodCert": {
                            "AdDeliberationNo": None,
                            "IsUse": None,
                            "CertificationOfficeName": None,
                            "CertificationNo": None,
                            "Operation": "0"
                        },
                        "EnvironmentFriendlyCert": {
                            "CertificationType": None,
                            "isIACEnvironmentFriendlyCertType": False,
                            "isGMKTEnvironmentFriendlyCertType": False,
                            "CertBizType": None,
                            "ProducerName": None,
                            "PresidentInfoNA": None,
                            "RepItemName": None,
                            "InfoHT": None,
                            "CertGroupType": None,
                            "InfoEM": None,
                            "CertStartDate": None,
                            "CertEndDate": None,
                            "InfoAD": None,
                            "CertificationOfficeName": None,
                            "CertificationExpiration": None,
                            "IsUse": None,
                            "CertificationNo": None,
                            "Operation": "0"
                        },
                        "SafeCert": {
                            "SafeCertType": "0",
                            "AuthItemType": "0",
                            "CertificationNo": None,
                            "IsUse": None,
                            "CertificationOfficeName": None,
                            "Operation": "0"
                        },
                        "ChildProductSafeCert": {
                            "SafeCertType": "0",
                            "ChangeType": "0",
                            "SafeCertDetailInfoList": []
                        },
                        "IntegrateSafeCert": {
                            "ItemNo": None,
                            "IntegrateSafeCertGroupList": []
                        }
                    },
                    "CertificationNoGMKT": None,
                    "LicenseSeqGMKT": [],
                    "OfficialNotice": {
                        "NoticeItemGroupNo": "0",
                        "NoticeItemCodes": []
                    },
                    "ItemWeight": "0",
                    "SkuList": [],
                    "SkuMatchingVerNo": "0",
                    "RentalAddInfo": {
                        "OutWarehousePrice": "0",
                        "OutWarehousePriceSpecified": False,
                        "MonthRentalPrice": "0",
                        "MonthRentalPriceSpecified": False,
                        "DutyUseDays": "0",
                        "DutyUseDaysSpecified": False,
                        "InstallPrice": "0",
                        "InstallPriceSpecified": False,
                        "RegistPrice": "0",
                        "RegistPriceSpecified": False,
                        "DutyUseDaysPrice": "0",
                        "DutyUseDaysPriceSpecified": False,
                        "OwnershipDays": "0",
                        "OwnershipDaysSpecified": False,
                        "OwnershipDaysPrice": "0",
                        "OwnershipDaysPriceSpecified": False
                    },
                    "CertificationTextGMKT": None,
                    "LicenseTextGMKT": None,
                    "InventoryNo": None,
                    "SingleSellerShop": None,
                    "IsUseSellerFunding": None,
                    "IsGift": None,
                    "ConsultingDetailList": [],
                    "Install": {
                        "IsInstall": False,
                        "InstallMakerId": "0",
                        "InstallModelCode": None
                    }
                },
                "SYIStep3": {
                    "G9RegisterCommand": "0",
                    "IsG9Goods": False,
                    "IsOnlyG9Goods": False,
                    "SellerDiscount": {
                        "DiscountAmtIac1": "0",
                        "DiscountAmtIac2": "0",
                        "DiscountAmtGmkt1": "0",
                        "DiscountAmtGmkt2": "0",
                        "IsSellerDCExceptionIacItem": False,
                        "IsSellerDCExceptionGmktItem": False,
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "DiscountType": "1",
                        "DiscountTypeSpecified": False,
                        "DiscountAmt": "0",
                        "DiscountAmtSpecified": False,
                        "DiscountAmt1": "0",
                        "DiscountAmt1Specified": False,
                        "DiscountAmt2": "0",
                        "DiscountAmt2Specified": False,
                        "StartDate": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecified": False,
                        "EndDate": "9999-12-31T14:59:59.999Z",
                        "EndDateSpecified": False,
                        "DiscountTypeIac": "0",
                        "DiscountTypeSpecifiedIac": False,
                        "StartDateIac": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecifiedIac": False,
                        "EndDateIac": "9999-12-31T14:59:59.999Z",
                        "IacEndDateSpecified": False,
                        "DiscountAmtIac": "0",
                        "DiscountAmtSpecifiedIac": False,
                        "DiscountTypeGmkt": "0",
                        "DiscountTypeSpecifiedGmkt": False,
                        "StartDateGmkt": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecifiedGmkt": False,
                        "EndDateGmkt": "9999-12-31T14:59:59.999Z",
                        "EndDateSpecifiedGmkt": False,
                        "DiscountAmtGmkt": "0",
                        "DiscountAmtSpecifiedGmkt": False
                    },
                    "FreeGift": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "IsOnly": "1",
                        "IsOnlySpecified": False,
                        "IacFreeGiftName": "",
                        "GmkFreeGiftName": ""
                    },
                    "IsPcs": True,
                    "IsPcsSpecified": False,
                    "IacPcsCoupon": True,
                    "IacPcsCouponSpecified": False,
                    "GmkPcsCoupon": True,
                    "GmkPcsCouponSpecified": False,
                    "GmkBargain": False,
                    "GmkBargainSpecified": False,
                    "IacFreeWishKeyword": [],
                    "IacDiscountAgreement": True,
                    "IacDiscountAgreementSpecified": False,
                    "GmkDiscountAgreement": True,
                    "GmkDiscountAgreementSpecified": False,
                    "GmkOverseaAgreementSeller": True,
                    "GmkOverseaAgreementSellerSpecified": False,
                    "IacBuyerBenefit": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.667Z",
                        "EndDateSpecified": False,
                        "IsMemberDiscount": False,
                        "IsMemberDiscountSpecified": False,
                        "MemberDiscountPrice": "0",
                        "MemberDiscountPriceSpecified": False,
                        "IsBulkDiscount": False,
                        "IsBulkDiscountSpecified": False,
                        "BulkDiscountQty": "0",
                        "BulkDiscountQtySpecified": False,
                        "BulkDiscountPrice": "0",
                        "BulkDiscountPriceSpecified": False
                    },
                    "GmkBuyerBenefit": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "Type": "",
                        "StartDate": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.667Z",
                        "EndDateSpecified": False,
                        "ConditionType": "",
                        "ConditionValue": "0",
                        "ConditionValueSpecified": False,
                        "Unit": "",
                        "UnitValue": "0",
                        "UnitValueSpecified": False,
                        "WhoFee": ""
                    },
                    "IacDonation": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.667Z",
                        "EndDateSpecified": False,
                        "DonationPrice": "0",
                        "DonationPriceSpecified": False,
                        "DonationMaxPrice": "0",
                        "DonationMaxPriceSpecified": False,
                        "DonationType": ""
                    },
                    "GmkDonation": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.667Z",
                        "EndDateSpecified": False,
                        "DonationPrice": "0",
                        "DonationPriceSpecified": False,
                        "DonationMaxPrice": "0",
                        "DonationMaxPriceSpecified": False,
                        "DonationType": ""
                    },
                    "IacSellerPoint": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "PointType": "1",
                        "PointTypeSpecified": False,
                        "Point": "0",
                        "PointSpecified": True
                    },
                    "GmkSellerMileage": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "PointType": "1",
                        "PointTypeSpecified": False,
                        "Point": "0",
                        "PointSpecified": True
                    },
                    "IacChance": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "StartDate": f"{current_time}T02:33:33.667Z",
                        "StartDateSpecified": False,
                        "EndDate": "2023-09-26T02:33:33.667Z",
                        "EndDateSpecified": False,
                        "ChanceQty": "0"
                    },
                    "IacBrandShop": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "LCategoryCode": "",
                        "MCategoryCode": "",
                        "SCategoryCode": "",
                        "BrandCode": "",
                        "BrandName": "",
                        "BrandImage": []
                    },
                    "GmkBizOn": {
                        "IsUsed": "2",
                        "IsUsedSpecified": False,
                        "LCategoryCode": "",
                        "MCategoryCode": "",
                        "SCategoryCode": ""
                    },
                    "IacAdditional": [],
                    "GmkAdditional": [],
                    "IacPayWishKeyword": [],
                    "IacAdPromotion": {
                        "CategorySmart": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "CategoryPower": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "Best100Smart": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "Chance": {
                            "LCategoryPrice": "0",
                            "LCategoryPriceSpecified": False,
                            "MCategoryPrice": "0",
                            "MCategoryPriceSpecified": False,
                            "SCategoryPrice": "0",
                            "SCategoryPriceSpecified": False,
                            "BestMainPrice": "0",
                            "BestMainPriceSpecified": False
                        },
                        "AccessMode": "1",
                        "AccessModeSpecified": False
                    },
                    "GmkAdPromotion": {
                        "LargePlus": "0",
                        "LargePlusSpecified": False,
                        "LargePowerMini": "0",
                        "LargePowerMiniSpecified": False,
                        "LargeBestPower": "0",
                        "LargeBestPowerSpecified": False,
                        "MiddlePlus": "0",
                        "MiddlePlusSpecified": False,
                        "MiddlePower": "0",
                        "MiddlePowerSpecified": False,
                        "MiddleDetailPower": "0",
                        "MiddleDetailPowerSpecified": False,
                        "MiddleBestPower": "0",
                        "MiddleBestPowerSpecified": False,
                        "SmallPlus": "0",
                        "SmallPlusSpecified": False,
                        "SmallPower": "0",
                        "SmallPowerSpecified": False
                    },
                    "OverseaAgree": {
                        "RegType": None,
                        "Gubun": "0",
                        "GubunSpecified": False,
                        "OverseaDisAgreeIs": False
                    },
                    "IsLeaseAvailableInIac": False,
                    "GmktShopGroupCd": "0",
                    "IsIacFreeWishKeyword": False,
                    "IacFreeWishKeywordEndDate": False,
                    "IacCommissionRate": "0",
                    "IacCommissionRateOpenMarket": "0",
                    "IacCommissionRateGroupBy": "0",
                    "IsIacFeeDiscountItem": False,
                    "IsDispExclude": True,
                    "IsDispExcludeSpecified": False
                },
                "IsSingleGoods": False,
                "SiteGoodsNoIac": None,
                "SiteGoodsNoGmkt": None,
                "GoodsKind": None,
                "BarCode": None,
                "IsSiteDisplayIac": False,
                "IsSiteDisplayGmkt": False,
                "SellingStatusIac": None,
                "SellingStatusGmkt": None,
                "MasterId": str(masterid),
                "LoginId": str(accountid),
                "IsDeleteGroup": False,
                "EditorUseYn": None,
                "SdInfo": {
                    "SdCategoryCode": None,
                    "SdBrandName": None,
                    "SdMakerId": None,
                    "SdMakerName": None,
                    "SdBrandId": None,
                    "SdProductBrandId": None,
                    "SdProductBrandName": None,
                    "EpinCodeList": [],
                    "SdAttrMatchingList": [],
                    "SdBasicAttrMatching": {
                        "SalesUnit": "0",
                        "SalesUnitSpecified": False,
                        "EaPerBox": "0",
                        "EaPerBoxSpecified": False,
                        "EaPerPack": "0",
                        "EaPerPackSpecified": False,
                        "TotalEa": "0",
                        "TotalEaSpecified": False,
                        "TotalUnitAmount": "0",
                        "TotalUnitAmountSpecified": False,
                        "UnitAttrSeq": "0",
                        "UnitAttrSeqSpecified": False,
                        "UnitAttrValueSeq": "0",
                        "UnitAttrValueSeqSpecified": False
                    },
                    "EpinCreateReqBarcode": None,
                    "EpinCreateReqModelName": None,
                    "EpinCreateReqModelNo": None
                },
                "BuyableQuantityMappingType": "1",
                "IsIacConvertToSingleGoods": False,
                "IsGmktConvertToSingleGoods": False,
                "AdminId": None
            }
        }

        url = "https://www.esmplus.com/Sell/SingleGoods/Save"
        payload = json.dumps(productjson)
        headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Cookie': esmcookie,
        'Origin': 'https://www.esmplus.com',
        'Referer': 'https://www.esmplus.com/Sell/SingleGoods?menuCode=TDM395',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Brave";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        # Parse the HTML content using Beautiful Soup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract the required values
        auction_product_number = soup.find('span', class_='ls0').text.strip()
        gmarket_product_number = soup.find_all('span', class_='ls0')[1].text.strip()
        
        return auction_product_number.replace("D", ""), gmarket_product_number
    
    except:
        print(traceback.format_exc())
        return 1,1



def delete_product(pi_item, esmcookie):
    headers1 = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
        'Connection': 'keep-alive',
        'Cookie': esmcookie,
        'Origin': 'https://www.esmplus.com',
        'Referer': 'https://www.esmplus.com/Sell/SingleGoods?cmd=2&goodsNo=2690663472&menuCode=TDM398',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Brave";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    
    #상품 검색하기
    product_resp = requests.post("https://www.esmplus.com/Sell/SingleGoodsMng/GetSingleGoodsList",
        headers=headers1,
        data = {
            "paramsData" : '{"Keyword":"","SiteId":"0","CategorySiteId":-1,"CategoryCode":"","CategoryLevel":"","TransPolicyNo":0,"StatusCode":"","SearchDateType":0,"SearchStartDate":"","SearchEndDate":"","SellerId":"","SellerSiteId":"","StockQty":-1,"SellPeriod":0,"DiscountUseIs":-1,"DeliveryFeeApplyType":0,"OptAddDeliveryType":0,"OptSelUseIs":-1,"PremiumEnd":0,"PremiumPlusEnd":0,"FocusEnd":0,"FocusPlusEnd":0,"GoodsIdType":"S","GoodsIds":"'+str(pi_item.GmarketID)+'","ShopCateReg":-1,"IsTPLUse":"","SellMinPrice":0,"SellMaxPrice":0,"OrderByType":11,"GroupOrderByType":1,"IsGroupUse":"","IsApplyEpin":"","IsConvertSingleGoods":"","DisplayLimityn":"","IsGift":""}',
            "page" : 1,
            "start" : 0,
            "limit" : 30
        })
    
    product_detail = product_resp.json()["data"][0]
    product_params = {
        "param": [
            {
            "SingleGoodsNo": product_detail["SingleGoodsNo"],
            "ShowIAC": True,
            "ShowGMKT": True,
            "popupParamModel": [
                {
                "SiteId": 1, #옥션거
                "GoodsNo": product_detail["SingleGoodsNo"],
                "SiteGoodsNo": product_detail["SiteGoodsNoIAC"],
                "SellerCustNo": product_detail["SellerCustNoIAC"],
                "SellerId": product_detail["SellerIdIAC"],
                "ItemName": product_detail["GoodsName"],
                "SellType": product_detail["SellType"],
                "SellPrice": product_detail["SellPriceIAC"],
                "StockQty": product_detail["StockQtyIAC"],
                "DispEndDate": "2024-02-03T14:59:59.000Z",
                "SiteCategoryCode": product_detail["CategoryCodeIAC"],
                "DistrType": product_detail["DistrType"],
                "GroupNo": product_detail["GroupNo"],
                "StatusCode": product_detail["StatusCodeIAC"]
                },
                {
                "SiteId": 2,
                "GoodsNo": product_detail["SingleGoodsNo"],
                "SiteGoodsNo": product_detail["SiteGoodsNoGMKT"],
                "SellerCustNo": product_detail["SellerCustNoGMKT"],
                "SellerId": product_detail["SellerIdGMKT"],
                "ItemName": product_detail["GoodsName"],
                "SellType": product_detail["SellType"],
                "SellPrice": product_detail["SellPriceGMKT"],
                "StockQty": product_detail["StockQtyGMKT"],
                "DispEndDate": "2024-02-03T14:59:59.000Z",
                "SiteCategoryCode": product_detail["CategoryCodeGMKT"],
                "DistrType": product_detail["DistrType"],
                "GroupNo": product_detail["GroupNo"],
                "StatusCode": product_detail["StatusCodeGMKT"]
                }
            ]
            }
        ],
        "siteType": "0"
    }
    

    #판매 상태 변경하기
    change_status_resp = requests.post("https://www.esmplus.com/Sell/SingleGoodsMng/SetSellStateChangeStop",
        headers=headers1,
        json = product_params
    )
    
    print(change_status_resp.text)
    
    #상품 삭제하기
    delete_request = requests.post("https://www.esmplus.com/Sell/SingleGoodsMng/SetSellStateDelete",
                  headers = headers1,
                  json = product_params)
    
    print(delete_request.text)