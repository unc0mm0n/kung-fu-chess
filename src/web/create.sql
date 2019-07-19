CREATE DATABASE IF NOT EXISTS `kfchess`;

USE `kfchess`;

CREATE TABLE IF NOT EXISTS `user` (
    `user_id` BIGINT NOT NULL AUTO_INCREMENT,
    `player_token` VARCHAR(45) NULL,
    `username` VARCHAR(45) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `email` VARCHAR(127) NULL,
    `rating` SMALLINT NULL,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`),
    UNIQUE INDEX `username_idx` (`username` ASC)
);

CREATE TABLE IF NOT EXISTS `game` (
    `game_id` BIGINT NOT NULL AUTO_INCREMENT,

    `white_user_id` BIGINT NULL,
    `black_user_id` BIGINT NULL,
    INDEX `white_user_idx` (`white_user_id` ASC),
    INDEX `black_user_idx` (`black_user_id` ASC),
    CONSTRAINT `white_user_id` 
        FOREIGN KEY (`white_user_id`) 
        REFERENCES `kfchess`.`user` (`user_id`)
        ON DELETE SET NULL,

    CONSTRAINT `black_user_id` 
        FOREIGN KEY (`black_user_id`) 
        REFERENCES `kfchess`.`user` (`user_id`)
        ON DELETE SET NULL,

    `white_rating` SMALLINT NULL,
    `black_int` SMALLINT NULL,

    `history` VARCHAR(1024) NULL,
    `winner` ENUM('BLACK', 'WHITE') NULL,
    `state` ENUM('WAITING', 'PLAYING', 'DONE') NOT NULL,
    PRIMARY KEY (`game_id`)
);
