-- DROP --
DROP TABLE bot_debts.wallets;




-- bot_debts.accountings определение

CREATE TABLE `accountings` (
  `name` varchar(64) DEFAULT NULL,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8;


-- bot_debts.users определение

CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_nic` varchar(16) NOT NULL,
  `current_accounting` INT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_nic` (`user_nic`),
  KEY `users_FK` (`current_accounting`),
  CONSTRAINT `users_FK` FOREIGN KEY (`current_accounting`) REFERENCES `accountings` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1386642469 DEFAULT CHARSET=utf8;


-- bot_debts.groups определение

CREATE TABLE `groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT DEFAULT NULL,
  `accounting_id` INT DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `accounting_id` (`accounting_id`),
  CONSTRAINT `accounting_id` FOREIGN KEY (`accounting_id`) REFERENCES `accountings` (`id`),
  CONSTRAINT `groups_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;


-- bot_debts.beneficiaries определение

CREATE TABLE `beneficiaries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT DEFAULT NULL,
  `bnfcr_group` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `beneficiaries_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;


-- bot_debts.payment_docs определение

CREATE TABLE `payment_docs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `payer` BIGINT DEFAULT NULL,
  `recipient` BIGINT DEFAULT NULL,
  `accounting_id` int(11) DEFAULT NULL,
  `amount` float DEFAULT NULL,
  `posted` tinyint(1) NOT NULL DEFAULT 0,
  `time` datetime NOT NULL DEFAULT current_timestamp(),
  `comment` varchar(100) DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `payer` (`payer`),
  KEY `recipient` (`recipient`),
  KEY `accounting_id` (`accounting_id`),
  CONSTRAINT `payment_docs_ibfk_1` FOREIGN KEY (`payer`) REFERENCES `users` (`id`),
  CONSTRAINT `payment_docs_ibfk_2` FOREIGN KEY (`recipient`) REFERENCES `users` (`id`),
  CONSTRAINT `payment_docs_ibfk_3` FOREIGN KEY (`accounting_id`) REFERENCES `accountings` (`id`),
  CONSTRAINT `amount_check` CHECK (`amount` > 0)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;


-- bot_debts.purchase_docs определение

CREATE TABLE `purchase_docs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `purchaser` BIGINT DEFAULT NULL,
  `accounting_id` int(11) DEFAULT NULL,
  `bnfcr_group` int(11) DEFAULT NULL,
  `amount` float DEFAULT NULL,
  `posted` tinyint(1) DEFAULT NULL,
  `time` datetime NOT NULL DEFAULT current_timestamp(),
  `comment` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `user_id` (`purchaser`),
  KEY `accounting_id` (`accounting_id`),
  CONSTRAINT `purchase_docs_ibfk_1` FOREIGN KEY (`purchaser`) REFERENCES `users` (`id`),
  CONSTRAINT `purchase_docs_ibfk_2` FOREIGN KEY (`accounting_id`) REFERENCES `accountings` (`id`),
  CONSTRAINT `amount_check` CHECK (`amount` > 0)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;


-- bot_debts.user_balance определение

CREATE TABLE `user_balance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT DEFAULT NULL,
  `accounting_id` int(11) DEFAULT NULL,
  `balance` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `balance_FK` (`accounting_id`),
  CONSTRAINT `balance_FK` FOREIGN KEY (`accounting_id`) REFERENCES `accountings` (`id`),
  CONSTRAINT `user_balance_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;


-- bot_debts.wallet_balance определение

CREATE TABLE `wallet_balance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `balance` float NOT NULL DEFAULT 0,
  `name` varchar(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;


-- bot_debts.wallets определение

CREATE TABLE `wallets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT DEFAULT NULL,
  `accounting_id` int(11) DEFAULT NULL,
  `wallet` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `accounting_id` (`accounting_id`),
  KEY `wallet` (`wallet`),
  CONSTRAINT `wallets_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `wallets_ibfk_2` FOREIGN KEY (`accounting_id`) REFERENCES `accountings` (`id`),
  CONSTRAINT `wallets_ibfk_3` FOREIGN KEY (`wallet`) REFERENCES `wallet_balance` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;



-- users --
INSERT INTO bot_debts.users (id, user_nic, current_accounting)
	VALUES(290053979, 'Svintus', NULL);
INSERT INTO bot_debts.users (id, user_nic, current_accounting)
	VALUES(547568761, 'Oksashka', NULL);
INSERT INTO bot_debts.users (id, user_nic, current_accounting)
	VALUES(991874515, 'Yar', NULL);
INSERT INTO bot_debts.users (id, user_nic, current_accounting)
	VALUES(1386642468, 'Виктория Шутова', NULL);
INSERT INTO bot_debts.users (id, user_nic, current_accounting)
	VALUES(5227410205, 'Nata', NULL);



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

SELECT user_id, balance FROM user_balance WHERE accounting_id = 14;

UPDATE purchase_docs SET bnfcr_group = 1 WHERE id = 1

SELECT id, name, balance FROM wallet_balance
WHERE id in (SELECT wallet FROM wallets
			 WHERE wallets.accounting_id = 1);

SELECT SUM(balance) FROM user_balance 
WHERE user_id in (SELECT user_id FROM wallets 
                  WHERE wallet = 1)

SELECT SUM(balance) AS balance FROM user_balance WHERE user_id in (SELECT user_id FROM wallets WHERE wallet = 1);
UPDATE wallet_balance SET balance = -333.3399963378906 WHERE id = 3;

SELECT DISTINCT wallets.wallet, wallet_balance.name, wallet_balance.balance  FROM wallets JOIN wallet_balance ON wallets.wallet = wallet_balance.id WHERE accounting_id = 16;

SELECT users.id, users.user_nic FROM wallets JOIN users ON users.id = wallets.user_id WHERE wallet = 5;

