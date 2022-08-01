# Upgrade VDB

## Upgrades
Periodically Lower environments are upgraded for various reasons like  

-   To be in compliance  
-   To mitigate bugs  
-   Security concerns  
-   To meet compatibility with other software.  

## Upgrade VDB to a higher version.  
- Step 1: Install the same version of Mongo software on the Target host.[ same version as Source/Target ].  
- Step 2: Update repoconfig file. Please refer [Discovery](../Discovery.md) Section.
- Step 3: Refresh Target Environment in Delphix.  
- Step 4: Verify new Mongo home is discovered in the environment with entry `PY EDSI MongoDB (vMONGO_VERSION)`.  
- Step 5: Disable VDB [ Manage Datasets → Select VDB → disable ]  
- Step 6: Update VDB configuration using Migrate option in Delphix GUI  
	- Manage Datasets → Select VDB → Migrate    
	- Select Correct Environment  
	- Select Correct Mongo Home under Installation  
	- Click on Migrate  
- Step 7: Enable VDB [ Manage Datasets → Select VDB → enable ]  
- Step 8: Take a new snapshot to validate VDB snapshot works as expected.  

**Note**: You may need to refresh VDB depending on mongo version compatability.


