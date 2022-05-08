from argparse import Action
from faulthandler import disable
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
import re
import shutil
import random
import openpyxl
from fake_useragent import UserAgent
import threading

# QT designer ui 파일 로드
form_class = uic.loadUiType("./driver/main_window_deluxe.ui")[0]

# UI 텍스트 출력 클래스
class TextBrowser(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.now_date = ''
        
    finished = pyqtSignal(str)

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
        self.start_btn.clicked.connect(self.MakeThread)
        self.process_delay = 5
        self.re_login = False
        self.open_url = True
        self.is_checked = False
        self.disable_follow = False
        self.is_reply = False
        self.is_like = False
        self.is_follow = False
        self.re_start = False
        self.comment_check.clicked.connect(self.IsCheckComment)
        self.relogin_checkBox.clicked.connect(self.IsCheckReLogin)
        self.disable_follow_check.clicked.connect(self.IsCheckDisableFollow)

    def closeEvent(self, QCloseEvent):
        ans = QMessageBox.question(self, "종료 확인", "종료하시겠습니까?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ans == QMessageBox.Yes:
            QCloseEvent.accept()
            self.KillThread()
        else:
            QCloseEvent.ignore()
    
    def IsCheckComment(self):
        self.is_checked = self.comment_check.isChecked()
        if self.is_checked == False:
            self.input_comment.setEnabled(False)
        elif self.is_checked == True:
            self.input_comment.setEnabled(True)

    def IsCheckDisableFollow(self):
        disable_follow_chk = self.disable_follow_check.isChecked()
        if disable_follow_chk == False:
            self.disable_follow = False
        elif disable_follow_chk == True:
            self.disable_follow = True

    def IsCheckReLogin(self):
        is_checked_relogin = self.relogin_checkBox.isChecked()
        if is_checked_relogin == False:
            self.re_login = False
            self.relogin_time.setEnabled(False)
        elif is_checked_relogin == True:
            self.re_login = True
            self.relogin_time.setEnabled(True)

    def ButtonFunction(self):
        self.text = TextBrowser(self)
        self.text.finished.connect(self.ConnectTextBrowser)
#        self.text.run('')
        
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
        try:
            self.count = int(self.input_cnt.text())
        except:
            self.count = 1
        
        if self.count > 800:
            self.count = 800
        
        try:
            self.comment = self.input_comment.text()
        except:
            self.comment = ''

        self.like_cnt = 0
        try:
            self.relogin_min = int(self.relogin_time.text()) * 60
        except:
            self.relogin_min = 600

        if self.open_url == True and self.re_start == False:
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

        self.driver.maximize_window()
        self.driver.get('https://instagram.com')
        self.text.run('Chrome 버전 : {}'.format(chrome_ver))
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
            self.main_dis = WebDriverWait(self.driver, 150).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > main > section')))
            print(self.main_dis)
        try:
            second_security = WebDriverWait(self.driver, 300).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > main > div > div > div:nth-child(1)')))
            if '코드를 입력하세요' in second_security.text:
                self.text.run('보안 코드를 입력해주세요.')
        except:
            pass
        try:
            username_box_check = WebDriverWait(self.driver, 300).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > main > div > div > div > div > button')))
            print(username_box_check)
        except:
#            self.text.run('인스타그램 log-in 오류 -> 타임 아웃1')
#            return 0
            pass
        username_box_check.click()
        time.sleep(self.process_delay)
        try:
            self.save_login_info_button = WebDriverWait(self.driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo.Yx5HN > div > div > div > div.mt3GC > button.aOOlW.HoLwm')))
            self.save_login_info_button.click()
#            self.act.click(self.save_login_info_button).perform()
        except:
            pass

        try:
            username_box_check = WebDriverWait(self.driver, 300).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
            self.text.run('인스타그램 log-in 오류 -> 타임 아웃3')
            self.LogOut()
            self.re_start = True
            return 0
        try:
            self.nickname = WebDriverWait(self.driver, 300).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > nav > div._8MQSO.Cx7Bp > div > div > div.ctQZg.KtFt3 > div > div:nth-child(6) > div.EforU > span > img')))\
                                                        .accessible_name.split('님의')[0]
        except:
            self.text.run('회원님의 Nickname을 가져오는데 실패했습니다.')
            self.LogOut()
            self.re_start = True
            return 0

        self.text.run('인스타그램 log-in 완료')

    def CrawlData(self):
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.append(['Time', 'ID', 'Date', 'Contents', 'Tag', 'Like', 'Link'])
        
        url = "https://www.instagram.com/explore/tags/{}/".format(self.target_word)
        self.driver.get(url)
        try:
            wait = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 'react-root')))
        except:
            self.text.run("해시태그 검색에 실패했습니다.")
            self.LogOut()
            self.re_start = True
            return 0
        try:
            wait = WebDriverWait(self.driver, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="react-root"]/section/main')))
        except:
            self.text.run("해시태그 검색에 실패했습니다.")
            self.LogOut()
            self.re_start = True
            return 0
        
        time.sleep(5)
        self.text.run("{} 해시태그 최근 게시물 searching 시작!".format(self.target_word))
        try:
            wait = WebDriverWait(self.driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > main > article > div:nth-child(3) > div > div:nth-child(1) > div:nth-child(1) > a > div > div._9AhH0')))
        except:
            self.text.run("최근 게시물을 찾을 수 없습니다.")
            self.LogOut()
            self.re_start = True
            return 0

        first_feed = self.driver.find_element_by_css_selector('#react-root > section > main > article > div:nth-child(3) > div > div:nth-child(1) > div:nth-child(1) > a > div > div._9AhH0')
        self.act.move_to_element(first_feed).perform()
        time.sleep(2)
        try:
            self.act.move_to_element(first_feed).click().perform()
        except:                                       
            self.text.run("최근 게시물 클릭에 실패했습니다.")
            self.LogOut()
            self.re_start = True
            return 0
        
        block_text_list = ['부업', '재테크', '출금', '공짜', '수익', '카톡', '원금', '부자', 'Repost', '문의전화', '직장인부업', '주부부업', '마케팅', 
                            '마케터']
        time.sleep(1)
        # 데이터 기록, 다음 게시물로 클릭
#        for i in range(self.count):
        i = 0
        more_like_idx = 0
        while i < self.count:
            block_point = False
            try :
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.eo2As > section.EDfFK.ygqzn > div > div > div')))
            except :
                try :
                    element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.eo2As > section.EDfFK.ygqzn > div > span > div')))
                except :
                    try :
                        element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/div/a[2]/div')))
                    except :
                        try :
                            element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/div')))
                        except : 
                            try :
                                element = WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/ul/div/li/div/div/div[2]')))
                            except :
                                try:
                                    element = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[1]')
                                except:
                                    self.driver.refresh()
                                    time.sleep(10)
                                    try:
                                        first_feed = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#react-root > section > main > article > div:nth-child(3) > div > div:nth-child(1) > div:nth-child(1) > a > div > div._9AhH0')))
                                        self.act.move_to_element(first_feed).click().perform()
                                        time.sleep(2)
                                        self.text.run("웹사이트 새로고침 후 재탐색 중.")
                                        continue
                                    except:
                                        self.text.run("피드 내용 크롤링에 실패했습니다.")
                                        self.open_url = False
                                        self.LogOut()
                                        self.re_start = True
                                        return 0

            is_skip = False
            self.is_like = False
            self.is_follow = False

            # 게시물 글에서 광고성글 단어 포함 여부 확인하기
            for word in block_text_list :
                if element.text.find(word) > 0 :
                    self.text.run( "Skip! block text " + word)
                    block_point = True
                    is_skip = True
                    break
                    
            if is_skip == True:
                self.driver.find_element_by_css_selector('div.l8mY4.feth3').click()
                time.sleep(1.5)
                self.text.run('광고성 게시물 skip'.format(i+1))
                if i != 0:
                    i -= 1                   
                continue

            if block_point == False :
                time.sleep(2)
                # 좋아요 누르기
                ret = self.ClickLikeButton()
                if ret == 0:
                    self.text.run("{}번째 피드에 좋아요 누르기 실패".format(i + 1))
                    self.open_url = False
                    self.LogOut()
                    self.re_start = True
                    return 0
            try:
                element = WebDriverWait(self.driver, 150).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[2]/div/a/div/time')))
            except:
                self.text.run("{}번째 피드 업로드 시간 크롤링 실패".format(i + 1))
                self.open_url = False
                self.LogOut()
                self.re_start = True
                return 0

            self.date = element.accessible_name
            self.current_link = self.driver.current_url
            
            # 팔로우 하기
            self.ClickFollow()

            # 댓글달기
            self.PutComment()

            if self.is_like == True and (self.is_follow == True or self.disable_follow == True) and (self.is_reply == True or self.is_checked == False):
                self.ClickNextButton()
                continue

            # 글쓴이 comment 수집
            time.sleep(random.randrange(5))
            raw_info = self.driver.find_element_by_css_selector('div.C4VMK').text.split()
            text = []
            # 해쉬태그 데이터 기록
            try:
                data = self.driver.find_element_by_css_selector('.C7I1f.X7jCj').text
                tag = re.findall('#[A-Za-z0-9가-힣]+', data)
                self.tag = ' '.join(tag)
            except:
                pass
            for n in range(len(raw_info)):
                ## 첫번째 text는 아이디니까 제외 
                if n == 0:
                    self.content_id = raw_info[n]
                ## 두번째부터 시작 
                else:
                    if '#' in raw_info[n][0:1]:
                        pass
                    else:
                        text.append(raw_info[n])
                self.content = ' '.join(text)
            
            # 피드 들어가서 최근 게시물 5개에 좋아요 누르기
            try:
                friend = self.driver.find_element_by_css_selector('body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.UE9AK > div > header > div.o-MQd.z8cbW > div.PQo_0.RqtMr > div.e1e1d > div > span')
            except:
                try:
                    friend = self.driver.find_element_by_css_selector('body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.UE9AK > div > header > div.o-MQd.z8cbW > div.RqtMr > div > div > span:nth-child(1) > a')
                except:
                    self.text.run('피드 계정을 찾을 수 없습니다. 다음 게시물로 넘어갑니다')
                    self.ClickNextButton()
                    continue

            friend_name = friend.text
            friend.click()
            time.sleep(5)
            try:
                WebDriverWait(self.driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.eLAPa'))).click()
            except:
                self.driver.refresh()
                time.sleep(10)
            loop_range = 5
            r = 0
            while r < loop_range:
                time.sleep(10)
                # 좋아요 누르기
                try:
                    like_btn = WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.eo2As > section.ltpMr.Slqrh > span.fr66n > button')))
                except:
                    like_btn = WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div[3]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]/button')))

                btn_svg = like_btn.find_element_by_tag_name('svg')
                svg_txt = btn_svg.get_attribute('aria-label')
                if svg_txt == '좋아요':
                    like_btn.click()
                    time.sleep(random.randrange(30, 100))

                    self.text.run('{}-{}번째 게시물 좋아요 완료'.format(i + 1, r + 1))
                else:
                    self.ClickNextButton()
                    continue

                time.sleep(2)
                if  r == (loop_range - 1):
                    break
                else:
                    ret = self.ClickNextButton()
                    if ret == 0:
                        self.text.run('{}번째 피드가 이 계정의 마지막 게시물'.format(r + 1))
                        break
                    r += 1

            more_like_idx += 1
            self.driver.get(url)
            time.sleep(3)
            try:
                first_feed = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#react-root > section > main > article > div:nth-child(3) > div > div:nth-child(1) > div:nth-child(1) > a > div > div._9AhH0')))
            except:                                                                                                 #react-root > section > main > article > div:nth-child(3) > div > div:nth-child(1) > div:nth-child(1) > a > div > div._9AhH0
                self.driver.refresh()                                                                               
                time.sleep(10)
                try:
                    first_feed = WebDriverWait(self.driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#react-root > section > main > article > div:nth-child(3) > div > div:nth-child(1) > div:nth-child(1) > a > div > div._9AhH0')))
                except:
                    self.text.run("크롤링이 비정상적으로 종료되었습니다")
                    self.open_url = False
                    self.LogOut()
                    self.re_start = True
                    return 0
            self.act.move_to_element(first_feed).click().perform()
            time.sleep(2)
#            check_friend = self.driver.find_element_by_css_selector('body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.UE9AK > div > header > div.o-MQd.z8cbW > div.PQo_0.RqtMr > div.e1e1d > div > span').text
            
            # rr = 0
            # while rr < more_like_idx:
            #     if check_friend != friend_name:
            #         if rr == more_like_idx - 1:
            #             break
            #         element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.l8mY4.feth3')))
            #         next_btn = self.driver.find_element_by_css_selector('div.l8mY4.feth3')
            #         self.act.click(next_btn).perform()
            #         time.sleep(5)
            #         rr += 1
            #     elif (check_friend == friend_name) and (rr == more_like_idx - 1):
            #         break
            #     else:
            #         element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.l8mY4.feth3')))
            #         next_btn = self.driver.find_element_by_css_selector('div.l8mY4.feth3')
            #         self.act.click(next_btn).perform()
            #         time.sleep(5)
            #         rr += 1

            current_path = os.getcwd()
            now_time = datetime.datetime.now()
            now_date = now_time.strftime('%Y-%m-%d') + '_'
            now = now_time.strftime('[%Y-%m-%d %H:%M:%S]  ')
            self.now = now_time.strftime('%Y-%m-%d-%H:%M:%S')
            sheet.append([self.now, self.content_id, self.date, self.content, self.tag, self.like_cnt, self.current_link])

            wb.save("{}\\".format(current_path) + now_date + self.target_word + "_results.xlsx")
            time.sleep(random.randrange(10, 150))
            
            self.text.run('{}번째 게시물 탐색 완료'.format(i + 1))
            print('{}{}번째 게시물 탐색 완료'.format(now, i + 1))
            if i == (self.count - 1):
                self.text.run('마지막 게시물입니다.')
                self.re_start = True
                break
            else:
                i += 1

            if i % 40 == 0 and i != 0 and i != self.count:
                self.userAgent = self.ua.random
                self.option.add_argument(f'user-agent={self.userAgent}')
                time.sleep(random.randrange(300, 600))
            
            self.ClickNextButton()
                
        # 크롬드라이버 종료
        self.end_time = self.text.GetTime()
        diff_time = self.end_time - self.start_time
        self.text.run('--End work--')
        self.text.run('총 소요시간은 {}초 입니다.'.format(diff_time.seconds))
        self.text.run('')
        self.driver.get('https://www.instagram.com')
        self.LogOut()

        if self.re_login == True:
            self.open_url = False
            self.Restart()

    def Restart(self):
        time.sleep(self.relogin_min)
        self.ButtonFunction()

    def MakeThread(self):
        self.th = threading.Thread(target=self.ButtonFunction)
        self.th.start()

    def KillThread(self):
        pid = os.getpid()
        os.kill(pid, 2)

    def PutComment(self):
        button = ''
        # 댓글 더보기 버튼 누르기
        try:
            cnt = 0
            while True:
                try:
                    button = self.driver.find_element_by_css_selector('body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.eo2As > div.EtaWk > ul > li > div > button > div > svg').click()
                except:                                                
                    break
                if cnt == 50:
                    break
                cnt += 1
        except:
            pass

        ids  = self.driver.find_elements_by_css_selector('div.qF0y9.Igw0E.IwRSH.eGOV_._4EzTm.ItkAi')
        self.is_reply = False
        for id in ids:
            if self.nickname in id.text:
                self.is_reply = True
                break

        if self.is_reply == False and self.is_checked == True:
            ## 댓글 달기
            try:
                comment_block = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[3]/div/form/textarea')
                self.act.move_to_element(comment_block).click().pause(5).send_keys(self.comment).pause(5).send_keys(Keys.ENTER).perform()
            except:
                try:
                    comment_block = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[3]/div')
                except:
                    pass

    def ClickFollow(self):
        if self.disable_follow == False:
            try:
                follow_btn = WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[1]/div/header/div[2]/div[1]/div[2]/button/div')))
                follow_text = follow_btn.text
                if follow_text == '팔로우':
                    follow_btn.click()
                else:
                    self.is_follow = True
            except:
                pass
    
    def ClickLikeButton(self):
        try:
            like_btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo._Yhr4 > div.pbNvD.QZZGH.bW6vo > div > article > div > div.HP0qD > div > div > div.eo2As > section.ltpMr.Slqrh > span.fr66n > button')))
        except:
            like_btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div[3]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]/button')))

        btn_svg = like_btn.find_element_by_tag_name('svg')
        svg_txt = btn_svg.get_attribute('aria-label')
        if svg_txt == '좋아요':
            like_btn.click()
            try:
                interrupt_like = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.RnEpo.Yx5HN > div > div')))
                self.driver.find_element_by_css_selector('body > div.RnEpo.Yx5HN > div > div > div > div.mt3GC > button.aOOlW.HoLwm').click()
                self.text.run('좋아요/팔로우 등의 자동 매크로 활동에 제한이 걸렸습니다. 1~2일 후 프로그램 사용 바랍니다.')
                return 0
            except:
                pass
        else:
            self.is_like = True
        try:
            wait = WebDriverWait(self.driver, 5)
            element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/div/a/div')))
        except:
            try:
                wait = WebDriverWait(self.driver, 0.5)
                element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/div')))
            except:
                try:
                    wait = WebDriverWait(self.driver, 0.5)
                    element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/div/a[2]/div')))
                except:
                    try:
                        wait = WebDriverWait(self.driver, 0.5)
                        element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[2]/div/span/div')))                               
                    except:
                        return 0
                
        like_text = element.text

        if '좋아요' in like_text:
            if '가장 먼저' in like_text:
                self.like_cnt = 1
            else:
                self.like_cnt = int(like_text.replace('좋아요 ','').replace('개','').replace(',',''))
        elif '조회' in like_text:
            self.like_cnt = int(like_text.replace('조회 ','').replace('회', '').replace(',',''))
        else:
            self.like_cnt = 0
        
        return 1

    def ClickNextButton(self):
        try:
            element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.l8mY4.feth3')))
        except:
            return 0
        next_btn = self.driver.find_element_by_css_selector('div.l8mY4.feth3')
        self.act.click(next_btn).perform()
        time.sleep(5)

        return 1

    def LogOut(self):
        self.driver.get('https://instagram.com')
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > nav > div._8MQSO.Cx7Bp > div > div > div.ctQZg.KtFt3 > div > div:nth-child(6) > div.EforU > span > img'))).click()
        time.sleep(2)
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#react-root > section > nav > div._8MQSO.Cx7Bp > div > div > div.ctQZg.KtFt3 > div > div:nth-child(6) > div.poA5q > div.uo5MA._2ciX.tWgj8.XWrBI > div._01UL2 > div:nth-child(6)'))).click()

    @pyqtSlot(str)
    def ConnectTextBrowser(self, print_str):
        self.textBrowser.append(print_str)
        self.textBrowser.repaint()

if __name__ == "__main__":  
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()