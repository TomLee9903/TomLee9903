import string
import random
import urllib.parse
import json

def generate_random_string(length):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_random_guid():
    guid = f"SE-{generate_random_string(8)}-{generate_random_string(4)}-{generate_random_string(4)}-{generate_random_string(12)}"
    return guid

def image_element_generator(imageurl):
    parsedurl = urllib.parse.urlparse(imageurl)
    image_element = {
        "@ctype": "image",
        "src": imageurl,
        "path": parsedurl.path,
        "domain": parsedurl.scheme + "://" + parsedurl.netloc,
        "internalResource": False,
        "fileSize": 0,
        "width": 860,
        "widthPercentage": 0,
        "height": 1000,
        "fileName": "image.jpg",
        "align": "center",
        "contentMode": "fit",
        "origin": {
            "srcFrom": "local",
            "@ctype": "imageOrigin"
        },
        "layout": "default",
        "id": generate_random_guid(),
        "represent": False,
        "imageLoaded": True,
        "format": "normal",
        "displayFormat": "normal",
        "caption": None
    }
    return image_element

def text_cell_generator(text):
    text_element = {
        "@ctype": "text",
        "value": [
            {
                "@ctype": "paragraph",
                "nodes": [
                    {
                        "@ctype": "textNode",
                        "style": {
                            "@ctype": "nodeStyle",
                            "fontSizeCode": "fs34",
                            "bold": True
                        },
                        "value": text,
                        "id": generate_random_guid()
                    }
                ],
                "style": {
                    "@ctype": "paragraphStyle",
                    "align": "center"
                },
                "id": generate_random_guid()
            }
        ],
        "layout": "default",
        "id": generate_random_guid()
    }
    return text_element

def smarteditorgenerator(processed_options, description_imageurls):
    ###스마트에디터 함수 생성
    element_list = []
    #앞 이미지 추가
    element_list.append(image_element_generator("https://store.img11.co.kr/73065084/887ce9b0-9805-4ad0-9b7a-6c9b5ddc4ffb_1694272851639.jpg"))

    #옵션 정보 추가
    for prop in processed_options['sku_props']:
        element_list.append(text_cell_generator(prop['prop_name']))
        cell_elements = []
        for value in prop['values']:
            name = value['name']
            optioncode = value['optioncode']
            if "imageUrl" in value:
                if value['imageUrl'] != None:
                    image_url = value['imageUrl']
                    parsedurl = urllib.parse.urlparse(image_url)
                else:
                    image_url = ""
            else:
                    image_url = ""
                    
            if image_url != "":
                cell_elements.append({
                    "cells": [
                        {
                            "width": 100,
                            "rowSpan": 1,
                            "colSpan": 1,
                            "value": [
                                {
                                    "@ctype": "paragraph",
                                    "nodes": [
                                        {
                                            "@ctype": "imageNode",
                                            "src": image_url,
                                            "path": parsedurl.path,
                                            "domain": parsedurl.scheme + "://" + parsedurl.netloc,
                                            "internalResource": False,
                                            "fileSize": 0,
                                            "width": 800,
                                            "height": 800,
                                            "fileName": "image.jpg",
                                            "id": generate_random_guid(),
                                            "represent": False
                                        }
                                    ],
                                    "style": {
                                        "@ctype": "paragraphStyle",
                                        "align": "center"
                                    },
                                    "id": generate_random_guid(),
                                }
                            ],
                            "@ctype": "tableCell",
                            "id": generate_random_guid(),
                            "height": 43
                        }
                    ],
                    "@ctype": "tableRow"
                })
            cell_elements.append({
                "cells": [
                    {
                        "width": 100,
                        "rowSpan": 1,
                        "colSpan": 1,
                        "value": [
                            {
                                "@ctype": "paragraph",
                                "nodes": [
                                    {
                                        "@ctype": "textNode",
                                        "style": {
                                            "@ctype": "nodeStyle",
                                            "fontColor": "#000000",
                                            "fontSizeCode": "fs19",
                                            "bold": True
                                        },
                                        "value": f"↑ 옵션{optioncode}↑" ,
                                        "id": "SE-69558e71-ad64-4b11-8f30-d56b5ae43212"
                                    }
                                ],
                                "style": {
                                    "@ctype": "paragraphStyle",
                                    "align": "center"
                                },
                                "id": "SE-28298c6c-d85f-41d0-8d15-7ce809372421"
                            }
                        ],
                        "@ctype": "tableCell",
                        "id": "SE-16e4260a-b845-4655-9ba1-ad67f2d62835",
                        "height": 43
                    }
                ],
                "@ctype": "tableRow"
            }) 
        table_element = {
            "@ctype": "table",
            "columnCount": 1,
            "rows": [
                
            ],
            "align": "center",
            "width": 100,
            "layout": "default",
            "id": "SE-e1fa7caf-030d-43a9-bc94-de473eec566e"
        }
        table_element["rows"] = cell_elements
        
        element_list.append(table_element)
            
    #이미지 정보 추가    
    for imageurl in description_imageurls:
        element_list.append(image_element_generator(imageurl))
    #뒷 이미지 추가
    element_list.append(image_element_generator("https://store.img11.co.kr/73065084/fe7ed03a-9aac-4dff-aee7-82b8e436bfd4_1694272919690.jpg"))

    #스마트에디터 JSON 생성
    defaultformat = {
        "document": {
            "version": "2.6.0",
            "theme": "default",
            "language": "ko-KR",
            "components": element_list
        },
        "documentId": ""
    }
    
    detailjson = '{"json":"'+ json.dumps(defaultformat).replace('"', '\\"') + '"}'
    
    return detailjson