
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
import random
import string
import copy

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

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
    url = "https://seller.interpark.com/api/product/file/upload"

    payload = {'accept': '.jpg,.png',
    'isProductImage': 'true',
    'limit': '1048576',
    'width': '600',
    'height': '600'}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    return response.json()["data"]
    
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

def string_to_cookie_dict(cookies_string):
    cookie_dict = {}
    if cookies_string:
        cookies_list = cookies_string.split("; ")
        for cookie in cookies_list:
            cookie_parts = cookie.split("=")
            if len(cookie_parts) == 2:
                cookie_dict[cookie_parts[0]] = cookie_parts[1]
    return cookie_dict

def product_upload(pi_item_dup, interparkcookie):
    try:
        pi_item = copy.deepcopy(pi_item_dup)
        current_time, future_time = generate_time_strings()
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': interparkcookie,
            'Origin': 'https://seller.interpark.com',
            'Referer': 'https://seller.interpark.com/views/products/regist',
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
        option_minprice = min(option_prices)
        pi_item.ProductOriginPrice = option_minprice

        pid_ls = []
        for skuprops in pi_item.ProductOptions["sku_props"]:
            pid = skuprops["pid"]
            for value in skuprops["values"]:
                pid_ls.append((pid + ":" + value["vid"], value["optioncode"]))

        #옵션 정보 정렬
        productOption = []
        optionCombinations = []
        optionorder = 1
        productOptionInsertYn = "Y"
        if len(pi_item.ProductOptions["sku_props"]) > 0:
            for num, sku_price in enumerate(pi_item.ProductOptions["sku_price"]):
                optioncombi = {}
                productcombi = {}
                if num == 0:
                    optioncombi.update({"optItemNm3": ""})
                    for itemnum, op in enumerate(pi_item.ProductOptions["sku_props"]):
                        if itemnum == 0:
                            optioncombi.update({
                                "optNm": op["prop_name"],
                            })
                        elif itemnum == 1:
                            optioncombi.update({
                                "optNm2": op["prop_name"],
                            })
                props_ids = sku_price["props_ids"].split(';')
                
                for i, props_id in enumerate(props_ids):
                    optionname = str(search_value(pid_ls, props_id))
                    if i == 0:
                        productcombi.update({
                        "optItemNm": optionname,
                        })
                        optioncombi.update({
                        "optItemNm": optionname,
                        })
                    elif i == 1:
                        productcombi.update({
                            "optItemNm2": optionname
                        })
                        optioncombi.update({
                            "optItemNm2": optionname
                        })
                stockcount = sku_price["stock"]
                if stockcount == 0:
                    stockcount = 1
                
                optioncombi.update({
                "optNo": "0",
                "prdNo": "0",
                "optTp": "01",
                "addPrice": str(sku_price["sale_price"] - pi_item.ProductOriginPrice),
                "salePossRestQty": str(stockcount),
                "saleLmtQty": str(stockcount),
                "externalPrdNo": str(sku_price["skuid"])
                })
                
                productOption.append(productcombi)
                optionCombinations.append(optioncombi)

        else:
            productOption = None
            optionCombinations.append({
                "optItemNm3": ""
            })
            productOptionInsertYn = "N"
        mainimg = upload_img(pi_item.ProductMainImage, headers)


        bigImgList = []
        for image in pi_item.ProductSubImages.split(",")[1:]:
            uploadedimg = upload_img(image, headers)
            bigImgList.append({
                "fileFnm": uploadedimg["filename"],
                "fileName": uploadedimg["originFilename"],
                "upldFileTp": "05",
                "imgUpdateYn": "Y"
            })
        productjson = {
            "product": {
            "productDetailDto": {
                "supplyEntrNo": string_to_cookie_dict(interparkcookie)["entrNo"], #이게 계정을 결정하는 정보임
                "supplyCtrtSeq": string_to_cookie_dict(interparkcookie)["supplyCtrtSeq"], #개인사업자면 2? 법인사업자면 1?
                "prdAttbt": "01",
                "minOrdQty": "1",
                "jobRoleNo": "9999",
                "giftInfo": "",
                "oldUseMonth": "",
                "abroadBsYn": "I",
                "salePossRestQty": "400",
                "perordRstrQty": "",
                "optPrirTp": "01",
                "addOptStkMgtYn": "",
                "addQtyUseTp": "01",
                "delvMthd": "01",
                "rtnDelvNo": "0",
                "prdrtnCostUseYn": "N",
                "rtndelvCost": "",
                "asYn": "불가",
                "prdOriginTp": "중국산",
                "prdModelNo": "",
                "externalPrdNo": str(pi_item.TaobaoID),
                "importLicense": "",
                "isbn": "",
                "importNo": "",
                "importNoFileUrl": "",
                "importNoFileName": ""
            },
            'prdNo': '0',
            'iciDelvYn': 'N',
            'sellerInfoOutYn': 'Y',
            'prdTp': '01',
            'prdConstTp': '01',
            'stdClsNo': '008006008004',
            'prdStat': '01',
            "prdNm": pi_item.ProductName[:50],
            "mainImg": mainimg["filename"],
            "mainImgFileName": mainimg["originFilename"],
            "saleStrDts": f"{current_time}T00:00:00+09:00",
            "saleEndDts": "9999-12-31T23:59:59+09:00",
            "prdReleaseDt": "",
            "saleStatTp": "01",
            "spsaleYn": "",
            "productPriceDto": {
                "mktPr": "",
                "saleUnitcost": str(option_minprice),
                "mgtUnitcost": str(int(option_minprice * 0.87)),
                "mgtUnitcostMargRt": "13",
                "unitcostCalStd": "2",
                "entrPoint": "",
                "bizdeptPoint": "",
                "taxTp": "01"
            },
            "salesRightUseQty": "",
            "optStkMgtYn": "Y",
            "smOptYn": "N",
            "smOptTeplTp": "01",
            "globalSaleYn": "N",
            "stdDelvwhDt": "05",
            "proddelvCostUseYn": "Y",
            "delvCostApplyTp": "",
            "stdQty": "",
            "delvCost": "",
            "freedelvStdCnt": "",
            "delvAmtPayTp": "03",
            "delvCostDispYn": "Y",
            "delvCostNote": "",
            "delvPlcNo": "1018868",
            "prdKeywd": pi_item.ProductTags,
            "ordAgeRstrYn": "N",
            "ordRstrAge": ""
            },
            "copyRegistPrdNo": "",
            "mainDisplay": {
            "dispNo": "001830228016",
            "shopNo": "0000100000"
            },
            "directSaleYn": "Y",
            "globalProduct": {
            "prdUsNm": "",
            "prdCnNm": "",
            "prdJaNm": "",
            "prdWeight": "",
            "prdUsKeywd": "",
            "prdCnKeywd": "",
            "prdJaKeywd": ""
            },
            "productImageInfo": {
            "bigImgList": bigImgList
            },
            "mainImg": "",
            "zoomImg": "",
            "listImg": "",
            "listImgStill": "",
            "salePeriodSetYn": "N",
            "mobileSaleCond": {
            "planCd": "",
            "planTxt": ""
            },
            "hpPrdUrlDto": {
            "applyUrl": "",
            "checkUrl": ""
            },
            "rentalSaleCond": {
            "suggestedPrice": "",
            "suggestedPriceYn": "Y",
            "dutyUsePeriod": "",
            "priceTp": "D",
            "installPrice": "",
            "registerPriceTp": "D",
            "registerPrice": ""
            },
            "entrDcPrice": {
            "useYn": "",
            "dcTp": "1",
            "dcNum": "",
            "dcStrDt": "",
            "dcEndDt": ""
            },
            "productUnitCostInfo": {
            "unitTp": "",
            "unitQuantity": ""
            },
            "saleCountLimit": "N",
            "productOptionInsertYn": productOptionInsertYn,
            "productOption": productOption,
            "productOptionList": optionCombinations,
            "addOptionInsertYn": "N",
            "addQtyUseYn": "N",
            "etc": "0",
            "specialNote": {
            "prdNo": "",
            "spcase": ""
            },
            "productDtlList": [
            {
                "dtlTp": "04",
                "dtl": pi_item.ProductHtmlDescription,
                "prdDtlNo": ""
            },
            {
                "dtlTp": "09",
                "dtl": ""
            },
            {
                "dtlTp": "10",
                "dtl": ""
            }
            ],
            "templateDetail": "1",
            "globalProductDtlList": [
            {
                "nationCd": "EN",
                "dtl": ""
            },
            {
                "nationCd": "CN",
                "dtl": ""
            },
            {
                "nationCd": "JA",
                "dtl": ""
            }
            ],
            "productCertInfoAll": {
            "productCertMasterDto": {
                "status": "N"
            }
            },
            "ecoCertOrgInput": "",
            "ecoCertNoInput": "",
            "repOrgInput": "",
            "repNoInput": "",
            "bookProduct": {
            "authorNames": "",
            "translatorNames": "",
            "illustratorNames": "",
            "publicationDate": "",
            "isbn13": "",
            "isbn10": "",
            "issn": "",
            "cultureDeductionYn": "N"
            },
            "productInfoNotiDtoList": [
            {
                "infoGroupNo": "35",
                "infoSubNo": "3501",
                "infoType": "R1",
                "infoCd": "C",
                "infoTx": ""
            },
            {
                "infoSubNo": "3502",
                "infoType": "R1",
                "infoCd": "C",
                "infoTx": ""
            },
            {
                "infoSubNo": "3503",
                "infoType": "R1",
                "infoCd": "C",
                "infoTx": ""
            },
            {
                "infoSubNo": "3504",
                "infoType": "R1",
                "infoCd": "C",
                "infoTx": ""
            },
            {
                "infoSubNo": "3505",
                "infoType": "R1",
                "infoCd": "C",
                "infoTx": ""
            },
            {
                "infoSubNo": "3506",
                "infoType": "M1",
                "infoCd": "M",
                "infoTx": ""
            }
            ],
            "infoCd0": "C",
            "infoCd1": "C",
            "infoCd2": "C",
            "infoCd3": "C",
            "infoCd4": "C",
            "deliveryInfo": {
            "productDelvEtcDto": {
                "delvAttbt": "01",
                "delvAttbtNo": "",
                "customMadeYn": "NORMAL",
                "installCostYn": "N",
                "customPrdYn": "NORMAL"
            },
            "prdDelvExctYn": "N",
            "addtionDelvcostPolicyDto": {
                "jejuDelvCost": "5000",
                "etcDelvCost": "5000"
            }
            },
            "searchAddrTxt": "",
            "dvdRecordProduct": {
            "artistNames": ""
            },
            "manufacturer": {
            "hdelvMafcEntrNm": "상세페이지참고",
            "hdelvMafcEntrNo": ""
            },
            "brand": {
            "brandNm": "",
            "brandNo": ""
            },
            "ippSubmitYn": "Y",
            "productIntfreeInfo": {
            "totalIntfreeInstmUseYn": "N",
            "freeRangeUseYn": "N",
            "maxInstmMonths": "3",
            "intfreeInstmStrDts": current_time.replace("-",""),
            "intfreeInstmEndDts": "",
            "oldIntfreeInstmStrDts": "",
            "oldIntfreeInstmEndDts": "",
            "oldListInstmMonths": ""
            },
            "sellerAdInfo": {
            "adNo": "96",
            "buyStrDt": "",
            "buyEndDt": "",
            "adAutoExtYn": "Y",
            "adBuyUnitCost": "",
            "adBuyRealCost": "",
            "adBuyDays": "",
            "advertiseYn": "N",
            "autoExtChangeYn": "",
            "adpId": ""
            }
        }
        sleep(2)
        productuploadres = requests.post("https://seller.interpark.com/api/products/save", headers=headers, json=productjson)

        if productuploadres.json()["code"] == 200:
            return productuploadres.json()["data"]["prdNo"]
        
        if "code" in productuploadres.json()["error"]:
            if productuploadres.json()["error"]["code"] == 2229:
                print("인터파크 이미지 업로드 오류 => 재시도 중...")
                return product_upload(pi_item_dup, interparkcookie)
            elif productuploadres.json()["error"]["code"] == 400:
                print(productuploadres.json())
                return 1
            
            else:
                print("UNKNOWN ERROR!!")
                print(productuploadres.json())
                return 1


    except Exception as e:
        print(e)
        return 1
        

def delete_product(pi_item, interparkcookie):
    headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': interparkcookie,
            'Origin': 'https://seller.interpark.com',
            'Referer': 'https://seller.interpark.com/views/products/regist',
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
    
    json_data = [
        {
            'prdNo': pi_item.InterparkID,
        },
    ]

    response = requests.post('https://seller.interpark.com/api/products/delete',  headers=headers, json=json_data).json()
    return response