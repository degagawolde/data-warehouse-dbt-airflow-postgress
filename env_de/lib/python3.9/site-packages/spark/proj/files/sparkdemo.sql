create database sparkdemo;
use sparkdemo;
create table wiki(
 word varchar(64) not null unique,
 content text not null
) engine=MyISAM default charset=utf8;
