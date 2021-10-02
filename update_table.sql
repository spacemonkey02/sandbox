DELIMITER $$
CREATE TRIGGER tbl_user_updates
AFTER UPDATE
ON tbl_user FOR EACH ROW
BEGIN
IF OLD.case_status<>new.case_status THEN
INSERT INTO tbl_user_updates(update_id,initial_status, updated_status)
VALUES(old.user_id, old.case_status, new.case_status);
END IF;
END $$
DELIMITER;