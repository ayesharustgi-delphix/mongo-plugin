# Staging Requirements

###### O/S User / Privileges

- Regular o/s user with primary group as mongod.  
- Execute access on mongo/mongod binaries  
- mongo and mongod binaries to be in same folder [ if required create softlink ]  
- Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]  
- Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as base folder for nfs mounts.  
- Access to source instance backup file(s) from Staging host logged as delphix user (applicable for mongo ops mgr / offline mongodump use case).  
- sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.  

```shell
Defaults:delphixos !requiretty
delphixos ALL=NOPASSWD: \
/bin/mount, /bin/umount
```  