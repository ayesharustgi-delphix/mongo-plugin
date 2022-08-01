# Oracle Backup Ingestion (OBI)

Oracle Backup Ingestion is virtualization plugin built on top of the Delphix Data Platform. Plugins are intended to enhance and extend the 
capabilities of the Delphix Virtualization platform. 

This repository serves as the central location for the documentation related to Mongo plugin.

## Getting Started
These instructions will get you a copy of the project up and running on your local 
machine for development and testing purposes. 


### Prerequisites

- macOS 10.15.7+ or Windows 10
- A Code Editor/IDE
- Python 3.9.x
- Python libraries in requirements.txt. ( Using a virtual environment is recommended.)


```
pip install -r requirements.txt
```

### Installing

We highly recommended using a virtual environment for development. 
To learn more about virtual environments, refer to [Virtualenv's documentation](https://virtualenv.pypa.io/en/latest/).

The virtual environment needs to use Python 3.9. This is configured when creating the virtualenv:
```
$ virtualenv -p /path/to/python3.9/binary ENV
```

Install all the libraries mentioned in the requirements.txt

```
pip install -r requirements.txt
```

The virtual environment is now ready to build and test the docs using mkdocs.

### Building
Navigate to the folder that contains mkdocs.yml

```
mkdocs build --clean -v
```
This builds the deployable content under /site/ directory. 

## Running the tests

To run a test on the local machine, use the following command. 
```
mkdocs serve 
```
To test on a custom IP:PORT combination, use the following command. 
```
mkdocs serve -a ip:port
```

### Deploying

To deploy documentation on to github, 

```
mkdocs gh-deploy --force
```

### Contributing

This repository is currently internal to Delphix Engineering and not accepting external contributions.
To contribute
1. Fork the repository
2. Build, Test and Push your changes to forked repository
3. Open a PR to the main repository. 
4. Add reviewers. 

## License

Delphix Internal. Copyright (c) 2021,2022 by Delphix. All rights reserved.
