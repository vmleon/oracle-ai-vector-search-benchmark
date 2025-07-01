-- 1. Create queue table (holds the actual messages) for VECTOR_PENDING_CHUNK
declare
   table_exists exception;
   pragma exception_init(table_exists, -24001);
begin
   dbms_aqadm.create_queue_table(
      queue_table        => 'PDBADMIN.VECTOR_PENDING_CHUNK_TABLE',
      queue_payload_type => 'SYS.AQ$_JMS_TEXT_MESSAGE'
   );
   dbms_output.put_line('Created queue table: VECTOR_PENDING_CHUNK_TABLE');
exception
   when table_exists then
      dbms_output.put_line('Queue table VECTOR_PENDING_CHUNK_TABLE already exists, skipping creation');
end;
/

-- 2. Create the queue for VECTOR_PENDING_CHUNK
declare
   queue_exists exception;
   pragma exception_init(queue_exists, -24006);
begin
   dbms_aqadm.create_queue(
      queue_name  => 'PDBADMIN.VECTOR_PENDING_CHUNK',
      queue_table => 'PDBADMIN.VECTOR_PENDING_CHUNK_TABLE'
   );
   dbms_output.put_line('Created queue: VECTOR_PENDING_CHUNK');
exception
   when queue_exists then
      dbms_output.put_line('Queue VECTOR_PENDING_CHUNK already exists, skipping creation');
end;
/

-- 3. Start the queue (enables enqueue/dequeue) for VECTOR_PENDING_CHUNK
declare
   already_enabled exception;
   pragma exception_init(already_enabled, -24010);
begin
   dbms_aqadm.start_queue(queue_name => 'PDBADMIN.VECTOR_PENDING_CHUNK');
   dbms_output.put_line('Started queue: VECTOR_PENDING_CHUNK');
exception
   when already_enabled then
      dbms_output.put_line('Queue VECTOR_PENDING_CHUNK already started');
end;
/
-- 1. Create queue table (holds the actual messages) for VECTOR_PENDING_DOCUMENT
declare
   table_exists exception;
   pragma exception_init(table_exists, -24001);
begin
   dbms_aqadm.create_queue_table(
      queue_table        => 'PDBADMIN.VECTOR_PENDING_DOCUMENT_TABLE',
      queue_payload_type => 'SYS.AQ$_JMS_TEXT_MESSAGE'
   );
   dbms_output.put_line('Created queue table: VECTOR_PENDING_DOCUMENT_TABLE');
exception
   when table_exists then
      dbms_output.put_line('Queue table VECTOR_PENDING_DOCUMENT_TABLE already exists, skipping creation');
end;
/

-- 2. Create the queue for VECTOR_PENDING_DOCUMENT
declare
   queue_exists exception;
   pragma exception_init(queue_exists, -24006);
begin
   dbms_aqadm.create_queue(
      queue_name  => 'PDBADMIN.VECTOR_PENDING_DOCUMENT',
      queue_table => 'PDBADMIN.VECTOR_PENDING_DOCUMENT_TABLE'
   );
   dbms_output.put_line('Created queue: VECTOR_PENDING_DOCUMENT');
exception
   when queue_exists then
      dbms_output.put_line('Queue VECTOR_PENDING_DOCUMENT already exists, skipping creation');
end;
/

-- 3. Start the queue (enables enqueue/dequeue) for VECTOR_PENDING_DOCUMENT
declare
   already_enabled exception;
   pragma exception_init(already_enabled, -24010);
begin
   dbms_aqadm.start_queue(queue_name => 'PDBADMIN.VECTOR_PENDING_DOCUMENT');
   dbms_output.put_line('Started queue: VECTOR_PENDING_DOCUMENT');
exception
   when already_enabled then
      dbms_output.put_line('Queue VECTOR_PENDING_DOCUMENT already started');
end;
/

exit;