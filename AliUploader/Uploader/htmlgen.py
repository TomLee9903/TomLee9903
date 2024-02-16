
from bs4 import BeautifulSoup
import json

def create_image_table(json_data):
    table_html = f"<div style='margin:80px'></div>"
    table_html += "<h1 style='text-align:center'><b>옵 션</b></h1>"
    table_html += f"<div style='margin:40px'></div>"
    for prop in json_data['sku_props']:
        #상품 이미지 및 이름 매칭 단계
        images_and_names = []
        for value in prop['values']:
            if 'imageUrl' in value:
                image_url = value['imageUrl']
            name = value['name']
            optioncode = value['optioncode']
            if image_url:
                image_html = f'<div style="text-align: center;"><img src="{image_url}" width="100%"></div>'
            else:
                image_html = '<div style="text-align: center; margin: 100px">N/A</div>'

            name_html = f'<div style="text-align:center; font-size: 22px; font-weight: bold; margin-bottom: 6px">{f"↑ 옵션{optioncode} ↑"}</div>'
            images_and_names.append((image_html, name_html))
            
        prop_name = f"<h2 style='text-align:center'>{prop['prop_name']}</h2>"
        table_html += f"<br style = 'display: inline-block; text-align: center;'>{prop_name}</br>"
        table_html += f"<div style='margin:20px'></div>"
        table_html += "<table style='width: 750px; border-collapse: collapse; border: 1px solid; text-align: center; margin-left: auto; margin-right: auto;'>"
        for productimage, productname in images_and_names:
            table_html += "<tr style = 'display: flex; flex-direction: column; border: 1px solid;'>"
            table_html += f"<td><div style='flex-grow: 3;  width:100%;'></div>{productimage}<div style='flex-grow: 3;  width:100%;'></div></td>"
            table_html += "</tr>"
            table_html += "<tr style = 'display: flex; flex-direction: column; border: 1px solid;'>"
            table_html += f"<td>{productname}</td></tr>"
        table_html += "</table>"
        table_html += f"<div style='margin:100px'></div>"
        
        
    return table_html

def start_img():
    return f"<img src='https://store.img11.co.kr/73065084/887ce9b0-9805-4ad0-9b7a-6c9b5ddc4ffb_1694272851639.jpg' width='860'; style='margin: auto; text-align: center; display: block;'>"

def end_img():
    return f"<img src='https://store.img11.co.kr/73065084/fe7ed03a-9aac-4dff-aee7-82b8e436bfd4_1694272919690.jpg' width='860'; style='margin: auto; text-align: center; display: block;'>"

def video_html(url):
    return f""" <div style="text-align: center;">
        <video controls width="600">
            <source src="{url}" type="video/mp4">
        </video>
    </div>"""

def htmlgenerator(options, imageurls, video = None):
    newsoup = BeautifulSoup(start_img(), "html.parser")
    
    if video != None:
        newsoup.append(BeautifulSoup(video_html(video), "html.parser"))
    
    newsoup.append(BeautifulSoup(create_image_table(options), "html.parser"))
    
    for image in imageurls:
        newsoup.append(BeautifulSoup(f"<img src='{image}' width='860'; style='margin: auto; text-align: center; display: block;'>", "html.parser"))
    newsoup.append(BeautifulSoup(end_img(), "html.parser"))
    
    

    return str(newsoup)
