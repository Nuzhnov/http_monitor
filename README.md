# Monitoring solution
The website monitor should perform the checks periodically and collect the request timestamp,
the response time, the HTTP status code, as well as optionally checking the returned page
contents for a regex pattern that is expected to be found on the page.

We use 2 tables in postgres:
- `monitor_queue` for tasks
- `monitor_metrics` for results

Scheduling works by selecting tasks from `monitor_queue` table with update on `next_check` timestamp by incrementing with `check_interval` seconds.

Results records are written with batches, configured by one of 2 parameters:
- `BATCH_INTERVAL` - time for collecting records to the batch (default 60 seconds)
- `BATCH_SIZE` - number of records per batch (default 100 records)

Monitoring services could be spawned. Perfromance of each one depends from number of workers `NUM_WORKERS` (default 10)


## Install
Create venv

```bash
python -m venv venv

. venv/bin/activate
```

Install requirements
```bash
pip install requirments
```

Run postgresql database with SSL connection.


## Usage
For initializing database and creating resource checking tasks use `cli` mode.
For service run use `service` mode.

## CLI tool mode

### Initialize db

```bash
python3 cli.py --host .. --user ... --dbname ... --port ... --password ... --secure init-db
```

### Add resources for monitoring

```bash
python3 cli.py --host .. --user ... --dbname ... --port ... --password ... insert-resource <url> <interval> <re_pattern> - optional
```

## Service mode

### Add next environment variables
`DB_HOST` - database host

`DB_PORT` - database port

`DB_USER` - databse user

`DB_PWD` - user password

`DB_NAME` - database name

 `BATCH_INTERVAL` - [**optinal**] time in seconds, how often you would like to export results
 
`BATCH_SIZE` - [**optional**] interval in number of results, in which you would like to export results

`NUM_WORKERS` - [**optional**] number of worker threads

Could be started:
 - as is:
   ```bash
   DB_HOST="..." DB_USER="..." DB_NAME="..." DB_PORT="..." DB_PWD="..."  python main.py
   ```
 - as docker container (pass environment variables with `-e`):
   ```bash
   docker run -it -e DB_HOST="..." -e DB_USER="..." -e DB_NAME="..." -e DB_PORT="..." 
   -e DB_PWD="..." <container_id>
   ```
 - with docker compose:
   ```bash
   docker-compose up -d
   ``` 
   (Dockerfile and example of compose file are included). 

In terms of perfromance you can add new instances of service (for example, scale number of pods in k8s environment.)