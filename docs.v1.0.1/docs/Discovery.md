# Discovery

Environment discovery is a process that enables the mongoDB Plugin to determine mongo installation details on a host. Whenever there is any changes (installing a new binary home) to an already set up environment in the Delphix application, environment refresh need to be performed. 

Prerequisites
-------------

- Install delphix engine 5.3.x and above  
- Install mongo binaries on staging and target servers  
- Installation of the mongoDB Plugin is required before the discovery  
- Environment variable `$MONGO_PATH ` should be set on staging/target host, which contains binary path of mongo

Mongo Binaries Discovery  
------------------------  
Mongo can be installed in different ways and so the path can vary in different environments. To discover correct binaries, follow steps as below

Steps: 

1. Login to the Staging Host as delphix os user.

2. Create a file name ".setDelphixMongoEnv" in home directory of delphix user.  

    ```
    touch $HOME/.setDelphixMongoEnv
    ```

3. Define variable pointing to config file for manual discovery of mongodb instances. Example as below.  

    ```
    echo "MONGO_REPO_CFGFILE=/home/delphix/.mongorepos.txt" > $HOME/.setDelphixMongoEnv
    ```

4. Define full path to mongod binary in file represented by $MONGO_REPO_CFGFILE. Example as below.  

    ```
    source $HOME/.setDelphixMongoEnv  
    ```

    ```
    echo "MONGO_PATH=/u01/mongodb366/bin/mongod" > $MONGO_REPO_CFGFILE  
    ```

    If there are multiple version binaries, specify each on seperate line as below  

    ```
    source $HOME/.setDelphixMongoEnv  
    ```

    ```
    echo "MONGO_PATH=/u01/mongodb366/bin/mongod" > $MONGO_REPO_CFGFILE  
    ```

    ```
    echo "MONGO_PATH=/u01/mongodb404/bin/mongod" >> $MONGO_REPO_CFGFILE  
    ```

5. Login to the Delphix Management application.
6. Click Manage.
7. Select Environments.
8. In the Environments panel, click the name of the environment you want to refresh.
9. Select the Refresh icon.
10. In the Refresh confirmation dialog select Refresh.

    ![Screenshot](image/image9.png)

Sourceconfig
------------
Every environment contains `repositories` and each environment may have any number of repositories associated with it. `Repository` represents the binaries for mongo instance. Each repository can have many `SourceConfig` which represent mongo instance. There is no sourceconfig generated automatically in mongo-plugin. We need to configure `SourceConfig` objects through which we can create a dSource. 
