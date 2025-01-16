CREATE TABLE user_commitment (
    user_id INT PRIMARY KEY,
    user_minutes INT,
    user_days INT,
    consecutive_weeks INT,
    commitment_last_updated datetime,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

