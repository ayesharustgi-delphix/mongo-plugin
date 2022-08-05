# Upgrade dSource

## Upgrades
Periodically Production and Lower environments are upgraded for various reasons like  

-   To be in compliance  
-   To mitigate bugs  
-   Security concerns  
-   To meet compatibility with other software.  

Upgrading the Source database to a higher version will impact dSource snapsyncs if the version upgraded is not compatible with version of staging database. Delphix can handle the upgrade of the databases by updating the configuration in dSource.

## Upgrade dSource to a higher version. (Until 1.0.2 MongoDB Plugin)
- Step 1: Install the same version of Mongo software on the staging host.[ same version as source ].  
- Step 2: Update repoconfig file. Please refer [Discovery](../Discovery.md) Section.
- Step 3: Refresh Staging Environment in Delphix.  
- Step 4: Verify new Mongo home is discovered in the environment with entry `PY EDSI MongoDB (vMONGO_VERSION)`.  
- Step 5: Disable dSource [ Manage Datasets → Select dSource → disable ].  
- Step 6: Log in to Delphix engine via CLI (ssh) interface and execute the following commands.  

```bash
cd sourceconfig  
select <dSource_Name>  
update  
set repository = <New Mongo Home discovered in Step 4 >  
commit; 
```

- Step 7: Enable dSource [ Manage Datasets → Select dSource → enable ]  
- Step 8: Take a new snapshot to validate that snapsync works as expected.

**Note**: You may need to resync dSource depending on mongo version compatability.