import sqlite3
import requests

#__________________________________________________________________________________

#Global variables

#Filter Settings
ageMin = 22
ageMax = 32
minIncome = 30000
maxIncome = 60000

#__________________________________________________________________________________

#Connect
conn = sqlite3.connect('data.db')
c = conn.cursor()

def createUserTable(): 
    c.execute("""CREATE TABLE IF NOT EXISTS customers (
                id text,
                givenName text,
                surName text,
                occupationIndustry integer,
                salary integer,
                age integer,
                spouse integer,
                lastDiscount integer,
                lastWeightedScore integer,
                couponHistory blob
                )""")

def deleteUserTable():
    #Purge and try again later
    c.execute("""DROP TABLE customers""")

def populateCustomerData():
    #Preset filter:
    url = 'https://api.td-davinci.com/api/simulants/page'
    #Filter Details
    payload = {'continuationToken' : '', 'gender' : 'null',  'maxAge' : '34', 'maxIncome' : '49999.99', 'minAge' : '25', 'minIncome' : '35000' , 'schoolAttendance' : 'null' , 'workActivity' : 'null'}

    headers = { 
        'Authorization' : 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiZTBmYzI2MGEtOTUyZS0zMzFlLTlmMTMtNzU4ODUzZGNkNDI1IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiJmMGVlMDA5Yy02ZmY3LTQ3ZmEtYWYzOC1hMDBlYTczMDk2NmEifQ.xHkemImCQr9sxUmV32vYz5wrKKeciLHFAxfdE3smN28' ,
        'Content-Type' : 'application/json', 
        'Accept' : 'application/json, text/plain, */*' ,
        'Accept-Encoding' : 'gzip, deflate, br' ,
        'Connection' : 'keep-alive',
        'Referer' : 'https://td-davinci.com/virtual-users?ageGroup=2^&incomeGroup=2',
        "Origin" : 'https://td-davinci.com',
        'Host' : 'api.td-davinci.com',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36' }

    response = requests.post(url, params=payload, headers=headers)
    data = response.json() 
    #Number of times to populate
    numToPop = 100

    #Filter manually, since it doesn't work when I curl request
    #This takes longer but allows for better granularity anyways

    totalMatched = 0

    while totalMatched < numToPop:
        for i in range(10):
            cust = data['result']['customers'][i]

            #Check if meets criteria
            if cust["age"] <= ageMin or cust["age"] >= ageMax or cust["totalIncome"] <= minIncome or cust["totalIncome"] >= maxIncome :
                continue
            
            #Parse data if meets criteria
            occupationalCode = cust["occupationIndustry"][0:4]
            if isinstance(occupationalCode, str): 
                occupationalCode = "0000"
            else:
                 occupationalCode = str(occupationalCode)

            query = "'" + cust["id"] + "'" + ","
            query += "'" + cust["givenName"] + "'" + ","
            query += "'" + cust["surname"] + "'" + ","
            query += occupationalCode  + "," #4 letter code
            query += str(round(cust["totalIncome"])) + ","
            query += str(cust["age"]) + ","
            query += ("0","1")[cust["relationshipStatus"] == "Married"] + ","

            #New user default starter
            query += "0,"
            query += "0,"
            query += "null"

            # print(query)
            print (cust["age"])

            #Add user to table
            # c.execute("INSERT INTO customers VALUES(" + query + ")" )
            # print(i)

            totalMatched += 1
            if (totalMatched > numToPop): break
        
        if (totalMatched > numToPop): break
        #Query again as not enough users
        contToken = data['result']['continuationToken']
        payload = {'continuationToken' : contToken, 'minAge' : 'null', 'maxAge' : 'null', 'gender' : 'null', 'workActivity' : 'null', 'schoolAttendance' : 'null' , 'minIncome' : 'null' , 'maxIncome' : 'null'}

        #...And request again
        response = requests.post(url, params=payload, headers=headers)
        data = response.json()
    
    #Finished gathering users




    

# createUserTable()
populateCustomerData()

#Exit 
conn.commit()
c.close()
conn.close()

  



