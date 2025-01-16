# Zeeguu-API ![Build Status](https://github.com/zeeguu-ecosystem/Zeeguu-API/actions/workflows/test.yml/badge.svg)

Zeeguu-API is an open API that allows tracking and modeling the progress of a learner in a foreign language with the
goal of recommending paths to accelerate vocabulary acquisition.

The API is also currently deployed as the backend for the [zeeguu.org](https://zeeguu.org) website.

## Overview

The API offers translations for the words that a learner encounters in their readings. The history of the translated
words and their context is saved and used to build a dynamic model of the user knowledge. The context is used to extract
the words the user knows and their topics of interest.

A teacher agent recommends the most important words to be studied next in order for the learner to accelerate his
vocabulary retention. This information can be used as input by language exercise applications, for example interactive
games.

A text recommender agent crawls websites of interest to the user and recommend materials to read which are in the zone
of proximal development.

## Read More

To read more about the API see
the [article](https://www.researchgate.net/publication/322489283_As_We_May_Study_Towards_the_Web_as_a_Personalized_Language_Textbook)
published about Zeeguu in the CHI'18 conference.

# Development Notes

Once you clone the repo, please run:

    git config --local core.hooksPath .githooks/

This will make the rules in the .githooks/rules
folder be run before every commit. The rules
check for well-known bugs and code conventions.

# Prerequisites

1. Install `docker` on your machine. For Ubuntu you can run the following:

```sh
sudo apt-get install docker.io -y
```

# With MySQL Locally

This is useful for MacOS machines (M1 and later) on which MySQL does not seem to be running within docker

1. Create a zeeguu_test DB

- Create zeeguu_test:zeeguu_test user with access to the DB
- Import anonymized db data from ...

1. Build the `zeguu_api_dev` development image

   `docker build -f Dockerfile.development -t zeeguu_api_dev .`

2. Run the \_playground.py to ensure that you have something in the DB

   `docker-compose up dev_play`

   To ensure that the changes to the files on your local dev machine are reflected inside the container try to modify
   something in the `tools\_playground.py` file and rerun this command. Do you see the changes? That's good.

3. Run the development server inside of the container

   `docker-compose up dev_server`

   to test it open http://localhost:9001/available_languages in your browser and you should be able to see a list of
   language codes that are supported by the system

4. Test the deployment

   `docker-compose up dev_test`

### Note

Running from a docker image, at least on my M1 Max from 2021, is terribly slow. The `_playground.py` script takes 1s
natively and 6s in Docker. Tests natively are 22s and in Docker are 280s!
So for running the development server this is ok, but for actual development, this might be quite annoying :(

# From docker-compose on Mac OS

## Starting the API

- create a local folder where you want to store zeeguu data, e.g. `mkdir /Users/mircea/zeeguu-data`
- make sure that you have `envsubst` installed (i.e. `brew install gettext`)
- copy the content of `default_env` to a newly created `.env` file
- run `generate-configs.sh`; verify that `api.cfg` and `fmd.cfg` have meaningful values inside
- run `docker compose up`
- once everything is up, go to `localhost:8080/available_languages`: if you see an array like `["de", "es", "fr", "nl", "en"]` you have the API working.

## Developing

Once you make changes to the code you have to restart the apache2ctl inside the container. To test this do the following:

- try to change the implementaiton of `available_languages` in `system_languages.py` and then
  run `docker exec -it api-zapi-1 apache2ctl restart`
- now if you revisit the api above you should see the modified response

That's all. Go have fun!

# Further Notes

## Running MySQL locally, not in a container on a mac

_(Mircea, Feb 2024)_

On Mac, if you want to run mysql locally, and not from within Docker, you need to install mysql-client with brew:

```
brew install mysql-client
```

Mircea: On my M2 mac the `pip instal mysqlclient` (called indirectly via `pip install -r requirements`) still fails till
I define the following:

```
export MYSQLCLIENT_CFLAGS="-I/opt/homebrew/opt/mysql-client/include/mysql/"
export MYSQLCLIENT_LDFLAGS="-L/opt/homebrew/opt/mysql-client/lib -lmysqlclient"
```

## How to initialize user_commitment table 

_(Chloe & Johanna, Dec 2024)_
Script for initializing the user_commitment table: api/tools/migrations/24-12-13--adding-user-commitment-table.sql.

## How to test the user commitment feature

_(Chloe & Johanna, Dec 2024)_
To test the consecutive weeks count:

1. **Register a new test user and set the goals** for the user during the registration (feature only works for new users at the moment)

2. **The consecutive weeks count relies on the consectuve_weeks field in the user_commitment table and the current week.** Therefore, to test the consecutive weeks count, add exersice or reading sessions to the current week. See example in script 24-12-14--insert_exercise_session.sql
   
3. **To test with a pre-existing conecutive weeks value > 0.** Update the consectuive_weeks field in the user_commitment table to a value greater than 0. Add the date of the last sessions that met the weekly goal. See example in script 24-12-15--update_consecutive_weeks_and_commitment_last_updated.sql

4. **Update goals:** You can modify goal preferences under Settings.

Note! The consecutive weeks count, is a little difficult to test, because of the code logic. The consecutive count depends on the consecutive_weeks field, which tracks how many consecutive weeks the user has met their goals. The logic verifies valied sessions for the current week, so testing required adding sessions only to the current week.

## Connecting and loading a database in DBeaver

- expose port 3306 to connect to local db by adding `- ports:"3306-3306"` to your docker-compose file
- create a new database connection in DBeaver and use Server Host `localhost`and Port `3306`
- import data to your local db by adding a `backups` folder to zeeguu-data and adding volume `- ${ZEEGUU_DATA_FOLDER}/backups:/backups` to the docker-compose file
- run `docker exec -it <CONTAINER ID FOR DB> sh`
- run `mysql -uroot -p -h localhost zeeguutest < zeeguu_db_anon_2024-10-16.sql` and enter the root password

