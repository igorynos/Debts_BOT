CREATE TABLE accountings (
	id			int	 AUTO_INCREMENT PRIMARY KEY,	 
	name		varchar(64)	UNIQUE,
	start_time	datetime,	
	end_time	datetime,
	group_id	int		
)

CREATE TABLE groups (
    id int AUTO_INCREMENT PRIMARY KEY,
    user_id int,
    accounting_id int,
    CONSTRAINT FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT FOREIGN KEY (accounting_id) REFERENCES accountings(id)
)

CREATE TABLE wallet_balance(
	id int AUTO_INCREMENT PRIMARY KEY,
	name	varchar(16)
    balance float
);

CREATE TABLE wallets (
    id int AUTO_INCREMENT PRIMARY KEY,
    user_id int,
    accounting_id int,
    wallet	int,
    CONSTRAINT FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT FOREIGN KEY (accounting_id) REFERENCES accountings(id),
    CONSTRAINT FOREIGN KEY (wallet) REFERENCES wallet_balance(id)
)

CREATE TABLE purchase_docs(
	id int AUTO_INCREMENT PRIMARY KEY,
	purchaser int,
	accounting_id int,
	bnfcr_group int,
	amount float,
	posted bool NOT NULL DEFAULT FALSE,
    CONSTRAINT FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT FOREIGN KEY (accounting_id) REFERENCES accountings(id),
    CONSTRAINT amount_check CHECK(amount>0)
)

CREATE TABLE payment_docs(
	id int AUTO_INCREMENT PRIMARY KEY,
	payer int,
	recipient int,
	accounting_id int,
	amount float,
	posted bool NOT NULL DEFAULT FALSE,
    CONSTRAINT FOREIGN KEY (payer) REFERENCES users(id),
    CONSTRAINT FOREIGN KEY (recipient) REFERENCES users(id),
    CONSTRAINT FOREIGN KEY (accounting_id) REFERENCES accountings(id),
    CONSTRAINT amount_check CHECK(amount>0)
)

CREATE TABLE beneficiaries(
	id int AUTO_INCREMENT PRIMARY KEY,
    user_id int,
    bnfcr_group int,
    CONSTRAINT FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE balance(
	id int AUTO_INCREMENT PRIMARY KEY,
    user_id int,
	accounting_id int,
    balance float,
    CONSTRAINT FOREIGN KEY (user_id) REFERENCES users(id)
    CONSTRAINT FOREIGN KEY (accounting_id) REFERENCES accountings(id)
);

ALTER TABLE purchase_docs ADD COLUMN posted bool;
ALTER TABLE payment_docs ADD COLUMN posted bool;
UPDATE purchase_docs SET posted = TRUE;
UPDATE payment_docs SET posted = TRUE;

INSERT INTO groups (group_id, user_id)
VALUES
	(2, 1),
	(2, 2)

UPDATE accountings 
SET start_time = NOW()
WHERE id = 1

INSERT INTO accountings (name, group_id, start_time) VALUES ('1', 4, NOW()) 

DELETE FROM user_balance WHERE id > 0;
DELETE FROM purchase_docs  WHERE id > 0;
DELETE FROM payment_docs  WHERE id > 0;
DELETE FROM groups WHERE accounting_id > 0;
DELETE FROM beneficiaries WHERE bnfcr_group > 0;
DELETE FROM wallets WHERE accounting_id > 0;
DELETE FROM wallet_balance WHERE id > 0;
DELETE FROM accountings WHERE id > 2;

ALTER TABLE user_balance AUTO_INCREMENT = 1;
ALTER TABLE purchase_docs AUTO_INCREMENT = 1;
ALTER TABLE payment_docs AUTO_INCREMENT = 1;
ALTER TABLE groups AUTO_INCREMENT = 1;
ALTER TABLE accountings AUTO_INCREMENT = 1;
ALTER TABLE beneficiaries AUTO_INCREMENT = 1;
ALTER TABLE wallet_balance AUTO_INCREMENT = 1;
ALTER TABLE wallets AUTO_INCREMENT = 1;

SELECT user_id, balance FROM balance WHERE accounting_id = 4;

UPDATE purchase_docs SET bnfcr_group = 1 WHERE id = 1

SELECT id, name, balance FROM wallet_balance
WHERE id in (SELECT wallet FROM wallets
			 WHERE wallets.accounting_id = 1);

SELECT SUM(balance) FROM user_balance 
WHERE user_id in (SELECT user_id FROM wallets 
                  WHERE wallet = 1)

SELECT SUM(balance) AS balance FROM user_balance WHERE user_id in (SELECT user_id FROM wallets WHERE wallet = 1);
UPDATE wallet_balance SET balance = -333.3399963378906 WHERE id = 3;
