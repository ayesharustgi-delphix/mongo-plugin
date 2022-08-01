Plugin Logs
----------------
Download the Plugin logs using the following methods:  

- Using dvp  ( from Plugin development environment )
dvp download-logs -c plugin_config.yml -e <Delphix_Engine_Name> -u admin --password <password>  

- Using GUI  
Help --> Supports Logs --> Plugin Logs --> Download  


Instance Logs
----------------
Mongo Instance logs are located at < delphix_mount_point >/logs  
Delphix logs names are in format dlpx.sNmM.port.mongod.log
where  
    N = 0,1,2,3,... [ Shard Number ]  [ Always 0 for any non-sharded implementation ]  
    M = 0,1 OR 2 [ Member Number ]  
    port = port number of mongo instance.

