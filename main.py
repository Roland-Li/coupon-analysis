import sqlite3
import requests
import tensorflow as tf
from tensorflow import keras
import numpy as np
import math
import json
import sys

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
    c.execute("""SELECT id,lastWeightedScore,lastDiscount,givenName,surName,address,couponHistory FROM customers""")

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
        newScore = round(newScore,2)

        #If the discount hasn't been set yet, just default it to a ratio
        if row[2] == 0:
            lastDiscount = round(min(newScore/5 * maxDiscount, maxDiscount),3)
            arr = [str(newScore), str(lastDiscount)]
            c.execute("UPDATE customers SET lastWeightedScore = ? , couponHistory = ?, lastDiscount = ? WHERE id = ?", (newScore,json.dumps(arr),lastDiscount,row[0]))
        else:
            # arr = row[6].append(lastDiscount)
            # arr.append(newScore)

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
    learning_rate = 0.01
    epochs = 200
    nSamples = 100
    
    #Base variables ("normalized" to be approx same value)
    industryV = tf.placeholder(tf.float32)
    salaryV = tf.placeholder(tf.float32) 
    ageV = tf.placeholder(tf.float32) 
    spouseV = tf.placeholder(tf.float32) 
    lastDiscountV = tf.placeholder(tf.float32)
    lastWeightedScoreV = tf.placeholder(tf.float32)
    coupon = tf.placeholder(tf.float32)

    #Weights
    industryW = tf.Variable(np.random.randn(), name='weights')
    salaryW = tf.Variable(np.random.randn(), name='weights')
    ageW = tf.Variable(np.random.randn(), name='weights')
    spouseW =tf.Variable(np.random.randn(), name='weights')
    lastDiscountW = tf.Variable(np.random.randn(), name='weights')
    lastWeightedScoreW = tf.Variable(np.random.randn(), name='weights')
    bias = tf.Variable(np.random.randn(), name='bias')

    pred = industryW * industryV + salaryW * salaryV + ageW * ageV + spouseW * spouseW + lastDiscountW * lastDiscountV + lastWeightedScoreW * lastWeightedScoreV + bias
    cost = tf.reduce_sum((pred - coupon) **2) / (2 * nSamples)
    optimizer = tf.train.GradientDescentOptimizer(learning_rate).minimize(cost)

    init = tf.global_variables_initializer()

    #Seperate out each variable and normalize it
    c = conn.cursor()
    c.execute("""SELECT occupationIndustry FROM customers""")
    occupationIndustry = []
    i = 0
    for strings in c.fetchall():
        occupationIndustry.append((strings[0]-1000)/9000)
        i += 1

    c.execute("""SELECT salary FROM customers""")
    salary = []
    for strings in c.fetchall():
        salary.append((math.log(strings[0],10)-4)/2)

    c.execute("""SELECT age FROM customers""")
    age = []
    for strings in c.fetchall():
        age.append(strings[0]-18/82)

    c.execute("""SELECT spouse FROM customers""")
    spouse = []
    for strings in c.fetchall():
        spouse.append(strings[0]) #already 0 or 1

    c.execute("""SELECT lastDiscount FROM customers""")
    lastDiscount = []
    for strings in c.fetchall():
        lastDiscount.append(strings[0]/maxDiscount)

    c.execute("""SELECT lastWeightedScore FROM customers""")
    lastWeightedScore = []
    for strings in c.fetchall():
        if strings[0] <= 0:
            lastWeightedScore.append(0)
        else:
            lastWeightedScore.append(strings[0]/10)
    
    c.execute("""SELECT id FROM customers""")
    ids = []
    for strings in c.fetchall():
        ids.append(strings[0])

    c.execute("""SELECT couponHistory FROM customers""")
    coupons = []
    i = 0

    for strings in c.fetchall():
        row = json.loads(strings[0])
        sc = float(row[len(row) - 2]) #Last time's Score
        ds = float(row[len(row) - 1]) #Last time's Discount

        #From best to worst
        #Reduce discount, increase score = continue
        #Increase discount, increase score = continue
        #Reduce discount, reduce score = stop
        #Increase discount, reduce score = stop
        # print(sc)
        # print(ds)
        # print(lastWeightedScore[i])
        # print(lastDiscount[i])
        val = (sc - lastWeightedScore[i] + 5)/10 * (ds - lastDiscount[i] + maxDiscount)/(maxDiscount*2) + ds

        coupons.append(val)
        sys.stdout.write(str(val) + '\n')
        sys.stdout.flush()

        i += 1
    
    #Now "normalize" certain variables so they are approx the same value

    #Now run the algo
    with tf.Session() as sesh:
        sesh.run(init)
        
        temp = 0
        storage = []
        
        for epoch in range(epochs):
            #Terrible variable names because I can
            i = 0
            for ai,bi,ci,di,ei,fi,gi,hi in zip(occupationIndustry, salary, age, spouse, lastDiscount, lastWeightedScore, coupons, ids):
                temp = fi * 10
                sesh.run(optimizer, feed_dict={industryV: ai, salaryV: bi, ageV: ci, spouseV: di, lastDiscountV: ei, lastWeightedScoreV: fi, coupon: gi})

                if epoch == epochs-1:
                    storage.append(round(temp,3))
                    storage.append(round(sesh.run(cost, feed_dict={industryV: occupationIndustry, salaryV: salary, ageV: age, spouseV: spouse, lastDiscountV: lastDiscount, lastWeightedScoreV: lastWeightedScore, coupon: coupons}),3))
                i += 1

            if epoch % 20 == 0:
                #Add this to the list
                a = sesh.run(cost, feed_dict={industryV: occupationIndustry, salaryV: salary, ageV: age, spouseV: spouse, lastDiscountV: lastDiscount, lastWeightedScoreV: lastWeightedScore, coupon: coupons})
                
                b = sesh.run(industryW)
                c = sesh.run(salaryW)
                d = sesh.run(ageW)
                e = sesh.run (spouseW)
                f = sesh.run (lastDiscountW)
                g = sesh.run (lastWeightedScoreW)
                h = sesh.run(bias)

                sys.stdout.write(f'epoch: {epoch:04d} lastWeightedScore={temp:.4f} a={a:.4f} b={b:.4f} c={c:.4f} d={d:.4f} e={e:.4f} f={f:.4f} g={g:.4f} h={h:.4f}' + '\n')
                sys.stdout.flush()
        
        c = conn.cursor()
        c.execute("""SELECT id,couponHistory FROM customers""")
   
        #Open file to save data
        newFile = open("log.txt", 'a')
        i = 0 
        for row in c.fetchall():    
            print(row[1]) 
            arr = json.loads(row[1])
            arr.append(str(storage[i]))
            i += 1
            arr.append(str(storage[i]))
            i += 1
            print(arr)

            c.execute("UPDATE customers SET couponHistory = ? WHERE id = ?", (str(json.dumps(arr)),row[0]))


    #Save 
    # model.save_weights('./my_model')

# rateCustomers()
determineCoupons()

#Exit 
conn.commit()
c.close()
conn.close()
