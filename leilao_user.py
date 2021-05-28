import psycopg2
import random


def get_options():
    pass


def connect_db():
    connection = psycopg2.connect(user= "Projeto",  # Coloca o teu user
                                  password="",  # Coloca a tua password
                                  host="localhost",
                                  port="5432",
                                  database="Projeto")

    return connection


def criarLeilao():
    connection = connect_db()
    cursor = connection.cursor()
    

    itemName = input('Nome do item')
    minPrice = input('Preço inicial: ') 
    while (isinstance(minPrice,int)):
        print('Valor inválido, insira de novo')
        minPrice = input('Preço inicial: ')
    
    title = input('Titulo do leilao: ')
    IdLeilao = random.randint(0, 10000000000)

    data = input('Data (Ano-Mes-Dia)')
    dataSplit = data.split("-")

    while (dataSplit[0] < 2021 or (dataSplit[1] < 1 or dataSplit[1] > 12) or (dataSplit[2] > 31 or dataSplit[2] < 1) or check(dataSplit) == 0):
        print("Valores invalidos")
        data = input('Data (Ano-Mes-Dia)')
        dataSplit = data.split("-")
        
    tempo = input('Data (horas:minutos:segundos)')
    tempoSplit = tempo.split(":")


    while (((tempoSplit[0]) > 24 or (tempoSplit[0]) < 1) or (tempoSplit[1]) > 60 or (tempoSplit[1]) < 1 or  
            (tempoSplit[2]) > 60 or (tempoSplit[2]) < 1 or check(tempoSplit) == 0):
        
        print("Valores invalidos")
        tempo = input('Data (horas:minutos:segundos)')
        tempoSplit = tempo.split(":")

    endDate = ("%s %s", data, tempo)
    
    id_vendedor = input("ID Vendedor: ")
    itemId = random.randint(1000000000000, 9999999999999)
    descricao = input('Descricao: ')
    

# Colocar as informacoes na base de dados
    cursor.execute("insert into leilao(minprice,auctiontitle,leilaoid,datafim,utilizador_userid,item_itemid) \
	values(minprice,title,IdLeilao,endDate,id_vendedor,itemId)")
    
    cursor.execute('insert into item(itemid, itemname, utilizador_userid) \
    values(itemId,itemName,id_vendedor)')

    cursor.execute("insert into description(description,data,leilao_leilaoid) \
	values(descricao,endDate,IdLeilao)")


def listarLeiloes():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("select description, data , leilao_leilaoid)\
	from description")
    for elem in cursor:
        print("LeilaoId: %d ,Descricao: %s  ", elem[2], elem[0])


def licitar():
    connection = connect_db()
    cursor = connection.cursor()

    # -------------------------------INTRODUZIR VALOR----------------------------------


    value = input("valor: ")
    aux = 0
    while (aux==0):
        cursor.execute("select valor \
                           from licitacao \
                           where valor > value\
                           if valor is null \
                           aux=1\
                           end if")
        if (aux==0):
            print("Valor invalido. Insira de novo")
            value = input("valor: ")

        # -------------------------------INTRODUZIR ID_USER----------------------------------
    idUser = input("ID utilizador: ")
    aux = 0
    while (aux==0):
        cursor.execute("select utilizador_userid \
                           from licitacao \
                           where utilizador_userid = idUser\
                           if utilizador_userid is not null\
                           aux=1\
                           end if")
        if (aux==0):
            print("ID invalido. Insira novo valor")
            idUser = input("ID utilizador: ")

    # -------------------------------INTRODUZIR auctionID----------------------------------
    auctionID = input("ID leilao: ")

    aux = 0
    while (aux==0):
        cursor.execute("select leilao_leilaoid \
                           from licitacao \
                           where leilao_leilaoid = auctionID\
                           if utilizador_userid is not null\
                           aux=1\
                           end if")
        if (aux==0):
            print("ID invalido. Insira novo valor")
            idUser = input("ID leilao: ")

# Inserir na BD
    cursor.execute("insert into licitacao(valor,utilizador_userid,leilao_leilaiid)\
                       values(value,idUser,auctionID)")
    
    
def alterarLeilao():
    idLeilao = input("Leilao a alterar")
    connection = connect_db()
    cursor = connection.cursor()
    
    cursor.execute("select * \
                   from leilao \
                   where leilaoid = idLeilao")

#Altera a informação do leilao
    
    price = cursor[0]
    title = input("Titulo")
    idLeilao = random.randint(0, 10000000000)
    endDate = cursor[3]
    idUser = cursor[4]
    idItem = cursor[5]
    cursor.execute("insert into leilao(minprice,auctiontitle,leilaoid,datafim,utilizador_userid,item_itemid) \
                   values(price,title,idLeilao,endDate,idUser,idItem)")
    
#Altera a descrição do item
    descricao = input("Descricao: ")
    
    cursor.execute("insert into description(description,data,leilao_leilaoid) \
	values(descricao,endDate,idLeilao)")
    
    

    
    

def check(array):
    
    if not isinstance(array[0],int):
        return 0
    if not isinstance(array[1],int):
        return 0
    if not isinstance(array[2],int):
        return 0
    return 1

def main():
    option = -1
    while (option != 0):
        option = get_options()
        
    