# Upgrade Plugin

Periodic upgrade of plugin is required to  

- Avail new features  
- Bugfixes  
- Stay in compliance  
- Stay Compatible with upgraded delphix data platform.  

Plugin upgrade need to be done in a order from current version to desired version sequentially.  
Below is the sample path from lowest to highest version. Depending on current version, follow the path to next version in sequence.  

**1.0.0 -> 1.0.1 -> 1.0.2 -> 1.1.0 -> 1.2.0** 

Upgrade need to be done in sequence without skipping intermediate version. It can be done one after another in same session.  
*Note*: There is no downtime required for dSources.

Things to consider during plugin upgrade:  

- `$MONGO_REPO_CFGFILE` file update with plugin upgrade:
    - After uploading 1.1.0 MongoDB Plugin, specify the MongoDB database tools path in `$MONGO_REPO_CFGFILE`.
    - After uploading 1.2.0 MongoDB Plugin, specify all relevant paths for `mongosh`/`mongo`, `mongod`, `mongorestore`, `mongodump`, `mongosync` in `$MONGO_REPO_CFGFILE`.
    - For more information, refer [Discovery](https://delphix.github.io/mongo-plugin/Discovery/#mongo-binaries-discovery) section.
- Upload plugin - refresh all environments and ensure plugin discovery is completed successfully.
- Enable all datasets and take a new snapshot.           
