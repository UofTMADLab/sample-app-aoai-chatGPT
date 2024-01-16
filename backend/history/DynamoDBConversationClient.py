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
        self.conversations_table = self.dynamodb_client.Table(f'aichat_conversations_{os.environ.get('AWS_DDB_ENV','dev')}')
        self.messages_table = self.dynamodb_client.Table(f'aichat_messages_{os.environ.get('AWS_DDB_ENV','dev')}')
        
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

