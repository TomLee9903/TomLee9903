import math 
#SQL 서버 정보
sqlinfo = {
    "host": "testdb-do-user-14707685-0.c.db.ondigitalocean.com",
    "user": "doadmin",
    "password": "AVNS_74mSk2Po9lt1bJAwIsP",
    "database": "GoodChoice",
    "port": 25060
}

sqlinfo_validator = { #6 POOL
    "host": "testdb-do-user-14707685-0.c.db.ondigitalocean.com",
    "user": "doadmin",
    "password": "AVNS_74mSk2Po9lt1bJAwIsP",
    "database": "Validator",
    "port": 25061
}

sqlinfo_scraper = {
    "host": "testdb-do-user-14707685-0.c.db.ondigitalocean.com",
    "user": "doadmin",
    "password": "AVNS_74mSk2Po9lt1bJAwIsP",
    "database": "Scraper",
    "port": 25061
}

sqlinfo_processor = {
    "host": "testdb-do-user-14707685-0.c.db.ondigitalocean.com",
    "user": "doadmin",
    "password": "AVNS_74mSk2Po9lt1bJAwIsP",
    "database": "Processor",
    "port": 25061
}

sqlinfo_other = {
    "host": "testdb-do-user-14707685-0.c.db.ondigitalocean.com",
    "user": "doadmin",
    "password": "AVNS_74mSk2Po9lt1bJAwIsP",
    "database": "Other",
    "port": 25061
}

store_owner = "굿초이스용인"

taobaousername = "yoongu123"
taobaopassword = "Deadpool87!"


#마진 계산기
def pricecalculation(yuan, deliveryfee):
    korean_won = (yuan * 190 * 1.03 * 1.3) + deliveryfee
    korean_won = math.ceil((korean_won)/100)*100
    return korean_won

def alipricecalculation(usdprice):
    korean_won = (usdprice * 1300 * 1.03 * 1.3)
    korean_won = math.ceil((korean_won)/100)*100
    return korean_won

def alipricecalculation_withmargin(usdprice, margin):
    korean_won = (usdprice * 1300 * margin) + 4000
    korean_won = math.ceil((korean_won)/100)*100
    return korean_won

def currencycalculation(yuan):
    return yuan * 190 * 1.03 * 1.3
