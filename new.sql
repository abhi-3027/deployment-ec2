DROP DATABASE `DBMS`;
CREATE DATABASE IF NOT EXISTS `` DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
USE `DBMS`;

 CREATE TABLE IF NOT EXISTS `program` (
	`program_id` varchar(100) NOT NULL,
    `program_name` varchar(100) NOT NULL,
    `description`varchar(200) NOT NULL,
    `duration` float(10) DEFAULT 0,
     PRIMARY KEY(`program_id`)
);

CREATE TABLE IF NOT EXISTS `student` (
	`roll_no` varchar(15) NOT NULL,
	`name` varchar(100) NOT NULL ,
	`email_id` varchar(100) NOT NULL,
	`year` integer NOT NULL,
	`phone_no` bigint NOT NULL ,
	`branch` varchar(50) NOT NULL,
	`job_offer` varchar(3) DEFAULT 'NO',
    `password` varchar(200) NOT NULL,
    PRIMARY KEY(`roll_no`)
);

CREATE TABLE IF NOT EXISTS `attends` (
	`roll_no` varchar(15) NOT NULL,
    `program_id` varchar(100) NOT NULL,
    `trained_hours` float(10) DEFAULT 1,
     primary key(`roll_no`,`program_id`),
     foreign key (`roll_no`) references student(`roll_no`) on update cascade on delete cascade,
     foreign key (`program_id`) references program(`program_id`) on update cascade on delete cascade
     
);

CREATE TABLE IF NOT EXISTS `adminn` (
	`email_id` varchar(100) NOT NULL,
    `password` varchar(200) NOT NULL,
	`name` varchar(100) NOT NULL ,
    `phone_no` bigint NOT NULL ,
     PRIMARY KEY(`email_id`)
);

CREATE TABLE IF NOT EXISTS `manage_student`(
	`email_id` varchar(100) NOT NULL,
	`roll_no` varchar(15) NOT NULL,
    primary key(`email_id`,`roll_no`),
	foreign key (`email_id`) references adminn(`email_id`) on update cascade on delete cascade,
    foreign key (`roll_no`) references student(`roll_no`) on update cascade on delete cascade
);

CREATE TABLE IF NOT EXISTS `manage_program`(
	`email_id` varchar(100) NOT NULL,
	`program_id` varchar(50) NOT NULL,
    primary key(`email_id`,`program_id`),
	foreign key (`email_id`) references adminn(`email_id`) on update cascade on delete cascade,
    foreign key (`program_id`) references program(`program_id`) on update cascade on delete cascade
);
insert into student values('1234',"stud","s@gmail.com",3, 989003742, "coe", "NO", "$2b$12$IJGoBvSZc.nNjX9mN96VpOVWeAgJJYENAz4.w3OIG5ftQdp.e.dhC");
insert into program values("UML501", "ML", "machine learning fundamentals", 10);
insert into attends (roll_no,program_id) values('1234', "UML501");
insert into adminn values("asharma1_be17@thapar.edu","$2b$12$IJGoBvSZc.nNjX9mN96VpOVWeAgJJYENAz4.w3OIG5ftQdp.e.dhC","admin",7973429113);
select * from student;
select * from program;
select * from attends;
select * from adminn;