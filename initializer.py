import sqlite3
import requests
import sys
import json
#__________________________________________________________________________________

#Global variables

#Filter Settings
minAge = 25
maxAge = 34
minIncome = 35000
maxIncome = 50000

#__________________________________________________________________________________

#Connect
conn = sqlite3.connect('data.db')
c = conn.cursor()

def createUserTable(): 
    c.execute("""CREATE TABLE IF NOT EXISTS customers (
                id text,
                givenName text,
                surName text,
                address text,
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
    url = 'https://api.td-davinci.com/api/simulants/page'
    contToken = None
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

    #Number of times to populate
    numToPop = 5

    #Filter manually, since it doesn't work when I curl request
    #This takes longer but allows for better granularity anyways

    totalMatched = 0

    while totalMatched < numToPop:
        payload = {'continuationToken' : contToken, 'minAge' : minAge, 'maxAge' : maxAge, 'gender' : None, 'workActivity' : None, 'schoolAttendance' : None , minIncome : None , 'maxIncome' : maxIncome}
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        data = response.json() 
        # print(data)
        contToken = data['result']['continuationToken']

        for i in range(len(data['result']['customers'])):
            cust = data['result']['customers'][i]

            #Check if meets criteria
            if cust["age"] <= minAge or cust["age"] >= maxAge or round(cust["totalIncome"]) <= minIncome or round(cust["totalIncome"]) >= maxIncome :
                continue
            
            #Parse data if meets criteria
            occupationalCode = cust["occupationIndustry"][0:4]
            if isinstance(occupationalCode, str): 
                occupationalCode = "0000"
            else:
                 occupationalCode = str(occupationalCode)

            address = cust["addresses"]["principalResidence"]["streetNumber"] + " "
            address += cust["addresses"]["principalResidence"]["streetName"] + ", "
            address += cust["addresses"]["principalResidence"]["municipality"] + " "
            address += cust["addresses"]["principalResidence"]["province"] + ", "
            address += cust["addresses"]["principalResidence"]["postalCode"]
            
            query = "'" + cust["id"] + "'" + ","
            query += "'" + cust["givenName"] + "'" + ","
            query += "'" + cust["surname"] + "'" + ","
            query += "'" + address + "'"  + ","
            query += occupationalCode  + "," #4 letter code
            query += str(round(cust["totalIncome"])) + ","
            query += str(cust["age"]) + ","
            query += ("0","1")[cust["relationshipStatus"] == "Married"] + ","

            print(query)
            # print (cust["age"])

            #Add user to table
            # c.execute("INSERT INTO customers VALUES(" + query + ")" )
            # print(i)

            totalMatched += 1
            if (totalMatched >= numToPop): break
    
        #Finshed checking query
        
        if (totalMatched >= numToPop): break
        #Query again as not enough users
        
    
    #Finished gathering users

def manualLoad():
    for i in range(10):
        with open("./files/file" + str(i+1) + ".json") as f:
            data = json.load(f)

            for i in range(len(data['result']['customers'])):
                cust = data['result']['customers'][i]
                
                #Parse data if meets criteria
                occupationalCode = cust["occupationIndustry"][0:4]
                if isinstance(occupationalCode, str): 
                    occupationalCode = "0000"
                else:
                    occupationalCode = str(occupationalCode)

                address = cust["addresses"]["principalResidence"]["streetNumber"] + " "
                address += cust["addresses"]["principalResidence"]["streetName"] + ", "
                address += cust["addresses"]["principalResidence"]["municipality"] + " "
                address += cust["addresses"]["principalResidence"]["province"] + ", "
                address += cust["addresses"]["principalResidence"]["postalCode"]

                query = "'" + cust["id"] + "'" + ","
                query += "'" + cust["givenName"] + "'" + ","
                query += "'" + cust["surname"] + "'" + ","
                query += "'" + address + "'"  + ","
                query += occupationalCode  + "," #4 letter code
                query += str(round(cust["totalIncome"])) + ","
                query += str(cust["age"]) + ","
                query += ("0","1")[cust["relationshipStatus"] == "Married"] + ","
     

                #New user default starter
                query += "0,"
                query += "0,"
                query += "null"

                print (cust["age"])

                #Add user to table
                c.execute("INSERT INTO customers VALUES(" + query + ")" )
    
# deleteUserTable()
# createUserTable()
populateCustomerData()
# manualLoad()

#Exit 
conn.commit()
c.close()
conn.close()

  



