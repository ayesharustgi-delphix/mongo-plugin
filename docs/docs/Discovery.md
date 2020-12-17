# Discovery

Environment discovery is a process that enables the mongoDB Plugin to determine mongo installation details on a host. Whenever there is any changes (installing a new binary home) to an already set up environment in the Delphix application, environment refresh need to be performed. 

Prerequisites
-------------

- Install delphix engine 5.3.x and above  
- Install mongo binaries on staging and target servers  
- Installation of the mongoDB Plugin is required before the discovery  
- Environment variable `$MONGO_PATH ` should be set on staging/target host, which contains binary path of mongo

Refresh Environment
----------------------
Environment refresh will update the metadata associated with that environment and copies new plugin to the host.

Steps: 

1. Login to the Delphix Management application.
2. Click Manage.
3. Select Environments.
4. In the Environments panel, click the name of the environment you want to refresh.
5. Select the Refresh icon.
6. In the Refresh confirmation dialog select Refresh.

    ![Screenshot](image/image9.png)

Sourceconfig
------------
Every environment contains `repositories` and each environment may have any number of repositories associated with it. `Repository` represents the binaries for mongo instance. Each repository can have many `SourceConfig` which represent mongo instance. There is no sourceconfig generated automatically in mongo-plugin. We need to configure `SourceConfig` objects through which we can create a dSource. 
