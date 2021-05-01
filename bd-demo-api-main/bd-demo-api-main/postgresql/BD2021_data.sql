/* 
	# 
	# Bases de Dados 2020/2021
	# Trabalho Prático
	#
*/


/* 
   Fazer copy-paste deste ficheiro
   para o Editor SQL e executar.
*/

/* 
Estes dois comandos drop (comentados) permitem remover as tabelas emp e dep da base de dados (se ja' tiverem sido criadas anteriormente)

drop table emp;
drop table dep;
*/

/* Cria a tabela dos departamentos
 */
CREATE TABLE leilao (
	minprice		 NUMERIC(8,2) NOT NULL,
	auctiontitle	 CHAR(255) NOT NULL,
	leilaoid		 NUMERIC(8,0) DEFAULT 0,
	datafim		 TIMESTAMP NOT NULL,
	utilizador_userid NUMERIC(8,0) NOT NULL DEFAULT 0,
	item_itemid	 NUMERIC(8,0) NOT NULL,
	PRIMARY KEY(leilaoid)
);

CREATE TABLE utilizador (
	userid	 NUMERIC(8,0) DEFAULT 0,
	username VARCHAR(512) UNIQUE NOT NULL,
	email	 VARCHAR(512) UNIQUE NOT NULL,
	password VARCHAR(512) NOT NULL,
	PRIMARY KEY(userid)
);

CREATE TABLE item (
	itemid		 NUMERIC(8,0),
	itemname		 VARCHAR(512) NOT NULL,
	utilizador_userid NUMERIC(8,0) NOT NULL DEFAULT 0,
	PRIMARY KEY(itemid)
);

CREATE TABLE licitacao (
	valor		 NUMERIC(8,2) NOT NULL,
	data		 TIMESTAMP NOT NULL,
	utilizador_userid NUMERIC(8,0) NOT NULL DEFAULT 0,
	leilao_leilaoid	 NUMERIC(8,0) NOT NULL DEFAULT 0,
	PRIMARY KEY(data)
);

CREATE TABLE mensagem (
	mensagem		 VARCHAR(512) NOT NULL,
	data		 TIMESTAMP NOT NULL,
	utilizador_userid NUMERIC(8,0) NOT NULL DEFAULT 0,
	leilao_leilaoid	 NUMERIC(8,0) NOT NULL DEFAULT 0,
	PRIMARY KEY(data)
);

CREATE TABLE description (
	description	 VARCHAR(512) NOT NULL,
	data		 TIMESTAMP NOT NULL,
	leilao_leilaoid NUMERIC(8,0) DEFAULT 0,
	PRIMARY KEY(data,leilao_leilaoid)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE leilao ADD CONSTRAINT leilao_fk2 FOREIGN KEY (item_itemid) REFERENCES item(itemid);
ALTER TABLE leilao ADD CONSTRAINT check_leiloes_minprice_constraint CHECK (MinPrice >= 0);
ALTER TABLE leilao ADD CONSTRAINT check_leiloes_datafim_constraint CHECK (DataFim >= current_timestamp);
ALTER TABLE item ADD CONSTRAINT item_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (leilao_leilaoid) REFERENCES leilao(leilaoid);
ALTER TABLE licitacao ADD CONSTRAINT check_licitacoes_valor_constrain CHECK (valor >= 0);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_leilaoid) REFERENCES leilao(leilaoid);
ALTER TABLE description ADD CONSTRAINT description_fk1 FOREIGN KEY (leilao_leilaoid) REFERENCES leilao(leilaoid);


