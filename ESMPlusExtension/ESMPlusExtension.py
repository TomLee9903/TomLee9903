# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSlot

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys
import time
import datetime
import os
import pandas as pd
import threading
import pyautogui
import pygetwindow as gw
import subprocess
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

# QT designer ui 파일 로드
form_class = uic.loadUiType("./driver/main_ui.ui")[0]

# UI 텍스트 출력 클래스
class TextBrowser(QThread):
    # signal을 MyWindow에 전달할 수 있게 하는 인자
    finished = pyqtSignal(str)
    now_date = ''

    @pyqtSlot(str)
    def run(self, print_str):
        self.make_log(print_str)

    @pyqtSlot(str)
    def make_log(self, print_str):
        self.now_time = datetime.datetime.now()
        self.now_date = self.now_time.strftime('[%Y-%m-%d %H:%M:%S]  ') + print_str
        self.finished.emit(self.now_date)   # signal MyWindow에 전달

    def GetTime(self):
        self.now_time = datetime.datetime.now()
        return self.now_time

# UI 구성 클래스
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('./driver/MainImage.png'))    # UI에 구글 번역 icon 설정
        self.run_btn.clicked.connect(self.Run)  # 검색 버튼 누르면 self.Run 함수 실행
        self.process_delay = 1.5
        self.text = TextBrowser()               # UI에 text 출력 위한 객체
        self.windows_user_name = os.path.expanduser('~')
        self.refresh = False

        self.text.finished.connect(self.ConnectTextBrowser) # TextBrowser한테서 signal 받으면 ConnectTextBrowser 함수 실행
        self.exit_btn.clicked.connect(self.QuitProgram) # 종료 버튼 클릭하면 프로그램 종료되게끔 설정 & thread 종료

        # self.setAcceptDrops(True)
        # self.acceptDrops()

    # UI 창닫기 버튼 클릭하면 종료 의사 묻는 팝업창 띄우기
    def closeEvent(self, QCloseEvent): 
        ans = QMessageBox.question(self, "종료 확인", "종료하시겠습니까?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ans == QMessageBox.Yes:
            QCloseEvent.accept()
            self.KillThread()
        else:
            QCloseEvent.ignore()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
 
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.filename = files[0]
        self.df = pd.read_excel(self.filename)
        self.df.fillna('', inplace=True)
        self.text.run('파일 이름 : {}'.format(self.filename.split('/')[-1].replace('.xlsx','')))

    # 종료 버튼 누르면 실행되는 함수
    def QuitProgram(self):
        QCoreApplication.instance().quit
        self.KillThread()

    # 검색 버튼 누르면 실행되는 Run 함수
    def Run(self):
        self.th = threading.Thread(target=self.Start)
        self.th.daemon = True
        self.th.start()

    # 파파고 URL 오픈
    @pyqtSlot()
    def OpenUrl(self):
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9225 --user-data-dir="C:\chrometemp"') # 디버거 크롬 구동
        except:
            subprocess.Popen(r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe --remote-debugging-port=9225 --user-data-dir="C:\chrometemp"') # 디버거 크롬 구동
        
        self.options = webdriver.ChromeOptions()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.83 Safari/537.36"
        self.options.add_argument('user-agent=' + user_agent)
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")

        # 크롬 버전을 확인하여 버전이 안맞으면 자동으로 업데이트 하여 설치해주는 옵션       
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.driver.implicitly_wait(10)
        
        # 속도 향상을 위한 옵션 해제
        self.options.add_argument("disable-gpu") 
        self.options.add_argument("disable-infobars")
        self.options.add_argument("--disable-extensions")
        prefs = {'profile.default_content_setting_values': {'cookies' : 2, 'images': 2, 'plugins' : 2, 'popups': 2, 'geolocation': 2, 'notifications' : 2, 'auto_select_certificate': 2, 'fullscreen' : 2, 'mouselock' : 2, 'mixed_script': 2, 'media_stream' : 2, 'media_stream_mic' : 2, 'media_stream_camera': 2, 'protocol_handlers' : 2, 'ppapi_broker' : 2, 'automatic_downloads': 2, 'midi_sysex' : 2, 'push_messaging' : 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop' : 2, 'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement' : 2, 'durable_storage' : 2}}   
        #self.options.add_experimental_option('prefs', prefs)
        # 크롬 브라우저와 셀레니움을 사용하면서 발생되는 '시스템에 부착된 장치가 작동하지 않습니다.' 라는 크롬 브라우저의 버그를 조치하기 위한 코드. 
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # 윈도우 사이즈 맥스로 키우기
        self.driver.maximize_window()
        self.driver.get('https://signin.esmplus.com/login')
        time.sleep(1)
        pyautogui.press('f12')
        time.sleep(2)
        pyautogui.press('f12')

        self.text.run('알리익스프레스 URL open 완료')
        self.ac = ActionChains(self.driver)  # 셀레니움 동작을 바인딩 하여 동작 할 수 있게 하는 모듈                    

        time.sleep(self.process_delay)
    
    @pyqtSlot()
    # 징동닷컴 크롤링 함수
    def Start(self):
        self.text.run('--Start work--')
        self.text.run('PGM ver : 22102308')
        self.start_time = self.text.GetTime()
        self.i = 0
        self.j = 0

        self.OpenUrl()
        time.sleep(2)
        self.LogIn()
        
        cnt = 0
        while cnt < 100:
            try:
                self.ExtendSalePeriod()
                # log-off
                self.driver.find_element(By.CSS_SELECTOR, '#logoff').click()
                time.sleep(self.process_delay)
            except:
                self.driver.close()
                self.OpenUrl()
                time.sleep(2)
                self.LogIn()
                cnt += 1
                continue
        
        self.end_time = self.text.GetTime()
        diff_time = self.end_time - self.start_time
        self.text.run('--End work--')
        self.text.run('총 소요시간은 {}초 입니다.'.format(diff_time.seconds))
        self.driver.close()

    def LogIn(self):
        ac = ActionChains(self.driver)
        # Get ID/PW
        self.id = self.id_input.text()
        self.pw = self.pw_input.text()

        #self.driver.find_element(By.CSS_SELECTOR, '#container > div > div > div.box__content > div > button.button__tab.button__tab--auction').click()
        self.driver.find_element(By.CSS_SELECTOR, '#container > div > div > div.box__content > div > button.button__tab.button__tab--gmarket').click()
        time.sleep(1)

        # 로그아웃 확인창
        # try:
        #     self.driver.find_element(By.CSS_SELECTOR, '#container > div > div > div.box__layer.is-active > div > div.button__wrap > button').click()
        # except:
        #     pass

        # log-in
        self.id_box = self.driver.find_element(By.CSS_SELECTOR, "#typeMemberInputId01")
        self.pw_box = self.driver.find_element(By.CSS_SELECTOR, "#typeMemberInputPassword01")
        self.login_button = self.driver.find_element(By.CSS_SELECTOR, '#container > div > div > div.box__content > form > div.box__submit > button')
        ac.send_keys_to_element(self.id_box, self.id).send_keys_to_element(self.pw_box, self.pw).click(self.login_button).pause(2).perform()
        time.sleep(5)
        
        # 팝업창 닫기
        if len(self.driver.window_handles) != 1:
            for n in range(len(self.driver.window_handles) - 1):
                last_tab = self.driver.window_handles[-1]
                self.driver.switch_to.window(window_name=last_tab)
                self.driver.close()
                time.sleep(1)
            first_tab = self.driver.window_handles[0]
            self.driver.switch_to.window(window_name=first_tab)
            time.sleep(self.process_delay)

    # 쓰레드 종료
    def KillThread(self):
        pid = os.getpid()
        os.kill(pid, 2)

    # UI에 텍스트 출력
    @pyqtSlot(str)
    def ConnectTextBrowser(self, print_str):
        self.textBrowser.append(print_str)
        self.textBrowser.repaint()

    def ExtendSalePeriod(self):
        while True:
            # 상품 등록/변경 -> 상품관리2.0
            self.driver.find_element(By.CSS_SELECTOR, '#TDM001').click()
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR, '#TDM396').click()
            time.sleep(2)

            # 판매중지 클릭
            cnt = 0
            while cnt < 60:
                ben_sale = pyautogui.locateCenterOnScreen('./driver/ben_sale.PNG', confidence=0.95)
                if ben_sale != None:
                    time.sleep(1)
                    break
                else:
                    time.sleep(1)
                    cnt += 1
            target_x = ben_sale.x - 30
            pyautogui.moveTo(target_x, ben_sale.y)
            pyautogui.click(target_x, ben_sale.y) # 해당 윈도우의 path 클릭
            time.sleep(2)
            
            # # 전체 마켓 선택
            # total_market = pyautogui.locateCenterOnScreen('./driver/select_all.PNG', confidence=0.7)
            # if total_market == None:
            #     break
            # target_x = total_market.x + 30
            # pyautogui.moveTo(target_x, total_market.y)
            # pyautogui.click(target_x, total_market.y)
            # time.sleep(3)

            # 검색하기 클릭
            cnt = 0
            while cnt < 60:
                search_btn = pyautogui.locateCenterOnScreen('./driver/search_btn.PNG', confidence=0.7)
                if search_btn != None:
                    break
                else:
                    time.sleep(1)
                    cnt += 1
            pyautogui.moveTo(search_btn.x, search_btn.y)
            pyautogui.click(search_btn.x, search_btn.y)
            time.sleep(1)

            self.driver.execute_script("window.scrollTo(0, 700)")
            time.sleep(1)

            # 수정 버튼 클릭
            modify_btn = pyautogui.locateCenterOnScreen('./driver/no1_btn.PNG', confidence=0.95)
            if modify_btn != None:
                time.sleep(1)
                target_x = modify_btn.x + 300
                target_y = modify_btn.y + 10
                pyautogui.moveTo(target_x, target_y)
                pyautogui.click(target_x, target_y)
            else:
                break
            time.sleep(5)

            cnt = 0
            while cnt < 60:
                # 판매가능 선택
                cnt = 0
                while cnt < 60:
                    enable_sale = pyautogui.locateCenterOnScreen('./driver/enable_sale.PNG', confidence=0.95)
                    if enable_sale != None:
                        time.sleep(1)
                        break
                    else:
                        time.sleep(1)
                        cnt += 1
                        continue
                target_x = enable_sale.x - 20
                pyautogui.moveTo(target_x, enable_sale.y)
                pyautogui.click(target_x, enable_sale.y)
                time.sleep(3)

                self.driver.execute_script("window.scrollTo(0, 900)")
                time.sleep(1)

                # 기간연장 선택
                extend_sale = pyautogui.locateCenterOnScreen('./driver/extend_btn.PNG', confidence=0.7)
                if extend_sale != None:
                    target_x = extend_sale.x - 20
                    pyautogui.moveTo(target_x, extend_sale.y)
                    pyautogui.click(target_x, extend_sale.y)
                    time.sleep(1)
                else:
                    time.sleep(1)
                    cnt += 1
                    continue
                
                # 판매기간 선택                
                sale_period = pyautogui.locateCenterOnScreen('./driver/select_sale_period.PNG', confidence=0.7)
                if sale_period != None:
                    pyautogui.moveTo(sale_period.x, sale_period.y)
                    pyautogui.click(sale_period.x, sale_period.y)
                    time.sleep(1)
                else:
                    time.sleep(1)
                    cnt += 1
                    continue
                
                # 90일연장 선택
                select_90days = pyautogui.locateCenterOnScreen('./driver/select_90days.PNG', confidence=0.8)
                if select_90days != None:
                    target_y = select_90days.y + 45
                    pyautogui.moveTo(select_90days.x, target_y)
                    pyautogui.click(select_90days.x, target_y)
                    time.sleep(1)
                else:
                    time.sleep(1)
                    cnt += 1
                    continue

                break

            # 수정하기 클릭
            cnt = 0
            while cnt < 60:
                final_btn = pyautogui.locateCenterOnScreen('./driver/final_btn.PNG', confidence=0.7)
                if final_btn != None:
                    break
                else:
                    time.sleep(1)
                    cnt += 1
            pyautogui.moveTo(final_btn.x, final_btn.y)
            pyautogui.click(final_btn.x, final_btn.y)
            time.sleep(1)

            # 팝업창 닫기
            if len(self.driver.window_handles) != 1:
                for n in range(len(self.driver.window_handles) - 1):
                    last_tab = self.driver.window_handles[-1]
                    self.driver.switch_to.window(window_name=last_tab)
                    self.driver.close()
                    time.sleep(1)
                first_tab = self.driver.window_handles[0]
                self.driver.switch_to.window(window_name=first_tab)
                time.sleep(self.process_delay)
            time.sleep(1)

            try:
                result = WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                result = Alert(self.driver)
                result.accept()
                time.sleep(1)
                cnt = 0
                is_done = False
                while cnt < 5:
                    modify_complete = pyautogui.locateCenterOnScreen('./driver/modify_complete.PNG', confidence=0.7)
                    if modify_complete != None:
                        is_done = True
                        break
                    else:
                        time.sleep(1)
                        cnt += 1

                if is_done == True:
                    continue

                self.driver.execute_script("window.scrollTo(0, 1800)")
                time.sleep(1)
                # 승인/신고대상아님
                cnt = 0
                y = 1800
                while cnt < 60:
                    no_approval = pyautogui.locateCenterOnScreen('./driver/no_approval.PNG', confidence=0.7)
                    if no_approval != None:
                        break
                    else:
                        y += 100
                        self.driver.execute_script("window.scrollTo(0, {})".format(y))
                        time.sleep(1)
                        cnt += 1
                pyautogui.moveTo(no_approval.x, no_approval.y)
                pyautogui.click(no_approval.x, no_approval.y)

                # 수정하기 클릭
                cnt = 0
                while cnt < 60:
                    final_btn = pyautogui.locateCenterOnScreen('./driver/final_btn.PNG', confidence=0.7)
                    if final_btn != None:
                        break
                    else:
                        time.sleep(1)
                        cnt += 1
                pyautogui.moveTo(final_btn.x, final_btn.y)
                pyautogui.click(final_btn.x, final_btn.y)
                time.sleep(1)
            except:
                pass
            
            cnt = 0
            while cnt < 60:
                modify_complete = pyautogui.locateCenterOnScreen('./driver/modify_complete.PNG', confidence=0.7)
                if modify_complete != None:
                    break
                else:
                    time.sleep(1)
                    cnt += 1

            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(1)
            self.i += 1
            self.text.run('{}번째 상품 상품기간 연장 성공!'.format(self.i))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()
