/*
 removes all searches and search aubscriptions from the database, which ensures no duplicates. 
*/
SET FOREIGN_KEY_CHECKS = 0;

DELETE FROM Search;

DELETE FROM search_subscription;

SET FOREIGN_KEY_CHECKS = 1;