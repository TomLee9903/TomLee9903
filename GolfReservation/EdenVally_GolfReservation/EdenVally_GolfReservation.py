from argparse import Action
from asyncore import loop
from calendar import month
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
from selenium.webdriver.common.alert import Alert

import time
import datetime
from fake_useragent import UserAgent
import schedule
import pandas as pd
import threading
import re
import os
import ctypes

# QT designer ui 파일 로드
form_class = uic.loadUiType("./driver/main_window_EdenVally.ui")[0]

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
#        self.setWindowIcon(QIcon('./driver/instagram_img.png'))
        self.start_btn.clicked.connect(self.MakeThread)
        self.auto_weekend_radio.clicked.connect(self.SetReserveType)
        self.auto_week_radio.clicked.connect(self.SetReserveType)
        self.manual_radio.clicked.connect(self.SetReserveType)
        self.retry_radio.clicked.connect(self.SetReserveType)
        self.week_cancel_btn.clicked.connect(self.WeekCanceljob)
        self.weekend_cancel_btn.clicked.connect(self.WeekendCanceljob)
        self.calendarWidget.selectionChanged.connect(self.ShowDate)
        self.exit_event_th1 = False
        self.exit_event_th2 = False
        self.cal_date = self.calendarWidget.selectedDate()

        self.reserve_type = 0
        self.retry = False
        self.process_delay = 5
        self.text = TextBrowser()
        self.text.finished.connect(self.ConnectTextBrowser)
        self.time_table = pd.read_excel('./driver/에덴밸리리조트+타임테이블.xlsx')
        self.time_table = self.time_table.dropna(axis=1)
        time_table = len(self.time_table['에덴코스'])
        self.course_names = list(self.time_table.columns)
        self.thread_list1 = []
        self.thread_list2 = []

        for m in range(time_table):
            self.start_time_combo.addItem(self.time_table.iloc[m][0].strftime('%H:%M'))
            self.end_time_combo.addItem(self.time_table.iloc[m][0].strftime('%H:%M'))

        columns = self.time_table.columns
        for j in range(len(columns)):
            for jj in range(len(self.time_table[columns[j]])):
                self.time_table.iloc[jj][j] = '{}:{}'.format(self.time_table.iloc[jj][j].isoformat().split(':')[0], 
                                                            self.time_table.iloc[jj][j].isoformat().split(':')[1])

    def closeEvent(self, QCloseEvent):
        ans = QMessageBox.question(self, "종료 확인", "종료하시겠습니까?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ans == QMessageBox.Yes:
            QCloseEvent.accept()
            self.KillThread()
        else:
            QCloseEvent.ignore()
    
    def ShowDate(self):
        self.cal_date = self.calendarWidget.selectedDate()
        str_date = self.cal_date.toString('yyyy년 MM월 dd일')
        self.text.run('선택된 날짜 : {}'.format(str_date))

    def SetReserveType(self):
        if self.auto_weekend_radio.isChecked():
            self.reserve_type = 0
        elif self.auto_week_radio.isChecked():
            self.reserve_type = 1
        elif self.manual_radio.isChecked():
            self.reserve_type = 2
        else:
            self.reserve_type = 3
            
    def AutoLogin(self):
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

        self.OpenUrl()
        self.LoginUrl(self.id, self.pw)

    def ManualReserve(self):
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

        self.OpenUrl()
        self.LoginUrl(self.id, self.pw)
        self.EnterReservePage()
        self.DoReserve()
    
    @pyqtSlot()
    def OpenUrl(self):
        self.option = webdriver.ChromeOptions()
        
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
        # 크롬 브라우저와 셀레니움을 사용하면서 발생되는 '시스템에 부착된 장치가 작동하지 않습니다.' 라는 크롬 브라우저의 버그를 조치하기 위한 코드. 
        self.option.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.driver.get('http://golf.edenvalley.co.kr/Member/Login.asp')
        self.text.run('에덴밸리리조트 골프예약 URL open 완료')

        time.sleep(1.5)

    def LoginUrl(self, id, pw):
        self.act = ActionChains(self.driver)
        try:
            self.id_box = self.driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr[6]/td[2]/input");
            self.pw_box = self.driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr[7]/td[2]/input");
            self.login_button = self.driver.find_element_by_xpath('/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr[6]/td[3]');
            self.act.send_keys_to_element(self.id_box, id).send_keys_to_element(self.pw_box, pw).click(self.login_button).perform()
        except:
            self.text.run('로그인 실패')
            self.driver.quit()

        self.text.run('에덴밸리리조트 log-in 완료')

    def DoReserve(self):
        if self.retry == False:
            self.text.run('실시간 예약 시작')
        else:
            self.text.run('다른세팅으로 예약 re-try 시작')
        
        # 주차 계산해서 당일 기준 UI에 세팅된 요일의 다음주 날짜 xpath 세팅
        self.date_dict = {'일요일':1, '월요일':2, '화요일':3, '수요일':4, '목요일':5, '금요일':6, '토요일':7}
        next_month_date_dict = {0:'월요일', 1:'화요일', 2:'수요일', 3:'목요일', 4:'금요일', 5:'토요일', 6:'일요일'}
        now = datetime.datetime.now()
        month = self.cal_date.month()
        str_date_time = self.cal_date.toString('yyyy-MM-dd')
        weekday = datetime.datetime.strptime(str_date_time, '%Y-%m-%d').weekday()
        today_week = self.get_week_no(now.year, now.month, now.day)
        selected_week = self.get_week_no(self.cal_date.year(), self.cal_date.month(), self.cal_date.day())
        week_delta = abs(today_week - selected_week)

        if week_delta >= 2 and now.month != self.cal_date.month():
            self.text.run('선택하신 날짜 {}년 {}월 {}일은 예약할 수 있는 날짜가 아닙니다.'.format(self.cal_date.year(), self.cal_date.month(), self.cal_date.day()))
            time.sleep(1)
            return 0
            
        target_date = next_month_date_dict[weekday]
        find_date = self.date_dict[target_date]
        if today_week < selected_week:
            if week_delta == 1:
                target_xpath = '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr[4]/td[{}]'.format(find_date)
            elif week_delta == 2:
                target_xpath = '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr[5]/td[{}]'.format(find_date)
        elif today_week == selected_week:
            target_xpath = '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr[3]/td[{}]'.format(find_date)
        else:
            self.text.run('선택하신 날짜 {}년 {}월 {}일은 예약할 수 있는 날짜가 지났습니다.'.format(self.cal_date.year(), self.cal_date.month(), self.cal_date.day()))
            time.sleep(1)
            return 0
#        target_xpath = '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr[3]/td[3]'
        
        try:
            clicked_date = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, target_xpath))).text
        except:
            self.text.run('아직 예약할 수 있는 날짜가 아닙니다.')
            time.sleep(1)
            return 0

        date = re.findall(r'\d+', clicked_date)
        if len(date) == 0:
            self.text.run('선택하신 날짜 {}년 {}월 {}일은 예약할 수 있는 날짜가 지났습니다.'.format(self.cal_date.year(), self.cal_date.month(), self.cal_date.day()))
            time.sleep(1)
            return 0

        self.text.run('타겟 예약 날짜 : {}월 {}일 {}'.format(date[0], date[1], target_date))
        
        # 캘린더에서 타겟 날짜 선택
        try:
            target_button = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, target_xpath + '/div')))
            click_btn = target_button.click()
            try:
                WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                alert = Alert(self.driver)
                message = alert.text
                alert.accept()
            except:
                message = ''
                pass
        except:
            self.text.run('아직 예약할 수 있는 날짜가 아닙니다.')
            time.sleep(1)
#            self.driver.quit()
            return 0

        if '지금은 예약시간이 아닙니다' in message:
            self.text.run('지금은 예약시간이 아닙니다. 예약시간은 10시 부터 17시 까지 입니다.')
#            self.driver.quit()
            return 0
        
        elif '해당날짜는 예약이 완료되었습니다' in message:
            self.text.run('해당날짜는 예약이 완료되었습니다')
            return 0
        
        # 에덴~밸리코스까지 UI에 세팅된 시작/종료 시간 사이 시간대로 예약 시작
        course_id = [1, 2]
        target_start_time = self.start_time_combo.currentText()
        target_end_time = self.end_time_combo.currentText()

        target_start_idx = self.time_table[self.time_table[0] == target_start_time].index[0]
        target_end_idx = self.time_table[self.time_table[0] == target_end_time].index[0]
        search_range_df = self.time_table[0][target_start_idx:target_end_idx+1]
        j = 0
        while j < search_range_df.shape[0]:
            time_text = search_range_df.iloc[j]
            break_loop = False
            previous_time = ''
            # 코스 내 타임 테이블과 UI의 시간을 비교하여 xpath setting
            target_idx = (2 * target_start_idx) + 1
            for ii in range(len(course_id)):
                tt = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[3]/td[{}]/table/tbody'.format(course_id[ii]))))
                r = re.compile('\d\d:\d\d')
                m = pd.DataFrame(r.findall(tt.text))
                try:
                    mm = sum(m[m[0].str.contains(time_text[0:3])].values.tolist(), [])
                    break_loop = True
                    break
                except:
                    self.text.run('{}의 {}시 시간대 예약이 다 찼습니다.'.format(self.course_names[ii], time_text[0:2]))
                    break_loop = False
                    previous_time = time_text[0:3]
                    self.driver.refresh()
                    continue

            if break_loop != True:
                amt_drop = len(search_range_df[search_range_df.str.contains(previous_time)])
                j += amt_drop
                self.driver.refresh()
                continue

            is_it = False
            delta = 0
            time_table_text = ''
            idx = -1
            if len(mm) != 0:
                try:
                    idx = m[m[0] == time_text].index[0]
                except:
                    for k in range(len(mm)):
                        i_time = datetime.datetime.strptime(mm[k], '%H:%M')
                        r_time = datetime.datetime.strptime(time_text, '%H:%M')
                        delta = int((r_time - i_time).seconds / 60)
                        if delta > 6:
                            self.text.run('설정된 시간 {} | 웹사이트 시간 {}'.format(time_text, mm[k]))
                            self.text.run('시간 차이가 7분 이상 나는 시간대입니다. 재탐색 중')
                            target_start_idx += 1
                            self.driver.refresh()
                            continue
                        else:
                            idx = m[m[0] == mm[k]].index[0]
                            break
                if idx == -1:
                    self.text.run('설정된 시간 {} | 웹사이트 시간 {}'.format(time_text, mm[k]))
                    self.text.run('설정된 시간이 타임테이블에 없습니다.')
                    j += 1
                    target_start_idx += 1
                    self.driver.refresh()
                    break_loop = False
                    continue
                target_idx = (2 * idx) + 1
                # if len(m) == 1:
                #     try:
                #         tt = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[3]/td[{}]/table/tbody/tr[{}]/td[2]'.format(course_id, target_idx))))
                #         time_table = self.driver.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_upPanel"]/div[2]/div/div[4]/div/div[{}]/table[2]'.format(course_id))
                #         time_table_text = time_table.text
                #     except:
                #         self.text.run('현재 타임테이블에 선택하신 시간이 없습니다. 다른 시간대를 선택해주세요.')
                #         self.text.run('Fail 코스 : {}'.format(course_text))
                #         self.text.run('Fail 시간 : {}'.format(time_text))
                #         j += 1
                #         continue
                #else:
                for ii in range(len(course_id)):
                    try:
                        time_table = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[3]/td[{}]/table/tbody/tr[{}]/td[1]'.format(course_id[ii], target_idx))))
                        time_click = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[3]/td[{}]/table/tbody/tr[{}]/td[2]/a'.format(course_id[ii], target_idx))))
                        time_table_text = time_table.text
                        actual_time = r.findall(time_table_text)[0]
                        break_loop = True
                        message = ''
                        try:
                            time_click.click()
                            WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                            alert = Alert(self.driver)
                            message = alert.text
                            if '현재 다른회원님이 예약중입니다.' in message:
                                alert.accept()
                                self.text.run('{}코스 {}시간은 현재 다른회원님이 예약중입니다. 다른시간대를 선택해 주세요.'.format(self.course_names[ii], actual_time))
                                continue
                            else:
                                self.text.run('{}코스 {}시간 선택에 성공했습니다!'.format(self.course_names[ii], actual_time))
                                is_it = True
                                course_text = self.course_names[ii]
                                break
                        except:
                            self.text.run('{}코스 {}시간 선택에 성공했습니다!'.format(self.course_names[ii], actual_time))
                            is_it = True
                            course_text = self.course_names[ii]
                            break
                    except:
                        self.text.run('설정된 시간 {} | 웹사이트 시간 {}'.format(time_text, mm[k]))
                        self.text.run('현재 {}코스 타임테이블에 선택하신 {} 시간이 없습니다. 다른 시간대를 선택해주세요.'.format(self.course_names[ii], time_text))
                        self.driver.refresh()
                        break_loop = False
                        continue

                if break_loop != True:
                    j += 1
                    target_start_idx += 1
                    self.driver.refresh()
                    continue
            else:
                self.text.run('{}시 시간대 예약이 다 찼습니다. 다른 시간대를 이용해주세요.'.format(time_text[0:2]))
                previous_time = time_text[0:3]
                amt_drop = len(search_range_df[search_range_df.str.contains(previous_time)])
                j += amt_drop
                self.driver.refresh()
                break_loop = False
                continue
            
            if is_it == True:
                confirm_reserve = self.driver.find_element_by_xpath('/html/body/table[1]/tbody/tr[7]/td/input').click()
    #                confirm_reserve = self.driver.find_element_by_xpath('/html/body/table[1]/tbody/tr[7]/td/input')
                try:
                    result = WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                    result = Alert(self.driver)
                    result.accept()
                except:
                    pass
                self.text.run('')
                self.text.run('{}코스 {} 예약이 성공적으로 완료 되었습니다.'.format(course_text, actual_time))
                time.sleep(3)
                self.end_time = self.text.GetTime()
                diff_time = self.end_time - self.start_time
                self.text.run('--End work--')
                self.text.run('총 소요시간은 {}초 입니다.'.format(diff_time.seconds))
                break
            else:
                if j == len(search_range_df.shape[0]) - 1:
                    self.end_time = self.text.GetTime()
                    diff_time = self.end_time - self.start_time
                    self.text.run('실시간 예약에 실패했습니다.')
                    self.text.run('--End work--')
                    self.text.run('총 소요시간은 {}초 입니다.'.format(diff_time.seconds))
                else:
                    self.text.run('실시간 예약에 실패했습니다. 다시 시도해주세요.')
                    j += 1
                    target_start_idx += 1
                    self.driver.refresh()
                    continue

    def get_week_no(self, y, m, d):
        target = self.get_date(y, m, d)
        firstday = target.replace(day=1)
        if firstday.weekday() == 6:
            origin = firstday
#        elif firstday.weekday() < 3:
        else:
            origin = firstday - datetime.timedelta(days=firstday.weekday() + 1)
        # else:
        #     origin = firstday + datetime.timedelta(days=6-firstday.weekday())
        return (target - origin).days // 7 + 1
    
    def get_date(self, y, m, d):
        '''y: year(4 digits)
        m: month(2 digits)
        d: day(2 digits'''
        s = f'{y:04d}-{m:02d}-{d:02d}'
        return datetime.datetime.strptime(s, '%Y-%m-%d')
    
    @pyqtSlot(str)
    def ConnectTextBrowser(self, print_str):
        self.textBrowser.append(print_str)
        self.textBrowser.repaint()
    
    def MakeThread(self):
        if self.reserve_type == 0:
            self.exit_event_th1 = False
            self.th1 = threading.Thread(target=self.ScheduleLoginForWeekend)
            self.th1.start()
            self.thread_list1.append(self.th1)
        
        elif self.reserve_type == 1:
            self.exit_event_th2 = False
            self.th2 = threading.Thread(target=self.ScheduleLoginForWeek)
            self.th2.start()
            self.thread_list2.append(self.th2)

        elif self.reserve_type == 2:
            self.th3 = threading.Thread(target=self.ManualReserve)
            self.th3.start()

        elif self.reserve_type == 3:
            self.th4 = threading.Thread(target=self.RetryReserve)
            self.th4.start()

    def RetryReserve(self):
        self.retry = True
        self.EnterReservePage()
        self.DoReserve()
    
    def EnterReservePage(self):
        # 실시간 예약 화면 enter
        try:
            calendar = self.driver.get('http://golf.edenvalley.co.kr/Reserve/Calendar.asp')
#            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#aspnetForm > div.mainContainer > div.cntContainer > h3')))
        except:
            self.text.run('예약 화면인지 확인 바람')
            self.driver.quit()
            return 0
        self.text.run('실시간 예약 화면으로 enter 성공!')

    def RefreshWeb(self):
        self.driver.refresh()
        self.text.run('웹페이지 refersh!')

    def ScheduleLoginForWeekend(self):

        self.text.run('주말 자동 예약 설정 완료. 수요일 오전 9시 58분 경 URL 오픈 및 로그인 예정')
        self.text.run('주말 자동 예약 설정 완료. 수요일 오전 9시 59분 30초 경 예약 화면 진입 예정')
        self.text.run('주말 자동 예약 설정 완료. 수요일 오전 10시 00분 경 새로고침 후 예약 시작 예정')

        self.job1 = schedule.every().wednesday.at('09:58').do(self.AutoLogin)
        self.job2 = schedule.every().wednesday.at('09:59:30').do(self.EnterReservePage)
        self.job3 = schedule.every().wednesday.at('10:00:00').do(self.RefreshWeb)
        self.job4 = schedule.every().wednesday.at('10:00:01').do(self.DoReserve)

        # self.job1 = schedule.every().day.at('02:45').do(self.AutoLogin)
        # self.job2 = schedule.every().day.at('02:45:30').do(self.EnterReservePage)
        # self.job3 = schedule.every().day.at('02:46:00').do(self.RefreshWeb)
        # self.job4 = schedule.every().day.at('02:46:01').do(self.DoReserve)

        while True:
            if self.exit_event_th1 == True:
                break
            schedule.run_pending()
            time.sleep(1)

    def ScheduleLoginForWeek(self):

        self.text.run('평일 자동 예약 설정 완료. 월요일 오전 9시 58분 경 URL 오픈 및 로그인 예정')
        self.text.run('평일 자동 예약 설정 완료. 월요일 오전 9시 59분 30초 경 예약 화면 진입 예정')
        self.text.run('평일 자동 예약 설정 완료. 월요일 오전 10시 00분 경 새로고침 후 예약 시작 예정')

        self.job5 = schedule.every().monday.at('09:58').do(self.AutoLogin)
        self.job6 = schedule.every().monday.at('09:59:30').do(self.EnterReservePage)
        self.job7 = schedule.every().monday.at('10:00:00').do(self.RefreshWeb)
        self.job8 = schedule.every().monday.at('10:00:01').do(self.DoReserve)

        # self.job5 = schedule.every().day.at('02:41').do(self.AutoLogin)
        # self.job6 = schedule.every().day.at('02:41:30').do(self.EnterReservePage)
        # self.job7 = schedule.every().day.at('02:42:00').do(self.RefreshWeb)
        # self.job8 = schedule.every().day.at('02:42:01').do(self.DoReserve)

        while True:
            if self.exit_event_th2 == True:
                break
            schedule.run_pending()
            time.sleep(1)

    def KillThread(self):
        self.driver.quit()
        pid = os.getpid()
        os.kill(pid, 2)

    def WeekendCanceljob(self):
        for t in self.thread_list1:
            self.exit_event_th1 = True
            schedule.cancel_job(self.job1)
            schedule.cancel_job(self.job2)
            schedule.cancel_job(self.job3)
            schedule.cancel_job(self.job4)
            t.join()
            self.th1.join()
        self.text.run('주말 자동 예약 설정 해제')
        self.thread_list1 = []

    def WeekCanceljob(self):
        for t in self.thread_list2:
            self.exit_event_th2 = True
            schedule.cancel_job(self.job5)
            schedule.cancel_job(self.job6)
            schedule.cancel_job(self.job7)
            schedule.cancel_job(self.job8)
            t.join()
            self.th2.join()
        self.text.run('평일 자동 예약 설정 해제')
        self.thread_list2 = []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()