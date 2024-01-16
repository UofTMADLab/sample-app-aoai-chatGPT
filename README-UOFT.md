## Environment Variables:

### Context Keys

e.g. UOFT_OAI_EUR, UOFT_OAI_CA, etc. - the env variable names map to RESOURCE_KEY_ENV_ID values in ./lti/course-config/course-env.json. The values of these variables are the resource keys for the specified resource for that LTI context.

AZURE_SEARCH_KEY=eifhdsk... 
Required secret key for AZURE search index. (May need to set up separate search keys for each LTI context, like UOFT_OAI_* keys above).

### Others
`FLASK_APP=application`
The name of the python flask application main file, e.g. application.py, or app.py. On AWS this is set to `application` in the WSGIPath configuration option.

`AWS_SAM_LOCAL=true`
Set to true for local dev, e.g. use local DynamoDB instance.

`AWS_DDB_REGION=ca-central-1`
The region where the DynamoDB is located.

`AWS_DDB_ENV=`
A suffix to apply to the DynamoDB Table names for this app. Use 'dev' if running locally. Defaults to 'dev'.

### on AWS
`PYTHONPATH=/var/app/venv/staging-LQM1lest/bin`

## Install/Run DynamoDB tables in Docker

Shell:
`$ pipenv shell`
`$ python ./dev/start-dynamodb.py`

## Integrating LTI

See canvas-config.md

## Build backend & frontend

```
#!/bin/sh
echo ""
echo "Restoring frontend npm packages"
echo ""
cd frontend
npm install
if [ $? -ne 0 ]; then
	echo "Failed to restore frontend npm packages"
	exit $?
fi

echo ""
echo "Building frontend"
echo ""
npm run build
if [ $? -ne 0 ]; then
	echo "Failed to build frontend"
	exit $?
fi

cd ..
. ./scripts/loadenv.sh
```

## Run backend locally

```
#!/bin/sh

echo ""
echo "Starting backend"
echo ""
./.venv/bin/python -m flask run --port=5000 --host=127.0.0.1 --reload --debug
if [ $? -ne 0 ]; then
	echo "Failed to start backend"
	exit $?
fi
```