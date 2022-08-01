# Architecture

## Overview
Various Mongo configurations ranging from Standalone to multi-node replicaset can be used with Delphix. This article contains an overview of how Delphix works with Mongo.

There are three key concepts when using Delphix with any data platform:

1. **Environments**: The server and software required to run a data set. For Mongo, this will be an operating system host with Mongo instances running on it.  
    a. Staging Environment: Source data is ingested into Delphix using Staging Host. These will be used to create dSources.  
    b. Target Environment: Target hosts to provision VDBs. These need Mongo installations that correspond to the versions of the Source environments, per our Mongo Support Matrix.
2. **dSource**: A database that the Delphix Virtualization Engine uses to create and update virtual copies of your database
3. **VDB**: A database provisioned from either a dSource or another VDB which is a copy of the source data. A VDB is created and managed by the Delphix Virtualization Engine.  
Explore how Delphix connects to Mongo environments and creates Mongo dSources and VDBs, with these concepts in mind.  

## Environment Linking and Provisioning Architecture
As shown in the diagram below Delphix begins by ingesting data from your source database / backups to create dSources. Data is ingested using existing backups on Disk or by connecting to Source. Once you have added an environment, Delphix will `discover` required Mongo binaries on it.  

#### Consolidated Seed, Extended Cluster, Offline/Online mongodump, Mongo Atlas, Non-Sharded Ingestion Types 
![Screenshot](../image/consolidated_architectures.png)

#### Sharded Mongo Ingestion Type 
![Screenshot](../image/sharded_architecture.png)
