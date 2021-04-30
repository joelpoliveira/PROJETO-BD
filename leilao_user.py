import psycopg2
import random

def get_options():
	pass

def main():
	option = -1:
	while( option!=0 ):
		option = get_options()


def connect_db():
    connection = psycopg2.connect(user = ,# Coloca o teu user
        password = ,   # Coloca a tua password
        host = "localhost",
        port = "5432",
        database = "Projeto")
    

    return connection


  
def criarLeilao():
	connection = connect_db()
	cursor = connection.cursor()
	
	#Input de informação
	minPrice = input('Preço mínimo: ')
	title = input('Titulo do leilão: ')
	IdLeilao = random.randint(0,10000000000)
	data = input('Data (Ano-Mes-Dia)')
	tempo = input('Data (horas:minutos:segundos)')
	endDate =("%s %s",data,tempo)
	id_vendedor = #ainda não definido
	itemId = random.randint(1000000000000, 9999999999999)
	descricao = input('Descricao: ')

	#Colocar as informações na base de dados
	cursor.execute("insert into leilao(minprice,auctiontitle,leilaoid,datafim,utilizador_userid,item_itemid \
	values(minprice,title,IdLeilao,endDate,id_vendedor,item_itemid)")

	cursor.execute("insert into description(description,data,leilao_leilaoid \
	values(descricao,endDate,IdLeilao)")
	
def listarLeiloes():
	connection = connect_db()
	cursor = connection.cursor()
	cursor.execute("select description, data ,(distinct leilao_leilaoid)\
	from description)")
	for elem in cursor:
		print("LeilaoId: %d ,Descricao: %s  ",elem[2],elem[0])
	
	
	