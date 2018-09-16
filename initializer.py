import sqlite3
import requests

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

def populateCustomerData():
    #Preset filter:
    url = 'https://api.td-davinci.com/api/simulants/page'
    #Filter Details
    payload = {'continuationToken' : '', 'minAge' : '25', 'maxAge' : '34', 'gender' : 'null', 'workActivity' : 'null', 'schoolAttendance' : 'null' , 'minIncome' : '35000' , 'maxIncome' : '49999.99'}
    headers = { 'Authorization' : 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiZTBmYzI2MGEtOTUyZS0zMzFlLTlmMTMtNzU4ODUzZGNkNDI1IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiJmMGVlMDA5Yy02ZmY3LTQ3ZmEtYWYzOC1hMDBlYTczMDk2NmEifQ.xHkemImCQr9sxUmV32vYz5wrKKeciLHFAxfdE3smN28' , 'Content-Type' : 'application/json', 'Accept' : 'application/json, text/plain, */*' , 'Accept-Encoding' : 'gzip, deflate, br' , 'Connection' : 'keep-alive', 'Referer' : 'https://td-davinci.com/virtual-users?ageGroup=2^&incomeGroup=2' , "Origin" : 'https://td-davinci.com' , 'Host' : 'api.td-davinci.com' , 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'  }

    response = requests.post(url, params=payload, headers=headers)

    #Number of times to populate
    numToPop = 100
    numIterations = round(numToPop/10)
    numIterations = (1, numIterations)[numIterations > 1] #Min 1
    print(numIterations)

    for i in range(numIterations):
        data = response.json()

        # print(data)
        # print(data['result'])
        # print(data['result']['customers'])

        #First loop through the customer data and add
        for cust in data['result']['customers']:
            print(i)
        
        #Exit if we're done (doing this like a do-while)
        if i == (numIterations - 1) : break

        #Now update the payload variable to contain the new continuationToken
        contToken = data['result']['continuationToken']
        payload = {'continuationToken' : contToken, 'minAge' : 'null', 'maxAge' : 'null', 'gender' : 'null', 'workActivity' : 'null', 'schoolAttendance' : 'null' , 'minIncome' : 'null' , 'maxIncome' : 'null'}

        #...And request again
        response = requests.post(url, params=payload, headers=headers)

    #First query
    # print(response.text)

    


# createUserTable()
populateCustomerData()

#Exit 
conn.commit()
c.close()
conn.close()

  



