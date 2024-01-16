import json
import os
import logging
import requests
import openai
import pprint
from azure.identity import DefaultAzureCredential
from flask import Flask, Response, request, jsonify, send_from_directory, redirect, url_for
from flask_caching import Cache
from dotenv import load_dotenv

from backend.auth.auth_utils import get_authenticated_user_details
# from backend.history.cosmosdbservice import CosmosConversationClient
from backend.history.DynamoDBConversationClient import DynamoDBConversationClient

from werkzeug.exceptions import Forbidden
from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskMessageLaunch, FlaskRequest, FlaskCacheDataStorage
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration

    
load_dotenv()

application = Flask(__name__, static_folder="static")
cache = Cache(application, config={'CACHE_TYPE': 'simple'})

def get_lti_context_config_path():
    return os.path.join(application.root_path, 'lti', 'course-config', 'course-env.json')

def load_lti_course_config(path):
    f = open(path)
    data = json.load(f)
    f.close()
    return data

lti_course_config = load_lti_course_config(get_lti_context_config_path())
conversation_client = DynamoDBConversationClient()

def get_lti_config_path():
    return os.path.join(application.root_path, 'lti', 'config', 'tool-conf.json')
def get_lti_context_config_path():
    return os.path.join(application.root_path, 'lti', 'course-config', 'course-env.json')


def get_launch_data_storage():
    return FlaskCacheDataStorage(cache)
    
def get_message_launch():
    launch_id = request.cookies.get('launch_id')
    # application.logger.info(pprint.pformat(launch_id))
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    return FlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf,
                                                launch_data_storage=launch_data_storage)

def get_lti_user_id(launch_data):
    return launch_data.get('sub')
    
def get_lti_context(launch_data):
    return launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('id', None)
    
def get_lti_name(launch_data):
    return launch_data.get('https://purl.imsglobal.org/spec/lti/claim/custom', {}).get('name', None)
    
def get_lti_course(launch_data):   
    return launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('title', None)

def get_lti_openai_context(launch_data):
    ai_context = {}
    
    lti_context =  get_lti_context(launch_data)
    name = get_lti_name(launch_data)
    course = get_lti_course(launch_data)
    
    context_data = lti_course_config.get(lti_context, lti_course_config['default'])
    
    ai_context['AZURE_SEARCH_SERVICE'] = context_data.get('AZURE_SEARCH_SERVICE', None)
    ai_context['AZURE_SEARCH_INDEX'] = context_data.get('AZURE_SEARCH_INDEX', None)
    ai_context['AZURE_SEARCH_KEY'] = context_data.get('AZURE_SEARCH_KEY', None)
    ai_context['AZURE_OPENAI_KEY'] = os.environ.get(context_data.get('RESOURCE_KEY_ENV_ID', ""), None)
    ai_context['AZURE_OPENAI_RESOURCE'] = context_data.get('AZURE_OPENAI_RESOURCE', None)
    ai_context['AZURE_OPENAI_MODEL'] = context_data.get('AZURE_OPENAI_MODEL', None)
    ai_context['AZURE_OPENAI_SYSTEM_MESSAGE'] = context_data.get('AZURE_OPENAI_SYSTEM_MESSAGE', None).replace("{person}", name).replace("{course}", course)    
    ai_context['AZURE_OPENAI_MODEL_NAME'] = context_data.get('AZURE_OPENAI_MODEL_NAME', "gpt-35-turbo-16k")
    return ai_context
    
# Static Files
@application.route('/', methods=['GET'])
def index():

    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
    
    # resp = application.send_static_file("index.html")
    # resp.set_cookie('launch_id', launch_id)
    return application.send_static_file("index.html")
    
@application.route('/jwks/', methods=['GET'])
def get_jwks():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    return jsonify(tool_conf.get_jwks())

@application.route('/login/', methods=['GET', 'POST'])
def login():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    launch_data_storage = get_launch_data_storage()

    flask_request = FlaskRequest()
    target_link_uri = flask_request.get_param('target_link_uri')
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')

    oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    return oidc_login\
        .enable_check_cookies()\
        .redirect(target_link_uri)


@application.route('/launch/', methods=['POST'])
def launch():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = FlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    launch_id = message_launch.get_launch_id()
    message_launch_data = message_launch.get_launch_data()
    # application.logger.info(pprint.pformat(message_launch_data))

    # difficulty = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/custom', {}) \
    #     .get('difficulty', None)
    # if not difficulty:
    #     difficulty = request.args.get('difficulty', 'normal')

    # tpl_kwargs = {
    #     'page_title': 'PAGE_TITLE',
    #     'is_deep_link_launch': message_launch.is_deep_link_launch(),
    #     'launch_data': message_launch.get_launch_data(),
    #     'launch_id': message_launch.get_launch_id(),
    #     'curr_user_name': message_launch_data.get('name', '')
    #     # 'curr_diff': difficulty
    # }
    # return render_template('game.html', **tpl_kwargs)
    # return application.send_static_file("index.html")
    resp = redirect(url_for('index'))
    if request.host.startswith("127.0.0.1"):
        resp.set_cookie('launch_id', launch_id)    
    else:
        resp.set_cookie('launch_id', launch_id, secure=True, samesite='None')
        
    return resp
        
@application.route("/lti/me")
def lti_id():
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
        
    launch_data = message_launch.get_launch_data()
    name = get_lti_name(launch_data)
    course = get_lti_course(launch_data)
    launch_context = get_lti_context(launch_data)
    # application.logger.info(pprint.pformat(message_launch_data))
    # application.logger.info(name)
    # application.logger.info(course)
    return jsonify([{'name':name, 'course':course, 'context':launch_context}]), 200

    
@application.route("/favicon.ico")
def favicon():
    return application.send_static_file('favicon.ico')

@application.route("/assets/<path:path>")
def assets(path):
    return send_from_directory("static/assets", path)


# ACS Integration Settings
AZURE_SEARCH_USE_SEMANTIC_SEARCH = os.environ.get("AZURE_SEARCH_USE_SEMANTIC_SEARCH", "false")
AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG = os.environ.get("AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG", "default")
AZURE_SEARCH_TOP_K = os.environ.get("AZURE_SEARCH_TOP_K", 5)
AZURE_SEARCH_ENABLE_IN_DOMAIN = os.environ.get("AZURE_SEARCH_ENABLE_IN_DOMAIN", "true")
AZURE_SEARCH_CONTENT_COLUMNS = os.environ.get("AZURE_SEARCH_CONTENT_COLUMNS")
AZURE_SEARCH_FILENAME_COLUMN = os.environ.get("AZURE_SEARCH_FILENAME_COLUMN")
AZURE_SEARCH_TITLE_COLUMN = os.environ.get("AZURE_SEARCH_TITLE_COLUMN")
AZURE_SEARCH_URL_COLUMN = os.environ.get("AZURE_SEARCH_URL_COLUMN")
AZURE_SEARCH_VECTOR_COLUMNS = os.environ.get("AZURE_SEARCH_VECTOR_COLUMNS")
AZURE_SEARCH_QUERY_TYPE = os.environ.get("AZURE_SEARCH_QUERY_TYPE")
AZURE_SEARCH_PERMITTED_GROUPS_COLUMN = os.environ.get("AZURE_SEARCH_PERMITTED_GROUPS_COLUMN")
AZURE_SEARCH_STRICTNESS = os.environ.get("AZURE_SEARCH_STRICTNESS", 3)

# AOAI Integration Settings
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_TEMPERATURE = os.environ.get("AZURE_OPENAI_TEMPERATURE", 0)
AZURE_OPENAI_TOP_P = os.environ.get("AZURE_OPENAI_TOP_P", 1.0)
AZURE_OPENAI_MAX_TOKENS = os.environ.get("AZURE_OPENAI_MAX_TOKENS", 1000)
AZURE_OPENAI_STOP_SEQUENCE = os.environ.get("AZURE_OPENAI_STOP_SEQUENCE")
AZURE_OPENAI_PREVIEW_API_VERSION = os.environ.get("AZURE_OPENAI_PREVIEW_API_VERSION", "2023-08-01-preview")
AZURE_OPENAI_STREAM = os.environ.get("AZURE_OPENAI_STREAM", "true")
AZURE_OPENAI_EMBEDDING_ENDPOINT = os.environ.get("AZURE_OPENAI_EMBEDDING_ENDPOINT")
AZURE_OPENAI_EMBEDDING_KEY = os.environ.get("AZURE_OPENAI_EMBEDDING_KEY")
AZURE_OPENAI_EMBEDDING_NAME = os.environ.get("AZURE_OPENAI_EMBEDDING_NAME", "")

SHOULD_STREAM = True if AZURE_OPENAI_STREAM.lower() == "true" else False

# # Initialize a CosmosDB client with AAD auth and containers
# cosmos_conversation_client = None
# if AZURE_COSMOSDB_DATABASE and AZURE_COSMOSDB_ACCOUNT and AZURE_COSMOSDB_CONVERSATIONS_CONTAINER:
#     try :
#         cosmos_endpoint = f'https://{AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/'
# 
#         if not AZURE_COSMOSDB_ACCOUNT_KEY:
#             credential = DefaultAzureCredential()
#         else:
#             credential = AZURE_COSMOSDB_ACCOUNT_KEY
# 
#         cosmos_conversation_client = CosmosConversationClient(
#             cosmosdb_endpoint=cosmos_endpoint, 
#             credential=credential, 
#             database_name=AZURE_COSMOSDB_DATABASE,
#             container_name=AZURE_COSMOSDB_CONVERSATIONS_CONTAINER
#         )
#     except Exception as e:
#         logging.exception("Exception in CosmosDB initialization", e)
#         cosmos_conversation_client = None


# def is_chat_model(model_name):
#     if 'gpt-4' in model_name.lower() or model_name.lower() in ['gpt-35-turbo-4k', 'gpt-35-turbo-16k']:
#         return True
#     return False

def should_use_data(ai_context):
    if ai_context['AZURE_SEARCH_SERVICE'] and ai_context['AZURE_SEARCH_INDEX'] and ai_context['AZURE_SEARCH_KEY']:
        return True
    return False


def format_as_ndjson(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False) + "\n"

def fetchUserGroups(userToken, nextLink=None):
    # Recursively fetch group membership
    if nextLink:
        endpoint = nextLink
    else:
        endpoint = "https://graph.microsoft.com/v1.0/me/transitiveMemberOf?$select=id"
    
    headers = {
        'Authorization': "bearer " + userToken
    }
    try :
        r = requests.get(endpoint, headers=headers)
        if r.status_code != 200:
            return []
        
        r = r.json()
        if "@odata.nextLink" in r:
            nextLinkData = fetchUserGroups(userToken, r["@odata.nextLink"])
            r['value'].extend(nextLinkData)
        
        return r['value']
    except Exception as e:
        return []


def generateFilterString(userToken):
    # Get list of groups user is a member of
    userGroups = fetchUserGroups(userToken)

    # Construct filter string
    if userGroups:
        group_ids = ", ".join([obj['id'] for obj in userGroups])
        return f"{AZURE_SEARCH_PERMITTED_GROUPS_COLUMN}/any(g:search.in(g, '{group_ids}'))"
    
    return None


def prepare_body_headers_with_data(request, ai_context):
    request_messages = request.json["messages"]

    # Set query type
    query_type = "simple"
    if AZURE_SEARCH_QUERY_TYPE:
        query_type = AZURE_SEARCH_QUERY_TYPE
    elif AZURE_SEARCH_USE_SEMANTIC_SEARCH.lower() == "true" and AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG:
        query_type = "semantic"

    # Set filter
    filter = None
    userToken = None
    if AZURE_SEARCH_PERMITTED_GROUPS_COLUMN:
        userToken = request.headers.get('X-MS-TOKEN-AAD-ACCESS-TOKEN', "")
        filter = generateFilterString(userToken)

    body = {
        "messages": request_messages,
        "temperature": float(AZURE_OPENAI_TEMPERATURE),
        "max_tokens": int(AZURE_OPENAI_MAX_TOKENS),
        "top_p": float(AZURE_OPENAI_TOP_P),
        "stop": AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        "stream": SHOULD_STREAM,
        "dataSources": [
            {
                "type": "AzureCognitiveSearch",
                "parameters": {
                    "endpoint": f"https://{ai_context['AZURE_SEARCH_SERVICE']}.search.windows.net",
                    "key": ai_context['AZURE_SEARCH_KEY'],
                    "indexName": ai_context['AZURE_SEARCH_INDEX'],
                    "fieldsMapping": {
                        "contentFields": AZURE_SEARCH_CONTENT_COLUMNS.split("|") if AZURE_SEARCH_CONTENT_COLUMNS else [],
                        "titleField": AZURE_SEARCH_TITLE_COLUMN if AZURE_SEARCH_TITLE_COLUMN else None,
                        "urlField": AZURE_SEARCH_URL_COLUMN if AZURE_SEARCH_URL_COLUMN else None,
                        "filepathField": AZURE_SEARCH_FILENAME_COLUMN if AZURE_SEARCH_FILENAME_COLUMN else None,
                        "vectorFields": AZURE_SEARCH_VECTOR_COLUMNS.split("|") if AZURE_SEARCH_VECTOR_COLUMNS else []
                    },
                    "inScope": True if AZURE_SEARCH_ENABLE_IN_DOMAIN.lower() == "true" else False,
                    "topNDocuments": AZURE_SEARCH_TOP_K,
                    "queryType": query_type,
                    "semanticConfiguration": AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG if AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG else "",
                    "roleInformation": ai_context['AZURE_OPENAI_SYSTEM_MESSAGE'],
                    "filter": filter,
                    "strictness": int(AZURE_SEARCH_STRICTNESS)
                }
            }
        ]
    }

    if "vector" in query_type.lower():
        if AZURE_OPENAI_EMBEDDING_NAME:
            body["dataSources"][0]["parameters"]["embeddingDeploymentName"] = AZURE_OPENAI_EMBEDDING_NAME
        else:
            body["dataSources"][0]["parameters"]["embeddingEndpoint"] = AZURE_OPENAI_EMBEDDING_ENDPOINT
            body["dataSources"][0]["parameters"]["embeddingKey"] = AZURE_OPENAI_EMBEDDING_KEY


    headers = {
        'Content-Type': 'application/json',
        'api-key': ai_context['AZURE_OPENAI_KEY'],
        "x-ms-useragent": "GitHubSampleWebApp/PublicAPI/2.0.0"
    }

    return body, headers


def stream_with_data(body, headers, endpoint, history_metadata={}):
    s = requests.Session()
    response = {
        "id": "",
        "model": "",
        "created": 0,
        "object": "",
        "choices": [{
            "messages": []
        }],
        "apim-request-id": "",
        'history_metadata': history_metadata
    }
    try:
        with s.post(endpoint, json=body, headers=headers, stream=True) as r:
            apimRequestId = r.headers.get('apim-request-id')
            for line in r.iter_lines(chunk_size=10):
                if line:
                    if AZURE_OPENAI_PREVIEW_API_VERSION == '2023-06-01-preview':
                        lineJson = json.loads(line.lstrip(b'data:').decode('utf-8'))
                    else:
                        try:
                            rawResponse = json.loads(line.lstrip(b'data:').decode('utf-8'))
                            lineJson = formatApiResponseStreaming(rawResponse)
                        except json.decoder.JSONDecodeError:
                            continue

                    if 'error' in lineJson:
                        yield format_as_ndjson(lineJson)
                    response["id"] = lineJson["id"]
                    response["model"] = lineJson["model"]
                    response["created"] = lineJson["created"]
                    response["object"] = lineJson["object"]
                    response["apim-request-id"] = apimRequestId

                    role = lineJson["choices"][0]["messages"][0]["delta"].get("role")

                    if role == "tool":
                        response["choices"][0]["messages"].append(lineJson["choices"][0]["messages"][0]["delta"])
                    elif role == "assistant": 
                        response["choices"][0]["messages"].append({
                            "role": "assistant",
                            "content": ""
                        })
                    else:
                        deltaText = lineJson["choices"][0]["messages"][0]["delta"]["content"]
                        if deltaText != "[DONE]":
                            response["choices"][0]["messages"][1]["content"] += deltaText

                    yield format_as_ndjson(response)
    except Exception as e:
        yield format_as_ndjson({"error" + str(e)})

def formatApiResponseNoStreaming(rawResponse):
    if 'error' in rawResponse:
        return {"error": rawResponse["error"]}
    response = {
        "id": rawResponse["id"],
        "model": rawResponse["model"],
        "created": rawResponse["created"],
        "object": rawResponse["object"],
        "choices": [{
            "messages": []
        }],
    }
    toolMessage = {
        "role": "tool",
        "content": rawResponse["choices"][0]["message"]["context"]["messages"][0]["content"]
    }
    assistantMessage = {
        "role": "assistant",
        "content": rawResponse["choices"][0]["message"]["content"]
    }
    response["choices"][0]["messages"].append(toolMessage)
    response["choices"][0]["messages"].append(assistantMessage)

    return response

def formatApiResponseStreaming(rawResponse):
    if 'error' in rawResponse:
        return {"error": rawResponse["error"]}
    response = {
        "id": rawResponse["id"],
        "model": rawResponse["model"],
        "created": rawResponse["created"],
        "object": rawResponse["object"],
        "choices": [{
            "messages": []
        }],
    }

    if rawResponse["choices"][0]["delta"].get("context"):
        messageObj = {
            "delta": {
                "role": "tool",
                "content": rawResponse["choices"][0]["delta"]["context"]["messages"][0]["content"]
            }
        }
        response["choices"][0]["messages"].append(messageObj)
    elif rawResponse["choices"][0]["delta"].get("role"):
        messageObj = {
            "delta": {
                "role": "assistant",
            }
        }
        response["choices"][0]["messages"].append(messageObj)
    else:
        if rawResponse["choices"][0]["end_turn"]:
            messageObj = {
                "delta": {
                    "content": "[DONE]",
                }
            }
            response["choices"][0]["messages"].append(messageObj)
        else:
            messageObj = {
                "delta": {
                    "content": rawResponse["choices"][0]["delta"]["content"],
                }
            }
            response["choices"][0]["messages"].append(messageObj)

    return response

def conversation_with_data(request_body, ai_context):
    body, headers = prepare_body_headers_with_data(request, ai_context)
    base_url = AZURE_OPENAI_ENDPOINT if AZURE_OPENAI_ENDPOINT else f"https://{ai_context['AZURE_OPENAI_RESOURCE']}.openai.azure.com/"
    endpoint = f"{base_url}openai/deployments/{ai_context['AZURE_OPENAI_MODEL']}/extensions/chat/completions?api-version={AZURE_OPENAI_PREVIEW_API_VERSION}"
    history_metadata = request_body.get("history_metadata", {})

    if not SHOULD_STREAM:
        r = requests.post(endpoint, headers=headers, json=body)
        status_code = r.status_code
        r = r.json()
        if AZURE_OPENAI_PREVIEW_API_VERSION == "2023-06-01-preview":
            r['history_metadata'] = history_metadata
            return Response(format_as_ndjson(r), status=status_code)
        else:
            result = formatApiResponseNoStreaming(r)
            result['history_metadata'] = history_metadata
            return Response(format_as_ndjson(result), status=status_code)

    else:
        return Response(stream_with_data(body, headers, endpoint, history_metadata), mimetype='text/event-stream')

def stream_without_data(response, history_metadata={}):
    responseText = ""
    for line in response:
        if line["choices"]:
            deltaText = line["choices"][0]["delta"].get('content')
        else:
            deltaText = ""
        if deltaText and deltaText != "[DONE]":
            responseText += deltaText

        response_obj = {
            "id": line["id"],
            "model": line["model"],
            "created": line["created"],
            "object": line["object"],
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": responseText
                }]
            }],
            "history_metadata": history_metadata
        }
        yield format_as_ndjson(response_obj)


def conversation_without_data(request_body, ai_context):
    openai.api_type = "azure"
    openai.api_base = AZURE_OPENAI_ENDPOINT if AZURE_OPENAI_ENDPOINT else f"https://{ai_context['AZURE_OPENAI_RESOURCE']}.openai.azure.com/"
    openai.api_version = "2023-08-01-preview"
    openai.api_key = ai_context['AZURE_OPENAI_KEY']

    request_messages = request_body["messages"]
    messages = [
        {
            "role": "system",
            "content": ai_context['AZURE_OPENAI_SYSTEM_MESSAGE']
        }
    ]

    for message in request_messages:
        messages.append({
            "role": message["role"] ,
            "content": message["content"]
        })

    response = openai.ChatCompletion.create(
        engine=ai_context['AZURE_OPENAI_MODEL'],
        messages = messages,
        temperature=float(AZURE_OPENAI_TEMPERATURE),
        max_tokens=int(AZURE_OPENAI_MAX_TOKENS),
        top_p=float(AZURE_OPENAI_TOP_P),
        stop=AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        stream=SHOULD_STREAM
    )

    history_metadata = request_body.get("history_metadata", {})

    if not SHOULD_STREAM:
        response_obj = {
            "id": response,
            "model": response.model,
            "created": response.created,
            "object": response.object,
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": response.choices[0].message.content
                }]
            }],
            "history_metadata": history_metadata
        }

        return jsonify(response_obj), 200
    else:
        return Response(stream_without_data(response, history_metadata), mimetype='text/event-stream')


@application.route("/conversation", methods=["GET", "POST"])
def conversation():
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
        
    launch_data = message_launch.get_launch_data()
    
    ai_context = get_lti_openai_context(launch_data)
    request_body = request.json
    return conversation_internal(request_body, ai_context)

def conversation_internal(request_body, ai_context):
    try:
        use_data = should_use_data(ai_context)
        if use_data:
            return conversation_with_data(request_body, ai_context)
        else:
            return conversation_without_data(request_body, ai_context)
    except Exception as e:
        logging.exception("Exception in /conversation")
        return jsonify({"error": str(e)}), 500

## Conversation History API ## 
@application.route("/history/generate", methods=["POST"])
def add_conversation():
    # authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    # user_id = authenticated_user['user_principal_id']
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
        
    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)
    ai_context = get_lti_openai_context(launch_data)
    
    ## check request for conversation_id
    conversation_id = request.json.get("conversation_id", None)

    try:
        # make sure cosmos is configured
        if not conversation_client:
            raise Exception("CosmosDB is not configured")

        # check for the conversation_id, if the conversation is not set, we will create a new one
        history_metadata = {}
        if not conversation_id:
            title = generate_title(request.json["messages"], ai_context)
            conversation_dict = conversation_client.create_conversation(canvas_context=canvas_context, user_id=user_id, title=title)
            conversation_id = conversation_dict['conversation_id']
            history_metadata['title'] = title
            history_metadata['date'] = conversation_dict['created_at']
            
        ## Format the incoming message object in the "chat/completions" messages format
        ## then write it to the conversation history in cosmos
        messages = request.json["messages"]
        if len(messages) > 0 and messages[-1]['role'] == "user":
            conversation_client.create_message(
                conversation_id=conversation_id,
                canvas_context=canvas_context,
                user_id=user_id,
                input_message=messages[-1]
            )
        else:
            raise Exception("No user message found")
        
        # Submit request to Chat Completions for response
        request_body = request.json
        history_metadata['conversation_id'] = conversation_id
        request_body['history_metadata'] = history_metadata
        return conversation_internal(request_body, ai_context)
       
    except Exception as e:
        logging.exception("Exception in /history/generate")
        return jsonify({"error": str(e)}), 500


@application.route("/history/update", methods=["POST"])
def update_conversation():
    # authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    # user_id = authenticated_user['user_principal_id']

    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
        
    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)
    
    ## check request for conversation_id
    conversation_id = request.json.get("conversation_id", None)

    try:
        # make sure cosmos is configured
        if not conversation_client:
            raise Exception("CosmosDB is not configured")

        # check for the conversation_id, if the conversation is not set, we will create a new one
        if not conversation_id:
            raise Exception("No conversation_id found")
            
        ## Format the incoming message object in the "chat/completions" messages format
        ## then write it to the conversation history in cosmos
        messages = request.json["messages"]
        if len(messages) > 0 and messages[-1]['role'] == "assistant":
            if len(messages) > 1 and messages[-2]['role'] == "tool":
                # write the tool message first
                conversation_client.create_message(
                    conversation_id=conversation_id,
                    canvas_context=canvas_context,
                    user_id=user_id,
                    input_message=messages[-2]
                )
            # write the assistant message
            conversation_client.create_message(
                conversation_id=conversation_id,
                canvas_context=canvas_context,
                user_id=user_id,
                input_message=messages[-1]
            )
        else:
            raise Exception("No bot messages found")
        
        # Submit request to Chat Completions for response
        response = {'success': True}
        return jsonify(response), 200
       
    except Exception as e:
        logging.exception("Exception in /history/update")
        return jsonify({"error": str(e)}), 500

@application.route("/history/delete", methods=["DELETE"])
def delete_conversation():
    ## get the user id from the request headers
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
        
    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)
    
    ## check request for conversation_id
    conversation_id = request.json.get("conversation_id", None)
    try: 
        if not conversation_id:
            logging.exception(f"request: {request}")
            return jsonify({"error": "conversation_id is required"}), 400
        
        ## delete the conversation messages from cosmos first
        deleted_messages = conversation_client.delete_messages(conversation_id, canvas_context, user_id)

        ## Now delete the conversation 
        deleted_conversation = conversation_client.delete_conversation(canvas_context, user_id, conversation_id)

        return jsonify({"message": "Successfully deleted conversation and messages", "conversation_id": conversation_id}), 200
    except Exception as e:
        logging.exception("Exception in /history/delete")
        return jsonify({"error": str(e)}), 500

@application.route("/history/list", methods=["GET"])
def list_conversations():
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
    
    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)

    ## get the conversations from cosmos
    conversations = conversation_client.get_conversations(canvas_context, user_id)    
    if not isinstance(conversations, list):
        return jsonify({"error": f"No conversations for {user_id} were found"}), 404

    ## return the conversation ids

    return jsonify(conversations), 200

@application.route("/history/read", methods=["POST"])
def get_conversation():
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')

    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)

    ## check request for conversation_id
    conversation_id = request.json.get("conversation_id", None)
    
    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400

    ## get the conversation object and the related messages from cosmos
    conversation = conversation_client.get_conversation(canvas_context, user_id, conversation_id)
    ## return the conversation id and the messages in the bot frontend format
    if not conversation:
        return jsonify({"error": f"Conversation {conversation_id} was not found. It either does not exist or the logged in user does not have access to it."}), 404
    
    # get the messages for the conversation from cosmos
    conversation_messages = conversation_client.get_messages(canvas_context, user_id, conversation_id)

    ## format the messages in the bot frontend format
    messages = [{'id': msg['message_id'], 'role': msg['role'], 'content': msg['content'], 'createdAt': msg['created_at']} for msg in conversation_messages]

    return jsonify({"conversation_id": conversation_id, "messages": messages}), 200

@application.route("/history/rename", methods=["POST"])
def rename_conversation():
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
    
    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)

    ## check request for conversation_id
    conversation_id = request.json.get("conversation_id", None)
    
    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400
    
    ## get the conversation from cosmos
    conversation = conversation_client.get_conversation(canvas_context, user_id, conversation_id)
    if not conversation:
        return jsonify({"error": f"Conversation {conversation_id} was not found. It either does not exist or the logged in user does not have access to it."}), 404

    ## update the title
    title = request.json.get("title", None)
    if not title:
        return jsonify({"error": "title is required"}), 400
    conversation['title'] = title
    updated_conversation = conversation_client.upsert_conversation(conversation)

    return jsonify(updated_conversation), 200

@application.route("/history/delete_all", methods=["DELETE"])
def delete_all_conversations():
    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
    
    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)


    # get conversations for user
    try:
        conversations = conversation_client.get_conversations(canvas_context, user_id)
        if not conversations:
            return jsonify({"error": f"No conversations for {user_id} were found"}), 404
        
        # delete each conversation
        for conversation in conversations:
            ## delete the conversation messages from cosmos first
            deleted_messages = conversation_client.delete_messages(conversation['conversation_id'], canvas_context, user_id)

            ## Now delete the conversation 
            deleted_conversation = conversation_client.delete_conversation(canvas_context, user_id, conversation['conversation_id'])

        return jsonify({"message": f"Successfully deleted conversation and messages for user {user_id}"}), 200
    
    except Exception as e:
        logging.exception("Exception in /history/delete_all")
        return jsonify({"error": str(e)}), 500
    

@application.route("/history/clear", methods=["POST"])
def clear_messages():

    message_launch = get_message_launch()
    if not message_launch:
        raise Forbidden('Not authorized.')
    
    launch_data = message_launch.get_launch_data()
    user_id = get_lti_user_id(launch_data)
    canvas_context = get_lti_context(launch_data)

    ## check request for conversation_id
    conversation_id = request.json.get("conversation_id", None)
    try: 
        if not conversation_id:
            return jsonify({"error": "conversation_id is required"}), 400
        
        ## delete the conversation messages from cosmos
        deleted_messages = conversation_client.delete_messages(conversation_id, canvas_context, user_id)

        return jsonify({"message": "Successfully deleted messages in conversation", "conversation_id": conversation_id}), 200
    except Exception as e:
        logging.exception("Exception in /history/clear_messages")
        return jsonify({"error": str(e)}), 500

@application.route("/history/ensure", methods=["GET"])
def ensure_ddb():
    # if not AZURE_COSMOSDB_ACCOUNT:
    #     return jsonify({"error": "CosmosDB is not configured"}), 404
    # 
    if not conversation_client or conversation_client.ensure() != True:
        return jsonify({"error": "Chat history database is not working"}), 500

    return jsonify({"message": "Chat history database is configured and working"}), 200

def generate_title(conversation_messages, ai_context):
    ## make sure the messages are sorted by _ts descending
    title_prompt = 'Summarize the conversation so far into a 4-word or less title. Do not use any quotation marks or punctuation. Respond with a json object in the format {{"title": string}}. Do not include any other commentary or description.'
 
    messages = [{'role': msg['role'], 'content': msg['content']} for msg in conversation_messages]
    messages.append({'role': 'user', 'content': title_prompt})

    try:
        ## Submit prompt to Chat Completions for response
        base_url = AZURE_OPENAI_ENDPOINT if AZURE_OPENAI_ENDPOINT else f"https://{ai_context['AZURE_OPENAI_RESOURCE']}.openai.azure.com/"
        openai.api_type = "azure"
        openai.api_base = base_url
        openai.api_version = "2023-03-15-preview"
        openai.api_key = ai_context['AZURE_OPENAI_KEY']
        completion = openai.ChatCompletion.create(    
            engine=ai_context['AZURE_OPENAI_MODEL'],
            messages=messages,
            temperature=1,
            max_tokens=64 
        )
        title = json.loads(completion['choices'][0]['message']['content'])['title']
        return title
    except Exception as e:
        return messages[-2]['content']

if __name__ == "__main__":
    # application.debug = True
    application.run()