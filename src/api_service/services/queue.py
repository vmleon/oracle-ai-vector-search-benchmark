import json
import logging
from database import get_db_pool, is_db_ready

logger = logging.getLogger(__name__)

def enqueue_document_for_chunking(document_id, file_path):
    """Enqueue a document for chunking processing."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    try:
        db_pool = get_db_pool()
        with db_pool.acquire() as connection:
            cursor = connection.cursor()
            
            queue_name = "vector_pending_document"
            
            # Create payload with document metadata
            payload = {
                'document_id': document_id,
                'file_path': file_path
            }
            
            # Enqueue message using Oracle AQ
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
            
            logger.info(f"Enqueued document {document_id} for chunking")
            
    except Exception as e:
        logger.error(f"Failed to enqueue document: {e}")
        raise

def enqueue_chunk_for_embedding(document_id, chunk_index, chunk_text):
    """Enqueue a chunk for embedding processing."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    try:
        db_pool = get_db_pool()
        with db_pool.acquire() as connection:
            cursor = connection.cursor()
            
            queue_name = "vector_pending_chunk"
            
            # Create payload with chunk metadata
            payload = {
                'document_id': document_id,
                'chunk_index': chunk_index,
                'chunk_text': chunk_text
            }
            
            # Enqueue message using Oracle AQ
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
            
            logger.info(f"Enqueued chunk {chunk_index} for document {document_id}")
            
    except Exception as e:
        logger.error(f"Failed to enqueue chunk: {e}")
        raise

def get_queue_depth(queue_name):
    """Get the number of pending messages in a queue."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    try:
        db_pool = get_db_pool()
        with db_pool.acquire() as connection:
            cursor = connection.cursor()
            
            # Use the actual queue table names from pdb_queues.sql
            table_mapping = {
                'vector_pending_document': 'PDBADMIN.VECTOR_PENDING_DOCUMENT_TABLE',
                'vector_pending_chunk': 'PDBADMIN.VECTOR_PENDING_CHUNK_TABLE'
            }
            
            table_name = table_mapping.get(queue_name.lower())
            if not table_name:
                logger.error(f"Unknown queue name: {queue_name}")
                return 0
            
            # Query the queue table directly for pending messages
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table_name}
                WHERE msg_state = 'READY'
            """)
            
            result = cursor.fetchone()
            return result[0] if result else 0
            
    except Exception as e:
        logger.error(f"Failed to get queue depth for {queue_name}: {e}")
        # Return 0 if we can't get the queue depth rather than failing
        return 0

def get_all_queue_depths():
    """Get depths for all queues used in the system.""" 
    return {
        'vector_pending_document': get_queue_depth('vector_pending_document'),
        'vector_pending_chunk': get_queue_depth('vector_pending_chunk')
    }

