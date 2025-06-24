-- Switch to the PDB
alter session set container = freepdb1;

-- Grant the required privileges
grant
   create table
to pdbadmin;
grant
   create sequence
to pdbadmin;
grant
   create procedure
to pdbadmin;
grant
   create trigger
to pdbadmin;
grant
   create view
to pdbadmin;

   -- Ensure unlimited tablespace quota
grant
   unlimited tablespace
to pdbadmin;

exit;