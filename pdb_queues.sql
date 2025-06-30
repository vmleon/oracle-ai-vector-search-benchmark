-- 1. Create queue table (holds the actual messages)
begin
   dbms_aqadm.create_queue_table(
      queue_table        => 'PDBADMIN.VECTOR_PENDING_CHUNK_TABLE',
      queue_payload_type => 'SYS.AQ$_JMS_TEXT_MESSAGE'  -- or your payload type
   );
end;
/

-- 2. Create the queue
begin
   dbms_aqadm.create_queue(
      queue_name  => 'PDBADMIN.VECTOR_PENDING_CHUNK',
      queue_table => 'PDBADMIN.VECTOR_PENDING_CHUNK_TABLE'
   );
end;
/

-- 3. Start the queue (enables enqueue/dequeue)
begin
   dbms_aqadm.start_queue(queue_name => 'PDBADMIN.VECTOR_PENDING_CHUNK');
end;
/

exit;