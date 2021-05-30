from jose import jwt
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import logging, psycopg2, time, sys, os
from random import randint
from hashlib import md5

app = Flask(__name__) 

def db_error_code(error):
    return error.pgcode

def get_isbn():
    v = [randint(0,9) for i in range(9)]
    ret = ''.join(list(map(str, v)))
    check = sum( (i+1)*v[i] for i in range(9))%11
    ret += 'X' if check==10 else str(check)
    return ret

def get_hashcode( string ):
    return md5( string.encode() ).hexdigest()
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

        values = (str(next_userid[0]), payload["username"].strip(), get_hashcode(payload["password"]), payload["email"].strip())

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
            if row[0] == get_hashcode(payload["password"]):
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

@app.route("/dbproj/item", methods=['POST','GET'])
def add_item_or_list(): 
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        
        if request.method=='POST':
            next_itemid = get_isbn()
            cur.execute("SELECT * FROM item WHERE itemid = %s", (next_itemid,))
            row = cur.fetchone()

            while row!=None:
                next_itemid = get_isbn()
                cur.execute("SELECT * FROM item WHERE itemid = %s", (next_itemid,))
                row = cur.fetchall()

            statement = """
                            INSERT INTO item VALUES ( %s, %s, %s)"""

            values = ( next_itemid , payload["itemname"], info["sub"])
            cur.execute(statement, values)
            cur.execute("commit")
            result = {"itemid": next_itemid }
        else:
            cur.execute("""SELECT itemid, itemname FROM item WHERE utilizador_userid = %s""", ( info["sub"] ,) )
            rows = cur.fetchall()

            result = []
            for i in rows:
                result.append( {
                                "itemid" : i[0],
                                "itemname": i[1]
                                } )
        
    except Exception as err:
        cur.execute("rollback")
        logger.error(err)
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
        
        statement = ("""SELECT utilizador_userid 
                    FROM item 
                    WHERE itemid = %s""")
        values = ( str(payload["item_id"]) ,)
        cur.execute(statement, values)
        row = cur.fetchone()
        if row is not None and row[0] == int(info["sub"]): 

        ## -------- add auction to auctions table ------##

            statement = """ 
                        
                            INSERT INTO leilao VALUES ( %s, %s, %s, %s, %s, %s)"""
    
            values = ( payload["min_price"], payload["auction_title"], str(next_leilaoid[0]), payload["data_fim"], info["sub"], payload["item_id"] )
            cur.execute(statement, values)
    
            ## ------- add description to descriptions table ------##
    
            statement = """
                            INSERT INTO description VALUES ( %s, %s, %s, %s )"""
            values = ( payload["description"], "now()", payload["auction_title"] ,str(next_leilaoid[0]) )
            cur.execute(statement, values)
    
            cur.execute("commit")
    
            result = {"leilaoid": str(next_leilaoid[0])}
        else: raise Exception
        
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

#---------------
#
# Change Auction Stats
#
#---------------

@app.route("/dbproj/leilao/<auctionid>",methods=['PUT'])
def alterarLeilao(auctionid):
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cursor = conn.cursor()

    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        
        logger.info("---- token loaded  ----")
        logger.debug(f'true_token: {info}')
        #Altera a informação na tabela leilao
        
        statement = """ UPDATE leilao 
                        SET auctiontitle = %s 
                        WHERE leilaoid = %s AND utilizador_userid = %s """ 
        values =( payload["auctiontitle"], str(auctionid), info["sub"])
        cursor.execute(statement, values)    
        # cursor.close()        

        logger.info("---- update finished  ----")
        #Altera a informacao na tabela descricao
        cursor = conn.cursor()
        statement = """ INSERT INTO description VALUES(%s, %s, %s, %s) """ 
        values = (str(payload["description"]), "now()", payload["auctiontitle"], str(auctionid))
        cursor.execute(statement,values)
        cursor.execute("commit")
        cursor.close()

        cursor = conn.cursor()
        statement = """SELECT * FROM leilao WHERE leilaoid = %s"""
        values = ( str(auctionid), )
        cursor.execute(statement, values)
        row = cursor.fetchone()

        result = dict( zip( ("minprice", "auctiontile", "leilaoid", "datafim", "userid", "itemid"), list(map(lambda x: str(x).strip(),row)) ) )

    except psycopg2.DatabaseError as error:
        cursor.execute("rollback")
        logger.error(error)
        result = {"erro": str(db_error_code(error))}
    except Exception as gen_error:
        cursor.execute("rollback")
        logger.error(gen_error)
        result = {"erro":str(gen_error)}
    finally:
            if conn is not None:
                conn.close()
    return jsonify(result)

# -------------
#
# Send Message to Auction
#
# -----------------

@app.route("/dbproj/mensagem/<idLeilao>", methods=['POST'])
def enviarMensagem(idLeilao):
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cursor = conn.cursor()

    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])
        
        statement = """INSERT INTO mensagem (mensagem, data, utilizador_userid, leilao_leilaoid)
                             VALUES ( %s, %s, %s, %s)"""
        values =(payload["mensagem"], "now()", info["sub"], str(idLeilao))
        
        cursor.execute(statement,values)
        cursor.execute("commit")
        result={"result":"Succeded"}
    except psycopg2.DatabaseError as error:
        logger.error(error)
        result = {"erro":str(db_error_code(error))}
    except Exception as generr:
        logger.error(generr)
        result = {"erro": str(generr.code)}
    finally:
            if conn is not None:
                conn.close()
    return jsonify(result)

# ------------------------
#
# Get Messages From Leilao
#
# ----------------------

@app.route("/dbproj/mensagem", methods=['GET'])
def mural():
    
    token = request.headers.get("Authorization").split()
    payload = request.get_json()

    conn = db_connection()
    cursor = conn.cursor()
    
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        statement = """
                        SELECT *
                        FROM get_messages(%s) 
                        ORDER BY data_envio DESC"""
        value = ( info["sub"], )
        cursor.execute(statement,value)
        rows = cursor.fetchall()
        result = []
        for i in rows:
            if i is not None:
                result.append( {
                                "mensagem" : i[1],
                                "data": str (i[0]),
                                #"userId": str (i[3]),
                                "auctionId":str(i[2])
                                } )
        
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = {"erro": str(error)}
    finally:
            if conn is not None:
                conn.close()
    return jsonify(result)


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

        statement = """SELECT * FROM leilao WHERE leilaoid in (SELECT DISTINCT(leilao_leilaoid)
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

# --------------
#
# Bid into Auction
#
# ----------------

@app.route("/dbproj/licitar/<leilaoid>/<licitacao>", methods = ['GET'])
def bid_auction(leilaoid, licitacao):
    token = request.headers.get("Authorization").split()

    logger.info("---- token retrieved  ----")
    logger.debug(f'token: {token}')

    conn = db_connection()
    cur = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        logger.info("---- info loaded  ----")
        logger.debug(f'info: {info}')

        statement = """ CALL licitar(%s, %s, %s) """
        values = ( str(licitacao), info["sub"] , str(leilaoid) )

        cur.execute(statement, values)
        cur.execute("commit")

        result = {"Resultado":"Sucesso"}
    except psycopg2.DatabaseError as dberr:
        logger.error(dberr)
        result = {"erro":str(db_error_code(dberr))}
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)

# -----------------------
#
# ENDPOINT QUE VERIFICA FIM DO LEILAO
#
# ------------------

@app.route("/dbproj/termino/<idleiao>", methods = ['GET'])
def fimLeilao(idleilao):
    token = request.headers.get("Authorization").split()

    logger.info("---- token retrieved  ----")
    logger.debug(f'token: {token}')

    conn = db_connection()
    cursor = conn.cursor()
    try:
        info = jwt.decode(token[1], 'secret', algorithms=["HS256"])

        logger.info("---- info loaded  ----")
        logger.debug(f'info: {info}')
        
        statement = """ UPDATE item 
                        SET utilizador_userid = (SELECT utilizador_userid FROM licitacao 
                                                    WHERE data = (SELECT max(data) FROM licitacao WHERE leilao_leilaoid = %s) 
                        """
        values = (idleilao, idleilao)

        cursor.execute(statement, values)
        cursor.execute("commit")

        result = {"result": "auction ended"}
    
    except psycopg2.DatabaseError as dberr:
        logger.error(dberr)
        result = {"erro":str(db_error_code(dberr))}
        cursor.execute("rollback")
    except Exception as err:
        logger.error(err)
        result = {"erro": str(err)}
        cursor.execute("rollback")
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



