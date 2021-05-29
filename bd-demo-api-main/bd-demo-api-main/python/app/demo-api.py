##
## =============================================
## ============== Bases de Dados ===============
## ============== LEI  2020/2021 ===============
## =============================================
## =================== Demo ====================
## =============================================
## =============================================
## === Department of Informatics Engineering ===
## =========== University of Coimbra ===========
## =============================================
##
## Authors: 
##   Nuno Antunes <nmsa@dei.uc.pt>
##   BD 2021 Team - https://dei.uc.pt/lei/
##   University of Coimbra

from jose import jwt
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import logging, psycopg2, time, sys, os

app = Flask(__name__) 

def db_error_code(error):
    return error.pgcode

@app.route('/') 
def hello(): 
    return """

    Hello World!  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/>
    BD 2021 Team<br/>
    <br/>
    """




##
##      Demo GET
##
## Obtain all departments, in JSON format
##
## To use it, access: 
## 
##   http://localhost:8080/departments/
##

@app.route("/dbproj/user", methods=['GET'], strict_slashes=True)
def get_all_departments():
    logger.info("###              DEMO: GET /dbproj              ###");   

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT userid, username, email FROM utilizador")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- departments  ----")
    for row in rows:
        logger.debug(row)
        content = {'userid': int(row[0]), 'username': row[1], 'email': row[2]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)



##
##      Demo GET
##
## Obtain department with ndep <ndep>
##
## To use it, access: 
## 
##   http://localhost:8080/departments/10
##

@app.route("/dbproj/user/<userid>", methods=['GET'])
def get_department(userid):
    logger.info("###              DEMO: GET /dbproj/<user>              ###");   

    logger.debug(f'user: {userid}')
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT userid, username, email FROM utilizador where userid = %s", (userid,) )
    rows = cur.fetchall()

    row = rows[0]

    logger.debug("---- selected department  ----")
    logger.debug(row)
    content = {'userid': int(row[0]), 'username': row[1], 'email': row[2]}

    conn.close ()
    return jsonify(content)


## ----------------------
##
## Login or Create a new User
##
## ----------------------
@app.route("/dbproj/user", methods=['POST','PUT'])
def add_user_or_login():
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    
    if request.method=='POST':
        cur.execute("SELECT coalesce(max(userid) + 1, 0) FROM utilizador")
        next_userid = cur.fetchone()
        cur.close()

        cur = conn.cursor()
        
        logger.info("---- new user  ----")
        logger.debug(f'payload: {payload}')


        statement = """
                    INSERT INTO utilizador (userid, username, password, email) 
                    VALUES ( %s, %s, %s, %s)"""

        values = (str(next_userid[0]), payload["username"].strip(), payload["password"], payload["email"].strip())

        try:
            cur.execute(statement, values)
            cur.execute("commit")
            result = { "userid" : str(next_userid[0]) }
        except Exception as erro:
            result = {"erro" : str(db_error_code(erro))}
        finally:
            if conn is not None:
                conn.close()
    else:
        cur.execute("""SELECT password, userid FROM utilizador where username = %s""", (payload["username"].strip(),))
        row = cur.fetchone()
        try:
            if row[0] == payload["password"]:
                to_token = { 
                            "sub": str(row[1]),
                            "username": payload["username"]    
                         }
                token = jwt.encode(to_token, 'secret', algorithm = 'HS256')
                result = {"authToken":token}
            else:
                result = {"erro":"401"}
        except Exception as error:
            result = {"erro":"401"}
        finally:
            if conn is not None:
                conn.close()
    return jsonify(result)


## ----------------------
##
## Create new Item
##
## ----------------------

@app.route("/dbproj/item", methods=['POST'])
def add_item():
    token = request.headers.get("authToken")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token, 'secret', algorithms=["HS256"])
    
        
        
    except Exception as err:
        result = { "erro" : "401"}
    
    return jsonify(result)

#-----------------
#
# Create new Auction
#
#------------------

@app.route("/dbproj/leilao", methods=['POST'])
def add_leilao():
    token = request.headers.get("Authorization").strip().split()
    payload = request.get_json()

    logger.info("---- token retrieved  ----")
    logger.debug(f'token: {token}')

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        logger.info("---- token loaded  ----")
        logger.debug(f'true_token: {info}')
        
        cur.execute("SELECT coalesce(max(leilaoid) + 1, 0) FROM leilao")
        next_leilaoid = cur.fetchone()
        cur.close()

        cur = conn.cursor()
        
        logger.info("---- new leilao  ----")
        logger.debug(f'payload: {payload}')


        ## -------- add auction to auctions table ------##

        statement = """
                        INSERT INTO leilao VALUES ( %s, %s, %s, %s, %s, %s)"""

        values = ( payload["min_price"], payload["auction_title"], str(next_leilaoid[0]), payload["data_fim"], info["sub"], payload["item_id"] )

        cur.execute(statement, values)

        ## ------- add description to descriptions table ------##

        statement = """
                        INSERT INTO description VALUES ( %s, %s, %s )"""

        values = ( payload["description"], "now()", str(next_leilaoid[0]) )

        cur.execute(statement, values)

        cur.execute("commit")

        result = {"leilaoid": str(next_leilaoid[0])}
    except Exception as err:
        result = { "erro" : "401"}
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)


#----------------------
#
# List All Auctions
#
#------------------

@app.route("/dbproj/leiloes", methods=['GET'])
def list_auctions():
    conn = db_connection()
    token = request.headers.get("Authorization").strip().split()

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        cur.execute("""SELECT leilao_leilaoid, description FROM description 
                        WHERE data = (SELECT MAX(data) FROM description
                                                        GROUP BY leilao_leilaoid)""")

        rows = cur.fetchall()

        result = []
        for i in rows:
            result.append( { 
                            "leilaoid" : str(i[0]), 
                            "descricao" : i[1]
                            } )
    except Exception as err:
        result = {"erro" : "401"}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)







##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    load_dotenv()

    db = psycopg2.connect(host = os.getenv('HOST'),
                            dbname = os.getenv('DB_NAME'),
                            port = os.getenv('PORT'),
                            user = os.getenv('USER'),
                            password = os.getenv('PASSWORD')
                        )
    return db


##########################################################
## MAIN
##########################################################
if __name__ == "__main__":
    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
                              # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    time.sleep(1) # just to let the DB start before this print :-)


    logger.info("\n---------------------------------------------------------------\n" + 
                  "API v1.0 online: http://localhost:8080/dbproj\n\n")


    

    app.run(host="0.0.0.0", debug=True, threaded=True)



