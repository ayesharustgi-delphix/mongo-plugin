# Source Requirements

###### Database instance

- Access to Source SSL Certificate (if applicable)  
- Access to KMIP Credentials (if applicable)  
- Access to Encryption KeyFile (if applicable)  
- Backup files from Mongo Ops Manager / Offline mongodump presented to Staging host.

***Database user with following privileges ( for extendedcluster dSource type ) ***  
- clusterAdmin  
- changeOwnPasswordRole  

```shell
use admin
db.createRole(
   { role: "changeOwnPasswordRole",
     privileges: [
        {
          resource: { db: "", collection: ""},
          actions: [ "changeOwnPassword" ]
        }
     ],
     roles: []
   }
)
db.createUser({user: "clusteradmin",pwd: "xxxxxx", roles: ["clusterAdmin","changeOwnPasswordRole"]})
```

***Database user with following privileges ( for onlinemongodump dSource type ) ***  
```shell
use admin 
db.createUser({user:"backupadmin", pwd:"xxxxxx", roles:[{role:"backup", db: 
"admin"}]})
```

***Database user with following privileges ( for shardedsource dSource type with cluster to cluster sync) ***  
```shell
use admin
db.createUser(
    {
        user: "syncadmin", 
        pwd: "xxxxx", 
        roles: [
            {role: "readAnyDatabase", db: "admin"}, 
            {role: "clusterMonitor", db: "admin"}, 
            {role: "backup", db: "admin"}
        ]
    }
)
```