import sqlite3
import requests

#__________________________________________________________________________________

#Global variables

#Score Settings
competitors={"Tim Hortons", "McDonald's"} #List of Competitors
ourBrand = "Metro" #Our Company
significantSpendAvg = 100 #If a company spends more than this, they are significant

#__________________________________________________________________________________

conn = sqlite3.connect('data.db')
c = conn.cursor()

#Theoretically once a month
def rateCustomers():
    c.execute("""SELECT id,lastWeightedScore FROM customers""")

    #For curl call later
    headers = { 
        'Authorization' : 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiZTBmYzI2MGEtOTUyZS0zMzFlLTlmMTMtNzU4ODUzZGNkNDI1IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiJmMGVlMDA5Yy02ZmY3LTQ3ZmEtYWYzOC1hMDBlYTczMDk2NmEifQ.xHkemImCQr9sxUmV32vYz5wrKKeciLHFAxfdE3smN28' ,
        'Accept' : 'application/json, text/plain, */*' }

    for row in c.fetchall():
        id = row[0]
        url = "https://api.td-davinci.com/api/customers/" + id + "/transactions"
        response = requests.post(url, data=None, headers=headers)
        data = response.json() 

        #Track use of money
        spentWithUs = 0
        spentAtComp = 0

        for transaction in data["result"]:
            if transaction["merchantName"] in competitors:
                spentAtComp += round(transaction["currencyAmount"])
            else if transaction["merchantName"] is ourBrand:
                spentWithUs += round(transaction["currencyAmount"])

        #Monetary significance * Ratio Spent at Comp
        newScore = ((spentWithUs+spentAtComp) / significantSpendAvg) * spentAtComp/spentWithUs

        #Now factor in the previous score; boost if they still aren't spending
        lastScore = row[1]
        if newScore > lastScore:
            if spentAtComp/spentWithUs < 0.1:
                newScore *= 0.5 #conversion not working
            else:
                newScore *= 1.1

#Exit 
conn.commit()
c.close()
conn.close()
