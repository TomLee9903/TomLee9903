
import sys
sys.path.append('Module')
sys.path.insert(1, '/Module')
import scrapedb

import requests
from bs4 import BeautifulSoup
import json
import re



def combine_lists(*lists):
    result = []
    # Get the Cartesian product of the elements in the lists
    product = [[]]
    for lst in lists:
        product = [x + [y] for x in product for y in lst]
    # Combine the elements of each combination into a single string
    for p in product:
        combined = ';'.join(map(str, p))
        if combined[-1] == ';':
            combined = combined[:-1]
        result.append(combined)
    return result

def scrapeali(productid, cookiestr):
    headers = {
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
        'Referer': 'https://ko.aliexpress.com/',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
        'cookie': cookiestr
    }
    result = requests.get(f"https://ko.aliexpress.com/item/{str(productid)}.html", headers=headers)
    si = scrapedb.ScrapedItem()
    soup = BeautifulSoup(result.text, "html.parser")
    
    #상품 정보가 저장된 script를 찾아 json 형태로 파싱
    selected_script = None
    for script in soup("script"):
        if "window.runParams" in script.text[:100]:
            selected_script = script.text.split("data: ")[1].split("\n")[0].strip()
            break
    productjson = json.loads(selected_script)
    
    si.ProductID = productjson["productInfoComponent"]["id"]
    si.ProductName = productjson["productInfoComponent"]["subject"]
    si.ProductSoldCount = int(re.sub("[^0-9]", "", str(productjson["tradeComponent"]["formatTradeCount"])))
    si.ProductMainImage = productjson["imageComponent"]["imagePathList"][0]
    si.ProductSubImages = ",".join(productjson["imageComponent"]["imagePathList"])
    si.SellerID = productjson["sellerComponent"]["storeName"]
    si.TaobaoID = si.ProductID
    si.TaobaoName = si.ProductName
    si.TaobaoMainImage = si.ProductMainImage
    if "videoComponent" in productjson:
        si.TaobaoVideoUrl = f"https://video.aliexpress-media.com/play/u/ae_sg_item/{str(productjson['videoComponent']['videoUid'])}/p/1/e/6/t/10301/{str(productjson['videoComponent']['videoId'])}.mp4"

    descurl = productjson["productDescComponent"]["descriptionUrl"]

    response = requests.get(
        descurl,
        headers=headers
    )

    si.TaobaoDescription = re.sub('\s+',' ',response.text)
    si.Type = 2
    si.Uploader = "Aliexpress"


    sku_prop_list = []
    #Sku Props 생성
    sku_props = []
    for props in productjson["skuComponent"]["productSKUPropertyList"]:
        sku_order_list = []
        pid = props["skuPropertyId"]
        
        prop_name = props["skuPropertyName"]
        values = []
        for prop_value in props["skuPropertyValues"]:
            vid = prop_value["propertyValueId"]

            if pid == 200007763: #배송 국가 선택하는 메뉴 -> Default로 중국 설정해야함. 나머지는 제거하기
                if vid != 201336100: #중국만 배송 가능하도록 설정해야함.
                    continue

            name = prop_value["propertyValueDisplayName"]
            imageurl = ""
            if "skuPropertyImagePath" in prop_value:
                imageurl = prop_value["skuPropertyImagePath"]
            values.append({"vid": str(vid), "name": name, "imageUrl": imageurl})
            sku_order_list.append(f"{str(pid)}:{str(vid)}")
        sku_props.append({"pid": str(pid), "prop_name": prop_name, "values": values})
        sku_prop_list.append(sku_order_list)
        
    #Sku Price 생성
    sku_price = []
    for sku in productjson["priceComponent"]["skuPriceList"]:
        sku_id = sku["skuId"]
        if "skuActivityAmount" in sku["skuVal"]:
            sale_price = sku["skuVal"]["skuActivityAmount"]["value"]
            origin_price = sku["skuVal"]["skuActivityAmount"]["value"]
        else:
            sale_price = sku["skuVal"]["skuCalPrice"]
            origin_price = sku["skuVal"]["skuCalPrice"]
        stock = sku["skuVal"]["availQuantity"]
        propsid = sku["skuAttr"]
        
        parsestr = ""
        for substr in propsid.split(";"):
            parsestr += substr.split("#")[0] + ";"
        if parsestr[-1] == ";":
            parsestr = parsestr[:-1]
        
        sku_price.append({
            "skuid":  str(sku_id),
            "sale_price": str(sale_price),
            "origin_price": str(origin_price),
            "stock": stock,
            "props_ids": parsestr,
            "props_names": "",
        })

    
    #Sku Props Order 생성
    sku_props_order = combine_lists(*sku_prop_list)
    #Sku Props Order를 기반으로 Sku Price Order 생성
    sku_price_order = []
    for order in sku_props_order:
        for price in sku_price:
            if price["props_ids"] == order:
                sku_price_order.append(price)
                break
    
    optionjson = {
        "sku_props": sku_props,
        "sku_price": sku_price_order
    }
    
    pricelist = []
    for price in sku_price_order:
        pricelist.append(float(price["sale_price"]))
    
    si.ProductPrice = si.TaobaoPrice = min(pricelist)
    si.TaobaoOptions = optionjson
    
    return si

