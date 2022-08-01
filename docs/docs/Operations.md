# Operations

Following are the list of operations and workflow associated with dSource and VDB operations:  

### dSource Operations  

**Linking / Create dSource** :  Linking a data source will create a dSource object on the engine and allow Delphix to ingest data from this source. The dSource is an object that the Delphix Virtualization Engine uses to create and update virtual copies of your database. Once a dSource has been linked, you can begin to perform dSource operations on it such as enable, disable, detach, delete, resync and more.   

<!-- <img src="../image/OBI_Workflow_dSource.svg" width="300"> -->

**Snapsync ( dSource Snapshot )** :  Snapsync is the process used by the Delphix Engine to create a Snapshot of dSource. An initial SnapSync is performed to create a copy of data on the Delphix Engine. Incremental SnapSyncs are performed to update the copy of data on the Delphix Engine.  

<!-- <img src="../image/OBI_Workflow_Snapsync.svg" width="500"> -->

**Snapsync ( dSource Snapshot with Params )** :  This method preserves the Source Timeflow with no impact to existing virtual databases (VDBs). Repair Source Timeflow after a corruption. This will use parameters defined for dSource creation and execute whole process as if its creating new dSource but maintains preserves previous timeflow so that VDBs are not impacted.
*Note*: This will use parameters defined and resynchronize the dsource.  

**Disable** :  This will disable dSource and filesystem related to dSource will be unmounted from Staging host. dSource will not be monitored till it is enabled.  

**Enable** :  This will enable dSource that is in disabled state.  

### VDB Operations  

**Provisioning / Create VDB** :  Create new virtual database using snapshot of dSource.  
**Snapshot** :  Capture current state of database as a snapshot which can be used to create child VDB or rewind database to a particular snapshot.  
**Enable** :  This will enable VDB that is in disabled state. Database is started in read write mode.  
**Disable** : This will disable VDB and filesystem related to VDB will be unmounted from Target host. VDB will not be monitored till it is enabled.  
**Stop** :  Stop database on Target host. Filesystem stays mounted.  
**Start** :  Start database that is in stop mode. Disabled database need to be enabled.  

