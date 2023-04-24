# Discovery

Environment discovery is a process that enables the mongoDB Plugin to determine mongo installation details on a host. Whenever there is any changes (installing a new binary home) to an already set up environment in the Delphix application, environment refresh need to be performed. 

Prerequisites
-------------

- Install delphix engine 6.0.7.x and above  
- Install mongo binaries on staging and target servers  
- Installation of the mongoDB Plugin is required before the discovery  
- Environment variable `$MONGO_PATH ` should be set on staging/target host using `$HOME/.setDelphixMongoEnv` and `MONGO_REPO_CFGFILE `, which contains binary path of mongo using below procedure.

Mongo Binaries Discovery  
------------------------  
Mongo can be installed in different ways and so the path can vary in different environments. To discover correct binaries, follow steps as below

Steps: 

1. Login to the Staging Host as delphix os user.

2. Create a file name ".setDelphixMongoEnv" in home directory of delphix user.  

    ```shell
    touch $HOME/.setDelphixMongoEnv
    ```

3. Define variable pointing to config file for manual discovery of mongodb instances. Example as below.  

    ```shell
    echo "MONGO_REPO_CFGFILE=/home/delphix/.mongorepos.txt" > $HOME/.setDelphixMongoEnv
    ```

4. Define full path to mongod binary in file represented by $MONGO_REPO_CFGFILE. Example as below.  

    ```shell
    source $HOME/.setDelphixMongoEnv  
    ```

    ```shell
    echo "MONGO_PATH=/u01/mongodb428/bin/mongod" > $MONGO_REPO_CFGFILE  
    ```

    If there are multiple version binaries, specify each on separate lines as below  

    ```shell
    source $HOME/.setDelphixMongoEnv  
    ```

    ```shell
    echo "MONGO_PATH=/u01/mongodb428/bin/mongod" > $MONGO_REPO_CFGFILE  
    ```

    ```shell
    echo "MONGO_PATH=/u01/mongodb509/bin/mongod" >> $MONGO_REPO_CFGFILE  
    ```
    If the MongoDB database tools are installed at different location, specify the MongoDB tools path on separate lines as below  

    ```shell
    source $HOME/.setDelphixMongoEnv  
    ```

    ```shell
    echo "MONGO_PATH=/u01/mongodb428/bin/mongod:/u01/mongodb428/mongodb-database-tools/bin" > $MONGO_REPO_CFGFILE  
    ```
    ```shell
    echo "MONGO_PATH=/u01/mongodb509/bin/mongod:/u01/mongodb509/mongodb-database-tools/bin" > $MONGO_REPO_CFGFILE  
    ```
    In a similar fashion, more directories (such as directory containing `mongosync` or `mongosh`)corresponding to a repository can be added as below:
    
    ```shell
    source $HOME/.setDelphixMongoEnv  
    ```
    ```shell
    echo "MONGO_PATH=/u01/mongodb603/bin/mongod:/u01/mongodb603/mongodb-database-tools/bin:/u01/mongodb603/mongosync/bin:/u01/mongodb603/mongo-shell/bin" > $MONGO_REPO_CFGFILE  
    ```
    For additional info refer [this section](#pts_repo_cfg)

5. Login to the **Delphix Management application**.
6. Click **Manage**.
7. Select **Environments**.
8. In the **Environments** panel, click the name of the environment you want to refresh.
9. Select the **Refresh icon**.
10. In the Refresh confirmation dialog select **Refresh**.

    ![Screenshot](../image/image9.png)


### <a id="pts_repo_cfg"></a>Points to Remember while creating `$MONGO_REPO_CFGFILE`:

1. Each line in the file represents a unique version of installation. If there are multiple installations in an environment, the file will contain multiple lines.
2. The mandatory binaries for a successful discovery are `mongod` and `mongo` / `mongosh`.
3. Discovery of `mongodump`, `mongorestore` and `mongosync` are optional based on dsource type.
4. Multiple paths for each repository can be provided separated my `:` (first priority given to first path provided) for discovering all the desired binaries listed above.
5. The path provided should contain the binary in the immediate directory. 
   For example, for discovering `/u01/mongo603/database-tools/bin/mongorestore`, the path provided should be `/u01/mongo603/database-tools/bin` and not `/u01/mongo603/database-tools`


Sourceconfig
------------
Every environment contains `repositories` and each environment may have any number of repositories associated with it. `Repository` represents the binaries for mongo instance. Each repository can have many `SourceConfig` which represent mongo instance. There is no sourceconfig generated automatically in mongo-plugin. We need to configure `SourceConfig` objects through which we can create a dSource. 
