-- View messages without removing them
select msg_id,
       msg_state,
       enq_time,
       consumer_name,
       user_data
  from aq$order_queue_tab
 where msg_state = 'READY';

-- Queue statistics
select name,
       enqueued_msgs,
       dequeued_msgs,
       ( enqueued_msgs - dequeued_msgs ) as pending_msgs
  from v$aq_message_cache;