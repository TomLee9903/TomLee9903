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

    def closeEvent(self, QCloseEvent):
        ans = QMessageBox.question(self, "종료 확인", "종료하시겠습니까?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ans == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()
        
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

        self.OpenUrl()
        self.LoginUrl(self.id, self.pw)
        self.CrawlData()
    
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
        try:
            wait = WebDriverWait(self.driver, 20)
            element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="react-root"]/section/main')))
        except:
            self.text.run("크롤링이 비정상적으로 종료되었습니다")
            self.driver.quit()
        try:
            wait = WebDriverWait(self.driver, 20)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.eLAPa')))
        except:
            self.text.run("크롤링이 비정상적으로 종료되었습니다")
            self.driver.quit()
        
        time.sleep(1)
        self.driver.find_element_by_css_selector('div.eLAPa').click()
        block_text_list = ['부업', '재테크', '출금', '공짜', '수익', '카톡', '원금', '부자', 'Repost', '문의전화', '직장인부업', '주부부업', '마케팅', 
                            '마케터']
        time.sleep(1)

        # 데이터 기록, 다음 게시물로 클릭
        for i in range(self.count):
            block_point = False
            try :
                wait = WebDriverWait(self.driver, 5)
                content = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div/li/div/div/div[2]')))
            except :
                try :
                    wait = WebDriverWait(self.driver, 0.5)
                    content = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div[3]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div/li/div/div/div[2]')))
                except :
                    try :
                        wait = WebDriverWait(self.driver, 0.5)
                        content = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[2]/div/article/div[3]/div[1]/ul/ul[1]/div/li/div/div[1]/div[2]/span')))
                    except :
                        try :
                            wait = WebDriverWait(self.driver, 0.5)
                            content = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[2]/div/article/div[3]/div[1]/ul/div/li/div/div/div[2]/span')))
                        except : 
                            try :
                                wait = WebDriverWait(self.driver, 0.5)
                                content = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/ul/div/li/div/div/div[2]')))
                            except :
                                try:
                                    content = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[1]')
                                except:
                                    self.text.run("Cannot found the comments")
                                    self.driver.get(url)
                                    break
            is_skip = False
            # 게시물 글에서 광고성글 단어 포함 여부 확인하기
            for word in block_text_list :
                if content.text.find(word) > 0 :
                    self.text.run( "Skip! block text " + word)
                    block_point = True
                    is_skip = True
                    break
                    
            if is_skip == True:
                self.driver.find_element_by_css_selector('div.l8mY4.feth3').click()
                time.sleep(1.5)
                self.text.run('광고성 게시물 skip'.format(i+1))
                self.count += 1
                continue

            if block_point == False :
                like_btn = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]') 
                btn_svg = like_btn.find_element_by_tag_name('svg') 
                svg_txt = btn_svg.get_attribute('aria-label')
                if svg_txt == '좋아요':
                    like_btn.click()

                follow_btn = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[1]/div/header/div[2]/div[1]/div[2]/button/div')
                follow_text = follow_btn.text
                if follow_text == '팔로우':
                    follow_btn.click()
                time.sleep(1.5)
                try:
                    self.driver.find_element_by_css_selector('div.l8mY4.feth3').click()
                except:
                    self.text.run('마지막 게시물입니다.')
                    break
        
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
