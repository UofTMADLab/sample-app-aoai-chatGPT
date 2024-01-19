import os
import uuid
import logging
from datetime import datetime
from flask import Flask, request
import boto3


class DynamoDBConversationClient():
    def get_dynamodb_instance(self):
        try:
            # on local, use localhost at port 8000
            if (os.environ.get('AWS_SAM_LOCAL') == 'true'):
                return boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
            # everywhere else use the ca-central-1 region
            return boto3.resource('dynamodb', region_name=os.environ.get("AWS_DDB_REGION", "ca-central-1"))
        except Exception as e:
            logging.exception("Exception in DynamoDB initialization", e)
            return None

    def __init__(self):
        self.dynamodb_client = self.get_dynamodb_instance()
        self.conversations_table = self.dynamodb_client.Table(f'aichat_conversations_{os.environ.get("AWS_DDB_ENV","dev")}')
        self.messages_table = self.dynamodb_client.Table(f'aichat_messages_{os.environ.get("AWS_DDB_EN","dev")}')
        self.users_table = self.dynamodb_client.Table(f'aichat_users_{os.environ.get("AWS_DDB_EN","dev")}')
        self.config_table = self.dynamodb_client.Table(f'aichat_all_configs_{os.environ.get("AWS_DDB_EN","dev")}')
        
    def ensure(self):
        try:
            if not self.dynamodb_client:
                logging.exception("Null dynamodb_client")
                return False
            if not self.conversations_table:
                logging.exception("Null conversations_table")
                return False
            if not self.messages_table:
                logging.exception("Null messages_table")
                return False
            if not self.users_table:
                logging.exception("Null users_table")
                return False
            if not self.config_table:
                logging.exception("Null config_table")
            return True
        except:
            return False
       
    def _convert_conversation_to_frontend_format(self, conversation):
        return {
            'id': conversation['conversation_id'],  
            'type': 'conversation',
            'createdAt': conversation['created_at'],  
            'updatedAt': conversation['updated_at'],  
            'userId': conversation['user_id'],
            'title': conversation['title']
        }
    def _convert_conversation_to_backend_format(self, canvas_context, conversation):
        return {
            'qcontext_user_id': f'{canvas_context}#{conversation["userId"]}',
            'conversation_id': conversation['id'],  
            'is_deleted': 'FALSE',
            'created_at': conversation['createdAt'],  
            'updated_at': conversation['updatedAt'],  
            'qcontext': canvas_context,
            'user_id': conversation['userId'],
            'title': conversation['title']
        }
        
    def _convert_message_to_frontend_format(self, message):
        return {
            'id': message['message_id'],
            'type': 'message',
            'userId' : message['user_id'],
            'createdAt': message['created_at'],
            'updatedAt': message['updated_at'],
            'conversationId' : message['conversation_id'],
            'role': message['role'],
            'content': message['content']
        }
    def _get_message_id_from_frontend_message(self, message):
        return message['id']
    
    def get_config(self, canvas_context, user_id="_default"):
        key = {
            'qcontext': canvas_context,
            'user_id_or_default': user_id
        }
        try:
            
            resp = self.config_table.get_item(
                Key=key
            )
            return resp['Item']
        except:
            return None
    
    def create_config(self, config, canvas_context, user_id="_default"):
        config['qcontext'] = canvas_context
        config['user_id_or_default'] = user_id
        
        try:
            resp = self.config_table.put_item(
                Item=config,
                ReturnValues="NONE",
            )
            return config
        except:
            return False
            
    def update_welcome_message_config(self, welcome_message, canvas_context, user_id="_default"):
        config = {
            'qcontext': canvas_context,
            "user_id_or_default": user_id,
            "welcome_message": welcome_message
        }
        try:
            resp = self.config_table.update_item(
                Key={
                    'qcontext': config['qcontext'],
                    'user_id_or_default':config['user_id_or_default']
                },
                ReturnValues='ALL_NEW',
                UpdateExpression="SET welcome_message=:welcome_message",
                ExpressionAttributeValues={
                    ":welcome_message":config["welcome_message"]
                }
            )
            return resp["Attributes"]
        except:
            return False
    
    def update_system_message_config(self, system_message, canvas_context, user_id="_default"):
        config = {
            'qcontext': canvas_context,
            "user_id_or_default": user_id,
            "system_message": system_message
        }
        try:
            resp = self.config_table.update_item(
                Key={
                    'qcontext': config['qcontext'],
                    'user_id_or_default':config['user_id_or_default']
                },
                ReturnValues='ALL_NEW',
                UpdateExpression="SET system_message=:system_message",
                ExpressionAttributeValues={
                    ":system_message":config["system_message"]
                }
            )
            return resp["Attributes"]
        except:
            return False
                 
    def create_or_update_user(self, canvas_context, user_id, name, course_title, lti_role):
        user = {
            'user_id': user_id,
            'qcontext': canvas_context,
            'sessions': [datetime.now().isoformat(timespec="minutes")],
            'lti_name': name,
            'course_title': course_title,
            'lti_role': lti_role,
        }
        
        try:
            resp = self.users_table.update_item(
                Key={
                    'user_id':user['user_id'],
                    'qcontext':user['qcontext']
                },
                ReturnValues="ALL_NEW",
                # UpdateExpression="SET lti_name=:name, course_title=:course_title, lti_role=:lti_role, sessions = list_append(if_not_exists(sessions, :empty_list), :sessions)",
                # ExpressionAttributeValues={
                #     ":name":user['lti_name'],
                #     ":course_title":user['course_title'],
                #     ":lti_role":user['lti_role'],   
                #     ":empty_list":[],             
                #     ":sessions":user['sessions']
                # }
                UpdateExpression="SET lti_name=:name, course_title=:course_title, lti_role=:lti_role",
                ExpressionAttributeValues={
                    ":name":user['lti_name'],
                    ":course_title":user['course_title'],
                    ":lti_role":user['lti_role']
                }
            )
            return resp['Attributes']
        except:
            return False
    
    def increment_user_token_count(self, canvas_context, user_id, token_count):
        try:
            resp = self.users_table.update_item(
                Key={
                    'user_id':user_id,
                    'qcontext':canvas_context
                },
                ReturnValues="ALL_NEW",
                UpdateExpression="ADD token_count :token_count",
                ExpressionAttributeValues={
                    ":token_count":token_count
                }
            )
            return resp['Attributes']
        except:
            return False
            
    def create_conversation(self, canvas_context, user_id, title = ''):
        conversation = {
            'qcontext_user_id': f'{canvas_context}#{user_id}',
            'conversation_id': str(uuid.uuid4()),  
            'is_deleted': 'FALSE',
            'created_at': datetime.utcnow().isoformat(),  
            'updated_at': datetime.utcnow().isoformat(),  
            'qcontext': canvas_context,
            'user_id': user_id,
            'title': title
        }
        
        try:
            resp = self.conversations_table.put_item(
                Item=conversation,
                ReturnValues="NONE",
            )
            return self._convert_conversation_to_frontend_format(conversation)
        except:
            return False
            
    def upsert_conversation(self, canvas_context, conversation):
        b_conversation = self._convert_conversation_to_backend_format(canvas_context, conversation)
        try:
            resp = self.conversations_table.put_item(Item=b_conversation, ReturnValues="NONE")
            return conversation
        except:
            return False
    
    def delete_conversation(self, canvas_context, user_id, conversation_id):
        key = {
            'qcontext_user_id': f'{canvas_context}#{user_id}',
            'conversation_id': conversation_id,  
        }
        resp = self.conversations_table.delete_item(
            Key=key,
            ReturnValues='ALL_OLD'
        )
        return resp
    
        
    def delete_messages(self, conversation_id, canvas_context, user_id):
        ## get a list of all the messages in the conversation
        frontend_style_messages = self.get_messages(canvas_context, user_id, conversation_id)
        response_list = []
        if frontend_style_messages:
            for message in frontend_style_messages:
                key = {
                    'qcontext_user_id_conversation_id': f'{canvas_context}#{user_id}#{conversation_id}',
                    'message_id': self._get_message_id_from_frontend_message(message),                     
                }
                resp = self.messages_table.delete_item(
                    Key=key,
                    ReturnValues='ALL_OLD'
                )
                response_list.append(resp)
            return response_list
    
    
    def get_conversations(self, canvas_context, user_id, sort_order = 'DESC'):

        scan_directions = {
            'ASC': True,
            'DESC': False
        }
        try:   
            resp = self.conversations_table.query(
                IndexName='ByUserAndDate',
                ScanIndexForward=scan_directions[sort_order],
                KeyConditionExpression="qcontext_user_id=:qcontext_user_id",
                ExpressionAttributeValues={":qcontext_user_id":f'{canvas_context}#{user_id}'}
            )
            return [self._convert_conversation_to_frontend_format(c) for c in resp['Items']]
        except:
            return None
    
    def get_conversation(self, canvas_context, user_id, conversation_id):
        key = {
            'qcontext_user_id': f'{canvas_context}#{user_id}',
            'conversation_id': conversation_id,  
        }
        try:
            
            resp = self.conversations_table.get_item(
                Key=key
            )
            return self._convert_conversation_to_frontend_format(resp['Item'])
        except:
            return None

    
    def create_message(self, conversation_id, canvas_context, user_id, input_message: dict):
        message = {
            'qcontext_user_id_conversation_id': f'{canvas_context}#{user_id}#{conversation_id}',
            'message_id': str(uuid.uuid4()),  
            'is_deleted': 'FALSE',
            'created_at': datetime.utcnow().isoformat(),  
            'updated_at': datetime.utcnow().isoformat(),  
            'qcontext': canvas_context,
            'user_id': user_id,
            'conversation_id': conversation_id,
            'role': input_message['role'],
            'content': input_message['content']
        }
        ## TODO: add some error handling based on the output of the upsert_item call
        try:
            resp = self.messages_table.put_item(
                Item=message,
                ReturnValues="NONE"            
            )
            return self._convert_message_to_frontend_format(message)
        except:
            return False
    
    
    def get_messages(self, canvas_context, user_id, conversation_id):

        scan_directions = {
            'ASC': True,
            'DESC': False
        }
        try:
            
            resp = self.messages_table.query(
                IndexName='ByUserConversationAndDate',
                ScanIndexForward=scan_directions['ASC'],
                KeyConditionExpression="qcontext_user_id_conversation_id=:qcontext_user_id_conversation_id",
                ExpressionAttributeValues={':qcontext_user_id_conversation_id': f'{canvas_context}#{user_id}#{conversation_id}'}
            )
                    
            return [self._convert_message_to_frontend_format(m) for m in resp['Items']]
        except:
            return None

