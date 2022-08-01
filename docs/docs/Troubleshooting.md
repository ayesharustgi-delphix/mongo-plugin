Plugin Logs
----------------
Download the Plugin logs using the following methods:  

- Using dvp  ( from Plugin development environment )
dvp download-logs -c plugin_config.yml -e <Delphix_Engine_Name> -u admin --password <password>  

- Using GUI  
Help --> Supports Logs --> Plugin Logs --> Download  


Instance Logs
----------------

- Mongo Instance logs are located at DSOURCE_MOUNT_PATH/logs  ( for dSource )
- Mongo Instance logs are located at VDB_MOUNT_PATH/logs  ( for VDB )
- Delphix logs names are in format dlpx.sNmM.port.mongod.log
where  
    N = 0,1,2,3,... [ Shard Number ]  [ Always 0 for any non-sharded implementation ]  
    M = 0,1 OR 2 [ Member Number ]  
    port = port number of mongo instance.

**Note** : Most of the mongo related errors are always hidden in logfile for the mongo instance. Please examine logs under DSOURCE_MOUNT_PATH/logs and VDB_MOUNT_PATH/logs for further investigation. 