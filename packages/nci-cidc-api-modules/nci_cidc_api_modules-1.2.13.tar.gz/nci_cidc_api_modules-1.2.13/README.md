# NCI CIDC API <!-- omit in TOC -->

The next generation of the CIDC API, reworked to use Google Cloud-managed services. This API is built with the Flask REST API framework backed by Google Cloud SQL, running on Google App Engine.

## Development <!-- omit in TOC -->

- [Install Python dependencies](#install-python-dependencies)
- [Database Management](#database-management)
  - [Setting up a local development database](#setting-up-a-local-development-database)
  - [Connecting to a Cloud SQL database instance](#connecting-to-a-cloud-sql-database-instance)
  - [Running database migrations](#running-database-migrations)
- [Serving Locally](#serving-locally)
- [Testing](#testing)
- [Code Formatting](#code-formatting)
- [Deployment](#deployment)
  - [CI/CD](#cicd)
  - [Deploying by hand](#deploying-by-hand)
- [Connecting to the API](#connecting-to-the-api)
- [Provisioning the system from scratch](#provisioning-the-system-from-scratch)
- [Docker Compose](#setting-up-docker-compose)

## Install Python dependencies

Use Python version 3.13

```bash
# make a virtual environment in the current direcory called "venv"
python3 -m venv venv
source venv/bin/activate
# optionally add an alias to your shell rc file
# alias activate='source venv/bin/activate'
```

Install both the production and development dependencies. 

```bash
pip install -r requirements.dev.txt
```

Install and configure pre-commit hooks for code formatting and commit message standardization.

```bash
pre-commit install
```

## Database Management

### Setting up a local development database

In production, the CIDC API connects to a PostgreSQL instance hosted by Google Cloud SQL, but for local development, you should generally use a local PostgreSQL instance.

To do so, first install and start PostgreSQL:

```bash
brew install postgresql@16
brew services start postgresql@16 # launches the postgres service whenever your computer launches
```

> The cidc-devops repo creates a Cloud SQL instance using postgresql@9.6 which is disabled through homebrew. The earliest non-deprecated version through homebrew is postgresql@11.

---

### Troubleshooting Homebrew PostgreSQL Installation

1. If you already have a different version of postgresql installed via homebrew, see this gist for upgrading help https://gist.github.com/olivierlacan/e1bf5c34bc9f82e06bc0. You could also try `brew postgresql-upgrade-database`.

2. If you see issues regarding "postmaster.pid already exists", see this post https://stackoverflow.com/questions/36436120/fatal-error-lock-file-postmaster-pid-already-exists.

3. You may see that `brew services start postgresql@11` succeeds, but when you list the services `brew services` you see an error for postgresql.

```bash
$ brew services
Name          Status  User     File
postgresql@11    error crouchcd ~/Library/LaunchAgents/homebrew.mxcl.postgresql@11.plist
```

In that case, use the plist file referenced in the command output to locate where the postgresql logs are written. The postgresql log file will help you detect the issue. If you see something regarding incompatible versions of postgresql, see issue #1.

---

Homebrew will install the psql client (psql) under /opt/homebrew/Cellar/postgresql@16/16.8/bin/ ; you may want to create a symlink from here to somewhere in your path.

By default, the postgres service listens on port 5432. Next, create the `cidcdev` user, your local `cidc` development database, and a local `cidctest` database that the unit/integration tests will use:

```bash
psql postgres -c "create user cidcdev with password '1234'"

# Database to use for local development
psql postgres -c "create database cidc"
psql cidc -c "grant all privileges on database cidc to cidcdev"
psql cidc -c "grant all privileges on schema public to cidcdev"
psql cidc -c "create extension citext"
psql cidc -c "create extension pgcrypto"

# Database to use for automated testing
psql postgres -c "create database cidctest"
psql cidctest -c "grant all privileges on database cidctest to cidcdev"
psql cidctest -c "grant all privileges on schema public to cidcdev"
psql cidctest -c "create extension citext"
psql cidctest -c "create extension pgcrypto"
```

Now, you should be able to connect to your development database with the URI `postgresql://cidcdev:1234@localhost:5432/cidc`. Or, in the postgres REPL:

```bash
psql cidc
```

---

## Install the gcloud CLI

https://cloud.google.com/sdk/docs/install. You will use this CLI to authenticate with GCP for development purposes.

### Setting Environment Variables

The app will use the environment variables defined in the [.env](./.env) file to connect to Auth0 and GCP. You will need to update those values with either the dev or staging Auth0 and GCP instances values provided by Essex or CBIIT/Cloud2. The following `flask db upgrade` command relies on these environment variables.

Each time the backend starts up (including cloud-functions), an object that pulls secrets from Secret Manager is used to initialize the google client libraries. You need to authenticate with gcloud beforehand so that the API can fetch the secrets. First, you will need to ensure that your account has the "Secret Manager Secrets Accessor" role. Then, generate Application Default Credentials by running the following,

```bash
gcloud auth application-default login
```

> To check that your gcloud config is set to the right config run `gcloud config list`.

The application reads environment variables that map to the appropriate secret ids for the selected project.  As of this writing, the env variables and secret ids are listed below (replace `[env_tag]` with the appropriate environment tag):

```yaml
env_variables:
  APP_ENGINE_CREDENTIALS_ID: "cidc_app_engine_credentials_[env tag]"
  AUTH0_CLIENT_SECRET_ID: "cidc_auth0_client_secret_[env tag]"
  CLOUD_SQL_DB_PASS_ID: "cidc_cloud_sql_db_pass_[env tag]"
  CSMS_BASE_URL_ID: "cidc_csms_base_url_[env tag]"
  CSMS_CLIENT_ID_ID: "cidc_csms_client_id_[env tag]"
  CSMS_CLIENT_SECRET_ID: "cidc_csms_client_secret_[env tag]"
  CSMS_TOKEN_URL_ID: "cidc_csms_token_url_[env tag]"
  INTERNAL_USER_EMAIL_ID: "cidc_internal_user_email_[env tag]"
  PRISM_ENCRYPT_KEY_ID: "cidc_prism_encrypt_key_[env tag]"
```

To ensure you are using the correct secret ids, you may list the secrets for the active project using the following command:

```
gcloud secrets list
```

#### Adding new secrets to the application

To add new secrets to the application, follow the instructions below:

1. Choose a name for the secret.  It should be snake case, and end in the relevant environment tag, as seen above.
1. Reach out to the DevOps team to add the secret to Secret Manager.  Include the secret value for each environment.
1. Choose an environment variable to map to the secret id.  It should end in `_ID`. This is because the secret will be passed in directly under testing conditions, using the same environment variable minus the `_ID` postfix to avoid conflicts.
1. Add the env variable mapping to the GAE environment configurations under the `secrets` section. These are the `app.[env].yaml` files.
1. Load the secret into the SETTINGS dictionary via the `cidc_api/config/settings.py` module. See the `# CSMS Integration Values` section for how to do this.


---

Next, you'll need to set up the appropriate tables, indexes, etc. in your local database. To do so, run:

```bash
FLASK_APP=cidc_api.app:app flask db upgrade
```

### Connecting to a Cloud SQL database instance

Make sure you are authenticated to gcloud:

```bash
gcloud auth login
gcloud auth application-default login
```

In your .env file, comment out `POSTGRES_URI` and uncommment
`CLOUD_SQL_INSTANCE_NAME CLOUD_SQL_DB_USER CLOUD_SQL_DB_NAME` Replace `CLOUD_SQL_DB_USER` with your NIH email.

### Running database migrations

This project uses [`Flask Migrate`](https://flask-migrate.readthedocs.io/en/latest/) for managing database migrations. To create a new migration and upgrade the database specified in your `.env` config:

```bash
export FLASK_APP=cidc_api/app.py
# Generate the migration script
flask db migrate -m "<a message describing the changes in this migration>"
# Apply changes to the database
flask db upgrade
```

To revert an applied migration, run:

```bash
flask db downgrade
```

If you're updating `models.py`, you should create a migration and commit the resulting

## Serving Locally

Once you have a development database set up and running, run the API server:

```bash
ENV=dev gunicorn cidc_api.app:app
```

## Testing

This project uses [`pytest`](https://docs.pytest.org/en/latest/) for testing.

To run the tests, simply run:

```bash
pytest
```

## Code Formatting

This project uses [`black`](https://black.readthedocs.io/en/stable/) for code styling.

We recommend setting up autoformatting-on-save in your IDE of choice so that you don't have to worry about running `black` on your code.

## Deployment

### CI/CD

This project uses [GitHub Actions](https://docs.github.com/en/free-pro-team@latest/actions) for continuous integration and deployment. To deploy an update to this application, follow these steps:

1. Create a new branch locally, commit updates to it, then push that branch to this repository.
2. Make a pull request from your branch into `master`. This will trigger GitHub Actions to run various tests and report back success or failure. You can't merge your PR until it passes the build, so if the build fails, you'll probably need to fix your code.
3. Once the build passes (and pending approval from collaborators reviewing the PR), merge your changes into `master`. This will trigger GitHub Actions to re-run tests on the code then deploy changes to the staging project.
4. Try out your deployed changes in the staging environment once the build completes.
5. If you're satisfied that staging should be deployed into production, make a PR from `master` into `production`.
6. Once the PR build passes, merge `master` into `production`. This will trigger GitHub Actions to deploy the changes on staging to the production project.

For more information or to update the CI workflow, check out the configuration in `.github/workflows/ci.yml`.

### Deploying by hand

Should you ever need to deploy the application to Google App Engine by hand, you can do so by running the following:

```bash
gcloud app deploy <app.staging.yaml or app.prod.yaml> --project <gcloud project id>
```

That being said, avoid doing this! Deploying this way circumvents the safety checks built into the CI/CD pipeline and can lead to inconsistencies between the code running on GAE and the code present in this repository. Luckily, though, GAE's built-in versioning system makes it hard to do anything catastrophic :-)

## Connecting to the API

Currently, the staging API is hosted at https://api.cidc-stage.nci.nih.gov and the production instance is hosted at https://api.cidc.nci.nih.gov.

To connect to the staging API with `curl` or a REST API client like Insomnia, get an id token from cidc-stage.nci.nih.gov, and include the header `Authorization: Bearer YOUR_ID_TOKEN` in requests you make to the staging API. If your token expires, generate a new one following this same procedure.

To connect to the production API locally, follow the same procedure, but instead get your token from cidc.nci.nih.gov.

## Provisioning the system from scratch

For an overview of how to set up the CIDC API service from scratch, see the step-by-step guide in `PROVISION.md`.

## Setting up Docker Compose

If you would like to run this project as a docker container.  We have dockerized the cidc-api-gae and cidc-ui so that you don't have to install all the requirements above.  Included in the docker-compose file are postgres:14 with data and test user login, bigquery-emulator, fake-gcs-server with buckets and data to match postgres, and gcs-oauth2-emulator to generate faked presigned urls.

**_NOTE:_** You must have docker installed and have this repository and cidc-ui in the same directory (~/git/cidc/cidc-ui and ~/git/cidc/cidc-api-gae), or you can download each and build the image with the command `docker build .`

**_NOTE:_** Having issues with the cidc-ui docker container. You'll have to start that manually using the instructions in the repo.

**_NOTE:_** You can't use Docker while simultaneously running your NIH VPN. This is due to a quirk with self-hosting a google secrets bucket. More work is required to make the docker containers work while the VPN is on.

This repo has hot code reloading. However, you will need to build the image again if there is an update to python libraries. Make sure you don't use a cached image when rebuilding.

Make sure you add this line to your /etc/hosts file: ```127.0.0.1       host.docker.internal```

To run everything simply run the following commands:
```bash
vim .env # uncomment the docker section in the .env file.  Comment out any overlaping variable defintions(POSTGRES)
cp ~/.config/gcloud/application_default_credentials.json .
cd docker
docker compose up
```
**_NOTE:_** You still need to install and signin to gcloud CLI. The application_default_credentials.json should be under the cidc-api-gae directory next to the Dockerfile. We have mocked most of the connection points to GCP but at startup it still checks for a valid user account. This is very similar behavior to aws's localstack. It requires a realistic token at the start even though it doesn't make connections to aws.

**_TODO:_** The application_default_credentials.json I think could be faked and pointed to the gcs-oauth2-emulator for startup.  In this case a gcloud cli wouldnt be needed at all and a faked application_default_credentials.json could be uploaded under the docker folder.



## JIRA Integration

To set-up the git hook for JIRA integration, run:

```bash
ln -s ../../.githooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
rm .git/hooks/commit-msg.sample
```

This symbolic link is necessary to correctly link files in `.githooks` to `.git/hooks`. Note that setting the `core.hooksPath` configuration variable would lead to [pre-commit failing](https://github.com/pre-commit/pre-commit/issues/1198). The `commit-msg` hook [runs after](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) the `pre-commit` hook, hence the two are de-coupled in this workflow.

To associate a commit with an issue, you will need to reference the JIRA Issue key (For eg 'CIDC-1111') in the corresponding commit message.

## API FAQ

#### How is the API repo structured?

At the top-level, there are a handful of files related to how and where the API code runs:

- [app.prod.yaml](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/app.prod.yaml) and [app.staging.yaml](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/app.staging.yaml) are the App Engine config files for the prod and staging API instances - these specify instance classes, autoscaling settings, env variables, and what command App Engine should run to start the app.
- [gunicorn.conf.py](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/gunicorn.conf.py) contains config for the [gunicorn](https://gunicorn.org/) server that runs the API’s flask app in production.

[The migrations/versions directory](https://github.com/NCI-CIDC/cidc-api-gae/tree/master/migrations/versions) contains SQLAlchemy database migrations generated using flask-sqlalchemy.

The core API code lives in a python module in the [cidc_api](https://github.com/NCI-CIDC/cidc-api-gae/tree/master/cidc_api) subdirectory. In this subdirectory, the [app.py](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/cidc_api/app.py) file contains the code that instantiates/exports the API’s flask app. Stepping through that file top to bottom is probably the best way to get an overall picture of the structure of the API code:

- [get_logger](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/config/logging.py#L11) instantiates a logger instance based on whether the app is running in a flask development server or gunicorn production server. We need this helper function (or something like it), because logs must be routed in a particular manner for them to show up in stderr when the app is running as a gunicorn server. Any python file in the cidc_api module that includes logging should call this get_logger helper at the top of the file.
- Next, the Flask app instance is created and configured using settings loaded from [settings.py](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/cidc_api/config/settings.py). This file contains a handful of constants used throughout the app code. Additionally, it contains code for [setting up the temporary directories](https://github.com/NCI-CIDC/cidc-api-gae/blob/001e12ac276a9632260fbddd54419cbcb8a5e2b5/cidc_api/config/settings.py#L37) where empty manifest/assay/analysis templates will live. [This line](https://github.com/NCI-CIDC/cidc-api-gae/blob/001e12ac276a9632260fbddd54419cbcb8a5e2b5/cidc_api/config/settings.py#L118) at the bottom of the file builds a settings dictionary mapping variable names to values for all constants (i.e., uppercase variables) defined above it.
- Next, [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) is enabled. CORS allows the API to respond to requests originating from domains other than the API’s domain. If we didn’t do this, then an API instance running at “api.cidc.nci.nih.gov” would be prohibited from responding to requests from a UI instance running at “cidc.nci.nih.gov”.
- Next, [init_db](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/config/db.py#L17) connects the flask-sqlalchemy package to a given API app instance. Moreover, it sets up our database migration utility, [flask-migrate](https://flask-migrate.readthedocs.io/en/latest/), which provides CLI shortcuts for generating migrations based on changes to the API’s sqlalchemy models. Currently, db migrations are [run every time init_db is called](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/config/db.py#L23), but this is arguably tech debt, since it slows down app startup for no good reason - it might be better to try running db migrations as part of CI. (All other code in this file is related to building database connections based on the environment in which the app is running).
- Next, [register_resources](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/resources/__init__.py#L12) “wires up” all of the REST resources in the API, which are organized as independent flask [blueprints](https://flask.palletsprojects.com/en/2.0.x/blueprints/). Each resource blueprint is a collection of flask endpoints. Resources are split up into separate blueprints solely for code organization purposes.
- Next, [validate_api_auth](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/shared/auth.py#L17) enforces that all endpoints configured in the API are explicitly flagged as public or private using the [public](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/shared/auth.py#L75) and [requires_auth](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/shared/auth.py#L34) decorators, respectively. This is intended to help prevent a developer from accidentally making a private endpoint public by forgetting to include the requires_auth decorator. If this validation check fails, the app won’t start up.
- Next, [register_dashboards](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/dashboards/__init__.py#L6) wires up our plot.ly dash dashboards.
- Next, [handle_errors](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/app.py#L37) adds generic code for formatting any error thrown while a request is being handled as JSON.
- Finally, if the app submodule is being run directly via “python -m cidc_api.app”, [this code](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/app.py#L65) will start a flask (non-gunicorn) server.

For diving deeper into the API code’s structure, the next place to look is the [resources](https://github.com/NCI-CIDC/cidc-api-gae/tree/master/cidc_api/resources) directory. Endpoint implementations string together code for authenticating users, loading and validating JSON input from requests, looking up or modifying database records, and dumping request output to JSON. For some endpoints, a lot of this work is handled using generic helper decorators - e.g., the [update_user](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/resources/users.py#L111) endpoint uses nearly every helper available in the [rest_utils.py](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/cidc_api/shared/rest_utils.py) file. For others, like the [upload_analysis](https://github.com/NCI-CIDC/cidc-api-gae/blob/1de8b59e87eb71a3f8f8e997225e81d6b04b73fd/cidc_api/resources/upload_jobs.py#L509) endpoint, the endpoint extracts request data and builds response data in an endpoint-specific way. Most endpoints will involve some interaction with sqlalchemy models, either directly in the function body or via helper decorators.

#### How do I add a new resource to the API?

1. Create a new file in the [resources](https://github.com/NCI-CIDC/cidc-api-gae/tree/master/cidc_api/resources) directory named “&lt;resource>.py”.
2. Create a flask blueprint for the resource, named “&lt;resource>\_bp” ([example](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/info.py#L13)).
3. Add the blueprint to the [register_resources](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/__init__.py#L12) function. The resource’s url_prefix should generally be “/&lt;resource>”.

#### How do I add a new endpoint to the API?

If you want to add an endpoint to an existing REST resource, open the file in the resources directory related to that resource. You can build an endpoint using some (almost definitely not all) of these steps:

- **Wire up the endpoint**. Find the [blueprint](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/users.py#L25) for the resource, usually named like “&lt;resource>\_bp”. You add an endpoint to the blueprint by decorating a python function using the [route](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/users.py#L33) method on the blueprint instance.
- **Configure endpoint auth**. Either flag the endpoint as public using the [public](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/info.py#L17) decorator, or configure authentication and authorization using the [requires_auth](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/users.py#L68) decorator. The requires_auth decorator takes a unique string identifier for this endpoint as its required first argument (potentially used for endpoint-specific role-based access control logic [here](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L252) - the string ID is passed to the “resource” argument), and an optional list of allowed roles as its second argument (if no second arg is provided, users with all roles will be able to access the endpoint).
- **Configure custom URL query params.** The API uses the [webargs](https://webargs.readthedocs.io/en/latest/) library for validating and extracting URL query param data. For example, the “GET /permissions/” endpoint [configures a query param "user_id"](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/permissions.py#L33) for filtering the resulting permissions list by user id.
- **Look up a database record associated with the request.** Use the [with_lookup](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/rest_utils.py#L94) decorator to load a database record based on a URL path parameter. The with_lookup decorator takes three arguments: the first is the sqlalchemy model class, the second is the name of the URL path parameter that will contain the ID of the database record to look up, and the third is whether or not to check that the client making the request has seen the most recent version of the object (an “etag” is a hash of a database record’s contents - set check_etag=True to ensure that the client’s provided etag is up-to-date in order to, e.g., prohibit updates based on stale data). See, for example, usage for [looking up a particular user by ID](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/users.py#L98) - note that “user” is the name of the URL path parameter in the argument to user_bp.route.
- **Deserialize the request body**. POST and PATCH endpoints generally expect some JSON data in the request body. Such endpoints should validate that this data has the expected structure and, if appropriate, load that data into a sqlalchemy model instance. The [unmarshal_request](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/rest_utils.py#L27) decorator makes it easy to do this. The unmarshal request decorator takes three arguments: the first is a [marshmallow](https://marshmallow.readthedocs.io/en/stable/) schema defining the expected request body structure, the second is the argument name through which the deserialized result data should be passed to the endpoint function (e.g., [“permission” ](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/permissions.py#L66)and [permission](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/permissions.py#L68)), and the third is whether to try loading the request body into a sqlalchemy model or to just leave it as a python dictionary. For schemas autogenerated from sqlalchemy models, see the [schemas.py](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/cidc_api/models/schemas.py) file - we use the [marshmallow-sqlalchemy](https://marshmallow-sqlalchemy.readthedocs.io/en/latest/) library for this.
- **Serialize the response body**. If an endpoint returns a database record (or a list of records), use the [marshal_response](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/rest_utils.py#L67) decorator to convert a sqlalchemy model instance (or list of instances) into JSON. See [this example](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/users.py#L99).

**Note**: when you add a new endpoint to the API, you’ll also need to add that endpoint to the [test_endpoint_urls](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/tests/test_api.py#L413) test. This test ensures that CIDC developers are aware of every endpoint that the API exposes (since under certain configurations Flask might expose unwanted default endpoints).

#### How does API authentication and authorization work?

First off - what’s the difference between authentication and authorization? Authentication is concerned with verifying a user’s identity. Authorization is concerned with restricting the actions a user is allowed to perform within an application based on their identity. Since we need to know a user’s identity in order to execute logic based on their identity, user authentication is required for authorization.

##### Authentication

We use a protocol called OpenID Connect to leverage Auth0/Google for verifying the identity of users accessing data from the API (rather than maintaining user identities and login sessions ourselves). Here’s [a talk ](https://www.youtube.com/watch?v=996OiexHze0)that might help in learning about OAuth 2.0 and OpenID Connect - I highly recommend watching it before making any non-trivial update to authentication-related logic or configuration.

API authentication relies on _identity tokens_ generated by Auth0 to verify that the client making the request is logged in. An identity token is a [JWT](https://jwt.io/) containing information about a user’s account (like their name, their email, their profile image, etc.) and metadata (like an expiry time after which the token should be considered invalid). Here’s the part that makes JWTs trustworthy and useful for authentication: they include a cryptographic signature from a trusted identity provider service (Auth0, in our case). So, an identity token represents a currently authenticated user if:

- It is a well-formatted JWT.
- It has not yet expired.
- Its cryptographic signature is valid. 

JWTs are a lot like passports - they convey personal information, they’re issued by a trusted entity, and they expire after a certain time. Moreover, like passports, JWTs **can be stolen** and used to impersonate someone. As such, JWTs should be kept private and treated sort of like short-lived passwords.

##### Authorization

The CIDC API takes a _role-based access control_ approach to implementing its authorization policy. Each user is assigned a role (like _cidc-admin_, _cimac-biofx-user_, etc.), and the actions they’re allowed to take in the system are restricted based on that role. For the most part, any two users with the same role will be allowed to take the same actions in the CIDC system.

The one exception to the role-based access control rule is file access authorization, which is configured at the specific user account level for non-admin users via trial/assay permissions.

##### Implementation

Here’s where this happens in the code. [check_auth](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L83) is the workhorse authentication and authorization function (this is what [requires_auth](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L34) calls under the hood). check_auth first authenticates the current requesting user’s identity then performs authorization checks based on that identity:

Here’s what the [authenticate](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L142) function does:

1. [Tries to extract](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L150) the identity token from the request’s HTTP headers. It expects a header with the structure “Authorization: Bearer &lt;id token>”. If the expected “Authorization” header is not present, it looks for an identity token in the request’s JSON body (this is specific to the way our plotly dash integration handles authentication).
2. [Gets a public key from Auth0](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L170) that it will use to verify that the identity token was signed by Auth0.
3. [Decodes the identity token](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L205) and verifies its signature using the public key obtained in the previous step. If the JWT is malformed, expired, or otherwise invalid, this step will respond to the requesting user with HTTP 401 Unauthorized.
4. [Initializes and returns a sqlalchemy model instance for the current user](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L147).

Next, check_auth passes the user info parsed from the identity token to the [authorize](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/shared/auth.py#L252) function. The function implements some access control logic based on whether the requesting user’s account is registered and their role gives them permission to access the endpoint they are trying to access. **Note**: this function encapsulates simple, generic RBAC operations (“only users with these roles can perform this HTTP action on this endpoint”) and does not encapsulate more complicated, endpoint-specific role-based access control logic (e.g., [this logic for listing file access permissions](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/cidc_api/resources/permissions.py#L46)). As things currently stand, understanding the RBAC policy for a particular endpoint requires reviewing that endpoint’s implementation in its entirety.

#### How do I propagate SQLAlchemy model updates to the database?

Updates to SQLAlchemy model python classes do not automatically update the corresponding tables in the database. Rather, you need to create a “migration” script to apply any model class updates to the database. We use the [flask-migrate](https://flask-migrate.readthedocs.io/en/latest/) plugin for managing our migration scripts. See this brief [overview](https://github.com/NCI-CIDC/cidc-api-gae/blob/master/README.md#running-database-migrations) of creating, running, and undoing migrations.

**Note:** although flask-migrate and alembic, the tool flask-migrate uses under the hood, can automatically pick up certain sqlalchemy model class changes (e.g., adding/removing models, adding/removing columns, column data type changes), there are other changes that it can’t pick up automatically. Two examples I’ve encountered are adding/removing values from enum types and adding/updating [CHECK constraints](https://docs.sqlalchemy.org/en/14/core/constraints.html#check-constraint). For this reason, always review the auto-generated migration file before applying it, making any required manually edits/additions.

#### How can I check that a database migration works?

First, I run the “flask db upgrade” against my local database - this can catch basic errors, like syntax or type issues, even if there’s no data currently stored in the local database.

Next, I’ll try running the migration against the staging database from my local computer (since the staging db generally has representative data in it, this can catch further errors you might miss in a local db test). To do this, you need to [set up a connection to the staging db](https://github.com/nci-cidc/cidc-api-gae#connecting-to-a-cloud-sql-database-instance) and to [update your .env file](https://github.com/NCI-CIDC/cidc-api-gae/blob/75e88280e1103b530f6e7bd7261ca90f933159b2/.env#L23) to tell your local api code to use this connection. **Make sure that no one else is using the staging db for anything critical**, then run the db upgrade. If you encounter new errors, fix them. Once the upgrade succeeds, undo it with “flask db downgrade”, then make a PR to deploy the new migration.

#### What happens when a database migration fails, and what should I do to remediate the situation?

Because database migrations are run when the app starts up, failed database migrations manifest as the API failing to start up. This usually looks like the “failed to load account information” error message appearing 5-10 seconds after trying to load the portal.

Remediating a failing migration requires two steps:

1. Redirect traffic to a previous app engine version that does not include the failing migration code. You can select a known-good version from [this page](https://console.cloud.google.com/appengine/versions) in the GCP console.
2. Debug and fix the migration locally following a process like the one described above.

**Note:** when you want to undo a migration that **did not fail to run**, but has some other issue with it, the solution is different. If you try to simply send traffic to a previous app engine version without the migration you want to undo included in it, you’ll get an error on app startup (something like “alembic.util.CommandError: Can't locate revision identified by '31b8ab83c7d'”). In order to undo this migration, you’ll need to [manually connect to the cloud sql instance](https://github.com/nci-cidc/cidc-api-gae#connecting-to-a-cloud-sql-database-instance), [update your .env file](https://github.com/NCI-CIDC/cidc-api-gae/blob/75e88280e1103b530f6e7bd7261ca90f933159b2/.env#L23) to tell your local api code to use this connection, then run “flask db downgrade”. Once that command succeeds, you’ve rolled back the unwanted migration, and you can safely send traffic to a previous app engine version that doesn’t include the migration.

#### What’s packaged up in cidc-api-modules pypi package?

The cidc-api-modules package includes only the submodules used in the cidc-cloud-functions module. Here’s the [full list](https://github.com/NCI-CIDC/cidc-api-gae/blob/ed18274bd413444157fb3d7af8e0dc3925079e6a/setup.py#L14). Notably, the “cidc_api.app” and “cidc_api.resources” submodules are excluded, since these pertain only to the API. To be perfectly honest, I don’t remember the issue that led to the decision to not simply package up and public the top-level “cidc_api” module (it’s possible even if it’s not necessary). Anyhow, this means that bumping the cidc-api-modules version is only necessary when making changes to the included submodules that you want to propagate to the cloud functions repo.

Relatedly, it could be worth looking into combining the cloud functions repo into the cidc-api-gae repo. There’s no great reason for them to be separate. In fact, since they share code related to interacting with the database and with GCP, the decision to separate the two repos likely creates more friction than it alleviates.
