# Release-v1.1.0

To deploy and configure Mongo plugin, 
refer to [Overview](/).

## New & Improved
* DXE-950 MongoDB: Allow user to specify location of mongodump and mongorestore.
* DXE-992 MongoDB: Added support to accept .tar extension of Mongo OPS Manager Backup file in addition to .tar.gz
* DXE-986 MongoDB: Remove extra prompt Source Sharded if dSource_Type is already selected as shardedsource
* DXE-987 MongoDB: Remove Convert each shards to replicaset” for dSource linking. Its applicable only for VDB.
* DXE-982 MongoDB: Certified support for MongoDB 5.0.9.  
* DXE-936 MongoDB: Added SDD supported.
* DXE-995 MongoDB: Mask sensitive information from plugin logs.


## Bug Fixes
* DXE-985 MongoDB: Incorrect date format in backup metadata file produces linking error
* DXE-964 MongoDB: Enable Authentication and “Enable Authentication” with “User Auth Mode” as “ldap” breaks dSource/VDB creation


## Known Issues

* Plugin does not recognize any environment variables in hooks.  
* dSource cannot be upgraded via GUI. Only CLI interface supported.    


### Support Matrix

| <span class="table-header">Platform \ Mongo Plugin Version </span><br/> <span class="table-header"></span>| <span class="table-header"> v1.1.0</span> |
| ------------------                                                                                        |-------------------------------------------|   
| Delphix Engine                                                                                            | 6.0.15.0                                  |
| Staging / Target Host                                                                                     | RHEL/CentOS 7.x.                          |


Future releases may add support for additional OS platforms and Delphix Engine versions.  
