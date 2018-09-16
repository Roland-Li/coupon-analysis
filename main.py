import sqlite3
import requests
import tensorflow as tf
from tensorflow import keras
import numpy as np
import math

#__________________________________________________________________________________

#Global variables

#Score Settings
competitors={"Tim Hortons", "McDonald's"} #List of Competitors
ourBrand = "Metro" #Our Company
significantSpendAvg = 100 #If a company spends more than this, they are significant
maxDiscount = 0.5
dayFilter = 30 #Limits transactions within 30 days

#__________________________________________________________________________________

conn = sqlite3.connect('data.db')
c = conn.cursor()

#Theoretically once a month, re-score a customer
def rateCustomers():
    c.execute("""SELECT id,lastWeightedScore,lastDiscount,givenName,surName,address FROM customers""")

    #For curl call later
    headers = { 
        'Authorization' : 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiZTBmYzI2MGEtOTUyZS0zMzFlLTlmMTMtNzU4ODUzZGNkNDI1IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiJmMGVlMDA5Yy02ZmY3LTQ3ZmEtYWYzOC1hMDBlYTczMDk2NmEifQ.xHkemImCQr9sxUmV32vYz5wrKKeciLHFAxfdE3smN28' ,
        'Accept' : 'application/json, text/plain, */*' }

    #Open file to save data
    newFile = open("log.txt", 'a')

    totalWithUs = 0
    totalAtComp = 0

    for row in c.fetchall():
        rowId = row[0]

        #Get data from API
        url = "https://api.td-davinci.com/api/customers/" + rowId + "/transactions"
        response = requests.get(url, data=None, headers=headers)
        data = response.json() 

        #Get data from file

        #Track use of money
        spentWithUs = 0
        spentAtComp = 0

        for transaction in data["result"]:
            # if transaction["originationDateTime"] - dayFilter:
            #     continue
            if transaction["merchantName"] in competitors:
                spentAtComp += round(transaction["currencyAmount"])
                totalAtComp += spentAtComp
            elif transaction["merchantName"] == ourBrand:
                spentWithUs += round(transaction["currencyAmount"])
                totalWithUs += spentWithUs

        #Monetary significance * Ratio Spent at Comp
        if spentWithUs == 0: 
            newScore = ((spentWithUs+spentAtComp) / significantSpendAvg) 
        else:
            newScore = ((spentWithUs+spentAtComp) / significantSpendAvg) * spentAtComp/spentWithUs
        newScore = round(newScore, 2)
        print(newScore)

        #Now factor in the previous score; boost if they still aren't spending
        lastScore = row[1]
        if newScore > lastScore:
            if spentWithUs == 0 or spentAtComp/spentWithUs < 0.1:
                newScore *= 0.5 #conversion not working
            else:
                newScore *= 1.1

        #If the discount hasn't been set yet, just default it to a ratio
        if row[2] == 0:
            lastDiscount = min(newScore/5 * maxDiscount, maxDiscount)
            c.execute("UPDATE customers SET lastWeightedScore = ? , lastDiscount = ? WHERE id = ?", (newScore,lastDiscount,row[0]))
        else:
            c.execute("UPDATE customers SET lastWeightedScore = ? WHERE id = ?", (newScore,row[0]))

        newFile.write(row[3] + " " + row [4] + ", " + row[5] + ", " + str(newScore) + '\n')


    #Done looping through customers
    newFile.seek(0,0)
    ratio = "infinity"
    if (totalWithUs > 0): 
        ratio = str(totalAtComp/totalWithUs)
    output = "Total Spent With Us: " + str(totalWithUs) + " Total Spent With Competitors: " + str(totalAtComp) + " Ratio: " + ratio 
    newFile.write(output + '\n')



#This is what does the training!
def determineCoupons():
    # model.load_weights('my_model')

    #Base variables ("normalized" to be approx same value)
    industryV = tf.placeholder(tf.float32)
    salaryV = tf.placeholder(tf.float32) 
    ageV = tf.placeholder(tf.float32) 
    spouseV = tf.placeholder(tf.float32) 
    lastDiscountV = tf.placeholder(tf.float32)
    lastWeightedScoreV = tf.placeholder(tf.float32)

    #Weights
    industryW = tf.Variable(np.random.randn(), name='weights')
    salaryW = tf.Variable(np.random.randn(), name='weights')
    ageW = tf.Variable(np.random.randn(), name='weights')
    spouseW =tf.Variable(np.random.randn(), name='weights')
    lastDiscountW = tf.Variable(np.random.randn(), name='weights')
    lastWeightedScoreW = tf.Variable(np.random.randn(), name='weights')

    #Seperate out each variable


    #Now "normalize" certain variables so they are approx the same value


    #Now run the algo


    #Save 
    # model.save_weights('./my_model')

# rateCustomers()
determineCoupons()

#Exit 
conn.commit()
c.close()
conn.close()
