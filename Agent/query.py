from enum import StrEnum

class DB_Query(StrEnum):
    INSERT_CHAT_LOGS: str = """
        INSERT INTO 
            tbl_chat_log (streamer, chat_user, chat_content, spon_cost)
        VALUES 
            ($1, $2, $3, $4);
    """