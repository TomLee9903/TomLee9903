import psycopg2
import json
from datetime import datetime
import defaultvar


pgdb = psycopg2.connect(
    host=defaultvar.sqlinfo_scraper["host"],
    user=defaultvar.sqlinfo_scraper["user"],
    password=defaultvar.sqlinfo_scraper["password"],
    database=defaultvar.sqlinfo_scraper["database"],
    port=defaultvar.sqlinfo_scraper["port"]
)
pgdb.autocommit = True
# Create the Processed_Item table
mycursor = pgdb.cursor()


# 결과값 반영하기
def Commit():
    pgdb.commit()


# 수집된 상품 정보를 저장해놓는 DB
class ScrapedItem:
    def __init__(self):
        self.ProductID = 0
        self.ProductName = ""
        self.ProductPrice = 0
        self.ProductSoldCount = 0
        self.ProductMainImage = ""
        self.ProductSubImages = ""
        self.ProductCategory = ""
        self.ProductTags = ""
        self.SellerID = "" ####
        self.TaobaoID = 0
        self.TaobaoName = ""
        self.TaobaoPrice = 0
        self.TaobaoMainImage = ""
        self.TaobaoVideoUrl = ""
        self.TaobaoProperties = json.dumps({})
        self.TaobaoDescription = ""
        self.TaobaoOptions = json.dumps({})
        self.KeywordDeliveryFee = 0
        self.Status = 0
        self.Uploader = ""
        self.DeliveryMethod = 0 #0: 해운 1: 항공
        self.Memo = ""
        self.Type = 0 #0: 스토어상품 1: 가격비교 상품
        self.Time = datetime.now()

    def __str__(self):
        return f"ProductID: {self.ProductID}\nProductName: {self.ProductName}\nProductPrice: {self.ProductPrice}\nProductSoldCount: {self.ProductSoldCount}\nProductMainImage: {self.ProductMainImage}\nProductSubImages: {self.ProductSubImages}\nProductCategory: {self.ProductCategory}\nProductTags: {self.ProductTags}\nSellerID: {self.SellerID}\nTaobaoID: {self.TaobaoID}\nTaobaoName: {self.TaobaoName}\nTaobaoPrice: {self.TaobaoPrice}\nTaobaoMainImage: {self.TaobaoMainImage}\nTaobaoVideoUrl: {self.TaobaoVideoUrl}\nTaobaoProperties: {self.TaobaoProperties}\nTaobaoDescription: {self.TaobaoDescription}\nTaobaoOptions: {self.TaobaoOptions}\nKeywordDeliveryFee: {self.KeywordDeliveryFee}\nStatus: {self.Status}\nUploader: {self.Uploader}\nDeliveryMethod: {self.DeliveryMethod}\nMemo: {self.Memo}\nType: {self.Type}\nTime: {self.Time}\n"
    

    def get_items_by_status(self, status):
        sql = """
            SELECT *
            FROM scrape.scrapeditem
            WHERE Status = %s
        """

        mycursor.execute(sql, (status,))
        result = mycursor.fetchall()
        items = []
        for row in result:
            item = ScrapedItem()
            item.ProductID = row[0]
            item.ProductName = row[1]
            item.ProductPrice = row[2]
            item.ProductSoldCount = row[3]
            item.ProductMainImage = row[4]
            item.ProductSubImages = row[5]
            item.ProductCategory = row[6]
            item.ProductTags = row[7]
            item.SellerID = row[8]
            item.TaobaoID = row[9]
            item.TaobaoName = row[10]
            item.TaobaoPrice = row[11]
            item.TaobaoMainImage = row[12]
            item.TaobaoVideoUrl = row[13]
            item.TaobaoProperties =row[14]
            item.TaobaoDescription = row[15]
            item.TaobaoOptions =row[16]
            item.KeywordDeliveryFee = row[17]
            item.Status = row[18]
            item.Uploader = row[19]
            item.DeliveryMethod = row[20]
            item.Memo = row[21]
            item.Type = row[22]
            item.Time = row[23]

            items.append(item)

        return items
    
    def get_items_by_statusandtype(self, status, type):
        sql = """
            SELECT *
            FROM scrape.scrapeditem
            WHERE Status = %s AND "Type" = %s
        """

        mycursor.execute(sql, (status,type,))
        result = mycursor.fetchall()
        items = []
        for row in result:
            item = ScrapedItem()
            item.ProductID = row[0]
            item.ProductName = row[1]
            item.ProductPrice = row[2]
            item.ProductSoldCount = row[3]
            item.ProductMainImage = row[4]
            item.ProductSubImages = row[5]
            item.ProductCategory = row[6]
            item.ProductTags = row[7]
            item.SellerID = row[8]
            item.TaobaoID = row[9]
            item.TaobaoName = row[10]
            item.TaobaoPrice = row[11]
            item.TaobaoMainImage = row[12]
            item.TaobaoVideoUrl = row[13]
            item.TaobaoProperties =row[14]
            item.TaobaoDescription = row[15]
            item.TaobaoOptions =row[16]
            item.KeywordDeliveryFee = row[17]
            item.Status = row[18]
            item.Uploader = row[19]
            item.DeliveryMethod = row[20]
            item.Memo = row[21]
            item.Type = row[22]
            item.Time = row[23]

            items.append(item)

        return items

    
    def get_scraped_from_taobaoid(self, taobao_id):
        mycursor.execute(f"SELECT * FROM ScrapedItem WHERE TaobaoID = {str(taobao_id)} LIMIT 1")
        row = mycursor.fetchone()
        if row:
            scraped_item = ScrapedItem()
            scraped_item.ProductID = row[0]
            scraped_item.ProductName = row[1]
            scraped_item.ProductPrice = row[2]
            scraped_item.ProductSoldCount = row[3]
            scraped_item.ProductMainImage = row[4]
            scraped_item.ProductSubImages = row[5]
            scraped_item.ProductCategory = row[6]
            scraped_item.ProductTags = row[7]
            scraped_item.SellerID = row[8]
            scraped_item.TaobaoID = row[9]
            scraped_item.TaobaoName = row[10]
            scraped_item.TaobaoPrice = row[11]
            scraped_item.TaobaoMainImage = row[12]
            scraped_item.TaobaoVideoUrl = row[13]
            scraped_item.TaobaoProperties = row[14]
            scraped_item.TaobaoDescription = row[15]
            scraped_item.TaobaoOptions = row[16]
            scraped_item.KeywordDeliveryFee = row[17]
            scraped_item.Status = row[18]
            scraped_item.Uploader = row[19]
            scraped_item.DeliveryMethod = row[20]
            scraped_item.Memo = row[21]
            scraped_item.Type = row[22]
            scraped_item.Time = row[23]
            
            return scraped_item
        else:
            return None
    
    
    def change_status(self, new_status):
        sql = """
            UPDATE scrape.scrapeditem
            SET Status = %s
            WHERE ProductID = %s
        """

        values = (new_status, self.ProductID)

        mycursor.execute(sql, values)
        pgdb.commit()
    
    def insert(self):
        sql = """
            INSERT INTO scrape.scrapeditem VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (productid) DO NOTHING;
        """
        values = (
            self.ProductID,
            self.ProductName,
            self.ProductPrice,
            self.ProductSoldCount,
            self.ProductMainImage,
            self.ProductSubImages,
            self.ProductCategory,
            self.ProductTags,
            self.SellerID,
            self.TaobaoID,
            self.TaobaoName,
            self.TaobaoPrice,
            self.TaobaoMainImage,
            self.TaobaoVideoUrl,
            self.TaobaoProperties,
            self.TaobaoDescription,
            self.TaobaoOptions,
            self.KeywordDeliveryFee,
            self.Status,
            self.Uploader,
            self.DeliveryMethod,
            self.Memo,
            self.Type,
            datetime.now()
        )
        mycursor.execute(sql, values)
        pgdb.commit()
        
    def searchsimilarcategory(self, name):
        sql = f"""SELECT "name", categoryid
                FROM scrape.category
                ORDER BY similarity("name" , '{name}') DESC
                LIMIT 1;"""
        mycursor.execute(sql)
        row = mycursor.fetchone()
        return row[1]
        
        
def is_productid_exist(productid):
    mycursor.execute(f"SELECT ProductID FROM scrape.scrapeditem WHERE ProductID = {str(productid)} LIMIT 1")
    row = mycursor.fetchone()
    
    if row:
        return True
    else:
        return False   

if __name__ == "__main__":
    print(is_productid_exist(641156780))
