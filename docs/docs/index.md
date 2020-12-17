# Overview

MongoDB plugin is developed to virtualize mongoDB data source leveraging the following built-in mongoDB technologies:


- Mongodump        : Export source data and import into Staging mongo instance (dSource). Useful for offline/online backups of small databases (onprem,Saas,MongoAtlas)
- Replication      : Add replicaset member to existing cluster.
- Mongo Ops Manager: Use existing backups as file from Mongo OPS Manager (Zero Touch Production).

Ingest MongoDB
----------------

1. MongoDB cluster/single instance offline backups using mongodump mechanism (Zero Touch Production).
2. MongoDB cluster/single instance online backups using mongodump mechanism.
3. MongoDB replicaset by adding replicaset member on delphix filesystem.
2. MongoDB sharded Cluster using Mongo OPS Manager backups (Zero Touch Production).

Prerequisites
----------------
### <a id="support matrix"></a>Support Matrix
|                      | RHEL 6.4                         | RHEL 7.4                         | RHEL 7.9                         | Windows x.x |
| :-------------       | :----------                      | :----------:                     | :----------                      | :---------- |
| mongoDB 4.2          | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |
| mongoDB 4.4          | -                                | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |
| mongoDB 4.2(sharded) | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |
| mongoDB 4.4(sharded) | -                                | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |

### <a id="source requirements-plugin"></a>Source Requirements
***O/S user with following privileges***  
- Access to Source SSL Certificate (if any)  
- Access to KMIP Credentials (if any)  
- Access to Encryption KeyFile (if any)  

***Database user with following privileges***  
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
db.createUser({user: "clusteradmin",pwd: "delphix", roles: ["clusterAdmin","changeOwnPasswordRole"]})

OR

For advmongodump method

use admin 
db.createUser({user: "clusteradmin",pwd: "delphix", roles: ["clusterAdmin","userAdminAnyDatabase"]})

```

### <a id="staging requirements-plugin"></a>Staging Requirements
***O/S user with following privileges***  
1. Regular o/s user with primary group as mongod.  
2. Execute access on mongo/mongod binaries  
3. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]  
4. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as base folder for nfs mounts.  
5. Access to source instance backup file(s) from Staging host logged as delphix user.  
6. sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.  

```shell
Defaults:delphixos !requiretty
delphixos ALL=NOPASSWD: \
/bin/mount, /bin/umount
```  

### <a id="target requirements-plugin"></a>Target Requirements  
***O/S user with following privileges***  
1. Regular o/s user with primary group as mongod.  
2. Execute access on mongo/mongod binaries  
3. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]  
4. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as base folder for nfs mounts.  
5. sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.  

```
Defaults:delphixos !requiretty
delphixos ALL=NOPASSWD: \
/bin/mount, /bin/umount
```  
