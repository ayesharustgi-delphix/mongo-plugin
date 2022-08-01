Build plugin
------------

- Create python3 virtual environment and install required libraries (dvp, pytest, pytest-html & pytest-cov)

```shell
cd <full path of project directory till `mongo-plugin`>  
source bin/activate

For example:  
cd /u01/github/delphix/Plugins/mongo-plugin   
source bin/activate
pip install dvp=4.0.0 
```

- Build the source code. It generates the build with name `artifacts.json`:

```bash
dvp build
```

Upload plugin
-------------

Upload the `artifacts.json` ( generated in step 3 ) on Delphix Engine:

```bash
dvp upload -e <Delphix_Engine_Name> -u <username> --password <password>
```

Debug plugin logs
-----------------

Download the plugin logs using below command:

```dvp download-logs -c plugin_config.yml -e <Delphix_Engine_Name> -u admin --password <password>```
