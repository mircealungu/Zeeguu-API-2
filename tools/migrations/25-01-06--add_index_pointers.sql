/* Text update */
ALTER TABLE
    `zeeguu_test`.`text`
ADD
    COLUMN `paragraph_i` INT NULL
AFTER
    `article_id`,
ADD
    COLUMN `sentence_i` INT NULL
AFTER
    `paragraph_i`,
ADD
    COLUMN `token_i` INT NULL
AFTER
    `sentence_i`
ADD
    COLUMN `in_content` TINYINT NULL
AFTER
    `token_i`;

/* Bookmark update */
ALTER TABLE
    `zeeguu_test`.`bookmark`
ADD
    COLUMN `sentence_i` INT NULL
AFTER
    `learned`
ADD
    COLUMN `token_i` INT NULL
AFTER
    `sentence_i`,
ADD
    COLUMN `total_tokens` INT NULL
AFTER
    `token_i`;