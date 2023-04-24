# Release-v1.2.0

To deploy and configure Mongo plugin, 
refer to [Overview](/).

## New & Improved
* CE-143 Support for MongoDB v6.x and Cluster to Cluster Sync
* CE-222 Source mongo instance password is visible on the staging host in "ps" output
* CE-68 MongoDB Plugin: Capture Mongo error from MongoDB logs
* IDEA-3171 Support MongoDB 6 on RHEL 8


## Bug Fixes
* CE-142 MongoDB: dSource enable fails with IllegalObjectAccess after Replication Failover
* CE-189 Bug Fix - MongoDB instance is killed with "kill <pid>" which fails sometimes and leaves child processes orphan
* CE-240 sh.addShard() fails if staging DB password contains special characters.
* CE-256 Sudo rule examples in MongoDB staging and target requirements need correcting 
* CE-79 MongoDB Plugin Docs : Addition of description of expected backup files format
* CE-186 Intermittent: MongoDB errors out saying Address already in use if temporary socket files for available ports exists on the staging.

## Known Issues

* Plugin does not recognize any environment variables in hooks.  
* dSource cannot be upgraded via GUI. Only CLI interface supported.    


### Support Matrix

| <span class="table-header">Platform \ Mongo Plugin Version </span><br/> <span class="table-header"></span>| <span class="table-header"> v1.2.0</span> |
| ------------------                                                                                        |-------------------------------------------|   
| Delphix Engine                                                                                            | >=7.0                                     |
| Staging / Target Host                                                                                     | RHEL/CentOS 7.x / 8.x                     |


Future releases may add support for additional OS platforms and Delphix Engine versions.  
