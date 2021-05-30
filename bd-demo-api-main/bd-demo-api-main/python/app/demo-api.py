from jose import jwt
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import logging, psycopg2, time, sys, os, random

app = Flask(__name__) 

def db_error_code(error):
    return error.pgcode

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
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        logger.debug(f"{info}")
        statement = """
                        INSERT INTO item VALUES ( %s, %s, %s)"""

        values = ( payload["itemid"], payload["itemname"], info["sub"])
        cur.execute(statement, values)
        cur.execute("commit")
        result = {"itemid": payload["itemid"]}
        
    except Exception as err:
        cur.execute("rollback")
        logger.error(str(err))
        result = { "erro" : str(err)}
    finally:
            if conn is not None:
                conn.close()
    
    return jsonify(result)

#-----------------
#
# Create new Auction
#
#------------------

@app.route("/dbproj/leilao", methods=['POST'])
def add_leilao():
    token = request.headers.get("Authorization").split()
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
        logger.error(str(err))
        result = { "erro" : str(err)}
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
    
    return jsonify(result)


# ------------
#
# Get Auction Details
#
# --------------

@app.route("/dbproj/leilao/<leilaoid>", methods=['GET'])
def auction_details(leilaoid):
    token = request.headers.get("Authorization")
    logger.info("---- leilaoid loaded  ----")
    logger.debug(f'leilaoid: {leilaoid}')

    token = request.headers.get("Authorization").split()

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        logger.info("---- token loaded  ----")
        logger.debug(f'true_token: {info}')

        statement = """SELECT description, datafim FROM description, leilao
                            WHERE leilaoid = %s AND data in (SELECT max(data) FROM description, leilao
                                                WHERE datafim>NOW() AND leilao_leilaoid = %s
                                                        GROUP BY leilao_leilaoid);"""
        values = ( str(leilaoid), str(leilaoid) )
        cur.execute(statement, values)
        row = cur.fetchone()

        if row is not None:
            result = {
                        "leilaoid":str(leilaoid),
                        "descricao":row[0],
                        "data_fim":str(row[1])
                    }

            cur.close()

            cur = conn.cursor()
            statement = """SELECT data, mensagem, utilizador_userid FROM mensagem WHERE leilao_leilaoid = %s"""
            values = (str(leilaoid), )
            cur.execute(statement, values)

            rows = cur.fetchall()

            for i in rows:
                result["mensagens"] = result.get("mensagens", []) + [ { "userid":str(i[2]),
                                                                        "data": str(i[0]),
                                                                        "mensagem":i[1] } ]
            cur.close()

            cur = conn.cursor()
            statement = """SELECT utilizador_userid, valor, data FROM licitacao WHERE leilao_leilaoid = %s""" 
            cur.execute(statement, values)

            rows = cur.fetchall()

            for i in rows:
                result["licitacoes"] = result.get("licitacoes", []) + [{"userid":str(i[0]),
                                                                        "data":str(i[1]),
                                                                        "valor":str(i[2]) } ]
        else:
            result = []
    except Exception as err:
        logger.error(str(err))
        result = {"erro" : "401"}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)
    
@app.route("/dbproj/leilao/<auctionid>",methods=['POST'])
def alterarLeilao(auctionid):
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cursor = conn.cursor()

    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        
    #Altera a informação do leilao
        
        statement = """ UPDATE leilao \
                      SET auctiontitle = %s \
                      WHERE leilaoid = %s""" 
        values =(str(payload["auctiontitle"]), str(auctionid))
        cursor.execute(statement, values)
        cursor.execute("commit")
        
        result = auctionid
        cursor.close()        
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    
#Altera a descrição do item
                
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        cursor = conn.cursor()
        statement = """ UPDATE description \
                      SET description = %s \
                      WHERE leilao_leilaoid = %s """ 
        
        values = (str(payload["description"]), str(auctionid))
        cursor.execute(statement,values)
        cursor.execute("commit")
        result = auctionid
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
            if conn is not None:
                conn.close()
    return result


@app.route("/dbproj/mensagem/<idLeilao>", methods=['POST'])
def enviarMensagem(idLeilao):
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cursor = conn.cursor()

    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        
        statement = """
                        INSERT INTO mensagem VALUES ( %s, %s, %s, %s)"""
        values =(payload["mensagem"], "now()", info["sub"], idLeilao)
        
        cursor.execute(statement,values)
        cursor.execute("commit")
        result=idLeilao
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
            if conn is not None:
                conn.close()
    return result

@app.route("/dbproj/mensagem", methods=['POST'])
def mural():
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cursor = conn.cursor()
    
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        statement = """
                        SELECT *
                        FROM mensagem
                        Where leilao_leilaoid = %s """
        value = (str(payload["idAuction"]))
        cursor.execute(statement,value)
        cursor.execute("commit")
        result=value
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
            if conn is not None:
                conn.close()
    return result


#----------------------
#
# List All Auctions
#
#------------------

@app.route("/dbproj/leiloes", methods=['GET'], strict_slashes=True)
def list_auctions():
    token = request.headers.get("Authorization").strip().split()

    logger.info("---- token retrieved  ----")
    logger.debug(f'token: {token}')

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        logger.info("---- token loaded  ----")
        logger.debug(f'true_token: {info}')
        
        cur.execute("""SELECT leilao_leilaoid,description FROM description 
                            WHERE data in (SELECT max(data) FROM description, leilao 
                                                WHERE datafim>NOW() AND leilaoid=leilao_leilaoid 
                                                        GROUP BY leilao_leilaoid)""")

        rows = cur.fetchall()

        result = []
        for i in rows:
            result.append( { 
                            "leilaoid" : str(i[0]), 
                            "descricao" : i[1]
                            } )
    except Exception as err:
        logger.error(str(err))
        result = {"erro" : "401"}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)

#----------------------
#
# List Auctions Searched
#
#------------------

@app.route("/dbproj/leiloes/<keyword>", methods=['GET'])
def search_auctions(keyword):
    logger.info("---- keyword loaded  ----")
    logger.debug(f'keyword: {keyword}')

    token = request.headers.get("Authorization").strip().split()

    logger.info("---- token retrieved  ----")
    logger.debug(f'token: {token}')

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        logger.info("---- token loaded  ----")
        logger.debug(f'true_token: {info}')

        statement = """SELECT leilao_leilaoid, description FROM description 
                            WHERE description like %s AND data in (SELECT max(data) FROM description, leilao 
                                                WHERE datafim>NOW() AND leilaoid=leilao_leilaoid 
                                                        GROUP BY leilao_leilaoid)"""
        values = ( f'%{keyword}%', )
        cur.execute(statement, values)
        rows = cur.fetchall()

        result = []
        for i in rows:
            result.append( { 
                            "leilaoid" : str(i[0]), 
                            "descricao" : i[1]
                            } )
        cur.close()

        if str(keyword).isnumeric():
            cur = conn.cursor()
            statement = """SELECT leilao_leilaoid, description FROM description,leilao 
                                WHERE item_itemid=%s AND leilaoid=leilao_leilaoid AND data in (SELECT max(data) FROM description, leilao 
                                                    WHERE datafim>NOW() AND leilaoid=leilao_leilaoid 
                                                            GROUP BY leilao_leilaoid)""" 
            values = (str(keyword), )
            cur.execute(statement, values)
            rows = cur.fetchall()

            for i in rows:
                result.append( { 
                                "leilaoid" : str(i[0]), 
                                "descricao" : i[1]
                                } )
    except Exception as err:
        logger.error(str(err))
        result = {"erro" : "401"}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)

# ----------------------------
#
# Get Auctions with User Participation
#
# ------------------------

@app.route("/dbproj/leilao/user", methods=['GET'])
def user_auctions():
    token = request.headers.get("Authorization").strip().split()

    logger.info("---- token retrieved  ----")
    logger.debug(f'token: {token}')

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        statement = """SELECT * FROM leilao WHERE leilaoid = (SELECT DISTINCT(leilao_leilaoid)
                                                                FROM licitacao
                                                                WHERE utilizador_userid = %s)"""
        values = (info["sub"],)
        cur.execute(statement, values)
        rows = cur.fetchall()
        
        result = []
        for i in rows:
            result.append( {
                            "leilaoid":str(i[2]),
                            "titulo":i[1].strip(),
                            "data_fim":str(i[3])
                            } )
        cur.close()

        cur = conn.cursor()

        statement = """SELECT * FROM leilao WHERE utilizador_userid = %s"""
        cur.execute(statement, values)
        rows = cur.fetchall()

        for i in rows:
            result.append( {
                            "leilaoid":str(i[2]),
                            "titulo":i[1].strip(),
                            "data_fim":str(i[3])
                            } )
    except Exception as err:
        logger.error(str(err))
        result = {"erro":str(err)}
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



