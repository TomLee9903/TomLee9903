from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import json
import pandas as pd

user_id = "id"
user_password = "password"
login_option = "facebook"
driver_path = "~/chromedriver"
instagram_id_name = "username"
instargram_pw_name = "password"
instagram_login_btn = ".sqdOP.L3NKy.y3zKF   "
facebook_login_page_css = ".sqdOP.L3NKy.y3zKF   "
facebook_ligin_page_css2 = ".sqdOP.yWX7d.y3zKF   "
facebook_id_from_name = "email"
facebook_pw_from_name = "pass"
facebook_login_btn_name = "login"

print("test")