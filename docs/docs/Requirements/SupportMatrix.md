# Support Matrix

### <a id="support matrix"></a>Database / OS Support Matrix

| Supported Mongo Version | mongoDB 4.2.x                     | mongoDB 4.4.x                     | mongoDB 5.0.x                     |
| :-                      | :-:                               | :-                                | :-                                |
| RHEL 6.x                | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |
| RHEL 7.x                | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |<!--| RHEL 8.x                | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |-->
| CentOS 6.x              | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |
| CentOS 7.x              | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |<!--| CentOS 8.x              | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |-->
| Windows                 | ![Screenshot](../image/error.svg) | ![Screenshot](../image/error.svg) | ![Screenshot](../image/error.svg) |

<!--
| Oracle Linux 6.x        | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |
| Oracle Linux 7.x        | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |
| Oracle Linux 8.x        | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |
-->
### <a id="architecture options"></a>Architecture Options Matrix

| Architecture | Non-Sharded Source | Non-Sharded Target | Sharded Source | Sharded Target |
| :-               | :-:                               | :-:                               | :-:                               | :-:                               |
| Seed             | N/A                               | ![Screenshot](../image/check.svg) | N/A                               | ![Screenshot](../image/error.svg) |
| extendedcluster  | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/error.svg) | ![Screenshot](../image/error.svg) |
| onlinemongodump  | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/error.svg) |
| offlinemongodump | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/error.svg) |
| shardedsource    | ![Screenshot](../image/error.svg) | ![Screenshot](../image/error.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |
| nonshardedsource | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/error.svg) | ![Screenshot](../image/error.svg) |
| stagingpush      | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/error.svg) | ![Screenshot](../image/error.svg) |

### <a id="engine compatibility"></a>Engine Compatibility Matrix

| Engine Version      | Mongopy 1.0.0                     | Mongopy 1.0.1                     | Mongopy 1.0.2                     | Mongopy 1.1.0                     |
| :-                  | :-:                               | :-:                               | :-:                               | :-:                               |
| 6.0.7.x  - 6.0.11.x | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/error.svg) | ![Screenshot](../image/error.svg) | 
| 6.0.12.x - 6.0.15.x | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) |  ![Screenshot](../image/check.svg) | 

<!--
| 6.0.2.x             | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | 
| 6.0.3.x  - 6.0.6.x  | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | ![Screenshot](../image/check.svg) | 
-->
### <a id="mongo_version_environment_compatibility_matrix"></a>Mongo Version compatability across delphix environments
- Mongo binaries in all environments ( staging and target ) should be of same version for all dSource Type.
- Mongo binaries in all environments ( source, staging and target ) should be of same version for dSource Type: extendedcluster, nonshardedmongo, shardedmongo and stagingpush.  
- Mongo binaries can be of same or higher version than source in staging environment for offlinemongodump, onlinemongodump adhering to MongoDB vendor support matrix.  
- Mongo binaries in staging and target should be of same or compatible version for dSource types offlinemongodump and onlinemongodump.
