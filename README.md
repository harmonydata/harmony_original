# Harmony

Harmony is a data harmonisation project that uses Natural Language Processing to helpresearchers make better use of existing data from different studies by supporting them with the harmonisation of various measures and items used in different studies.. Harmony is a collaboration project between the University of Ulster, University College London, the Universidade Federal de Santa Maria in Brazil, and Fast Data Science Ltd.

You can read more at https://harmonydata.org.

There is a live demo at: https://app.harmonydata.org/

This front end is based on the Dash Food Footprint demo: https://dash.gallery/dash-food-footprint/

Runs on Dash interactive Python framework developed by [Plotly](https://plot.ly/). 

Developed by Thomas Wood / Fast Data Science
thomas@fastdatascience.com

This tool is written in Python using the Dash front end library and the Java library Tika for reading PDFs, and runs on Linux, Mac, and Windows, and can be deployed as a web app using Docker.

# Very quick guide to running the tool on your computer

1. Install [Docker](https://docs.docker.com/get-docker/).
2. Open a command line or Terminal window. Change folder to where you downloaded and unzipped the repository, and go to the folder `front_end`.  Run the following command:
```
docker build -t harmony
docker run harmony
```
5. Open your browser at `https://localhost:80`. You will see the web app running.

# Deploying the tool to Azure using the Azure Command Line Interface via Azure Container Registry

In command line, if you have installed Azure CLI, log into both the Azure Portal and Azure Container Registry:

```
az login
az acr login --name regprotocolsfds
```

If the admin user is not yet enabled, you can use the command:
```
az acr update -n regprotocolsfds --admin-enabled true
```

Run this script:

```
./build_deploy.sh
```

## Developer's guide: Running the tool on your computer in Python and without using Docker

### Architecture

TODO

### Installing requirements

Download and install Java if you don't have it already. Download and install Apache Tika and run it on your computer https://tika.apache.org/download.html

```
java -jar tika-server-standard-2.3.0.jar
```

(the version number of your Jar file name may differ.)

Install everything in `requirements.txt`:

```
pip install -r requirements.txt
```

### Running the front end app locally

Go into `front_end` and run

```
python application.py
```

You can then open your browser at `localhost:8050` and you will see the tool.

## Built With

- [Dash](https://dash.plot.ly/) - Main server and interactive components
- [Plotly Python](https://plot.ly/python/) - Used to create the interactive plots
- [Docker](https://docs.docker.com/) - Used for deployment to the web
- [Apache Tika](https://tika.apache.org/) - Used for parsing PDFs to text
- [spaCy](https://spacy.io/) - Used for NLP analysis
- [NLTK](https://www.nltk.org/) - Used for NLP analysis
- [Scikit-Learn](https://scikit-learn.org/) - Used for machine learning

## Licences of Third Party Software

- Apache Tika: [Apache 2.0 License](https://tika.apache.org/license.html)
- spaCy: [MIT License](https://github.com/explosion/spaCy/blob/master/LICENSE)
- NLTK: [Apache 2.0 License](https://github.com/nltk/nltk/blob/develop/LICENSE.txt)
- Scikit-Learn: [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/main/COPYING)

## References

* Deploying a Dash webapp via Docker to Azure: https://medium.com/swlh/deploy-a-dash-application-in-azure-using-docker-ed46c4b9d2b2
