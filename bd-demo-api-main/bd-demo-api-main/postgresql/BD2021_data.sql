CREATE TABLE leilao (
	minprice		 NUMERIC(8,2) NOT NULL,
	auctiontitle	 CHAR(255) NOT NULL,
	leilaoid		 NUMERIC(8,0) DEFAULT 0,
	datafim		 TIMESTAMP NOT NULL,
	utilizador_userid NUMERIC(8,0) NOT NULL DEFAULT 0,
	item_itemid	 CHAR(10) NOT NULL,
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
	itemid		 CHAR(10),
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
	title		 VARCHAR(50) NOT NULL,
	leilao_leilaoid NUMERIC(8,0) DEFAULT 0,
	PRIMARY KEY(data,leilao_leilaoid)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE leilao ADD CONSTRAINT leilao_fk2 FOREIGN KEY (item_itemid) REFERENCES item(itemid);
ALTER TABLE leilao ADD CONSTRAINT check_leiloes_minprice_constraint CHECK (MinPrice >= 0);
ALTER TABLE leilao ADD CONSTRAINT check_leiloes_datafim_constraint CHECK (DataFim >= now());
ALTER TABLE item ADD CONSTRAINT item_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (leilao_leilaoid) REFERENCES leilao(leilaoid);
ALTER TABLE licitacao ADD CONSTRAINT check_licitacoes_valor_constrain CHECK (valor >= 0);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_leilaoid) REFERENCES leilao(leilaoid);
ALTER TABLE description ADD CONSTRAINT description_fk1 FOREIGN KEY (leilao_leilaoid) REFERENCES leilao(leilaoid);

\set autocommit off;
SET TIME ZONE 'Europe/London';

create or replace procedure licitar(p_valor licitacao.valor%type, 
									p_user_id licitacao.utilizador_userid%type, 
									p_leilaoid licitacao.leilao_leilaoid%type)
language plpgsql
as $$
declare
	c_licitacao cursor for SELECT * FROM licitacao FOR UPDATE;
	c_leilao cursor (c_p_leilaoid leilao.leilaoid%type) FOR 
												SELECT minprice, utilizador_userid 
												FROM leilao 
												WHERE leilaoid = c_p_leilaoid;
	v_valor leilao.minprice%type;
	v_user_id leilao.utilizador_userid%type;
begin
	OPEN c_leilao(p_leilaoid);
	OPEN c_licitacao;
	fetch c_leilao into v_valor, v_user_id;
	
	IF p_user_id!=v_user_id THEN
		IF (SELECT EXISTS(SELECT COUNT(*) FROM licitacao WHERE leilao_leilaoid = p_leilaoid GROUP BY leilao_leilaoid))='f' THEN
			IF p_valor > v_valor THEN
				INSERT INTO licitacao VALUES (p_valor, NOW(), p_user_id, p_leilaoid);
			ELSE
				RAISE 'BID MUST BE LARGER MINPRICE OF AUCTION' USING ERRCODE = '23514';
			END IF;
		ELSIF p_valor > (SELECT MAX(valor) FROM licitacao WHERE leilao_leilaoid = p_leilaoid GROUP BY leilao_leilaoid) THEN
			INSERT INTO licitacao VALUES (p_valor, NOW(), p_user_id, p_leilaoid);
		ELSE
			RAISE 'BID MUST BE LARGER THAN LARGEST BIT AT THE MOMENT' USING ERRCODE = '23514';
		END IF;
	ELSE
		RAISE 'CANNOT BID YOUR OWN AUCTION' USING ERRCODE = '23514';
	END IF;
end;
$$;

