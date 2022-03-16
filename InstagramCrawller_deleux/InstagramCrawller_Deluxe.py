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
form_class = uic.loadUiType("./driver/main_window_deluxe.ui")[0]

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
        self.comment_check.clicked.connect(self.ISCheckComment)

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
        self.text.run('인스타그램 URL open 완료')

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
            self.text.run('인스타그램 log-in 오류 -> 타임 아웃1')
            self.driver.quit()
        time.sleep(self.process_delay)

        self.save_login_info_button = self.driver.find_element_by_css_selector('#react-root > section > main > div > div > div > div > button');
        act.click(self.save_login_info_button).perform()
        try:
            username_box_check = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
            self.text.run('인스타그램 log-in 오류 -> 타임 아웃2')
            self.driver.quit()
        
        time.sleep(1.5)
        self.set_alarm = self.driver.find_element_by_css_selector('body > div.RnEpo.Yx5HN > div > div > div > div.mt3GC > button.aOOlW.HoLwm');
        act.click(self.set_alarm).perform()
        try:
            username_box_check = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'react-root')))
            print(username_box_check)
        except:
            self.text.run('인스타그램 log-in 오류 -> 타임 아웃3')
            self.driver.quit()

        self.text.run('인스타그램 log-in 완료')

    def CrawlData(self):
        idx = 0
        final_res = [['']] * self.count
        final_res2 = [['', '', '', '', '', '']] * self.count
        act = ActionChains(self.driver)
        url = "https://www.instagram.com/explore/tags/{}/".format(self.target_word)
        self.driver.get(url)
        try:
            wait = WebDriverWait(self.driver, 20)
            element = wait.until(EC.presence_of_element_located((By.ID, 'react-root')))
        except:
            self.text.run("크롤링이 비정상적으로 종료되었습니다")
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
                i -= 1
                continue

            if block_point == False :
                time.sleep(1.5)
                try:
                    like_btn = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]')
                except:
                    like_btn = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]/button/div[2]/span/svg')

                btn_svg = like_btn.find_element_by_tag_name('svg') 
                svg_txt = btn_svg.get_attribute('aria-label')
                if svg_txt == '좋아요':
                    like_btn.click()
                try:
                    wait = WebDriverWait(self.driver, 10)
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
                                self.text.run("크롤링이 비정상적으로 종료되었습니다")
                                self.driver.quit()                
                
                like_text = element.text

                if '좋아요' in like_text:
                    self.like_cnt = element.text.strip('좋아요 ')

                try:
                    wait = WebDriverWait(self.driver, 3)
                    element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[2]/div/a/div/time')))
                except:
                    self.text.run("크롤링이 비정상적으로 종료되었습니다")
                    self.driver.quit()
                self.date = element.accessible_name
                self.current_link = self.driver.current_url

                follow_btn = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[1]/div/header/div[2]/div[1]/div[2]/button/div')
                follow_text = follow_btn.text
                if follow_text == '팔로우':
                    follow_btn.click()
                
                ac = ActionChains(self.driver)
                try:
                    comment_block = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/section[3]/div/form/textarea')
                    ac.move_to_element(comment_block).click().pause(2).send_keys(self.comment).pause(1).send_keys(Keys.ENTER).perform()
                except:
                    try:
                        comment_block = self.driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/article/div/div[2]/div/div/div[2]/div[3]/div')
                    except:
                         pass
                
                time.sleep(1.5)

                # 글쓴이 comment 수집
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
#                time.sleep(self.process_delay)
                
                final_res2 = pd.DataFrame(final_res2)
                final_res2.columns = ['ID', 'Date', 'Contents', 'Tag', 'Like', 'Link']
                final_res2.iloc[i][0] = self.content_id
                final_res2.iloc[i][1] = self.date
                final_res2.iloc[i][2] = self.content
                final_res2.iloc[i][3] = self.tag
                final_res2.iloc[i][4] = self.like_cnt
                final_res2.iloc[i][5] = self.current_link
                
                self.content = ''
                self.tag = ''
                self.like_cnt = 0
                # button = ''
                # # 댓글 더보기 버튼 누르기
                # while True:
                #     try:
                #         button = self.driver.find_element_by_css_selector('body > div._2dDPU.CkGkG > div.zZYga > div > article > div.eo2As > div.EtaWk > ul > li > div > button > span')
                #     except:
                #         pass

                #     if button is not None:
                #         try:
                #             self.driver.find_element_by_css_selector('body > div._2dDPU.CkGkG > div.zZYga > div > article > div.eo2As > div.EtaWk > ul > li > div > button > span').click()
                #         except:
                #             break

                # # 대댓글 버튼 누르기
                # buttons = self.driver.find_elements_by_css_selector('li > ul > li > div > button')

                # for button in buttons:
                #     button.send_keys(Keys.ENTER)

                # ids  = self.driver.find_elements_by_css_selector('div.qF0y9.Igw0E.IwRSH.eGOV_._4EzTm.ItkAi')
                # replies = self.driver.find_elements_by_css_selector('div.C7I1f > div.C4VMK > div.MOdxS > span._7UhW9.xLCgt.MMzan.KV-D4.se6yk.T0kll')
                # results = [['' for col in range(2)] for row in range(len(ids))]
                # final_res = pd.DataFrame(final_res)

                # for id, reply in zip(ids, replies):
                #     results[idx][0] = id.text
                #     results[idx][1] = reply.text
                #     idx += 1
                # result_temp = list(itertools.chain.from_iterable(results))
                # final_res.iloc[i] = result_temp
                
                time.sleep(1.5)
                try:
                    self.driver.find_element_by_css_selector('div.l8mY4.feth3').click()
                except:
                    self.text.run('마지막 게시물입니다.')
                    break

                time.sleep(1.5)
                self.text.run('{}번째 게시물 탐색 완료'.format(i+1))
                
        # list_size = []
        # for j in range(len(final_res)):
        #     list_size.append(len(final_res[j]))

        # total_list_size = sum(list_size)
        # final_tmp = [['', '']] * int(total_list_size / 2)
        # final_tmp = pd.DataFrame(final_tmp, columns=['ID', 'Reply'])
        # df_idx = 0
        # for ii in range(len(final_res)):
        #     size = int(len(final_res[ii]) / 2)
        #     for n in range(size):
        #         if n == 0:
        #             final_tmp.iloc[df_idx][0] = final_res[ii][0]       # odd
        #             final_tmp.iloc[df_idx][1] = final_res[ii][1]       # even
        #         else:
        #             final_tmp.iloc[df_idx][0] = final_res[ii][n*2]         # even
        #             final_tmp.iloc[df_idx][1] = final_res[ii][n*2+1]       # odd
        #         df_idx += 1
        
        # df_idx = 0
        current_path = os.getcwd()
        now_time = datetime.datetime.now()
        now_date = now_time.strftime('%Y-%m-%d-%H%M') + '_'
        # 결과값 저장
        final_res2.to_excel("{}\\".format(current_path) + now_date + self.target_word + "_results.xlsx")
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
