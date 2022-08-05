# Overview

MongoDB plugin helps to virtualize mongoDB data source leveraging the built-in mongoDB technologies like Replication, Mongodump/MongoRestore, Mongo OpsManager Backups:

Supported Mongo Technologies for Ingestion (create dSource) :

- **Mongodump**        : Export source data and import into Staging mongo instance (dSource). Useful for offline/online backups of small databases (onprem, Saas, MongoAtlas)
- **Replication**      : Add replicaset member to existing cluster. Fastest way to capture incrementals from the source.
- **Mongo Ops Manager**: Leverage existing backups, downloaded as compressed file(s), from Mongo OPS Manager. This mechanism can be used for ingesting sharded mongo database backups.


## <a id="Ingestion_Types"></a> Ingestion Types:

| dSource Type         | Mechanism                        | Zero Touch Prod | Description | Support Incrementals |
| :-------------       | :----------                      | :----------: | :---------- | :---------- |
| Seed                 | New Mongo Instance               | N/A | New empty mongo instance created by delphix. This is for development of new applications without ingesting data from any source. | N/A |
| extendedcluster      | Add member to existing replicaset| N | Add member to existing source replicaset. Instant and near realtime incremental data capture in delphix | Y |
| onlinemongodump      | mongodump                        | N | Delphix connects to source from staging environments, executes mongodump utility and captures source data. Delphix captures all databases from the mongo instance. | N |
| offlinemongodump     | mongodump                        | Y | Delphix leverages existing mongodumps made available to staging host. Supports backups taken using  `mongodump --oplog --gzip -o < bkp_dir >` OR `mongodump --gzip -o < bkp_dir >` command. database dumps for 1 or more database OR 1 or more collections is supported. | N |
| shardedsource        | Mongo OPS Manager Backups        | Y | Delphix leverages existing mongo ops manager backups of sharded source as backup files presented to staging host. Delphix expects 1 configserver backup file and 1 backup file per shard available in backup location. | N |
| nonshardedsource     | Mongo OPS Manager Backups        | Y | Delphix leverages existing mongo ops manager backup of non sharded source. Backup file need to be available on staging host file system. | N |
| stagingpush          | User created mongo instance      | Y/N | Delphix provides filesystem on Staging host that can be used for deploying mongo instance by User. User responsible to create working mongo instance on staging host either manually or using any tools like mongo ops manager after the filesystem creation.| Y/N |

<small>

-  Zero Touch Prod (Y) = Interaction with Source Server is not required by Delphix.  
-  Zero Touch Prod (N) = Interaction with Source Server is needed by Delphix. Delphix expects connection to source using credentials etc.  

</small>

### <a id="Seed"></a>Seed
This type of dSource is generally used for pure development purpose. There is no source instance associated with it. It creates a empty instance which is managed by delphix and helps to create virtual mongo instance to avail benefits of all delphix features.


### <a id="Mongodump_offline"></a>Mongodump (offlinemongodump)
This type of dsource is created using mongodump backup file(s) of source mongo instance. It helps to create dsource using zero touch production. Periodic backups can be loaded to create timeline of dsource.

### <a id="Mongodump_online"></a>Mongodump (onlinemongodump)
This type of dsource is created using mongodump backup of source mongo instance. It helps to create dsource using online backup. Policy can be scheduled to capture Periodic backup and generate timeline of dsource.

### <a id="online_replicaset"></a>Extended Cluster (extendedcluster)
This type of dsource is created by adding secondary member to existing source cluster. This member does not participate in voting and never becomes primary nor serves any read operations. Its the fastest way of capturing incrementals. Policy can be set to take snapshots to generate desired timeline.

### <a id="opsmgr_sharded"></a>Mongo OPS Manager backups (shardedmongo)
This type of dsource is created using backup files of source mongo instance created by mongo ops manager. It helps to create dsource of sharded source cluster. It helps to create dsource using zero touch production. Periodic backups can be loaded to create timeline of dsource.

### <a id="opsmgr_nonsharded"></a>Mongo OPS Manager backups (nonshardedmongo replicaet)
This type of dsource is created using backup file of source mongo instance created by mongo ops manager. It helps to create dsource of non-sharded source cluster. It helps to create dsource using zero touch production. Periodic backups can be loaded to create timeline of dsource.

### <a id="stagingpush"></a>Staging Push (stagingpush)
This type of dsource can be created in multiple ways. It varies based on use case. It can be created manually, copy of files at o/s level or using tools like Mongo OPS Manager. Below are some of the methods that can be used to create mongo instance on stagingpush delphix filesystem.  
**Note:** Delphix only exhibits the operations needed to capture data. Creation and Deletion of Mongo Instance on staging host will be responsibility of user.  
#### **New Mongo Database**  
1. Create new dSource of type stagingpush and Capture name of mountpoint filesystem provided to delphix while creating dsource.
2. Create new empty single member mongo replicaset cluster using Mongo OPS Manager or by any other tool/mechanism. Make sure to use same delphix mountpoint path used in dsource creation, appended with `/s0m0`, as location for datafiles. Also use same port that was provided while creating dSource.   
3. You can optionally restore any required data on this instance using mongorestore or scripts.
4. Update permissions of mongo files if any other user is used to create mongo instance than configured environment user in delphix. e.g.  

login as root
```
  su -m mongod -c 'chmod -R 775 /mnt/provision/stagingpush/s0m0'
```
OR  
login as mongod
```
  chmod -R 775 /mnt/provision/stagingpush/s0m0
```
_Note_: Delphix always appends `/s0m0` as subfolder to the filesystem provuded while creating stagingpush dSource. If `/mnt/provision/stagingpush` was provided as mountpoint while creating dsource, provide `/mnt/provision/stagingpush/s0m0` as datafile location while creating mongo Instance manually or via tools.

#### **Restore Mongo Database backup using Mongo OPS Manager  [ Non-Sharded ONLY ]**
1. Create new dSource of type stagingpush and Capture name of mountpoint filesystem, replicaset name provided to delphix while creating dsource. 
2. Create new empty single member mongo replicaset cluster using Mongo OPS Manager or by any other tool/mechanism. Make sure to use same delphix mountpoint path used in dsource creation, appended with `s0m0` as location for datafiles. Also use same port and replicaset name that was provided while creating dSource.  
3. Select desired backup to restore from Mongo OPS Manager.
4. Restore backup to existing cluster and select the name of cluster that was created for dSource.
5. Mongo OPS Manager will restore backup replacing existing data (empty instance) and keep same port and datafile location.
6. Once the restoration is complete, Take snapshot from delphix and discard/delete any snapshots that was created before restoring database.
7. Update permissions of mongo files if any other user is used to create mongo instance than configured environment user in delphix. e.g.   

login as root
```
  su -m mongod -c 'chmod -R 775 /mnt/provision/stagingpush/s0m0'
```
OR  
login as mongod
```
  chmod -R 775 /mnt/provision/stagingpush/s0m0
```

_Note_: Delphix always appends `/s0m0` as subfolder to the filesystem provided while creating stagingpush dSource. If `/mnt/provision/stagingpush` was provided as mountpoint while creating dsource, provide `/mnt/provision/stagingpush/s0m0` as datafile location while creating mongo Instance manually or via tools.

#### **Create Mongo Secondary Instance  [ Non-Sharded ONLY ]**  
1. Create new dSource of type stagingpush and Capture name of mountpoint filesystem provided to delphix while creating dsource. Provide correct primary source hostname, port and replicaset name during dSource creation. 
2. Modify existing replicaset Cluster using OPS Manager or Manually.   
    - Add new `hidden` member to existing replicaset. Make sure to use same delphix mountpoint path used in dsource creation, appended with `s0m0` as location for datafiles. Also use same port that was provided while creating dSource.  
    - Set Votes = 0, Priority = 0. This will ensure this member never contributes in election and never becomes primary.
3. Mongo will start replicating data from existing node to newly created instance.
4. Once the initial sync is complete, Take snapshot of dsource from delphix and discard/delete any snapshots that were created before initial sync was completed.
5. Update permissions of mongo files if any other user is used to create mongo instance than configured environment user in delphix. e.g.   

login as root
```
  su -m mongod -c 'chmod -R 775 /mnt/provision/stagingpush/s0m0'
```
OR  
login as mongod
```
  chmod -R 775 /mnt/provision/stagingpush/s0m0
```

_Note_: Delphix always appends `/s0m0` as subfolder to the filesystem provuded while creating stagingpush dSource. If `/mnt/provision/stagingpush` was provided as mountpoint while creating dsource, provide `/mnt/provision/stagingpush/s0m0` as datafile location while creating mongo Instance manually or via tools.