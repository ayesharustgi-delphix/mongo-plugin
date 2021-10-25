# Overview

MongoDB plugin helps to virtualize mongoDB data source leveraging the following built-in mongoDB technologies:

Supported Backup Mechanisms:

- **New Instance**     : Delphix creates new mongo instances when there is no source associated for ingestion.
- **Mongodump**        : Export source data and import into Staging mongo instance (dSource). Useful for offline/online backups of small databases (onprem, Saas, MongoAtlas)
- **Replication**      : Add replicaset member to existing cluster.
- **Mongo Ops Manager**: Use existing backups downloaded as compressed file(s) from Mongo OPS Manager.


#### <a id="Ingestion_Types"></a> Ingestion Types:

| dSource Type         | Mechanism                        | Zero Touch Prod | Description |
| :-------------       | :----------                      | :----------: | :---------- |
| Seed                 | New Mongo Instance               | -                   | New empty mongo instance created by delphix. This is for development purpose without any source |
| extendedcluster      | Add member to existing replicaset| N | Add member to existing source replicaset. Instant and near realtime snapshots |
| onlinemongodump      | mongodump                        | N | Delphix connects to source from staging environments, executes mongodump and capture source data. |
| offlinemongodump     | mongodump                        | Y | Delphix leverages existing mongodumps made available to staging host. Supports backups taken using "mongodump --oplog --gzip -o < bkp_dir >" command |
| shardedsource        | Mongo OPS Manager Backups        | Y | Delphix leverages existing mongo ops manager backups of sharded source as backup files presented to staging host |
| nonshardedsource     | Mongo OPS Manager Backups        | Y | Delphix leverages existing mongo ops manager backups of non sharded source as backup files presented to staging host |
| stagingpush          | User created mongo instance      | Y/N | New empty mongo instance created by user or mongo ops manager automation. User responsible to create working mongo instance on staging host |

## Architecture  
#### Consolidated Seed, Extended Cluster, Offline/Online mongodump, Mongo Atlas, Non-Sharded Ingestion Types 
![Screenshot](image/consolidated_architectures.png)

#### Sharded Mongo Ingestion Type 
![Screenshot](image/sharded_architecture.png)

## Network Port requirements
#### Delphix Network Architecture 
![Screenshot](image/mongo_networkports.png)

Support Matrix
--------------
### <a id="support matrix"></a>Mongo Instance / OS Support Matrix
| Mongo Versions                     | RHEL 6.4                         | RHEL 7.4                         | RHEL 7.9                         | Windows x.x |
| :-------------       | :----------                      | :----------:                     | :----------                      | :---------- |
| mongoDB 4.2          | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |
| mongoDB 4.4          | -                                | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |
| mongoDB 4.2(sharded) | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |
| mongoDB 4.4(sharded) | -                                | ![Screenshot](image/check.svg)   | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg) |

### <a id="engine_compatibility_matrix"></a>Engine Compatibility Matrix
| Engine Versions      | Mongo 4.4.2                      | Mongopy 0.0.9                    |
| :-------------       | :----------                      | :----------:                     |
| 5.2.x.x              | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg)   |
| 5.3.5.x              | ![Screenshot](image/check.svg)   | ![Screenshot](image/error.svg)   |
| 6.0.2.x              | ![Screenshot](image/error.svg)   | ![Screenshot](image/check.svg)   |
| >6.0.3.x - 6.0.10.0  | ![Screenshot](image/error.svg)   | ![Screenshot](image/check.svg)   |

Prerequisites
-------------
### <a id="source requirements-plugin"></a>Source Requirements
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
```
use admin 
db.createUser({user: "clusteradmin",pwd: "xxxxxx", roles: ["clusterAdmin","backup"]})
```

### <a id="staging requirements-plugin"></a>Staging Requirements
***O/S user with following privileges***

- Regular o/s user with primary group as mongod.  
- Execute access on mongo/mongod binaries  
- mongo and mongod binaries to be in same folder [ if required create softlink ]  
- Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]  
- Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as base folder for nfs mounts.  
- Access to source instance backup file(s) from Staging host logged as delphix user (applicable for mongo ops mgr / offline mongodump use case).  
- sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.  

```shell
Defaults:delphixos !requiretty
delphixos ALL=NOPASSWD: \
/bin/mount, /bin/umount
```  



### <a id="target requirements-plugin"></a>Target Requirements  
***O/S user with following privileges***  

- Regular o/s user with primary group as mongod.  
- Execute access on mongo/mongod binaries  
- mongo and mongod binaries to be in same folder [ if required create softlink ]  
- Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]  
- Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as base folder for nfs mounts.  
- sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.  

```shell
Defaults:delphixos !requiretty
delphixos ALL=NOPASSWD: \
/bin/mount
```
Limitations
-----------
- V2P not supported
- Password Vault not supported
- PITR not supported
