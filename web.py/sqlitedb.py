import web
from operator import itemgetter



db = web.database(dbn='sqlite',
        db='auctions.db'
    )

######################BEGIN HELPER METHODS######################

# Enforce foreign key constraints
# WARNING: DO NOT REMOVE THIS!
def enforceForeignKey():
    db.query('PRAGMA foreign_keys = ON')

# initiates a transaction on the database
def transaction():
    return db.transaction()
# Sample usage (in auctionbase.py):
#
# t = sqlitedb.transaction()
# try:
#     sqlitedb.query('[FIRST QUERY STATEMENT]')
#     sqlitedb.query('[SECOND QUERY STATEMENT]')
# except Exception as e:
#     t.rollback()
#     print str(e)
# else:
#     t.commit()
#
# check out http://webpy.org/cookbook/transactions for examples

# returns the current time from your database
#-------------------------------------------------------------------------------------------------------------------
#This two methods are used to manipulate with time to get the current time or
# set the current time

def getTime():
    # the correct column and table name in your database
    query_string = 'select Time from CurrentTime'
    results = query(query_string)
    return results[0].Time

#update the current time
def setTime(select_time):
    query_string = 'Update CurrentTime Set Time = $time'
    query(query_string, {'time': select_time})


#-------------------------------------------------------------------------------------------------------------------
#Those two methods are related with add bit, first check if this auction is open or not,
#if all information is correct, it add this bid to database

#return true, if it is open
def checkStatus(itemID):
    time = getTime()
    Item = getItemById(itemID)
    print(Item)
    # it is open current time is within start and end and buyprice is not reached
    return (time >= Item['Started'] and time <= Item['Ends']) \
           and not (Item["Buy_Price"] != None and Item["Buy_Price"] <= Item["Currently"] and Item["Number_of_Bids"] != 0)


def insertBids(itemID, userID, Amount):
    Time = getTime()
    query_string = "Insert Into Bids(ItemID, UserID, Amount, Time) values ($itemid, $userid, $amount, $time)"
    query(query_string, {'itemid': itemID, 'userid': userID, 'amount': Amount, 'time': Time})
#-------------------------------------------------------------------------------------------------------------------
#Those methods are used to search for an sepcific item by its attributes such as ItemID,
#sellerID, price, status, description, category, etc.
#return a single item specified by the Item's category
def getItemByCategory(cat):
    query_string = "SELECT i.ItemID FROM Categories c , Items i WHERE Category = $category AND c.ItemID = i.ItemID"
    result = query(query_string, {'category': cat})
    result = map(itemgetter('ItemID'), result)
    return result

def getItemByUserID(user_id):
    query_string = "SELECT ItemID FROM Items WHERE Seller_UserID = $Seller_ID"
    result = query(query_string, {'Seller_ID': user_id})
    result = map(itemgetter('ItemID'), result)
    return result

def getItemByDesc(Desc):
    query_string = "SELECT ItemID FROM Items WHERE Description LIKE $itemDesc"
    result = query(query_string, {'itemDesc': "%" + Desc + "%"})
    result = map(itemgetter('ItemID'), result)
    return result

#search item by its current price
def getItemByMaxPrice(max):
    query_string = "SELECT ItemID FROM Items WHERE Currently <= $maxPrice"
    result = query(query_string, {'maxPrice': max})
    result = map(itemgetter('ItemID'), result)
    return result

def getItemByMinPrice(min):
    query_string = "SELECT ItemID FROM Items WHERE Currently >= $minPrice"
    result = query(query_string, {'minPrice': min})
    result = map(itemgetter('ItemID'), result)
    return result

def getItemByStatus(status):
    if status == 'open':
        query_string = "SELECT i.ItemID FROM Items i, CurrentTime CT WHERE CT.Time <= i.Ends AND CT.Time >= i.Started " \
                       "AND ((i.Buy_Price != -999 AND i.Currently < i.Buy_Price) OR i.Buy_Price == -999)"
    elif status == 'close':
        query_string = "SELECT i.ItemID FROM Items i, CurrentTime CT WHERE CT.Time > i.Ends " \
                       "OR (i.Buy_Price != -999 AND i.Currently >= i.Buy_Price)"
    elif status == "notStarted":
        query_string = "SELECT i.ItemID FROM Items i, CurrentTime CT WHERE CT.Time < i.Started"
    else:
        query_string = "SELECT i.ItemID FROM Items"
    result = query(query_string)
    result = map(itemgetter('ItemID'), result)
    return result

def search(itemID, userID, cat, Desc, max, min, status):
    setList = []
    if itemID == userID == cat == Desc == max == min == "" and status == "all":
        raise Exception("Please fill in a search field!")
    if itemID != "":
        newList = [int(itemID)]
        setList.append(set(newList))
    if userID != "":
        setList.append(set(getItemByUserID(userID)))
    if cat != "":
        setList.append(set(getItemByCategory(cat)))
    if Desc != "":
        setList.append(set(getItemByDesc(Desc)))
    if max != "":
        setList.append(set(getItemByMaxPrice(max)))
    if min != "":
        setList.append(set(getItemByMinPrice(min)))
    if status != "all":
        setList.append(set(getItemByStatus(status)))
    print(setList)
    u = set.intersection(*setList)
    print(u)
    #print(u)
    return u

#-------------------------------------------------------------------------------------------------------------------
#Those method is used for the search method in auctionbase.py, it mainly returns the
#information of an item by its itemID when it satisfies all constraints.
def getItemById(item_id):
    query_string = 'select * from Items where ItemID = $itemID'
    result = query(query_string, {'itemID': item_id})
    print(result[0].Currently)
    print(result[0].Buy_Price)
    return result[0]

def getCategoryByID(item_id):
    query_string = "SELECT category FROM Categories WHERE ItemID = $itemID"
    result = query(query_string, {'itemID': item_id})
    return result

def getBidsByID(item_id):
    query_string = "SELECT * From Bids WHERE ItemID = $itemID"
    result = query(query_string, {'itemID': item_id})
    return result

def getWinnerByID(item_id):
    query_string = "SELECT UserID From Bids WHERE ItemID = $itemID Order BY Amount Desc LIMIT 1"
    result = query(query_string, {'itemID': item_id})
    return result
#-------------------------------------------------------------------------------------------------------------------

# wrapper method around web.py's db.query method
# check out http://webpy.org/cookbook/query for more info
def query(query_string, vars = {}):
    value = db.query(query_string, vars)
    if not isinstance(value, int):
        return list(value)
    #return list(db.query(query_string, vars))

#####################END HELPER METHODS#####################

#TODO: additional methods to interact with your database,
# e.g. to update the current time
