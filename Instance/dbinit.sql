CREATE DATABASE `userdb` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
use `userdb`;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(45) NOT NULL,
  `password` varchar(255) NOT NULL,
  `pwsalt` varchar(45) NOT NULL,
  `email` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userid` int NOT NULL,
  `imagepath` varchar(45) NOT NULL,
  `num_faces` int DEFAULT NULL,
  `num_masked` int DEFAULT NULL,
  `num_unmasked` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`userid`) REFERENCES `users`(`id`) 
  ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `userdb`.`users`
(
`username`,
`password`,
`pwsalt`,
`email`)
VALUES
(
'admin',
'ef5ba017e3bac8bb52eac2ebb1635650c85e1ecc5fe9fc9ba5ecf54ce60b9568',
'YBq5zHiAb6PTrdSW',
'diamondhands1779@gmail.com');