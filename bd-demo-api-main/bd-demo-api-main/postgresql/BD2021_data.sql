CREATE TABLE leilao (
	minprice		 NUMERIC(8,2) NOT NULL,
	auctiontitle	 CHAR(255) NOT NULL,
	leilaoid		 NUMERIC(8,0) DEFAULT 0,
	datafim		 TIMESTAMP NOT NULL,
	isgoing		 BOOLEAN,
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
	directedto	 NUMERIC(8,0),
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


-- FUNCAO LICITAR -----------------
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


--- Funcao Ver Mensagens ----------------
create or replace function get_messages(p_user_id mensagem.utilizador_userid%type)
returns table ( data_envio timestamp, mensagens varchar, msg_leilaoid leilao.leilaoid%type, msg_userid utilizador.userid%type )
language plpgsql
as $$
declare
	c_mensagens cursor for select DISTINCT leilao_leilaoid
							from mensagem
							where utilizador_userid = p_user_id;
	c_leilao cursor for select leilaoid
						from leilao
						where utilizador_userid = p_user_id;
	v_leilaoid leilao.leilaoid%type;
	v_userid utilizador.userid%type;
	row_now record;
begin
	open c_mensagens;
	loop
		fetch c_mensagens into v_leilaoid;
		exit when not found;
			
		SELECT utilizador_userid INTO v_userid FROM leilao WHERE leilaoid = v_leilaoid;				 
		continue when v_userid = p_user_id;
		
			for row_now in ( SELECT * FROM mensagem
								WHERE (directedto is NULL
									AND leilao_leilaoid = v_leilaoid) OR directedto = p_user_id) loop
				data_envio := row_now.data;
				mensagens := row_now.mensagem;
				msg_leilaoid := row_now.leilao_leilaoid;
				msg_userid := row_now.utilizador_userid;
				return next;
			end loop;
	end loop;

	open c_leilao;
	loop
		fetch  c_leilao into v_leilaoid;
		exit when not found;
			for row_now in ( SELECT * FROM mensagem  
							WHERE directedto is NULL
									AND leilao_leilaoid = v_leilaoid) loop
				data_envio := row_now.data;
				mensagens := row_now.mensagem;
				msg_leilaoid := row_now.leilao_leilaoid;
				msg_userid := row_now.utilizador_userid;
				return next;
			end loop;
	end loop;
end;
$$;


-- Funcao Para trigger licitacao ultrapassada --------------
create or replace function notify_user_bid_exceeded()
returns trigger
language plpgsql
as $$
declare 
	c_licitacao_trigger cursor for SELECT utilizador_userid FROM licitacao 
							WHERE data = (SELECT max(data) FROM licitacao WHERE leilao_leilaoid = new.leilao_leilaoid);
	v_userid mensagem.utilizador_userid%type;
begin
	open c_licitacao_trigger;
	fetch c_licitacao_trigger into v_userid;
	if not found then
		v_userid := NULL;
	end if;
	if v_userid!=new.utilizador_userid then
		insert into mensagem values('Licitacao Ultrapassada', NOW(), v_userid, new.utilizador_userid, new.leilao_leilaoid);
	end if;
	return new;
end;
$$;

create trigger tbi_licitacao_into_mensagem
before insert on licitacao
for each row 
execute procedure notify_user_bid_exceeded();

