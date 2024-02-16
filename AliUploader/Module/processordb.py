import psycopg2
import json
from datetime import datetime
import defaultvar

pgdb = psycopg2.connect(
    host=defaultvar.sqlinfo_processor["host"],
    user=defaultvar.sqlinfo_processor["user"],
    password=defaultvar.sqlinfo_processor["password"],
    database=defaultvar.sqlinfo_processor["database"],
    port=defaultvar.sqlinfo_processor["port"]
)
pgdb.autocommit = True

mycursor = pgdb.cursor()

# 결과값 반영하기
def Commit():
    pgdb.commit()

def lst2pgarr(alist):
    return '{' + ','.join(alist) + '}'

def getuserinfo(userid):
    sql = """
        SELECT
            smartstoreauth,
            gmarketauth,
            auctionauth,
            elevenauth,
            interparkauth,
            coupangauth
        FROM process.userinfo
        WHERE ownerid = %s
    """

    mycursor.execute(sql, (userid,))
    result = mycursor.fetchone()

    userinfo = {
        "smartstoreauth": result[0],
        "gmarketauth": result[1],
        "auctionauth": result[2],
        "elevenauth": result[3],
        "interparkauth": result[4],
        "coupangauth": result[5]
    }
    return userinfo

def getuploadinfo(productid):
    sql = """
        SELECT
            smartstoreid,
            gmarketid,
            auctionid,
            elevenid,
            interparkid,
            coupangid
        FROM process.uploadeditem
        WHERE productid = %s
    """

    mycursor.execute(sql, (productid,))
    result = mycursor.fetchone()

    uploadinfo = {
        "smartstoreid": result[0],
        "gmarketid": result[1],
        "auctionid": result[2],
        "elevenid": result[3],
        "interparkid": result[4],
        "coupangid": result[5]
    }
    return uploadinfo

# SEO 작업을 거친 상품 DB
class ProcessedItem:
    def __init__(self):
        self.ProductID = 0
        self.TaobaoID = 0
        self.ProductName = ""
        self.ProductOriginPrice = 0
        self.ProductPrice = 0
        self.ProductDeliveryFee = 0
        self.ProductCategory = 0
        self.ProductMainImage = ""
        self.ProductSubImages = ""
        self.ProductVideo = ""
        self.ProductDescData = [] ## Array
        self.ProductProperties = json.dumps({})
        self.ProductOptions = json.dumps({})
        self.ProductTags = ""
        self.Status = 0
        self.Type = 0
        self.Owner = ""
        self.Time = datetime.now()
        self.ProductHtmlDescription = ""
        self.CoupangHtmlDescription = ""
        
    def get_items_by_status(self, status):
        sql = """
            SELECT
                productid,
                taobaoid,
                name,
                originprice,
                price,
                deliveryfee,
                category,
                mainimage,
                subimages,
                video,
                descdata,
                properties,
                options,
                tags,
                status,
                type,
                ownerid,
                lastupdated
            FROM process.processeditem
            WHERE Status = %s
        """

        mycursor.execute(sql, (status,))
        result = mycursor.fetchall()

        items = []
        for row in result:
            item = ProcessedItem()
            item.ProductID = row[0]
            item.TaobaoID = row[1]
            item.ProductName = row[2]
            item.ProductOriginPrice = row[3]
            item.ProductPrice = row[4]
            item.ProductDeliveryFee = row[5]
            item.ProductCategory = row[6]
            item.ProductMainImage = row[7]
            item.ProductSubImages = row[8]
            item.ProductVideo = row[9]
            item.ProductDescData = row[10] #
            item.ProductProperties = row[11]
            item.ProductOptions = row[12]
            item.ProductTags = row[13]
            item.Status = row[14]
            item.Type = row[15]
            item.Owner = row[16]
            item.Time = row[17]
            
            items.append(item)

        return items
    
    def get_ali_items(self, status):
        sql = """
            SELECT
                productid,
                taobaoid,
                name,
                originprice,
                price,
                deliveryfee,
                category,
                mainimage,
                subimages,
                video,
                descdata,
                properties,
                options,
                tags,
                status,
                type,
                ownerid,
                lastupdated
            FROM process.processeditem
            WHERE Status = %s AND "type" = 2
        """

        mycursor.execute(sql, (status,))
        result = mycursor.fetchall()

        items = []
        for row in result:
            item = ProcessedItem()
            item.ProductID = row[0]
            item.TaobaoID = row[1]
            item.ProductName = row[2]
            item.ProductOriginPrice = row[3]
            item.ProductPrice = row[4]
            item.ProductDeliveryFee = row[5]
            item.ProductCategory = row[6]
            item.ProductMainImage = row[7]
            item.ProductSubImages = row[8]
            item.ProductVideo = row[9]
            item.ProductDescData = row[10] #
            item.ProductProperties = row[11]
            item.ProductOptions = row[12]
            item.ProductTags = row[13]
            item.Status = row[14]
            item.Type = row[15]
            item.Owner = row[16]
            item.Time = row[17]
            
            items.append(item)

        return items
    
    def get_item_by_ProductID(self, productid):
        sql = """
            SELECT
                productid,
                taobaoid,
                name,
                originprice,
                price,
                deliveryfee,
                category,
                mainimage,
                subimages,
                video,
                descdata,
                properties,
                options,
                tags,
                status,
                type,
                ownerid,
                lastupdated
            FROM process.processeditem
            WHERE ProductID = %s
        """

        mycursor.execute(sql, (productid,))
        result = mycursor.fetchone()

        row = result
        self.ProductID = row[0]
        self.TaobaoID = row[1]
        self.ProductName = row[2]
        self.ProductOriginPrice = row[3]
        self.ProductPrice = row[4]
        self.ProductDeliveryFee = row[5]
        self.ProductCategory = row[6]
        self.ProductMainImage = row[7]
        self.ProductSubImages = row[8]
        self.ProductVideo = row[9]
        self.ProductDescData = row[10] #
        self.ProductProperties = row[11]
        self.ProductOptions = row[12]
        self.ProductTags = row[13]
        self.Status = row[14]
        self.Type = row[15]
        self.Owner = row[16]
        self.Time = row[17]

    def change_status(self, new_status):
        sql = """
            UPDATE process.processeditem
            SET status = %s
            WHERE taobaoid = %s
        """
        values = (new_status, self.TaobaoID)
        mycursor.execute(sql, values)
        pgdb.commit()
    
    ####
    def change_storeids(self, smartstoreid = 0, gmartketid = 0, auctionid = 0, elevenid = 0, interparkid = 0, coupangid = 0):
        sql = """
            UPDATE process.uploadeditem
            SET SmartStoreID = %s, GmarketID = %s, AuctionID = %s, ElevenID = %s, InterparkID = %s, CoupangID = %s
            WHERE ProductID = %s 
        """
        values = (smartstoreid, gmartketid, auctionid, elevenid, interparkid, coupangid, self.ProductID)
        print(mycursor.execute(sql, values))
        pgdb.commit()


    def insert(self):
        sql = """
            INSERT INTO process.processeditem VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            self.ProductID,
            self.TaobaoID,
            self.ProductName,
            self.ProductOriginPrice,
            self.ProductPrice,
            self.ProductDeliveryFee,
            self.ProductCategory,
            self.ProductMainImage,
            self.ProductSubImages,
            self.ProductVideo,
            lst2pgarr(self.ProductDescData),
            self.ProductProperties,
            self.ProductOptions,
            self.ProductTags,
            self.Status,
            self.Type,
            self.Owner,
            datetime.now()
        )
        mycursor.execute(sql, values)
        pgdb.commit()
        

if __name__ == "__main__":
    pass