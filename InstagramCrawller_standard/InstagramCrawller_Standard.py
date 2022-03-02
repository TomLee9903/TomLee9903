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
import time
import datetime
import os
import re
import pandas as pd
import numpy as np
import itertools

# QT designer ui 파일 로드
form_class = uic.loadUiType("./driver/main_window_standard.ui")[0]

class TextBrowser(QThread):
    finished = pyqtSignal(str)
    now_date = ''

    @pyqtSlot(str)
    def run(self, print_str):
        self.make_log(print_str)

    @pyqtSlot(str)
    def make_log(self, print_str):
        now_time = datetime.datetime.now()
        self.now_date = now_time.strftime('[%Y-%m-%d %H:%M:%S]  ') + print_str
        self.finished.emit(self.now_date)

    def GetText(self):
        return self.now_date

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

    def closeEvent(self, QCloseEvent):
        ans = QMessageBox.question(self, "종료 확인", "종료하시겠습니까?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ans == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()
        
    def ButtonFunction(self):
#        if self.cnt == 0:
#            self.textBrowser.setPlainText('----------Start----------')
        self.text.run('--Start work--')
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

        self.cnt += 1

        self.OpenUrl()
        self.LoginUrl(self.id, self.pw)
        self.CrawlData()
        self.cnt = 0

    @pyqtSlot()
    def OpenUrl(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome("./driver/chromedriver.exe", options=self.options);
        self.driver.maximize_window()
        self.driver.get('https://instagram.com')
#        self.text.run('인스타그램 URL open 완료')

        time.sleep(self.process_delay)

    def LoginUrl(self, id, pw):
        act = ActionChains(self.driver)
        self.id_box = self.driver.find_element_by_css_selector("#loginForm > div > div:nth-child(1) > div > label > input");
        self.pw_box = self.driver.find_element_by_css_selector("#loginForm > div > div:nth-child(2) > div > label > input");
        self.login_button = self.driver.find_element_by_css_selector('#loginForm > div > div:nth-child(3) > button');
        act.send_keys_to_element(self.id_box, id).send_keys_to_element(self.pw_box, pw).click(self.login_button).perform()
        try:
            username_box_check = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
#            self.text.run('인스타그램 log-in 오류 -> 타임 아웃1')
            self.driver.quit()
        time.sleep(self.process_delay)

        self.save_login_info_button = self.driver.find_element_by_css_selector('#react-root > section > main > div > div > div > div > button');
        act.click(self.save_login_info_button).perform()
        try:
            username_box_check = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
#            self.text.run('인스타그램 log-in 오류 -> 타임 아웃2')
            self.driver.quit()
        
        time.sleep(1.5)
        self.set_alarm = self.driver.find_element_by_css_selector('body > div.RnEpo.Yx5HN > div > div > div > div.mt3GC > button.aOOlW.HoLwm');
        act.click(self.set_alarm).perform()
        try:
            username_box_check = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
#            self.text.run('인스타그램 log-in 오류 -> 타임 아웃3')
            self.driver.quit()

#        self.text.run('인스타그램 log-in 완료')

    def CrawlData(self):
        idx = 0
        final_res = [['']] * self.count
        act = ActionChains(self.driver)
        url = "https://www.instagram.com/explore/tags/{}/".format(self.target_word)
        self.driver.get(url)
        try:
            wait = WebDriverWait(self.driver, 20)
            element = wait.until(EC.presence_of_element_located((By.ID, 'react-root')))
        except:
#            self.text.run("크롤링이 비정상적으로 종료되었습니다")
            self.driver.quit()

        time.sleep(self.process_delay)
        self.driver.find_element_by_css_selector('div.eLAPa').click()
        
        # 데이터 기록, 다음 게시물로 클릭
        for i in range(self.count):
            # 해쉬태그 데이터 기록
            try:
                data = self.driver.find_element_by_css_selector('.C7I1f.X7jCj').text
                tag = re.findall('#[A-Za-z0-9가-힣]+', data)
                tag = ' '.join(tag)
            except:
                pass
            time.sleep(1.5)
            like_btn = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]') 
            btn_svg = like_btn.find_element_by_tag_name('svg') 
            svg_txt = btn_svg.get_attribute('aria-label')
            if svg_txt == '좋아요':
                like_btn.click()

            follow_btn = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[1]/div/header/div[2]/div[1]/div[2]/button/div')
            follow_text = follow_btn.text
            if follow_text == '팔로우':
                follow_btn.click()
            time.sleep(0.5)
            
            button = ''
            # 댓글 더보기 버튼 누르기
            while True:
                try:
                    button = self.driver.find_element_by_css_selector('body > div._2dDPU.CkGkG > div.zZYga > div > article > div.eo2As > div.EtaWk > ul > li > div > button > span')
                except:
                    pass

                if button is not None:
                    try:
                        self.driver.find_element_by_css_selector('body > div._2dDPU.CkGkG > div.zZYga > div > article > div.eo2As > div.EtaWk > ul > li > div > button > span').click()
                    except:
                        break

            # 대댓글 버튼 누르기
            buttons = self.driver.find_elements_by_css_selector('li > ul > li > div > button')

            for button in buttons:
                button.send_keys(Keys.ENTER)

            ids  = self.driver.find_elements_by_css_selector('div.qF0y9.Igw0E.IwRSH.eGOV_._4EzTm.ItkAi')
            replies = self.driver.find_elements_by_css_selector('div.C7I1f > div.C4VMK > div.MOdxS > span._7UhW9.xLCgt.MMzan.KV-D4.se6yk.T0kll')
#            time_raw = self.driver.find_element_by_css_selector('div.C4VMK > div.qF0y9 > div._7UhW9 > a > time')
#            time_info = time_raw.get_attribute('datetime')
            results = [['' for col in range(2)] for row in range(len(ids))]

            for id, reply in zip(ids, replies):
                results[idx][0] = id.text
                results[idx][1] = reply.text
                idx += 1
            result_temp = list(itertools.chain.from_iterable(results))
            final_res[i] = result_temp
            
            self.driver.find_element_by_css_selector('div.l8mY4.feth3').click()
            time.sleep(1.5)
            if i == (self.count - 1):
                self.driver.find_element_by_xpath('/html/body/div[6]/div[1]/button').click()
            
            time.sleep(1.5)
            idx = 0
        
        # 크롬드라이버 종료
        self.text.run('--End work--')
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
