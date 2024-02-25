
import aliextractor
import aliprocessor
import sys
sys.path.append('Uploader')
sys.path.insert(1, '/Uploader')
import uploadermanager
import json
import openpyxl

class aliitem:
    def __init__(self, code, title,tag, navercategory):
        self.code = code
        self.title = title
        self.tag = tag
        self.navercategory = navercategory

def get_cookies_string(driver):
    cookiels = []
    for cookie in driver.get_cookies():
        if cookie["name"] == "aep_usuc_f":
            cookie["value"] = 'site=kor&province=919800080000000000&city=919800080008000000&c_tp=USD&region=KR&b_locale=ko_KR'
        cookiels.append(cookie["name"] + "=" + cookie["value"])
    return "; ".join(cookiels)
    
def chunklist(l,n):
    for i in range(0,len(l),n):
        yield l[i:i+n]

accinfo = json.load(open("accinfo.json"))
driver = uploadermanager.GetDriver()
print("Please login to Aliexpress and press enter")
input()

workbook = openpyxl.load_workbook('alidata.xlsx')
sheet = workbook.worksheets[0]

aliitems = []
for row in sheet.iter_rows(min_row=2):
    alilink = str(row[13].value)
    aliname = str(row[15].value)
    alitag = str(row[8].value)
    navercategory = str(row[6].value)
    if alilink == None:
        continue
    if alitag == None:
        alitag = ""
    if "/item/" in alilink:
        alilink = alilink.split('.html')[0].split('/')[-1]
    
    aliitems.append(aliitem(alilink, aliname, alitag, navercategory))
        
completed = [line.strip() for line in open('completed.txt', 'r').readlines() if line.strip() != '']
    
for i in range(len(completed)):
    if "/item/" in completed[i]:
        completed[i] = completed[i].split('.html')[0].split('/')[-1]

todo_process = []

for ai in aliitems:
    if ai.code in completed:
        aliitems.remove(ai)
        print(f"Skipping {ai.code}")
    elif ai.code == "None" or ai.code == None:
        print(f"Skipping {ai.code}")
    else:
        todo_process.append(ai)

for chunk in chunklist(todo_process, accinfo["chunksize"]):
    pils = []
    for ai in chunk:
        try:
            si = aliextractor.scrapeali(ai.code, cookiestr=get_cookies_string(driver))
            pi = aliprocessor.processali(si)
            if type(pi.ProductOptions) == str:
                pi.ProductOptions = json.loads(pi.ProductOptions)
            pi.ProductName = ai.title
            pi.ProductTags = ai.tag
            pi.ProductCategory = ai.navercategory
            pils.append(pi)
        except:
            print(f"Error occured while processing {ai.code}")

    uploadermanager.uploaditem(pils)

    open('completed.txt', 'a').write('\n'+'\n'.join([ai.code for ai in chunk]))
    completed += [ai.code for ai in chunk]