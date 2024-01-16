import subprocess
import json
import boto3

def run(args):
  process = subprocess.run(args, capture_output=True)
  if (process.returncode != 0): exit(process.stderr.decode())
  return process

# Creates the Docker network if it does not exist.
def create_docker_network(network):
  ls = run([
    'docker', 'network', 'ls',     # list existing networks
    '--filter', f'name={network}',  # filter to those with given name
    '--format', '{{.Name}}',        # only show names
  ])
  if network not in [name.decode() for name in ls.stdout.split()]:
    print('Missing docker network...')
    create = run(['docker', 'network', 'create', network])
    print(f'Created network {network} (id={create.stdout.decode().strip()}).\n')

# Creates the Docker container if it does not exist. If it does exist, makes
# sure it's running and not paused.
def start_container(container, network, port):
  ps = run([
    'docker', 'ps', '--all',          # list all containers
    '--filter', f'name={container}',  # filter to those with given name
    '--format', '{{.Names}}',         # only show names
  ])

  # container exists?
  if container in [name.decode() for name in ps.stdout.split()]:
    inspect = run([
      'docker', 'inspect', container, # inspect given container
      '--format', '{{json .State}}',  # only show status
    ])
    state = json.loads(inspect.stdout.decode())
    # if not running, start it
    if not state['Running']:
      print('Container is not running...')
      start = run(['docker', 'start', container])
      print(f'Started container {start.stdout.decode().strip()}.\n')
    # if paused, resume it
    elif state['Paused']:
      print('Container is paused...')
      resume = run(['docker', 'unpause', container])
      print(f'Resumed container {resume.stdout.decode().strip()}.\n')

  # container doesn't exist?
  else:
    # create the container
    print('Missing container...')
    create = run([
      'docker', 'run', '--detach',            # run container in the background
      '--name', container,                    # name the container 
      '--publish', f'{port}:8000',            # publish container's port 8000 to host
      '--network', network,                   # add container to given network
      'amazon/dynamodb-local',                # define which image to run
      '-jar', 'DynamoDBLocal.jar', '-sharedDb'  # expose db to other processes
    ])
    print(f'Created container {container} (id={create.stdout.decode().strip()}).\n')

# Creates the given DynamoDB table if it doesn't exist.
def create_table(name, opts, port):
  ddb = boto3.resource('dynamodb', endpoint_url=f'http://localhost:{port}', region_name='ca-central-1')
  # if table doesn't exist, create it
  if name not in [t.name for t in ddb.tables.all()]:
    print('Missing table...')
    table = ddb.create_table(
      TableName=name,
      KeySchema=opts['key'],
      AttributeDefinitions=opts['attrs'],
      # provisioned throughput doesn't matter on local
      ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
      },
      GlobalSecondaryIndexes=opts['gsindexes']
    )
    # wait until the table exists and print
    table.meta.client.get_waiter('table_exists').wait(TableName=name)
    print(f'Created table {table.name}.\n')


if __name__ == '__main__':
  print("NOTE: This script assumes the Docker daemon is already running.\n")

  # constant params
  NAME = 'oaiddb'
  NETWORK = 'oaichat'
  PORT = 8000
  TABLES = {
    'aichat_conversations': {
      'key':   [{'AttributeName':'qcontext_user_id', 'KeyType':'HASH'}, {'AttributeName':'conversation_id', 'KeyType': 'RANGE'}],
      'attrs': [
                  {'AttributeName':'qcontext_user_id', 'AttributeType':'S'},
                  {'AttributeName':'conversation_id', 'AttributeType':'S'},
                  {'AttributeName':'updated_at', 'AttributeType':'S'}
              ],
      'gsindexes': [
          {
              'IndexName': 'ByUserAndDate',
              'KeySchema': [
                  {
                      'AttributeName': 'qcontext_user_id',
                      'KeyType': 'HASH'
                  },
                  {
                      'AttributeName': 'updated_at',
                      'KeyType': 'RANGE'
                  }
              ],
              'Projection': {
                  'ProjectionType': 'ALL'
              },
              'ProvisionedThroughput': {
                  'ReadCapacityUnits': 5,
                  'WriteCapacityUnits': 5
              }
          }
      ]
    },
    'aichat_messages': {
      'key':   [{'AttributeName':'qcontext_user_id_conversation_id', 'KeyType':'HASH'}, {'AttributeName':'message_id', 'KeyType': 'RANGE'}],
      'attrs': [
                  {'AttributeName':'qcontext_user_id_conversation_id', 'AttributeType':'S'},
                  {'AttributeName':'message_id', 'AttributeType':'S'},
                  {'AttributeName':'updated_at', 'AttributeType':'S'}
              ],
      'gsindexes': [
          {
              'IndexName': 'ByUserConversationAndDate',
              'KeySchema': [
                  {
                      'AttributeName': 'qcontext_user_id_conversation_id',
                      'KeyType': 'HASH'
                  },
                  {
                      'AttributeName': 'updated_at',
                      'KeyType': 'RANGE'
                  }
              ],
              'Projection': {
                  'ProjectionType': 'ALL'
              },
              'ProvisionedThroughput': {
                  'ReadCapacityUnits': 5,
                  'WriteCapacityUnits': 5
              }
          }
      ]
    },
  }

  create_docker_network(NETWORK)
  start_container(NAME, NETWORK, PORT)
  for table in TABLES:
    create_table(table, TABLES[table], PORT)

  print("All done!")
