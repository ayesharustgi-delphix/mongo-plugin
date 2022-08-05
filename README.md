# MongoDB Plugin

## What Does a Delphix Plugin Do?

Delphix is a data management platform that provides the ability to securely copy and share datasets. Using virtualization, you will ingest your data sources and create virtual data copies, which are full read-write capable database instances that use a small fraction of the resources a normal database copy would require. The Delphix engine has built-in support for interfacing with certain types of datasets, such as Oracle, SQL Server and ASE.

The Delphix virtualization SDK (https://github.com/delphix/virtualization-sdk) provides an interface for building custom data source integrations for the Delphix Dynamic Data Platform. The end users can design/implement a custom plugin which enable them to use custom data source like MongoDB, MySQL, Cassandra, Couchbase or any other datasource similar to built-in dataset types like Oracle, SQL Server, vFiles etc with Delphix Engine.

## About MongoDB Plugin:
MongoDB plugin is developed to virtualize mongoDB data source leveraging the following built-in mongoDB technologies:


- Mongodump        : Export source data and import into Staging mongo instance (dSource). Useful for offline/online backups of small databases (onprem,Saas,MongoAtlas)
- Replication      : Add replicaset member to existing cluster.
- Mongo Ops Manager: Use existing backups as file from Mongo OPS Manager (Zero Touch Production).

## What's new

Please check a [change log](./CHANGELOG.md) for list of changes.
## User Documentation
Documentation to install, build, upload and use the plugin is available at: https://delphix.github.io/mongo-plugin.

## <a id="contribute"></a>Contribute

1.  Fork the project.
2.  Make your bug fix or new feature.
3.  Add tests for your code.
4.  Send a pull request.

Contributions must be signed as `User Name <user@email.com>`. Make sure to [set up Git with user name and email address](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup). Bug fixes should branch from the current stable branch. New features should be based on the `master` branch.

#### <a id="code-of-conduct"></a>Code of Conduct

This project operates under the [Delphix Code of Conduct](https://delphix.github.io/code-of-conduct.html). By participating in this project you agree to abide by its terms.

#### <a id="contributor-agreement"></a>Contributor Agreement

All contributors are required to sign the Delphix Contributor agreement prior to contributing code to an open source repository. This process is handled automatically by [cla-assistant](https://cla-assistant.io/). Simply open a pull request and a bot will automatically check to see if you have signed the latest agreement. If not, you will be prompted to do so as part of the pull request process.


## <a id="reporting_issues"></a>Reporting Issues

Issues should be reported in the GitHub repo's issue tab. Include a link to it.

## <a id="statement-of-support"></a>Statement of Support

This software is provided as-is, without warranty of any kind or commercial support through Delphix. See the associated license for additional details. Questions, issues, feature requests, and contributions should be directed to the community as outlined in the [Delphix Community Guidelines](https://delphix.github.io/community-guidelines.html).


## License

This is code is licensed under the Apache License 2.0. Full license is available [here](./LICENSE).
