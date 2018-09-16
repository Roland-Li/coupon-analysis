import sqlite3

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

def populateValues():
    #First query
    

    


# createUserTable()


#Exit 
conn.commit()
c.close()
conn.close()

  



