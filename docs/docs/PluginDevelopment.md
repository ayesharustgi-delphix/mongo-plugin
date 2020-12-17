Build plugin
------------

- Create python virtual environment and install required libraries (dvp, pytest, pytest-html & pytest-cov) using script `virtualEnvSetup.sh`  
    
```shell  
cd <full path of project directory till `mongo-plugin`>  
./test/virtualEnvSetup.sh <virtual enviornment name>  

For example:  
cd /u01/github/delphix/Plugins/mongo-plugin   
./test/virtualEnvSetup.sh "MyLocalEnv"  
```  

- Run this command to activate the virtual environment created in step 1.
```bash
. test/MyLocalEnv/bin/activate
```

- Build the source code. It generates the build with name `artifacts.json`:
```bash
dvp build
```

Upload plugin
----------------
Upload the `artifacts.json` ( generated in step 3 ) on Delphix Engine:
```bash
dvp upload -e <Delphix_Engine_Name> -u <username> --password <password>
```

Debug plugin logs
------------------
Download the plugin logs using below command:

```dvp download-logs -c plugin_config.yml -e <Delphix_Engine_Name> -u admin --password <password>```
