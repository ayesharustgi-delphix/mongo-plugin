# Release-v1.0.2

To deploy and configure Mongo plugin, 
refer to [Overview](/).

## New & Improved
* DXE-936 Added SDD supported.  
* DXE-950 Allow user to specify location of mongodump and mongorestore.  
* DXE-992 Added support to accept `.tar` extension of Mongo OPS Manager Backup file in addition to `.tar.gz`.  
* DXE-982 Mongo: Certified support for MongoDB 5.0.9.  


## Bug Fixes
* DXE-985 Incorrect date format in backup metadata file produces linking error.  
* DXE-964 Mongo : Enable Authentication with `User Auth Mode` as `ldap` breaks dSource/VDB creation


## Known Issues

* Plugin does not recognize any environment variables in hooks.  
* dSource cannot be upgraded via GUI. Only CLI interface supported.    


### Support Matrix

| <span class="table-header">Platform \ Mongo Plugin Version </span><br/> <span class="table-header"></span>|<span class="table-header"> v1.0.2</span> |
| ------------------                                                                                        | -------------------------                |   
| Delphix Engine                                                                                            | 6.0.15.0                                 |
| Staging / Target Host                                                                                     | RHEL/CentOS 7.x, 8.0                     |


Future releases may add support for additional OS platforms and Delphix Engine versions.  
