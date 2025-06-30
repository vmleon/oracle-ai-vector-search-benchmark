import os
import logging
import oracledb
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_db_pool = None

def create_connection_pool():
    """Create Oracle database connection pool."""
    global _db_pool
    
    if _db_pool is not None:
        return _db_pool
    
    try:
        ORACLE_USER = os.getenv('ORACLE_USER')
        ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD')
        ORACLE_HOST = os.getenv('ORACLE_HOST')
        ORACLE_PORT = os.getenv('ORACLE_PORT')
        ORACLE_SERVICE_NAME = os.getenv('ORACLE_SERVICE_NAME')
        ORACLE_DSN = os.getenv('ORACLE_DSN') or f'{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE_NAME}'
        pool_min = int(os.getenv('ORACLE_POOL_MIN', '1'))
        pool_max = int(os.getenv('ORACLE_POOL_MAX', '5'))
        pool_increment = int(os.getenv('ORACLE_POOL_INCREMENT', '1'))
        ping_interval = int(os.getenv('ORACLE_POOL_PING_INTERVAL', '60'))

       
        if not all([ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN]):
            raise ValueError("Missing required Oracle connection parameters")
        
        logger.info(f"Creating Oracle connection pool to {ORACLE_DSN}")
        
        _db_pool = oracledb.create_pool(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            min=pool_min,
            max=pool_max,
            increment=pool_increment,
            ping_interval=ping_interval
        )

        # TODO run a sql test, something like select 1 from dual
        
        return _db_pool
        
    except Exception as e:
        logger.error(f"Failed to create connection pool: {e}")
        raise

def queue_and_unqueue(message):
    # Test connection
    with get_connection() as connection:
        cursor = connection.cursor()

        queue_name="vector_pending_chunk"

        # Enqueue message using Oracle AQ
        payload = {'content': message}
        cursor.execute("""
            DECLARE
                enqueue_options    DBMS_AQ.ENQUEUE_OPTIONS_T;
                message_properties DBMS_AQ.MESSAGE_PROPERTIES_T;
                message_handle     RAW(16);
                message            SYS.AQ$_JMS_TEXT_MESSAGE;
            BEGIN
                message := SYS.AQ$_JMS_TEXT_MESSAGE.construct;
                message.set_text(:payload);
                
                DBMS_AQ.ENQUEUE(
                    queue_name         => :queue_name,
                    enqueue_options    => enqueue_options,
                    message_properties => message_properties,
                    payload            => message,
                    msgid              => message_handle
                );
                COMMIT;
            END;
        """, payload=json.dumps(payload), queue_name=queue_name)

        try:
            timeout=5
            cursor.execute("""
                DECLARE
                    dequeue_options    DBMS_AQ.DEQUEUE_OPTIONS_T;
                    message_properties DBMS_AQ.MESSAGE_PROPERTIES_T;
                    message_handle     RAW(16);
                    message            SYS.AQ$_JMS_TEXT_MESSAGE;
                    text_content       VARCHAR2(4000);
                BEGIN
                    dequeue_options.wait := :timeout;
                    
                    DBMS_AQ.DEQUEUE(
                        queue_name         => :queue_name,
                        dequeue_options    => dequeue_options,
                        message_properties => message_properties,
                        payload            => message,
                        msgid              => message_handle
                    );
                    
                    message.get_text(text_content);
                    :result := text_content;
                    COMMIT;
                EXCEPTION
                    WHEN OTHERS THEN
                        :result := NULL;
                END;
            """, timeout=timeout, queue_name=queue_name, result=cursor.var(str))
            
            result = cursor.bindvars['result'].getvalue()
            return json.loads(result) if result else None
            
        except Exception as e:
            logger.error(e)
            return None

def get_connection():
    """Get a connection from the pool."""
    if _db_pool is None:
        create_connection_pool()
    return _db_pool.acquire()

def close_pool():
    """Close the connection pool."""
    global _db_pool
    if _db_pool:
        try:
            _db_pool.close()
            _db_pool = None
            logger.info("Connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Create connection pool
        create_connection_pool()
        
        message = queue_and_unqueue("test message")
        print(f"Unqueued message: {message}")
        
        print("Connection test successful")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close pool
        close_pool()