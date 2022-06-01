from argparse import Action
import sys
from typing import Text
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from PyQt5.QtCore import pyqtSlot

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import subprocess

import time
import datetime
import os
import pandas as pd
import numpy as np
import shutil
import random
import openpyxl
from fake_useragent import UserAgent

# QT designer ui 파일 로드
form_class = uic.loadUiType("./driver/main_window_deluxe_dateCrawller.ui")[0]

# UI 텍스트 출력 클래스
class TextBrowser(QThread):
    finished = pyqtSignal(str)
    now_date = ''

    @pyqtSlot(str)
    def run(self, print_str):
        self.make_log(print_str)

    @pyqtSlot(str)
    def make_log(self, print_str):
        self.now_time = datetime.datetime.now()
        self.now_date = self.now_time.strftime('[%Y-%m-%d %H:%M:%S]  ') + print_str
        self.finished.emit(self.now_date)

    def GetTime(self):
        self.now_time = datetime.datetime.now()
        return self.now_time

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cnt = 0
        self.setWindowIcon(QIcon('./driver/instagram_img.png'))
        self.start_btn.clicked.connect(self.ButtonFunction)
        self.process_delay = 5
        self.text = TextBrowser()
        self.text.finished.connect(self.ConnectTextBrowser)
#        self.comment_check.clicked.connect(self.ISCheckComment)

    def closeEvent(self, QCloseEvent):
        ans = QMessageBox.question(self, "종료 확인", "종료하시겠습니까?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ans == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()
    
    def ISCheckComment(self):
        is_checked = self.comment_check.isChecked()
        if is_checked == False:
            self.input_comment.setEnabled(False)
        elif is_checked == True:
            self.input_comment.setEnabled(True)
            
    def ButtonFunction(self):
        self.text.run('--Start work--')
        self.start_time = self.text.GetTime()
        try:
            self.id = self.input_id.text()
        except:
            self.id = ''
            self.text.run('아이디를 입력해주세요!')
            return
        try:
            self.pw = self.input_pw.text()
        except:
            self.pw == ''
            self.text.run('패스워드를 입력해주세요!')
            return
        try:
            self.target_word = self.input_search.text()
        except:
            self.target_word == ''
            self.text.run('검색어(해시태그)를 입력해주세요!')
            return
        # try:
        #     self.count = int(self.input_cnt.text())
        # except:
        #     self.count = 1
        
        # if self.count > 800:
        #     self.count = 800
        
        # try:
        #     self.comment = self.input_comment.text()
        # except:
        #     self.comment = ''

        self.like_cnt = 0

        self.OpenUrl()
        self.LoginUrl(self.id, self.pw)
        self.CrawlData()
    
    @pyqtSlot()
    def OpenUrl(self):
        try:
            shutil.rmtree(r"c:\chrometemp")  #쿠키 / 캐쉬파일 삭제
        except FileNotFoundError:
            pass
        
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrometemp"') # 디버거 크롬 구동
        except:
            subprocess.Popen(r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrometemp"') # 디버거 크롬 구동
    

        self.option = webdriver.ChromeOptions()
        self.option.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        PROXY = "117.1.16.131:8080" # IP:Port

        webdriver.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy": PROXY,
            "ftpProxy": PROXY,
            "sslProxy": PROXY,
            "proxyType": "MANUAL"
        }
        
        chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
        try:
            self.driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options=self.option)
        except:
            chromedriver_autoinstaller.install(True)
            self.driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options=self.option)
        self.driver.implicitly_wait(10)

        self.option.add_argument("disable-gpu") 
        self.option.add_argument("disable-infobars")
        self.option.add_argument("--disable-extensions")
        # 속도 향상을 위한 옵션 해제
        prefs = {'profile.default_content_setting_values': {'cookies' : 2, 'images': 2, 'plugins' : 2, 'popups': 2, 'geolocation': 2, 'notifications' : 2, 'auto_select_certificate': 2, 'fullscreen' : 2, 'mouselock' : 2, 'mixed_script': 2, 'media_stream' : 2, 'media_stream_mic' : 2, 'media_stream_camera': 2, 'protocol_handlers' : 2, 'ppapi_broker' : 2, 'automatic_downloads': 2, 'midi_sysex' : 2, 'push_messaging' : 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop' : 2, 'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement' : 2, 'durable_storage' : 2}}   
        self.option.add_experimental_option('prefs', prefs)
        self.option.add_argument("--proxy-server=socks5://127.0.0.1:9050")
        self.option.add_argument('--no-sandbox')
        self.option.add_argument('--disable-dev-shm-usage')
        self.ua = UserAgent()
        self.userAgent = self.ua.random
        self.option.add_argument(f'user-agent={self.userAgent}')
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", { "source": """ Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) """ })

        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.driver.get('https://instagram.com')
        self.text.run('인스타그램 URL open 완료')

        time.sleep(self.process_delay)

    def LoginUrl(self, id, pw):
        self.act = ActionChains(self.driver)
        try:
            self.id_box = self.driver.find_element_by_css_selector("#loginForm > div > div:nth-child(1) > div > label > input");
            self.pw_box = self.driver.find_element_by_css_selector("#loginForm > div > div:nth-child(2) > div > label > input");
            self.login_button = self.driver.find_element_by_css_selector('#loginForm > div > div:nth-child(3) > button');
            self.act.send_keys_to_element(self.id_box, id).send_keys_to_element(self.pw_box, pw).click(self.login_button).perform()
        except:
            self.main_dis = WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > main > section')))
            print(self.main_dis)
        try:
            username_box_check = WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
            self.text.run('인스타그램 log-in 오류 -> 타임 아웃1')
            self.driver.quit()
        time.sleep(self.process_delay)
        try:
            self.save_login_info_button = self.driver.find_element_by_css_selector('#react-root > section > main > div > div > div > div > button');
            self.act.click(self.save_login_info_button).perform()
        except:
            pass
        try:
            username_box_check = WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
            self.text.run('인스타그램 log-in 오류 -> 타임 아웃2')
            self.driver.quit()

        time.sleep(1.5)
        try:
            self.set_alarm = self.driver.find_element_by_css_selector('body > div.RnEpo.Yx5HN > div > div > div > div.mt3GC > button.aOOlW.HoLwm');
            self.act.click(self.set_alarm).perform()
        except:
            pass
        try:
            username_box_check = WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
            self.text.run('인스타그램 log-in 오류 -> 타임 아웃3')
            self.driver.quit()

        self.text.run('인스타그램 log-in 완료')

    def CrawlData(self):
        idx = 0
        act = ActionChains(self.driver)
        url = "https://www.instagram.com/explore/tags/{}/".format(self.target_word)
        self.driver.get(url)
        try:
            wait = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, 'react-root')))
        except:
            self.text.run("크롤링이 비정상적으로 종료되었습니다")
            self.driver.quit()
        try:
            wait = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="react-root"]/section/main')))
        except:
            self.text.run("크롤링이 비정상적으로 종료되었습니다")
            self.driver.quit()       
        
        time.sleep(3)
    
        try:
            wait = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.eLAPa')))
            self.driver.find_element_by_css_selector('div.eLAPa').click()
        except:
            self.text.run("크롤링이 비정상적으로 종료되었습니다")
            self.driver.quit()
        
        time.sleep(1.5)

        # 데이터 기록, 다음 게시물로 클릭
        self.count = int(self.driver.find_element_by_css_selector('#react-root > section > main > header > div.WSpok > div > div.qF0y9.Igw0E.IwRSH.eGOV_._4EzTm.a39_R > div > span').text.split('게시물 ')[0].replace(',', ''))
        final_res2 = [['', '', '']] * self.count 
        final_res2 = pd.DataFrame(final_res2)
        final_res2.columns = ['ID', 'Date', 'Like']#, 'Contents', 'Tag', 'Like', 'Link']

        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.append(['ID', 'Date', 'Like'])

        for i in range(self.count):
            try:
                element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.eo2As > section.EDfFK.ygqzn > div > div > div')))
            except:
                try:
                    element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.eo2As > section.EDfFK.ygqzn > div > span > div')))
                except:
                    try:
                        element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/div/a[2]/div')))
                    except:
                        try:
                            element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/div')))
                        except:
                            self.text.run("크롤링이 비정상적으로 종료되었습니다")
                            break
            
            like_text = element.text

            if '좋아요' in like_text:
                if '가장 먼저' in like_text:
                    self.like_cnt = 0
                else:
                    self.like_cnt = int(like_text.replace('좋아요 ','').replace('개','').replace(',',''))
            elif '조회' in like_text:
                self.like_cnt = int(like_text.replace('조회 ','').replace('회', '').replace(',',''))
            else:
                self.like_cnt = 0

            try:
                element = WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[2]/div/a/div/time')))
            except:
                self.text.run("크롤링이 비정상적으로 종료되었습니다")
                break

            self.date = element.accessible_name
            self.current_link = self.driver.current_url

            #글쓴이 comment 수집
#            time.sleep(random.randrange(5))
#            time.sleep(1.5)
            time.sleep(random.randrange(10, 15))
            try:
                element = WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.UE9AK > div > header > div.o-MQd.z8cbW > div.PQo_0.RqtMr > div.e1e1d > div > span > a')))
            except:
                self.content_id = ''
            
            self.content_id = element.text

            final_res2.iloc[i][0] = self.content_id
            final_res2.iloc[i][1] = self.date
            final_res2.iloc[i][2] = self.like_cnt
            sheet.append([self.content_id, self.date, self.like_cnt])

            self.like_cnt = 0
            current_path = os.getcwd()
            now_time = datetime.datetime.now()
            now_date = now_time.strftime('%Y-%m-%d') + '_'
            wb.save("{}\\".format(current_path) + now_date + self.target_word + "_results.xlsx")
            # 결과값 저장
#            final_res2.to_excel("{}\\".format(current_path) + now_date + self.target_word + "_results.xlsx")

            try:
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.l8mY4.feth3')))
                next_btn = self.driver.find_element_by_css_selector('div.l8mY4.feth3')
                self.act.click(next_btn).perform()
            except:
                self.text.run('마지막 게시물입니다.')
                break
            
            self.text.run('{}번째 게시물 탐색 완료'.format(i+1))
            print('{}번째 게시물 탐색 완료'.format(i+1))
            if i % 40 == 0 and i != 0:
                self.userAgent = self.ua.random
                self.option.add_argument(f'user-agent={self.userAgent}')
                time.sleep(300)
            
        # 크롬드라이버 종료
        self.end_time = self.text.GetTime()
        diff_time = self.end_time - self.start_time
        self.text.run('--End work--')
        self.text.run('총 소요시간은 {}초 입니다.'.format(diff_time.seconds))
        self.driver.quit()
    
    @pyqtSlot(str)
    def ConnectTextBrowser(self, print_str):
        self.textBrowser.append(print_str)
        self.textBrowser.repaint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()
