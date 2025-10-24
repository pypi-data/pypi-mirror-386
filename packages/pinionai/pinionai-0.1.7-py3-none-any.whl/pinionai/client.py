_Bh="Twilio 'from' number not configured. Cannot send SMS."
_Bg='completedAt'
_Bf='Error: URL template evaluation failed.'
_Be='contentType'
_Bd='access_token'
_Bc='token_type'
_Bb='client_credentials'
_Ba='function_call'
_BZ='Error: AI client is not configured.'
_BY='Cannot get Gemini response: AI client is not initialized.'
_BX='Using environment credentials/IAM role for S3.'
_BW='boto3 library is required for S3 operations.'
_BV='Using Application Default Credentials for GCS.'
_BU='google-cloud-storage library is required for GCS operations.'
_BT='action_action_key'
_BS='__builtins__'
_BR='destinationVariable'
_BQ='sourceVariable'
_BP='promptName'
_BO='unknown_intent'
_BN='Error: AI response was malformed (function call had no name).'
_BM='resp_mime_type'
_BL='gemini-2.5-flash-preview-04-17'
_BK='safetySettings'
_BJ='mime_type'
_BI='noInputIntentNameList'
_BH='variables'
_BG='DEEPSEEK_API_KEY'
_BF='ANTHROPIC_API_KEY'
_BE='OPENAI_API_KEY'
_BD='EMAIL_FROM_ADDRESS'
_BC='EMAIL_API_KEY'
_BB='GEMINI_API_KEY'
_BA='GCP_REGION'
_B9='GCP_PROJECT'
_B8='WEBSOCKET_URL'
_B7='user_input'
_B6='Journey token not available.'
_B5='Accept-Encoding'
_B4='client_secret'
_B3='client_id'
_B2='grant_type'
_B1='tool_choice'
_B0='max_tokens'
_A_='clientId'
_Az='action_event'
_Ay='delivery_method'
_Ax='subject'
_Aw='function'
_Av='header'
_Au='gemini-2.0-flash'
_At='model_provider'
_As='agentDefaultIntent'
_Ar='intentContainsPairsList'
_Aq='intentNameList'
_Ap='value'
_Ao='action_flow'
_An='action_type'
_Am='iframeId'
_Al='externalRef'
_Ak='uniqueId'
_Aj='customer'
_Ai='pipelineKey'
_Ah='assistant'
_Ag='input'
_Af='actionFlow'
_Ae='deliveryMethod'
_Ad='privacy'
_Ac='prompt_type'
_Ab='gcs_service_account'
_Aa='ragStoreVectorDistanceThreshold'
_AZ='ragStoreTopK'
_AY='ragStoreResourceId'
_AX='transferPasskeyFlag'
_AW='transferAllowed'
_AV='TWILIO_NUMBER'
_AU='TWILIO_AUTH_TOKEN'
_AT='TWILIO_ACCOUNT_SID'
_AS='parameters'
_AR='Accept'
_AQ='failureResponseMessage'
_AP='gzip'
_AO='response'
_AN='string'
_AM='enum'
_AL='required'
_AK='properties'
_AJ='deepseek'
_AI='resp_schema'
_AH='thinking_budget'
_AG='maxTokens'
_AF='candidates'
_AE='top_k'
_AD='temp'
_AC='file_uri_var'
_AB='resp_var'
_AA='startPrompt'
_A9='scope'
_A8='prompt'
_A7='action'
_A6='classification'
_A5='temperature'
_A4='json'
_A3='*/*'
_A2='result'
_A1='env'
_A0='command'
_z='system'
_y='anthropic'
_x='messages'
_w='var'
_v='actionKey'
_u='vectorDistanceThreshold'
_t='topK'
_s='resourceId'
_r='expectedInput'
_q='accept'
_p='object'
_o='mcp'
_n='journey_iframeId'
_m='delivery'
_l='clientSecret'
_k='grantType'
_j='agentConnector'
_i='message'
_h='error'
_g='openai'
_f='action_response_message'
_e='phoneNumber'
_d='method'
_c='google'
_b='language'
_a='user'
_Z='Content-Type'
_Y='resultVariable'
_X='url'
_W='top_p'
_V='model'
_U='body'
_T='connector'
_S=','
_R='role'
_Q='content'
_P='text'
_O='tools'
_N='utf-8'
_M='application/json'
_L='Authorization'
_K='description'
_J='agent'
_I='args'
_H='DEBUG'
_G=False
_F='type'
_E='session'
_D=True
_C='data'
_B='name'
_A=None
import asyncio,base64,datetime,json,logging,os,random,re,sys,secrets,time,uuid,websockets,xmltodict
from contextlib import asynccontextmanager
import zoneinfo
from io import StringIO
from typing import Any,Dict,List,Optional,Tuple,Union
from urllib.parse import quote
import gzip,grpc,grpc.aio as agrpc,httpx,Levenshtein,markdown,pandas as pd,xmltodict
from google.auth import credentials as auth_credentials
from google.oauth2 import service_account
from google.api_core import exceptions as google_api_exceptions
from google import genai
from google.genai import types as google_genai_types
from google.genai.types import FunctionDeclaration,GenerateContentConfig,GoogleSearch,HarmBlockThreshold,HarmCategory,Part,SafetySetting,ThinkingConfig,Tool,ToolCodeExecution,UrlContext,Retrieval,VertexRagStore,VertexRagStoreRagResource
from fastmcp.client import Client
from fastmcp.client.transports import StdioTransport
from jsonpath_ng.ext import parse as jsonpath_parse
try:import sendgrid;from sendgrid.helpers.mail import From,Mail,Personalization,To,Cc,Bcc,ReplyTo
except ImportError:sendgrid=_A;From=_A;Mail=_A;Personalization=_A;To=_A;Cc=_A;Bcc=_A;ReplyTo=_A;logging.info('sendgrid library not found. Email sending will not be available.')
try:from twilio.rest import Client as TwilioClient
except ImportError:TwilioClient=_A;logging.info('twilio library not found. SMS sending will not be available.')
try:from google.cloud import storage
except ImportError:storage=_A;logging.info('google-cloud-storage library not found. GCS file operations will not be available.')
try:import boto3;from botocore.exceptions import ClientError
except ImportError:boto3=_A;ClientError=_A;logging.info('boto3 library not found. AWS S3 file operations will not be available.')
try:from openai import AsyncOpenAI
except ImportError:AsyncOpenAI=_A;logging.info('openai library not found. OpenAI models will not be available.')
try:from anthropic import AsyncAnthropic
except ImportError:AsyncAnthropic=_A;logging.info('anthropic library not found. Anthropic models will not be available.')
try:from py_mini_racer import MiniRacer
except ImportError:MiniRacer=_A;logging.info('mini-racer not found. JavaScript script execution will not be available.')
try:from pinionai_extensions import*
except ImportError:pass
from.chatservice_pb2 import ChatClient,ChatMessageRequest
from.chatservice_pb2_grpc import ChatServiceStub
from.exceptions import PinionAIAPIError,PinionAIConfigurationError,PinionAIGrpcError,PinionAISessionError
logger=logging.getLogger(__name__)
def _json_datetime_serializer(obj):
	'JSON serializer for datetime objects.'
	if isinstance(obj,(datetime.datetime,datetime.date)):return obj.isoformat()
	raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
class AsyncPinionAIClient:
	'\n    An asynchronous client for interacting with the PinionAI platform.\n\n    This client leverages async/await to handle I/O-bound operations concurrently,\n    improving throughput and responsiveness for scalable AI agent development.\n    ';_create_key=object()
	def __init__(self,create_key,agent_id,host_url,client_id,client_secret,version=_A,initial_engagement_data=_A,grpc_server_address=_A,gcp_project_id=_A,gcp_region=_A,gemini_api_key=_A,twilio_account_sid=_A,twilio_auth_token=_A,twilio_number=_A,email_api_key=_A,email_from_address=_A,openai_api_key=_A,anthropic_api_key=_A,deepseek_api_key=_A):
		'\n        Initializes the AsyncPinionAIClient.\n\n        NOTE: This __init__ is synchronous and should not be called directly.\n        You must use the async class method `AsyncPinionAIClient.create(...)`\n        to get a fully initialized instance.\n        '
		if create_key is not self._create_key:raise PinionAIConfigurationError('AsyncPinionAIClient must be created using the `create` classmethod.')
		self._agent_id=agent_id;self._host_url=host_url.rstrip('/');self._client_id=client_id;self._client_secret=client_secret;self._version=version;self._grpc_server_address=grpc_server_address or os.environ.get(_B8,'localhost:50051');self._gcp_project_id=gcp_project_id or os.environ.get(_B9);self._gcp_region=gcp_region or os.environ.get(_BA);self._gemini_api_key=gemini_api_key or os.environ.get(_BB);self._twilio_account_sid=twilio_account_sid or os.environ.get(_AT);self._twilio_auth_token=twilio_auth_token or os.environ.get(_AU);self._twilio_number=twilio_number or os.environ.get(_AV);self._email_api_key=email_api_key or os.environ.get(_BC);self._email_from_address=email_from_address or os.environ.get(_BD);self._openai_api_key=openai_api_key or os.environ.get(_BE);self._anthropic_api_key=anthropic_api_key or os.environ.get(_BF);self._deepseek_api_key=deepseek_api_key or os.environ.get(_BG);self._http_session=httpx.AsyncClient(base_url=self._host_url,timeout=12e1,follow_redirects=_D);self._token=_A;self._session_id=_A;self._raw_session_data=_A;self.var={};self.engagement=''
		if initial_engagement_data:self.var=initial_engagement_data;self.engagement='active'
		self._class_intent_data='';self._class_message='';self._sub_message='';self._fin_message='';self.transfer_requested='';self.transfer_accepted='';self._privacy_level='';self.current_pipeline='';self.unique_id='';self.phone_number='';self.stepup_authorized=_G;self.authorized=_G;self.next_intent='';self.last_session_post_modified=_A;self._grpc_listener_task=_A;self._grpc_channel=_A;self._grpc_stub=_A;self._grpc_last_update_time=time.time();self.chat_messages=[];self.grpc_sender_id=_a;self._genai_client=_A;self._journey_bearer_token=_A;self._account_id=_A;self._customer_id=_A;self._agent_id_from_api=_A;self._agent_description=_A
	@classmethod
	async def create(cls,*args,**kwargs):
		'\n        Factory method to create and asynchronously initialize the client.\n        This is the preferred way to instantiate the client.\n        ';client=cls(cls._create_key,*args,**kwargs)
		if not client.engagement:
			try:await client._initialize_session_and_vars()
			except(PinionAIAPIError,PinionAISessionError)as e:logger.error(f"Fatal error during client initialization: {e}");await client.close();raise PinionAIConfigurationError(f"Client initialization failed: {e}")from e
		return client
	async def _initialize_session_and_vars(self):
		'Initializes session, fetches token, and sets up initial variables.';B='transferTypes';A='accentColor';self._token=await self._get_token_api(self._host_url,self._client_id,self._client_secret)
		if self._version:logger.info(f"Starting session with version: {self._version}");self._session_id,self._raw_session_data=await self._start_version_api(self._host_url,self._agent_id,self._token,self._version)
		else:logger.info('Starting session without version.');self._session_id,self._raw_session_data=await self._start_session_api(self._host_url,self._agent_id,self._token)
		if not self._session_id or not self._raw_session_data:raise PinionAISessionError('Failed to start session (no session_id or data returned).')
		if _C in self._raw_session_data and self._raw_session_data[_C]:
			self.var=self._extract_data_from_session(self._raw_session_data[_C]);agent_data=self._raw_session_data[_C][_E][_C][_J];self.var['sessionId']=self._session_id;self.var['agentTitle']=agent_data.get('title');self.var['agentSubtitle']=agent_data.get('subtitle');self.var[A]=agent_data.get(A);self.var['userImage']=agent_data.get('userImagePath','').strip();self.var['assistImage']=agent_data.get('assistantImagePath','').strip();self.var[_AW]=agent_data.get(_AW);self.var[_AX]=agent_data.get(_AX);self.var[B]=agent_data.get(B);self.var['sessionDateTime']=datetime.datetime.now(zoneinfo.ZoneInfo('UTC')).astimezone().isoformat();self.var[_r]='';startStatement=self._clean_text(agent_data.get('startStatement'));self.var['agentStart']=self._evaluate_f_string(startStatement or'',self.var);self.var[_j]=agent_data.get(_j);stores_data=agent_data.get('stores',[]);self._rag_stores_by_name={}
			if stores_data and isinstance(stores_data,list)and len(stores_data)>0:
				for s in stores_data:
					try:
						name=s.get(_B)
						if not name:continue
						self._rag_stores_by_name[name]={_s:s.get(_s,''),_t:s.get(_t,10),_u:s.get(_u,.5)}
					except Exception:continue
			if self._rag_stores_by_name:first_store_cfg=next(iter(self._rag_stores_by_name.values()));self.var[_AY]=first_store_cfg.get(_s,'');self.var[_AZ]=first_store_cfg.get(_t,10);self.var[_Aa]=first_store_cfg.get(_u,.5)
			else:self.var[_AY]='';self.var[_AZ]=10;self.var[_Aa]=.5
			self._account_id=self._raw_session_data[_C][_E].get('accountId');self._customer_id=self._raw_session_data[_C][_E].get('customerId');self._agent_id_from_api=agent_data.get('agentId');self._agent_description=self._clean_text(agent_data.get(_K,''))
		else:logger.error('Session data is missing expected structure.');raise PinionAISessionError('Session data from API is missing expected structure.')
		self._genai_client=self._initialize_genai_client()
	async def close(self):'Closes the underlying httpx client session.';await self._http_session.aclose()
	async def __aenter__(self):"Enables use of the client in an 'async with' statement.";return self
	async def __aexit__(self,exc_type,exc_val,exc_tb):"Ensures resources are cleaned up when exiting an 'async with' block.";logger.info('AsyncPinionAIClient exiting context, cleaning up resources...');await self.end_grpc_chat_session(send_goodbye=_G);await self.close()
	def _initialize_genai_client(self):
		'\n        Initializes the Gemini client (genai.Client) for Vertex AI or the Gemini API.\n        If a connector_name for a service account is provided, it will be used for\n        Vertex AI authentication. Otherwise, it falls back to Application Default\n        Credentials (ADC) or an API key.\n\n        Args:\n            connector_name: The name of the connector to use for authentication.\n\n        Returns:\n            An initialized genai.Client instance or None if configuration is missing.\n        ';creds=_A;GCP_SCOPES=['https://www.googleapis.com/auth/cloud-platform']
		if self.var[_j]:
			conn_config=self._get_connector_details(self.var[_j])
			if conn_config and conn_config.get(_k)==_Ab:
				try:sa_info=json.loads(conn_config.get(_l,'{}'));creds=service_account.Credentials.from_service_account_info(sa_info,scopes=GCP_SCOPES);logger.info(f"Loaded service account from connector '{self.var[_j]}' for Gemini client.")
				except(json.JSONDecodeError,KeyError)as e:logger.error(f"Failed to load service account from connector '{self.var[_j]}': {e}")
		if self._gcp_project_id and self._gcp_region:
			if creds:logger.info(f"Initializing Gemini client for Vertex AI with specific credentials.")
			else:logger.info(f"Initializing Gemini client for Vertex AI using Application Default Credentials.")
			return genai.Client(project=self._gcp_project_id,location=self._gcp_region,vertexai=_D,credentials=creds)
		elif self._gemini_api_key:
			if creds:logger.warning('Connector credentials provided but initializing with an API key; credentials will be ignored.')
			logger.info('Initializing Gemini client with direct API key.');return genai.Client(api_key=self._gemini_api_key)
		else:logger.warning('Gemini client not initialized: Missing GCP_PROJECT/GCP_REGION or GEMINI_API_KEY.');return
	async def get_pinionai_version_info(self):
		'\n        Fetches PinionAI agent version information.\n        ';logger.info('Get Pinionai version info');token=await self._get_token_api(self._host_url,self._client_id,self._client_secret)
		if token:
			session_id,data=await self._start_session_api(self._host_url,self._agent_id,token)
			if not session_id:logger.error('Currently unavailable (session could not be started).');return{}
			data_only=data.get(_C,{}).get(_E,{}).get(_C,{});logger.info(f"Version data loaded.");return data_only
		else:logger.error('Currently unavailable (token could not be obtained).')
		return{}
	def _normalize_intent_vars(self,intent_vars):
		if not intent_vars:return[]
		is_new_format=all(key.isdigit()for key in intent_vars.keys())
		if is_new_format:
			normalized_list=[];sorted_keys=sorted(intent_vars.keys(),key=int)
			for key in sorted_keys:
				if intent_vars[key]and isinstance(intent_vars[key],dict):normalized_list.append(list(intent_vars[key].items())[0])
			return normalized_list
		else:return list(intent_vars.items())
	async def process_user_input(self,user_input='',sender=_a):
		'\n        Processes user input, interacts with AI, and determines the next response.\n        ';L='Transfer requested, but gRPC client is not connected.';K='authentication_step_up_pipeline';J='privacyAction';I='highly';H='finalprocess';G='subprocess';F='preprocess';E='contextFlow';D='final prompt';C='subprompt';B='intent_resp';A='inputVars';preprocess_response='';subprocess_response='';final_response='';self.grpc_sender_id=sender
		if not self.transfer_requested:
			prompt_resp_var_name=_A
			if self.next_intent:self.var['prompt_resp_var']=self.next_intent;prompt_type=self.var[_Ac]=_A6;user_input=self.next_intent;intent_data=self._get_intent_details(self.next_intent);self.next_intent=''
			else:
				self.var,prompt_resp_var_name=await self._classify_input(user_input)
				if not prompt_resp_var_name:return"I'm sorry, I couldn't understand that. Could you please rephrase?"
				prompt_type=self.var.get(_Ac);intent_data=self._get_intent_details(self.var[prompt_resp_var_name])
			self.var[_r]=''
			if not intent_data:logger.error(f"Intent details not found for: {self.var[prompt_resp_var_name]}");return"I'm sorry, there was an issue processing your request (intent details missing)."
			intent_type=intent_data[_F];self.var[B]=intent_data[_B];self._privacy_level=self.var['privacy_resp']=intent_data[_Ad];self.current_pipeline=self.var['pipeline_resp']=intent_data[_v];delivery_method=intent_data[_Ae];language=intent_data[_b];intent_input_vars=self._normalize_intent_vars(intent_data.get(A,{}));context_flow=intent_data.get(E,{});intent_subprompt=context_flow.get(C,{});intent_finalprompt=context_flow.get(D,{});intent_preprocess=context_flow.get(F,{});intent_subprocess=context_flow.get(G,{});intent_finalprocess=context_flow.get(H,{});intent_actionprocess=intent_data.get(_Af,{})
			if self.var.get(_H):logger.debug(f"Classification | {self.var[B]}");logger.debug(f"Sensitivity | {self._privacy_level}");logger.debug(f"Intent Type | {intent_type}")
			if intent_type!=_Ag:
				if intent_input_vars:
					agent_vars_config=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get(_BH,[])
					for(key,_)in intent_input_vars:
						for var_def in agent_vars_config:
							if var_def.get(_B)==key and var_def.get('reset',_G)is _D:self.var[key]='';break
				if prompt_type==_A6:self._class_message=user_input;self._class_intent_data=intent_data
				elif prompt_type==C:self._sub_message=user_input
				elif prompt_type==D:self._fin_message=user_input
			elif intent_type==_Ag:
				action_key_for_input=intent_data.get(_v,'')
				if any(keyword in intent_data[_B]for keyword in['phone','mobile','cell']):_,self.unique_id,self.phone_number=format_phone(user_input);self.var[action_key_for_input]=self.phone_number
				else:self.var[action_key_for_input]=user_input
				if self._class_intent_data:intent_data=self._class_intent_data;user_input=self._class_message;intent_type=intent_data[_F];self.var[B]=intent_data[_B];delivery_method=intent_data[_Ae];language=intent_data[_b];intent_input_vars=self._normalize_intent_vars(intent_data.get(A,{}));context_flow=intent_data.get(E,{});intent_subprompt=context_flow.get(C,{});intent_finalprompt=context_flow.get(D,{});intent_preprocess=context_flow.get(F,{});intent_subprocess=context_flow.get(G,{});intent_finalprocess=context_flow.get(H,{});intent_actionprocess=intent_data.get(_Af,{});self._privacy_level=intent_data[_Ad];self.current_pipeline=intent_data[_v]
				original_intent_input_vars=self._class_intent_data.get(A,{})if self._class_intent_data else{};original_keys={item[0]for item in self._normalize_intent_vars(original_intent_input_vars)}
				if action_key_for_input not in original_keys and self._class_intent_data:final_response=f"'{user_input}' is a {intent_data[_B]} . Please respond to trigger an intent or input I am listening for such as: {self.var.get(_BI,[])}."
			if intent_input_vars:
				intent_input_vars=self._normalize_intent_vars(intent_data.get(A,{}));self.var,collect_prompt,waiting_for_inputs=await self._collect_required_inputs(self.var,intent_input_vars)
				if waiting_for_inputs:
					final_response=collect_prompt
					if final_response:self.chat_messages.append({_R:_Ah,_Q:final_response})
					return final_response
			if not final_response:
				if intent_preprocess:self.var,preprocess_response=await self._process_routing(self.var,intent_preprocess,user_input=user_input)
				if preprocess_response:final_response=preprocess_response
				if not final_response:
					if not self.authorized and'private'in self._privacy_level or I in self._privacy_level:
						_,self.unique_id,self.phone_number=format_phone(self.var.get('phone_number',self.phone_number))
						if intent_data[J]:
							current_var,step_response=await self._run_action_action(self.var,intent_data[J],'',user_input=user_input)
							if step_response and not self.authorized:final_response=step_response
						else:
							customer_id,enrolled,_=await self._journey_lookup(self.unique_id,self.var);auth_response_msg=''
							if customer_id and enrolled:
								pipeline_key=self.var[K]if I in self._privacy_level else self.var['authentication_pipeline'];json_payload={_Ai:pipeline_key,_m:{_d:delivery_method,_e:self.phone_number},_Aj:{_Ak:self.unique_id,_e:self.phone_number},_E:{_Al:self._session_id},_b:language}
								if self.var.get(_n):json_payload[_Am]=self.var[_n]
								execution_id,execution_url,error_msg=await self._journey_send_pipeline(self.var,json_payload,delivery_method)
								if error_msg:auth_response_msg=error_msg
								else:
									logger.info(f"Sent authentication for {self.unique_id} to complete.");is_authenticated,message=await self._journey_execution_status_check(execution_id,self.var,120);auth_response_msg=message;self.authorized=is_authenticated
									if pipeline_key==self.var[K]and self.authorized:self.stepup_authorized=_D
									if is_authenticated:logger.info('Authorization successful.')
							else:
								auth_response_msg=f"You are not enrolled. We are sending a link to {self.phone_number} so that you can enroll your device.";json_payload={_Ai:self.var['enroll_pipeline'],_m:{_d:delivery_method,_e:self.phone_number},_Aj:{_Ak:self.unique_id,_e:self.phone_number},_E:{_Al:self._session_id},_b:language}
								if self.var.get(_n):json_payload[_Am]=self.var[_n]
								_,execution_url,error_msg=await self._journey_send_pipeline(self.var,json_payload,delivery_method)
								if error_msg:auth_response_msg=error_msg
							if auth_response_msg and not self.authorized:final_response=auth_response_msg
			if not final_response:
				if intent_type=='fixed':fixed_message_template=self._clean_text(intent_data['fixedResponseMessage']);final_response=self._evaluate_f_string(fixed_message_template,self.var)
				elif intent_type==_A7:
					action_details_from_intent=self._map_to_standard_action_details(intent_data);action_type=action_details_from_intent.get(_An)
					if action_type=='journey':self.var,final_response=await self._run_journey_action(self.var,action_details_from_intent)
					elif action_type=='transfer':self.var,final_response=self._run_transfer_action(self.var,action_details_from_intent)
					else:
						action_flow=action_details_from_intent.get(_Ao)
						if action_flow:
							self.var,action_response=await self._process_routing(self.var,action_flow,user_input=user_input)
							if action_details_from_intent.get(_f):response_msg_template=self._clean_text(action_details_from_intent[_f]);final_response=self._evaluate_f_string(response_msg_template,self.var)
							elif action_response:final_response=action_response
							else:final_response='Actions triggered. :wrench:'
						else:final_response='No working actions configured. :wrench:'
				if final_response and intent_finalprocess:self.var,final_process_response=await self._process_routing(self.var,intent_finalprocess,final_response,user_input=user_input)
			if not final_response:
				if intent_subprompt:self.var,self._sub_message=await self._run_prompt_action(user_input,intent_subprompt)
				if intent_subprocess:self.var,subprocess_response=await self._process_routing(self.var,intent_subprocess,user_input=user_input)
				if subprocess_response:final_response=subprocess_response
				if not final_response:
					if intent_finalprompt:
						for(_indx,item_config)in sorted(intent_finalprompt.items()):
							if isinstance(item_config,dict):
								if _A8 in item_config:
									target_prompt=item_config[_A8];self.var,resp_var_name=await self._prompt_response(target_prompt,user_input)
									if resp_var_name and self.var.get(resp_var_name):final_response=self.var[resp_var_name]
								elif _o in item_config:
									mcp_name=item_config[_o];self.var,mcp_response=await self._run_mcp_action(self.var,mcp_name,user_input)
									if mcp_response:final_response=mcp_response
							elif isinstance(item_config,str):
								self.var,resp_var_name=await self._prompt_response(item_config,user_input)
								if resp_var_name and self.var.get(resp_var_name):final_response=self.var[resp_var_name]
					if intent_finalprocess:self.var,final_process_response=await self._process_routing(self.var,intent_finalprocess,final_response,user_input=user_input)
		elif self._grpc_stub:await self.send_grpc_message(user_input);final_response='Message sent to live agent. Waiting for reply...'
		else:final_response=L;logger.warning(L)
		if final_response:self.chat_messages.append({_R:_Ah,_Q:final_response})
		return final_response
	async def update_pinion_session(self):
		'\n        Posts the current session data to the PinionAI backend.\n        '
		if not self._session_id or not self._token or not self._raw_session_data:logger.error('Cannot update session: session not properly initialized.');return
		data_to_post=json.loads(json.dumps(self._raw_session_data.get(_C,{})))
		if _E not in data_to_post:data_to_post[_E]={}
		data_to_post[_E][_w]=self.var;messages_for_api=[{k:v for(k,v)in msg.items()if k!='avatar'}for msg in self.chat_messages];data_to_post[_E][_x]=messages_for_api;response_obj,response_data=await self._post_session_api(self._host_url,self._token,self._session_id,data_to_post,self.transfer_requested,self.transfer_accepted)
		if response_obj and response_obj.status_code==200:
			try:last_modified_time=response_data[_C]['Lastmodified']['Time'];self.last_session_post_modified=last_modified_time;return last_modified_time
			except(KeyError,TypeError)as e:logger.error(f"Error parsing Lastmodified from session post response: {e} - Data: {response_data}");return
		elif response_obj:logger.error(f"Error posting session data: Status Code {response_obj.status_code}, Message: {response_data}");return
		else:logger.error(f"Network error posting session data: {response_data}");return
	async def get_latest_session_modification_time(self):
		'\n        Fetches the last modified timestamp for the current session.\n        '
		if not self._session_id or not self._token:return _A,'Session or token not initialized.'
		return await self._get_session_lastmodified_api(self._host_url,self._session_id,self._token)
	async def start_grpc_client_listener(self,sender_id=_a):
		'\n        Establishes a secure async gRPC connection to the Cloud Run service and starts the listener task.\n        '
		if not self._grpc_server_address:logger.error('gRPC server address not configured.');return _G
		if not self._session_id:logger.error('Session ID not available for gRPC client.');return _G
		self.grpc_sender_id=sender_id
		try:credentials=grpc.ssl_channel_credentials();self._grpc_channel=agrpc.secure_channel(self._grpc_server_address,credentials);self._grpc_stub=ChatServiceStub(self._grpc_channel);logger.info(f"gRPC client connected to {self._grpc_server_address} for session {self._session_id} as {sender_id}");self._grpc_listener_task=asyncio.create_task(self._grpc_read_handler(self.grpc_sender_id,self._session_id,self._grpc_stub));return _D
		except grpc.aio.AioRpcError as e:logger.error(f"gRPC connection failed: {e.code()} - {e.details()}",exc_info=_D);raise PinionAIGrpcError(f"Failed to connect to gRPC server: {e.details()}")from e
		except Exception as e:logger.error(f"An unexpected error occurred while starting gRPC client: {e}",exc_info=_D);raise PinionAIGrpcError(f"Failed to start gRPC client listener: {e}")from e
	async def _grpc_read_handler(self,client_id,session_id,stub):
		'Handles receiving messages from the server in an asyncio task.';logger.info(f"gRPC read_handler task started for client: {client_id}, session: {session_id}");request=ChatClient(recipient_id=client_id,session_id=str(session_id))
		try:
			read_stream=stub.ReceiveMessages(request)
			async for response in read_stream:logger.info(f"gRPC message received: {response.sender_id} ({response.timestamp}): {response.message}");self.chat_messages.append({_R:response.sender_id,_Q:response.message});self._grpc_last_update_time=time.time()
		except agrpc.AioRpcError as e:
			if e.code()==grpc.StatusCode.CANCELLED:logger.info(f"gRPC read_handler stream cancelled: {e.details()}")
			else:logger.error(f"gRPC AioRpcError in read_handler: {e.code()} - {e.details()}")
		except Exception as e:logger.error(f"Unexpected error in gRPC read_handler: {e}",exc_info=_D)
		finally:logger.info(f"gRPC read_handler task for client {client_id} terminated.")
	async def send_grpc_message(self,message_text):
		'Sends a message via async gRPC.'
		if not self._grpc_stub or not self._session_id:logger.error('gRPC stub or session ID not available. Cannot send message.');return
		try:recipient_id=_Ah if self.grpc_sender_id==_a else _a;request=ChatMessageRequest(thread_id=1,message=message_text,sender_id=self.grpc_sender_id,recipient_id=recipient_id,session_id=str(self._session_id));await self._grpc_stub.SendMessage(request);logger.info(f"gRPC message sent by {self.grpc_sender_id}: {message_text}")
		except agrpc.AioRpcError as e:raise PinionAIGrpcError(f"Failed to send gRPC message: {e.details()}",grpc_code=e.code())from e
	async def end_grpc_chat_session(self,send_goodbye=_D):
		'Handles the end of a gRPC chat session logic.';logger.info('Ending gRPC chat session.')
		if self._grpc_listener_task and not self._grpc_listener_task.done():self._grpc_listener_task.cancel()
		if self._grpc_stub and self._session_id and send_goodbye:
			try:logger.info("Sending gRPC end message 'X'.");await self.send_grpc_message('X')
			except Exception as e:logger.error(f"Error sending 'X' message during gRPC end: {e}")
		if self._grpc_channel:await self._grpc_channel.close();logger.info('gRPC channel closed.')
		self._grpc_channel=_A;self._grpc_stub=_A;self._grpc_listener_task=_A;logger.info('gRPC chat session ended and resources cleaned up.')
	async def _process_routing(self,current_var,process_items,initial_final_response=_A,user_input=_A):
		'Handles routing activities from intent and action flows.';G='intent';F='file';E='rule';D='script';C='merger';B='parser';A='api'
		if current_var.get(_H):logger.debug(f"Process Routing | {process_items}")
		generated_final_response=initial_final_response
		for(_key,item_config)in sorted(process_items.items()):
			step_response=_A
			if A in item_config:current_var,step_response=await self._run_api_action(current_var,item_config[A])
			elif B in item_config:current_var,step_response=self._run_parser_action(current_var,item_config[B])
			elif C in item_config:current_var,step_response=self._run_merger_action(current_var,item_config[C])
			elif D in item_config:current_var,step_response=await self._run_script_action(current_var,item_config[D])
			elif E in item_config:current_var,step_response=await self._run_rule_action(current_var,item_config[E],user_input=user_input)
			elif _m in item_config:current_var,step_response=await self._run_delivery_action(current_var,item_config[_m])
			elif _A7 in item_config:current_var,step_response=await self._run_action_action(current_var,item_config[_A7],generated_final_response,user_input=user_input)
			elif _o in item_config:current_var,step_response=await self._run_mcp_action(current_var,item_config[_o],user_input)
			elif F in item_config:current_var,step_response=await self._run_file_action(current_var,item_config[F])
			elif G in item_config:self.next_intent=item_config[G];logger.info(f"Next intent set to: {self.next_intent}")
			if step_response:generated_final_response=step_response
		return current_var,generated_final_response
	async def _run_async_prompts_for_list(self,prompt_list,user_input_val,shared_var_copy):
		tasks=[self._async_prompt_response(p_text,user_input_val,shared_var_copy)for p_text in prompt_list];gathered_results=await asyncio.gather(*tasks);current_batch_response_strings=[];updates_to_apply_to_shared_var={}
		for(resp_key_name,value_for_key)in gathered_results:
			if resp_key_name:updates_to_apply_to_shared_var[resp_key_name]=value_for_key
			if isinstance(value_for_key,str):current_batch_response_strings.append(value_for_key)
			elif value_for_key is not _A:current_batch_response_strings.append(str(value_for_key))
		return current_batch_response_strings,updates_to_apply_to_shared_var
	def _extract_data_from_session(self,session_data_root):
		'Extracts variables and agent configuration into the var dictionary.';var_dict={};agent_config=session_data_root.get(_E,{}).get(_C,{}).get(_J,{});global_to_self_attr_map={_B8:'_grpc_server_address',_B9:'_gcp_project_id',_BA:'_gcp_region',_BB:'_gemini_api_key',_AT:'_twilio_account_sid',_AU:'_twilio_auth_token',_AV:'_twilio_number',_BC:'_email_api_key',_BD:'_email_from_address',_BE:'_openai_api_key',_BF:'_anthropic_api_key',_BG:'_deepseek_api_key'}
		for variable_def in agent_config.get(_BH,[]):
			name=variable_def[_B];value=variable_def[_Ap];var_type=variable_def.get(_F)
			if variable_def.get(_A9)=='global':
				os.environ[name]=str(value)
				if name in global_to_self_attr_map:attr_name=global_to_self_attr_map[name];setattr(self,attr_name,str(value));logger.info(f"Updated client attribute '{attr_name}' from global agent variable '{name}'.")
			elif var_type=='integer':
				try:var_dict[name]=int(value)
				except(ValueError,TypeError):var_dict[name]=value
			elif var_type=='boolean':var_dict[name]=str(value).lower()=='true'
			elif var_type=='float':
				try:var_dict[name]=float(value)
				except(ValueError,TypeError):var_dict[name]=value
			else:var_dict[name]=value
		intent_names,no_input_intent_names,input_intent_names=[],[],[];intent_privacy_pairs,intent_type_pairs=[],[];intent_contains_word_pairs,intent_action_key_pairs_raw=[],[]
		for intent in agent_config.get('intents',[]):
			intent_name=intent[_B];intent_names.append(intent_name)
			if intent[_F]=='information'or intent[_F]==_A7:no_input_intent_names.append(intent_name)
			if intent[_F]==_Ag:input_intent_names.append(intent_name)
			intent_privacy_pairs.append((intent_name,intent[_Ad]));intent_type_pairs.append((intent_name,intent[_F]));intent_contains_word_pairs.append((intent_name,intent.get('containsWord','')));intent_action_key_pairs_raw.append((intent_name,intent.get(_v,'')))
		var_dict[_Aq]=intent_names;var_dict[_BI]=no_input_intent_names;var_dict['inputIntentNameList']=input_intent_names;var_dict['intentPrivacyPairsList']=intent_privacy_pairs;var_dict['intentTypePairsList']=intent_type_pairs;var_dict[_Ar]=intent_contains_word_pairs;resolved_action_key_pairs=[]
		for(intent,action_key_val_or_var)in intent_action_key_pairs_raw:
			if action_key_val_or_var in var_dict:resolved_action_key_pairs.append((intent,var_dict[action_key_val_or_var]))
			else:resolved_action_key_pairs.append((intent,action_key_val_or_var))
		var_dict['intentActionPairsList']=resolved_action_key_pairs;var_dict[_AA]=agent_config.get(_AA);var_dict[_As]=agent_config.get('defaultIntent');return var_dict
	async def _classify_input(self,user_input):
		if not self.var.get(_AA):logger.error('startPrompt not defined in agent configuration.');return self.var,_A
		_current_var_state,resp_var_name=await self._prompt_response(self.var[_AA],user_input)
		if not resp_var_name:logger.error('No response variable name set for classification prompt.');return self.var,_A
		return self.var,resp_var_name
	async def _collect_required_inputs(self,current_var,required_vars):
		'\n        required_vars: list of (variable_name, prompt_message).\n        Returns: (updated_current_var, prompt_message_or_None, waiting_bool)\n        If waiting_bool is True the caller should present the prompt_message to the user and pause further processing.\n        '
		if not required_vars:current_var[_r]='';return current_var,_A,_G
		for(key_req,prompt_msg)in required_vars:
			val=current_var.get(key_req)
			if val is _A or isinstance(val,str)and not val.strip()or isinstance(val,(list,dict))and not val:current_var[_r]=f"Strongly consider the expected input field should be {key_req}";final_prompt=prompt_msg or f"Please provide a value for {key_req}.";return current_var,final_prompt,_D
		current_var[_r]='';return current_var,_A,_G
	async def _prompt_response(self,target_prompt,user_input=''):
		prompt_config,direct_tool_configs,processed_fd_dicts=self._get_prompt_details(target_prompt)
		if not prompt_config:logger.error(f"Prompt '{target_prompt}' not found. Check configuration.");return self.var,_A
		self.var[_Ac]=prompt_config[_F];prompt_resp_var_name=prompt_config[_AB];prompt_body_template=self._clean_text(prompt_config[_U]);current_prompt_text=self._evaluate_f_string(prompt_body_template,self.var,user_input=user_input);model_provider=prompt_config.get(_At,_c).lower();model_name=prompt_config.get(_V);llm_response_text=_A;function_calls=_A;system_instruction=self._evaluate_f_string(self._agent_description or'',self.var)
		if model_provider==_c:
			content_parts=[]
			if prompt_config.get(_AC):
				file_uri_template=self._clean_text(prompt_config[_AC]);file_uri=self._evaluate_f_string(file_uri_template,self.var)
				if file_uri:content_parts.append(Part.from_uri(file_uri=file_uri,mime_type=prompt_config[_BJ]))
			content_parts.append(current_prompt_text);gen_config=google_genai_types.GenerateContentConfig(system_instruction=system_instruction if system_instruction else _A,temperature=prompt_config[_AD],top_p=prompt_config[_W],top_k=prompt_config[_AE],candidate_count=prompt_config[_AF],max_output_tokens=prompt_config[_AG],stop_sequences=prompt_config.get('stop')or _A,safety_settings=prompt_config.get(_BK))
			if model_name in[_BL]and prompt_config.get(_AH)is not _A:gen_config.thinking_config=ThinkingConfig(thinking_budget=prompt_config[_AH])
			if prompt_config.get(_AI):gen_config.response_schema=prompt_config[_AI];gen_config.response_mime_type=prompt_config.get(_BM,_M)
			gen_config.tools=self._configure_tools_for_request(direct_tool_configs,processed_fd_dicts,model_name);llm_response_text,_,function_calls=await self._get_gemini_response_async(model_name,content_parts,gen_config)
		elif model_provider in[_g,_y,_AJ]:
			messages=[]
			if system_instruction and model_provider in[_g,_AJ]:messages.append({_R:_z,_Q:system_instruction})
			messages.append({_R:_a,_Q:current_prompt_text});tools_for_provider=self._translate_tools_for_provider(model_provider,direct_tool_configs,processed_fd_dicts)
			if model_provider==_g:llm_response_text,function_calls=await self._get_openai_response_async(model_name,messages,prompt_config,tools_for_provider)
			elif model_provider==_y:anthropic_messages=[m for m in messages if m[_R]!=_z];llm_response_text,function_calls=await self._get_anthropic_response_async(model_name,system_instruction,anthropic_messages,prompt_config,tools_for_provider)
			elif model_provider==_AJ:llm_response_text,function_calls=await self._get_deepseek_response_async(model_name,messages,prompt_config,tools_for_provider)
		else:logger.error(f"Unsupported model provider: {model_provider}");return self.var,f"Error: Unsupported model provider '{model_provider}'"
		if function_calls:
			function_call=function_calls[0];function_name=function_call.get(_B);function_args=function_call.get(_I,{})
			if not function_name:logger.error(f"LLM response contained a function call with no name: {function_call}");return self.var,_BN
			logger.info(f"LLM requested to call function '{function_name}' with args: {function_args}")
			if function_name in globals()and callable(globals()[function_name]):
				function_to_call=globals()[function_name]
				try:
					if asyncio.iscoroutinefunction(function_to_call):tool_response=await function_to_call(**function_args)
					else:tool_response=await asyncio.to_thread(function_to_call,**function_args)
					if isinstance(tool_response,(dict,list)):tool_response_str=json.dumps(tool_response,indent=2)
					else:tool_response_str=str(tool_response)
					if prompt_resp_var_name:self.var[prompt_resp_var_name]=tool_response_str
					return self.var,prompt_resp_var_name
				except Exception as e:
					logger.error(f"Error executing tool function '{function_name}': {e}",exc_info=_D);error_message=f"Error: Failed to execute tool '{function_name}': {e}"
					if prompt_resp_var_name:self.var[prompt_resp_var_name]=error_message
					return self.var,prompt_resp_var_name
			else:
				logger.error(f"Function '{function_name}' requested by LLM is not a defined callable function.");error_message=f"Error: The AI tried to call a function named '{function_name}' which is not available."
				if prompt_resp_var_name:self.var[prompt_resp_var_name]=error_message
				return self.var,prompt_resp_var_name
		if llm_response_text:
			if prompt_config[_F]==_A6:
				raw_response=llm_response_text.strip().lower()
				if self.var.get(_H):logger.debug(f"Raw Intent Response | {raw_response}")
				matched_intent_key=self._match_intent_from_text(raw_response,self.var.get(_Ar,[]),self.var.get(_As,_BO),self.var.get(_Aq,[]));self.var[prompt_resp_var_name]=matched_intent_key
			else:self.var[prompt_resp_var_name]=llm_response_text
		else:self.var[prompt_resp_var_name]=''
		return self.var,prompt_resp_var_name
	async def _async_prompt_response(self,target_prompt,user_input='',var_snapshot=_A):
		current_var=var_snapshot if var_snapshot is not _A else self.var.copy();prompt_config,direct_tool_configs,processed_fd_dicts=self._get_prompt_details(target_prompt,current_var)
		if not prompt_config:logger.error(f"Prompt '{target_prompt}' not found. Skipping async call.");return _A,_A
		prompt_resp_var_name=prompt_config[_AB];prompt_body_template=self._clean_text(prompt_config[_U]);current_prompt_text=self._evaluate_f_string(prompt_body_template,current_var,user_input=user_input);model_provider=prompt_config.get(_At,_c).lower();model_name=prompt_config.get(_V);llm_response_text=_A;function_calls=_A;system_instruction=self._evaluate_f_string(self._agent_description or'',current_var)
		if model_provider==_c:
			content_parts=[]
			if prompt_config.get(_AC):
				file_uri_template=self._clean_text(prompt_config[_AC]);file_uri=self._evaluate_f_string(file_uri_template,current_var)
				if file_uri:content_parts.append(Part.from_uri(file_uri=file_uri,mime_type=prompt_config[_BJ]))
			content_parts.append(current_prompt_text);gen_config=google_genai_types.GenerateContentConfig(system_instruction=system_instruction if system_instruction else _A,temperature=prompt_config[_AD],top_p=prompt_config[_W],top_k=prompt_config[_AE],candidate_count=prompt_config[_AF],max_output_tokens=prompt_config[_AG],stop_sequences=prompt_config.get('stop')or _A,safety_settings=prompt_config.get(_BK))
			if model_name in[_BL]and prompt_config.get(_AH)is not _A:gen_config.thinking_config=ThinkingConfig(thinking_budget=prompt_config[_AH])
			if prompt_config.get(_AI):gen_config.response_schema=prompt_config[_AI];gen_config.response_mime_type=prompt_config.get(_BM,_M)
			gen_config.tools=self._configure_tools_for_request(direct_tool_configs,processed_fd_dicts,model_name);llm_response_text,_,function_calls=await self._get_gemini_response_async(model_name,content_parts,gen_config)
		elif model_provider in[_g,_y]:
			messages=[]
			if system_instruction and model_provider==_g:messages.append({_R:_z,_Q:system_instruction})
			messages.append({_R:_a,_Q:current_prompt_text});tools_for_provider=self._translate_tools_for_provider(model_provider,direct_tool_configs,processed_fd_dicts)
			if model_provider==_g:llm_response_text,function_calls=await self._get_openai_response_async(model_name,messages,prompt_config,tools_for_provider)
			elif model_provider==_y:anthropic_messages=[m for m in messages if m[_R]!=_z];llm_response_text,function_calls=await self._get_anthropic_response_async(model_name,system_instruction,anthropic_messages,prompt_config,tools_for_provider)
		else:logger.error(f"Unsupported model provider: {model_provider}");return _A,f"Error: Unsupported model provider '{model_provider}'"
		if function_calls:
			function_call=function_calls[0];function_name=function_call.get(_B);function_args=function_call.get(_I,{})
			if not function_name:logger.error(f"LLM async response contained a function call with no name: {function_call}");return prompt_resp_var_name,_BN
			logger.info(f"LLM requested async call to function '{function_name}' with args: {function_args}")
			if function_name in globals()and callable(globals()[function_name]):
				function_to_call=globals()[function_name]
				try:
					if asyncio.iscoroutinefunction(function_to_call):tool_response=await function_to_call(**function_args)
					else:tool_response=await asyncio.to_thread(function_to_call,**function_args)
					if isinstance(tool_response,(dict,list)):tool_response_str=json.dumps(tool_response,indent=2)
					else:tool_response_str=str(tool_response)
					return prompt_resp_var_name,tool_response_str
				except Exception as e:logger.error(f"Error executing tool function '{function_name}' in async prompt: {e}",exc_info=_D);error_message=f"Error: Failed to execute tool '{function_name}': {e}";return prompt_resp_var_name,error_message
			else:logger.error(f"Function '{function_name}' requested by LLM is not a defined callable function.");error_message=f"Error: The AI tried to call a function named '{function_name}' which is not available.";return prompt_resp_var_name,error_message
		final_value_for_var=''
		if llm_response_text:
			if prompt_config[_F]==_A6:
				raw_response=llm_response_text.strip().lower()
				if current_var.get(_H):logger.debug(f"Async Raw Intent Response | {raw_response}")
				final_value_for_var=self._match_intent_from_text(raw_response,current_var.get(_Ar,[]),current_var.get(_As,_BO),current_var.get(_Aq,[]))
			else:final_value_for_var=llm_response_text
		return prompt_resp_var_name,final_value_for_var
	def _match_intent_from_text(self,response_text,intent_contains_pairs,default_intent,intent_name_list):
		'Helper to match intent from LLM response text.';threshold_ratio=.85
		if response_text in intent_name_list:return response_text
		matched_intent_key=default_intent;best_similarity_score=.0
		for(intent_key,search_phrases_str)in intent_contains_pairs:
			if not search_phrases_str:continue
			search_phrases=[phrase.strip()for phrase in str(search_phrases_str).split(_S)]
			for phrase in search_phrases:
				if phrase and phrase in response_text:return intent_key
		for(intent_key,search_phrases_str)in intent_contains_pairs:
			if not search_phrases_str:continue
			search_phrases=[phrase.strip()for phrase in str(search_phrases_str).split(_S)]
			for phrase in search_phrases:
				if not phrase:continue
				similarity=Levenshtein.ratio(response_text,phrase)
				if similarity>threshold_ratio and similarity>best_similarity_score:best_similarity_score=similarity;matched_intent_key=intent_key
		return matched_intent_key
	def _get_prompt_details(self,target_prompt_name,current_var_snapshot=_A):
		'Fetches prompt configuration, processing tools and functional declarations.';A='functionalDeclarations';var_to_use=current_var_snapshot if current_var_snapshot is not _A else self.var;direct_tool_configs=[];processed_fd_dicts=[];agent_prompts=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('prompts',[]);agent_tools_config=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get(_O,[])
		for prompt_config in agent_prompts:
			if target_prompt_name==prompt_config.get(_B):
				if prompt_config.get(_O):
					for tool_name_in_prompt_config in prompt_config[_O]:
						for actual_tool_def in agent_tools_config:
							if actual_tool_def.get(_B)==tool_name_in_prompt_config:
								if actual_tool_def.get(_O):direct_tool_configs.extend(actual_tool_def[_O])
								if actual_tool_def.get(A):
									declarations_data=actual_tool_def.get(A);declaration_templates=[]
									if isinstance(declarations_data,list):declaration_templates=declarations_data
									elif isinstance(declarations_data,dict):declaration_templates=[declarations_data]
									elif isinstance(declarations_data,str):
										try:
											cleaned_str=self._clean_text(declarations_data);parsed_json=json.loads(cleaned_str)
											if isinstance(parsed_json,list):declaration_templates=parsed_json
											elif isinstance(parsed_json,dict):declaration_templates=[parsed_json]
											else:logger.warning(f"Functional declaration string did not parse into a list or dictionary: {cleaned_str}")
										except json.JSONDecodeError:logger.warning(f"Could not parse functional declaration string as JSON: {declarations_data}")
									for template in declaration_templates:
										if isinstance(template,dict):processed_fd=self._evaluate_vars_in_structure(json.loads(json.dumps(template)),var_to_use,user_input=_A);processed_fd_dicts.append(processed_fd)
										else:logger.warning(f"Skipping item in functionalDeclarations because it is not a dictionary: {template}")
								break
				return prompt_config,direct_tool_configs,processed_fd_dicts
		return _A,[],[]
	def _get_intent_details(self,intent_name):
		'Fetches intent configuration.';intents=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('intents',[])
		for intent_config in intents:
			if intent_config.get(_B)==intent_name:return intent_config
	def _get_api_details(self,api_name):
		apis=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('apis',[])
		for api_config in apis:
			if api_config.get(_B)==api_name:return api_config
	def _get_parser_details(self,parser_name):
		parsers=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('parsers',[])
		for parser_config in parsers:
			if parser_config.get(_B)==parser_name:return parser_config
	def _get_merger_details(self,merger_name):
		mergers=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('mergers',[])
		for merger_config in mergers:
			if merger_config.get(_B)==merger_name:return merger_config
	def _get_script_details(self,script_name):
		scripts=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('scripts',[])
		for script_config in scripts:
			if script_config.get(_B)==script_name:return script_config
	def _get_rule_details(self,rule_name):
		rules=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('rules',[])
		for rule_config in rules:
			if rule_config.get(_B)==rule_name:return rule_config
	def _get_delivery_details(self,delivery_name):
		deliveries=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('deliveries',[])
		for delivery_config in deliveries:
			if delivery_config.get(_B)==delivery_name:return delivery_config
	def _get_action_details(self,action_name):
		actions=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('actions',[])
		for action_config in actions:
			if action_config.get(_B)==action_name:return action_config
	def _get_file_details(self,file_name):
		'Fetches file operation configuration.';files=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('files',[])
		for file_config in files:
			if file_config.get(_B)==file_name:return file_config
	def _get_connector_details(self,connector_name):
		connectors=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('connectors',[])
		for connector_config in connectors:
			if connector_config.get(_B)==connector_name:return connector_config
	def _get_mcp_details(self,mcp_name,current_var):
		mcps=self._raw_session_data.get(_C,{}).get(_E,{}).get(_C,{}).get(_J,{}).get('mcps',[]);mcp_config=next((mcp_config for mcp_config in mcps if mcp_config.get(_B)==mcp_name),_A)
		if mcp_config:
			mcp_config=self._evaluate_vars_in_structure(mcp_config,current_var);mcp_config[_K]=self._clean_text(mcp_config.get(_K,''));mcp_config[_X]=self._evaluate_f_string(mcp_config.get(_X,''),current_var);mcp_config[_A0]=self._clean_text(mcp_config.get(_A0,''));mcp_config['cwd']=self._clean_text(mcp_config.get('cwd',''))
			if _I in mcp_config and isinstance(mcp_config.get(_I),dict):args_dict=mcp_config[_I];sorted_arg_list=[value for(key,value)in sorted(args_dict.items(),key=lambda item:int(item[0]))];mcp_config[_I]=[self._clean_text(arg)for arg in sorted_arg_list]
			if mcp_config.get(_A1):mcp_config[_A1]={k:self._clean_text(v)for(k,v)in mcp_config[_A1].items()}
		else:logger.warning(f"MCP configuration '{mcp_name}' not found in session data.")
		return mcp_config
	async def _run_prompt_action(self,user_input,intent_subprompt):
		if not intent_subprompt:return self.var,''
		all_individual_subprompt_responses=[]
		for(_indx,current_prompt_item)in sorted(intent_subprompt.items()):
			if _A8 in current_prompt_item:
				prompt_value=current_prompt_item[_A8]
				if isinstance(prompt_value,list)and len(prompt_value)>1:batch_responses,updated_var=await self._run_async_prompts_for_list(prompt_value,user_input,self.var.copy());self.var.update(updated_var);all_individual_subprompt_responses.extend(batch_responses)
				else:
					target_prompt=prompt_value[0]if isinstance(prompt_value,list)else prompt_value;self.var,resp_var_name=await self._prompt_response(target_prompt,user_input)
					if resp_var_name and self.var.get(resp_var_name):all_individual_subprompt_responses.append(str(self.var[resp_var_name]))
			elif _o in current_prompt_item:
				self.var,step_response=await self._run_mcp_action(self.var,current_prompt_item[_o],user_input)
				if step_response:all_individual_subprompt_responses.append(step_response)
		self._sub_message=' '.join(filter(_A,all_individual_subprompt_responses)).strip();return self.var,self._sub_message
	@staticmethod
	@asynccontextmanager
	async def _websocket_client_context(uri):
		'A context manager for a WebSocket client connection that yields read/write callables.'
		try:
			async with websockets.connect(uri)as websocket:
				async def read():
					message=await websocket.recv()
					if isinstance(message,str):return message.encode(_N)
					return message
				async def write(data):await websocket.send(data.decode(_N))
				yield(read,write)
		except(websockets.exceptions.ConnectionClosedError,websockets.exceptions.InvalidURI,OSError)as e:logger.error(f"WebSocket connection to {uri} failed: {e}");raise PinionAIGrpcError(f"WebSocket connection failed: {e}")from e
	async def _select_mcp_config(self,mcp_group_names,current_var,user_input,mcp_group_config):
		'\n        Selects an MCP configuration from a group using an LLM.\n        ';C='mcp_descriptions';B='select_mcp';A='mcp_name';mcp_options=[]
		for name in mcp_group_names:
			config=self._get_mcp_details(name,current_var)
			if config:mcp_options.append(config)
		if not mcp_options:logger.warning('No valid MCP options found in the group.');return
		select_mcp_declaration=FunctionDeclaration(name=B,description="Select the most appropriate MCP from the list based on the user's request.",parameters={_F:_p,_AK:{A:{_F:_AN,_K:'The name of the selected MCP.',_AM:[mcp.get(_B)for mcp in mcp_options]}},_AL:[A]});prompt_name=mcp_group_config.get(_BP,'');prompt_config=_A;prompt_resp_var_name=_A;current_prompt_text=user_input or''
		if prompt_name:
			logger.info(f"MCP '{mcp_name}' is using prompt '{prompt_name}'.");prompt_config,_,_=self._get_prompt_details(prompt_name,current_var)
			if not prompt_config:error_msg=f"Error: Prompt '{prompt_name}' for MCP '{mcp_name}' not found.";logger.error(error_msg);return current_var,error_msg
			prompt_model_provider=prompt_config.get('modelProvider',_c);prompt_model=_Au
			if prompt_config.get(_V):prompt_model=prompt_config.get(_V)
			prompt_resp_var_name=prompt_config.get(_AB,'');prompt_body_template=self._clean_text(prompt_config.get(_U,''));mcp_group_prompt_text=self._evaluate_f_string(prompt_body_template,current_var,user_input=user_input)
		self.var[C]=' '.join([f"- {mcp.get(_B)}: {mcp.get(_K,'No description')}"for mcp in mcp_options]);prompt_text=f"Based on the user's request: '{user_input}', and the following available MCPs, which one should be used? {self.var[C]} Please select the closest match to the user's request for the MCP fit. Return Only the name of the MCP as a string.";config=google_genai_types.GenerateContentConfig(tools=[Tool(function_declarations=[select_mcp_declaration])]);selected_mcp_name,_,function_calls=await self._get_gemini_response_async(prompt_model,[mcp_group_prompt_text],config)
		if function_calls and function_calls[0][_B]==B:selected_mcp_name=function_calls[0][_I].get(A);logger.info(f"LLM selected MCP '{selected_mcp_name}' from the group.")
		if selected_mcp_name:
			for mcp_option in mcp_options:
				if mcp_option.get(_B)==selected_mcp_name:return mcp_option
		logger.warning('LLM did not select an MCP from the group. Cannot proceed.')
	async def _run_mcp_action(self,current_var,mcp_name,user_input=_A):
		"\n        Runs a multi-step process (MCP) action defined by the mcp_name.\n        This function retrieves the MCP configuration and executes it by connecting to a\n        local (stdio) or remote (http) MCP server using fastmcp.\n        Args:\n            current_var: The current variable dictionary to update.\n            mcp_name: The name of the MCP to execute.\n            user_input: The user's input to pass to the MCP.\n\n        Returns:\n            The updated variable dictionary and an optional final response message.\n        ";M='mcpServers';L='streamable-http';K='groupNames';J='get_mcp_prompt_handler';I='read_mcp_resource_handler';H='call_mcp_tool_handler';G='http';F='transport';E='prompt_args';D='prompt_name';C='resource_uri';B='tool_name';A='tool_args';mcp_config=self._get_mcp_details(mcp_name,current_var)
		if not mcp_config:logger.warning(f"MCP configuration '{mcp_name}' not found.");return current_var,f"Error: MCP configuration '{mcp_name}' not found."
		try:
			if mcp_config.get('serverGroup',_G)and mcp_config.get(K):
				logger.info(f"MCP Group '{mcp_name}' detected. Selecting a member to run...");group_names=mcp_config[K]
				if isinstance(group_names,str):group_names=[group_names]
				selected_config_from_group=await self._select_mcp_config(group_names,current_var,user_input,mcp_config)
				if not selected_config_from_group:logger.warning(f"Could not select an MCP from group '{mcp_name}'.");return current_var,f"Error: Could not decide which MCP to use from group '{mcp_name}'."
				mcp_config=selected_config_from_group;mcp_name=mcp_config.get(_B,mcp_name)
			prompt_name=mcp_config.get(_BP,'');prompt_config=_A;prompt_resp_var_name=_A;current_prompt_text=user_input or''
			if prompt_name:
				logger.info(f"MCP '{mcp_name}' is using prompt '{prompt_name}'.");prompt_config,_,_=self._get_prompt_details(prompt_name,current_var)
				if not prompt_config:error_msg=f"Error: Prompt '{prompt_name}' for MCP '{mcp_name}' not found.";logger.error(error_msg);return current_var,error_msg
				prompt_resp_var_name=prompt_config.get(_AB,'');prompt_body_template=self._clean_text(prompt_config.get(_U,''));current_prompt_text=self._evaluate_f_string(prompt_body_template,current_var,user_input=user_input)
			mcp_transport=mcp_config.get(F,'');mcp_url=mcp_config.get(_X,'');mcp_description=mcp_config.get(_K,'');mcp_command=mcp_config.get(_A0,'');mcp_args=mcp_config.get(_I,{});mcp_cwd=mcp_config.get('cwd','');mcp_args=mcp_config.get(_I,[]);mcp_params=mcp_config.get('parametersJson',{});mcp_env=mcp_config.get(_A1,{});mcp_name=mcp_config.get(_B,'default');required_inputs=[]
			if mcp_params:
				for(param_key,param_value_template)in mcp_params.items():
					evaluated_value=self._evaluate_f_string(str(param_value_template),current_var)
					if not evaluated_value:
						logger.warning(f"MCP parameter '{param_key}' evaluated to an empty value.");required_inputs.append((param_key,f"Please provide a value for'{param_key}'."))
						if not param_key in current_var:current_var[param_key]=''
					else:mcp_params[param_key]=evaluated_value
			if required_inputs:
				normalized_required=[(it[0],it[1]if len(it)>1 else _A)for it in required_inputs];current_var,prompt_msg,waiting=await self._collect_required_inputs(current_var,normalized_required)
				if waiting:return current_var,prompt_msg
			session_context=_A;is_http_call=mcp_transport in[G,L]or not mcp_transport and mcp_url.startswith(('http://','https://'));is_stdio_call=mcp_transport=='stdio'or not mcp_transport and not mcp_url and mcp_config.get(_A0)
			if is_http_call:
				eval_mcp_url=mcp_url;http_headers=self._evaluate_vars_in_structure(mcp_config.get(_Av,{}),current_var);mcp_connector=mcp_config.get(_T,'')
				if mcp_connector:
					connector_config=self._get_connector_details(mcp_connector)
					if connector_config:
						try:
							token=await self._get_token_for_connector(connector_config)
							if token:http_headers[_L]=token
						except PinionAIAPIError as e:logger.warning(f"Could not get token for connector '{mcp_connector}': {e}. Proceeding without token.")
					else:logger.warning(f"Connector '{mcp_connector}' not found for MCP '{mcp_name}'.")
				logger.info(f"Connecting to remote HTTP MCP '{mcp_name}' at URL: {eval_mcp_url}");logger.debug(f"  [MCP HTTP Headers]: {http_headers}");client_transport=mcp_config.get(F,G)
				if client_transport==L:client_transport=G
				client_config={M:{mcp_name:{F:client_transport,_X:eval_mcp_url}}}
				if http_headers:client_config[M][mcp_name]['headers']=http_headers
				session_context=Client(client_config,timeout=18e1)
			elif is_stdio_call:
				command=self._evaluate_f_string(self._clean_text(mcp_config.get(_A0,'')),current_var)
				if not command or command.lower()=='python':command=sys.executable
				args=[self._evaluate_f_string(self._clean_text(arg),current_var)for arg in mcp_config.get(_I,[])]
				if command==sys.executable and args:
					script_path_arg=args[0];absolute_script_path=os.path.abspath(script_path_arg)
					if not os.path.exists(absolute_script_path):error_msg=f"MCP script file not found at path: {absolute_script_path}. Please check the 'args' in your MCP configuration for '{mcp_name}' and ensure the file exists.";logger.error(error_msg);return current_var,error_msg
				mcp_env_from_config=self._evaluate_vars_in_structure(mcp_config.get(_A1,{}),current_var);final_env=_A
				if mcp_env_from_config:final_env=os.environ.copy();str_mcp_env={k:str(v)for(k,v)in mcp_env_from_config.items()};final_env.update(str_mcp_env)
				cwd=self._evaluate_f_string(self._clean_text(mcp_config.get('cwd','')),current_var);transport=StdioTransport(command=command,args=args,env=final_env,cwd=cwd if cwd else _A,keep_alive=mcp_config.get('keepAlive',_D));session_context=Client(transport,timeout=18e1)
			else:error_msg=f"Unsupported or ambiguous transport for MCP '{mcp_name}'. Configure URL for http or command for stdio.";logger.error(error_msg);return current_var,error_msg
			if session_context:
				async with session_context as session:
					gemini_client=self._genai_client
					if not gemini_client:return current_var,'Error: Gemini AI client is not configured. Required for MCP.'
					mcp_tools,mcp_resources,mcp_prompts=[],[],[]
					for attempt in range(5):
						try:
							mcp_tools_resp=await session.list_tools()
							if hasattr(mcp_tools_resp,_O)and mcp_tools_resp.tools or isinstance(mcp_tools_resp,list)and mcp_tools_resp:mcp_tools=mcp_tools_resp.tools if hasattr(mcp_tools_resp,_O)else mcp_tools_resp;logger.info(f"MCP '{mcp_name}' is ready with tools after {attempt+1} attempt(s).");break
						except Exception as e:logger.warning(f"Could not list tools from MCP '{mcp_name}' on attempt {attempt+1}. Error: {e}")
						if is_stdio_call:await asyncio.sleep(.2*(attempt+1))
						else:break
					try:
						mcp_resources_resp=await session.list_resources()
						if hasattr(mcp_resources_resp,'resources')and mcp_resources_resp.resources:mcp_resources=mcp_resources_resp.resources
						elif isinstance(mcp_resources_resp,list):mcp_resources=mcp_resources_resp
					except Exception as e:logger.warning(f"Could not list resources from MCP '{mcp_name}'. This may be expected. Error: {e}")
					try:
						mcp_prompts_resp=await session.list_prompts()
						if hasattr(mcp_prompts_resp,'prompts')and mcp_prompts_resp.prompts:mcp_prompts=mcp_prompts_resp.prompts
						elif isinstance(mcp_prompts_resp,list):mcp_prompts=mcp_prompts_resp
					except Exception as e:logger.warning(f"Could not list prompts from MCP '{mcp_name}'. This may be expected. Error: {e}")
					llm_tools=[]
					if mcp_tools:llm_tools.append(FunctionDeclaration(name=H,description='Calls a specific tool available on the MCP server.',parameters={_F:_p,_AK:{B:{_F:_AN,_AM:[t.name for t in mcp_tools],_K:'The name of the tool to call.'},A:{_F:_p,_K:'The arguments for the tool as a JSON object.'}},_AL:[B,A]}))
					if mcp_resources:llm_tools.append(FunctionDeclaration(name=I,description='Reads a specific resource (e.g., a file or data entry) from the MCP server.',parameters={_F:_p,_AK:{C:{_F:_AN,_AM:[r.uri for r in mcp_resources],_K:'The URI of the resource to read.'}},_AL:[C]}))
					if mcp_prompts:llm_tools.append(FunctionDeclaration(name=J,description='Gets a pre-defined, rendered prompt template from the MCP server.',parameters={_F:_p,_AK:{D:{_F:_AN,_AM:[p.name for p in mcp_prompts],_K:'The name of the prompt to get.'},E:{_F:_p,_K:'The arguments for rendering the prompt template.'}},_AL:[D]}))
					if not llm_tools:return current_var,f"Error: MCP '{mcp_name}' has no tools, resources, or prompts to use."
					logger.info(f"Asking LLM to choose a mcp activity: '{current_prompt_text[:100]}...'");model_provider=prompt_config.get(_At,_c)if prompt_config else _c;model_to_use=_Au
					if prompt_config and prompt_config.get(_V):model_to_use=prompt_config.get(_V)
					selection_prompt_text=f"For {mcp_name}, decide which available tool, resource or prompt to use based on the user's request: '{user_input}' and consider the description {mcp_description} and the available parameters and arguments: {mcp_params} {mcp_args}. Which should be used? Please select the closest match to the user's request and available variables. Return only the name of the selected tool, resource or prompt."
					if model_provider==_c:config=google_genai_types.GenerateContentConfig(tools=[Tool(function_declarations=llm_tools)],temperature=mcp_config.get('initialTemperature',.5));selected_option,_,function_calls=await self._get_gemini_response_async(model_to_use,[selection_prompt_text],config);llm_response_text=selected_option
					else:logger.error(f"Unsupported model provider '{model_provider}' for MCP '{mcp_name}'. Only 'google' is supported.");return current_var,f"Error: Unsupported model provider '{model_provider}' for MCP '{mcp_name}'."
					mcp_result=_A;chosen_call=_A
					if function_calls:chosen_call=function_calls[0]
					elif selected_option:
						selected_name=selected_option.strip()
						if any(t.name==selected_name for t in mcp_tools):chosen_call={_B:H,_I:{B:selected_name,A:mcp_params}}
						elif any(r.uri==selected_name for r in mcp_resources):chosen_call={_B:I,_I:{C:selected_name}}
						elif any(p.name==selected_name for p in mcp_prompts):chosen_call={_B:J,_I:{D:selected_name,E:mcp_params}}
					if chosen_call:
						handler_name=chosen_call.get(_B);handler_args=chosen_call.get(_I,{})
						if handler_name==H:
							tool_to_call=handler_args.get(B);final_params=mcp_params.copy()
							if handler_args.get(A):final_params.update(handler_args.get(A,{}))
							mcp_result=await self._call_mcp_tool(session,tool_to_call,final_params)
						elif handler_name==I:resource_to_read=handler_args.get(C);mcp_result=await self._read_mcp_resource(session,resource_to_read)
						elif handler_name==J:
							prompt_to_get=handler_args.get(D);final_prompt_args=mcp_params.copy()
							if handler_args.get(E):final_prompt_args.update(handler_args.get(E,{}))
							mcp_result=await self._get_mcp_prompt(session,prompt_to_get,final_prompt_args)
						else:logger.warning(f"LLM chose an unknown handler: {handler_name}");mcp_result=f"Error: AI tried to call an unknown handler '{handler_name}'."
					else:logger.warning(f"LLM response '{selected_option}' did not result in a valid action.");mcp_result=selected_option
					final_result_value=mcp_result
					if hasattr(mcp_result,_A2)and getattr(mcp_result,_A2)is not _A:final_result_value=getattr(mcp_result,_A2)
					elif hasattr(mcp_result,_C)and getattr(mcp_result,_C)is not _A:final_result_value=getattr(mcp_result,_C)
					mcp_result_str=json.dumps(final_result_value,indent=2)if isinstance(final_result_value,(dict,list))else str(final_result_value)if final_result_value is not _A else _A;mcp_result_variable=mcp_config.get(_Y)
					if mcp_result_variable:current_var[mcp_result_variable]=final_result_value
					if prompt_resp_var_name:current_var[prompt_resp_var_name]=final_result_value
					return current_var,mcp_result_str
			return current_var,f"Error: Could not establish session for MCP '{mcp_name}'."
		except Exception as e:logger.error(f"Error during MCP execution for '{mcp_name}': {e}",exc_info=_D);return current_var,f"Error in MCP execution: {e}"
	@staticmethod
	async def _call_mcp_tool(session,tool_name,args):
		'Helper to call a tool on the MCP session.'
		try:
			result=await session.call_tool(tool_name,args)
			if hasattr(result,_C)and result.data:return result.data
			if hasattr(result,_A2)and result.result is not _A:return result.result
			return result
		except Exception as e:logger.error(f"Error calling MCP tool '{tool_name}': {e}");return{_h:f"Failed to call tool '{tool_name}': {e}"}
	@staticmethod
	async def _read_mcp_resource(session,resource_uri):
		'Helper to read a resource from the MCP session.'
		try:
			result=await session.get_resource(resource_uri)
			if result and isinstance(result,list)and hasattr(result[0],_P):return result[0].text
			return result
		except Exception as e:logger.error(f"Error reading MCP resource '{resource_uri}': {e}");return{_h:f"Failed to read resource '{resource_uri}': {e}"}
	@staticmethod
	async def _get_mcp_prompt(session,prompt_name,args):
		'Helper to get a prompt from the MCP session.'
		try:
			result=await session.get_prompt(prompt_name,args)
			if hasattr(result,_C)and result.data:return result.data
			return result
		except Exception as e:logger.error(f"Error getting MCP prompt '{prompt_name}': {e}");return{_h:f"Failed to get prompt '{prompt_name}': {e}"}
	@staticmethod
	async def _execute_tool_calls(function_calls,session):
		"\n        Executes a list of function calls requested by the Gemini model via the session.\n\n        Args:\n            function_calls: A list of FunctionCall objects from the model's response.\n            session: The session object capable of executing tools via `call_tool`.\n\n        Returns:\n            A list of Part objects, each containing a FunctionResponse corresponding\n            to the execution result of a requested tool call.\n        ";tool_response_parts=[]
		for func_call in function_calls:
			tool_name=func_call.name;args=dict(func_call.args)if func_call.args else{};tool_result_payload:0
			try:
				tool_result=await session.call_tool(tool_name,args);result_text=''
				if hasattr(tool_result,_Q)and tool_result.content and hasattr(tool_result.content[0],_P):result_text=tool_result.content[0].text or''
				if hasattr(tool_result,'isError')and tool_result.isError:error_message=result_text or f"Tool '{tool_name}' failed without specific error message.";tool_result_payload={_h:error_message}
				else:tool_result_payload={_A2:result_text}
			except Exception as e:error_message=f"Tool execution framework failed: {type(e).__name__}: {e}";tool_result_payload={_h:error_message}
			tool_response_parts.append(google_genai_types.Part.from_function_response(name=tool_name,response=tool_result_payload))
		return tool_response_parts
	async def _run_agent_loop(self,prompt,client,session,model_id,max_tool_turns,initial_temperature,tool_call_temperature,mcp_description=_A):
		'\n        Runs a multi-turn conversation loop with a Gemini model, handling tool calls \n        that occur after tool execution.\n\n        This function orchestrates the interaction between a user prompt, a Gemini\n        model capable of function calling, and a session object that provides\n        and executes tools. It handles the cycle of:\n        1. Sending the user prompt (and conversation history) to the model.\n        2. If the model requests tool calls, executing them via the `session`.\n        3. Sending the tool execution results back to the model.\n        4. Repeating until the model provides a text response or the maximum\n        number of tool execution turns is reached.\n\n        Args:\n            prompt: The initial user prompt to start the conversation.\n            client: An initialized Gemini GenerativeModel client object\n\n            session: An active session object responsible for listing available tools\n                    via `list_tools()` and executing them via `call_tool(tool_name, args)`.\n                    It\'s also expected to have an `initialize()` method.\n            model_id: The identifier of the Gemini model to use (e.g., "gemini-2.0-flash").\n            max_tool_turns: The maximum number of consecutive turns dedicated to tool calls\n                            before forcing a final response or exiting.\n            initial_temperature: The temperature setting for the first model call.\n            tool_call_temperature: The temperature setting for subsequent model calls\n                                that occur after tool execution.\n            mcp_description: An optional high-level description of the MCP\'s purpose,\n                             used as a system instruction for the model.\n\n        Returns:\n            The final text response from the Gemini model after the\n            conversation loop concludes (either with a text response or after\n            reaching the max tool turns). An empty string may be returned on error or no response.\n\n        Raises:\n            ValueError: If the session object does not provide any tools.\n            Exception: Can potentially raise exceptions from the underlying API calls\n                    or session tool execution if not caught internally by `_execute_tool_calls`.\n        ';contents=[google_genai_types.Content(role=_a,parts=[google_genai_types.Part(text=prompt)])]
		if hasattr(session,'initialize')and callable(session.initialize):await session.initialize()
		else:logger.debug('Session object does not have an initialize() method, proceeding anyway.')
		session_tool_list=await session.list_tools()
		if not session_tool_list or not session_tool_list.tools:raise ValueError('No tools provided by the session. Agent loop cannot proceed.')
		gemini_tool_config=google_genai_types.Tool(function_declarations=[types.FunctionDeclaration(name=tool.name,description=tool.description,parameters=tool.inputSchema)for tool in session_tool_list.tools]);base_gen_config_dict={_O:[gemini_tool_config]}
		if mcp_description:base_gen_config_dict['system_instruction']=mcp_description
		initial_config=google_genai_types.GenerateContentConfig(temperature=initial_temperature,**base_gen_config_dict);response=await client.aio.models.generate_content(model=model_id,contents=contents,config=initial_config)
		if not response.candidates:return''
		contents.append(response.candidates[0].content);turn_count=0;latest_content=response.candidates[0].content;has_function_calls=any(part.function_call for part in latest_content.parts)
		while has_function_calls and turn_count<max_tool_turns:
			turn_count+=1;function_calls_to_execute=[part.function_call for part in latest_content.parts if part.function_call];tool_response_parts=await self._execute_tool_calls(function_calls_to_execute,session);contents.append(google_genai_types.Content(role=_Aw,parts=tool_response_parts));subsequent_config=google_genai_types.GenerateContentConfig(temperature=tool_call_temperature,**base_gen_config_dict);response=await client.aio.models.generate_content(model=model_id,contents=contents,config=subsequent_config)
			if not response.candidates:break
			latest_content=response.candidates[0].content;contents.append(latest_content);has_function_calls=any(part.function_call for part in latest_content.parts)
			if not has_function_calls:logger.debug('Model response contains text, no further tool calls requested this turn.')
		if turn_count>=max_tool_turns and has_function_calls:logger.debug(f"Maximum tool turns ({max_tool_turns}) reached. Exiting loop even though function calls might be pending.")
		elif not has_function_calls:logger.debug('Tool calling loop finished naturally (model provided text response).')
		logger.debug('Agent loop finished. Returning final response.');final_text_response=''
		if response.candidates:
			try:final_text_response=''.join(part.text for part in response.candidates[0].content.parts if hasattr(part,_P)and part.text)
			except(AttributeError,IndexError):logger.debug('Could not extract final text from response parts.')
		return final_text_response
	async def _run_api_action(self,current_var,api_name):
		B='GET';A='content_type'
		if current_var.get(_H):logger.debug(f"Run API | {api_name}")
		api_config=self._get_api_details(api_name)
		if not api_config:logger.warning(f"API configuration '{api_name}' not found.");return current_var,_A
		headers={}
		if api_config.get(_Av):
			try:headers.update(json.loads(api_config[_Av]))
			except json.JSONDecodeError:logger.warning(f"Invalid JSON in API header for {api_name}")
		else:headers[_q]=_A3
		if api_config.get(A):headers[_Z]=api_config[A]
		if api_config.get(_T):
			connector_config=self._get_connector_details(api_config[_T])
			if connector_config:
				try:
					token=await self._get_token_for_connector(connector_config)
					if token:headers[_L]=token
				except PinionAIAPIError as e:logger.warning(f"Could not get token for connector '{api_config[_T]}': {e}. Proceeding without token.")
			else:logger.warning(f"Connector '{api_config[_T]}' not found for API '{api_name}'.")
		method=api_config.get(_d,B).upper()
		try:
			if method in['POST','PUT']:current_var,_,_,final_response_message=await self._generic_api_post_put(current_var,api_config,headers,method)
			elif method==B:current_var,_,_,final_response_message=await self._generic_api_get(current_var,api_config,headers)
			else:logger.warning(f"Unsupported API method '{method}' for API '{api_name}'.")
		except PinionAIAPIError as e:
			logger.error(f"Failed to execute API action '{api_name}': {e}")
			if api_config.get(_Y):current_var[api_config[_Y]]={_h:str(e)}
		return current_var,final_response_message
	def _run_parser_action(self,current_var,parser_name):
		if current_var.get(_H):logger.debug(f"Run Parser | {parser_name}")
		parser_config=self._get_parser_details(parser_name)
		if not parser_config:logger.warning(f"Parser configuration '{parser_name}' not found.");return current_var,_A
		source_var_name=parser_config.get(_BQ)
		if not source_var_name or source_var_name not in current_var:logger.warning(f"Parser source variable '{source_var_name}' not found in var for parser '{parser_name}'.");return current_var
		parser_source_data=current_var[source_var_name];parser_type=parser_config.get(_F);var_map=parser_config.get('varNameToValueMap',{})
		try:
			if parser_type==_A4:
				json_data=json.loads(parser_source_data)if isinstance(parser_source_data,str)else parser_source_data
				for(out_var_name,json_path_expr_str)in var_map.items():match=jsonpath_parse(json_path_expr_str).find(json_data);current_var[out_var_name]=match[0].value if match else _A
			elif parser_type=='xml':
				xml_data=xmltodict.parse(parser_source_data)
				for(out_var_name,xml_path_str)in var_map.items():
					value=xml_data
					try:
						for key_part in xml_path_str.split('.'):value=value.get(key_part)
						current_var[out_var_name]=value
					except AttributeError:current_var[out_var_name]=_A
			elif parser_type=='csv':
				csv_io=StringIO(parser_source_data);df=pd.read_csv(csv_io)
				for(out_var_name,column_name)in var_map.items():current_var[out_var_name]=df[column_name].tolist()if column_name in df.columns else _A
			elif parser_type==_P:
				method=parser_config.get(_d);delimiter=parser_config.get('delimiter')
				if method=='split'and delimiter is not _A:
					parts=str(parser_source_data).split(delimiter)
					for(out_var_name,index_str)in var_map.items():
						try:idx=int(index_str);current_var[out_var_name]=parts[idx].strip()if 0<=idx<len(parts)else _A
						except(ValueError,IndexError):current_var[out_var_name]=_A
				elif method=='partition'and delimiter is not _A:
					parts=str(parser_source_data).partition(delimiter)
					for(out_var_name,index_str)in var_map.items():
						try:idx=int(index_str);current_var[out_var_name]=parts[idx].strip()if 0<=idx<3 else _A
						except(ValueError,IndexError):current_var[out_var_name]=_A
				elif method=='regex':
					for(out_var_name,pattern_str)in var_map.items():match=re.search(pattern_str,str(parser_source_data));current_var[out_var_name]=match.group(0)if match else _A
				else:logger.warning(f"Unknown text parsing method '{method}' or missing delimiter for parser '{parser_name}'.")
			else:logger.warning(f"Unknown parser type '{parser_type}' for parser '{parser_name}'.")
		except Exception as e:
			logger.error(f"Error during parsing with '{parser_name}' on source '{source_var_name}': {e}",exc_info=_D)
			for out_var_name in var_map.keys():current_var[out_var_name]=_A
		return current_var,_A
	def _run_merger_action(self,current_var,merger_name):
		if current_var.get(_H):logger.debug(f"Run Merger | {merger_name}")
		merger_config=self._get_merger_details(merger_name)
		if not merger_config:logger.warning(f"Merger configuration '{merger_name}' not found.");return current_var,_A
		dest_var_name=merger_config.get(_BR)
		if not dest_var_name:logger.warning(f"Merger destination variable not specified for merger '{merger_name}'.");return current_var,_A
		template_str=self._clean_text(merger_config.get('mergerTemplate',''));merged_output_str=self._evaluate_f_string(template_str,current_var);output_type=merger_config.get('outputType',_P)
		try:
			if output_type==_A4:current_var[dest_var_name]=json.loads(merged_output_str)
			elif output_type=='xml':current_var[dest_var_name]=xmltodict.parse(merged_output_str)
			elif output_type=='csv':current_var[dest_var_name]=pd.read_csv(StringIO(merged_output_str))
			else:current_var[dest_var_name]=merged_output_str
		except Exception as e:logger.error(f"Error processing merged output for type '{output_type}' in merger '{merger_name}': {e}");current_var[dest_var_name]=_A
		return current_var,_A
	async def _run_script_action(self,var,script_name):
		if var.get(_H):logger.debug(f"Run Script | {script_name}")
		script_config=self._get_script_details(script_name)
		if not script_config:logger.warning(f"Script configuration '{script_name}' not found.");return var,_A
		script_type=script_config.get(_F);script_code=script_config.get(_U);result_var_name=script_config.get(_Y)
		if not script_code:logger.warning(f"Script body is empty for script '{script_name}'.");return var,_A
		try:
			if script_type=='javascript':
				if not MiniRacer:raise PinionAIConfigurationError("The 'py-mini-racer' library is required to run JavaScript scripts. Please install it with 'pip install py-mini-racer'.")
				ctx=MiniRacer();pyvar=var.copy()
				try:ctx.eval(script_code)
				except Exception as e:logger.error(f"Error adding function into JS: {e}",exc_info=_D);return var,_A
				try:
					script_result=ctx.call('main',pyvar)
					if script_result and isinstance(script_result,str):
						try:script_result_obj=json.loads(script_result)
						except Exception:script_result_obj=script_result
					else:script_result_obj=script_result
					if result_var_name and script_result_obj is not _A:var[result_var_name]=script_result_obj
				except Exception as e:logger.error(f"Error executing JS script: {e}",exc_info=_D)
				return var,_A
			elif script_type=='python':
				local_script_vars=var.copy();logger.warning('Executing Python scripts from the database is a security risk and is currently disabled.');exec(script_code,{_BS:{}},local_script_vars)
				if result_var_name and result_var_name in local_script_vars:var[result_var_name]=local_script_vars[result_var_name]
			else:logger.warning(f"Unsupported script type '{script_type}' for script '{script_name}'.")
		except Exception as e:logger.error(f"Error executing script '{script_name}': {e}",exc_info=_D)
		return var,_A
	async def _run_rule_action(self,current_var,rule_name,user_input):
		if current_var.get(_H):logger.debug(f"Run Rule | {rule_name}")
		rule_config=self._get_rule_details(rule_name)
		if not rule_config:logger.warning(f"Rule configuration '{rule_name}' not found.");return current_var,_A
		expr=rule_config.get('condition')
		if not expr:logger.warning(f"Rule '{rule_name}' has no 'rule_condition' defined.");return current_var,_A
		result=await self._evaluate_rule(expr,current_var);logger.info(f"Rule '{rule_name}' triggered and evaluated. Result: {result}")
		if(result_variable:=rule_config.get(_Y)):
			self.var[result_variable]=result
			if current_var.get(_H):logger.debug(f"Rule '{rule_name}' result ({result}) stored in var['{result_variable}']")
		outcome_key=_A
		if result is _D:outcome_key='trueOutcome';outcome_key_type='trueType'
		elif result is _G:outcome_key='falseOutcome';outcome_key_type='falseType'
		step_response=_A
		if outcome_key:
			if(outcome_statement:=rule_config.get(outcome_key)):
				outcome_type=rule_config.get(outcome_key_type)
				if current_var.get(_H):logger.debug(f"Executing {outcome_type} '{outcome_key}' for rule '{rule_name}'")
				current_var,step_response=await self._execute_outcome(outcome_statement,outcome_type,user_input=user_input)
		return current_var,step_response
	async def _evaluate_rule(self,expr,var):
		'\n        Evaluates a rule expression string by first formatting it with variable data.\n\n        The expression string can contain f-string-like placeholders that reference\n        the \'var\' dictionary, which holds the provided variable data.\n\n        Example:\n            expr = "{var[\'value\']} > 10 and \'{var[\'status\']}\' == \'active\'"\n            var = {"value": 20, "status": "active"}\n            result = evaluate_rule(expr, var)  # result will be True\n\n        Args:\n            expr: The rule expression string to evaluate.\n            var: A dictionary of variables to be used in the expression.\n\n        Returns:\n            The result of the evaluated expression. Returns None if an error occurs\n            during formatting or evaluation.\n        '
		if not isinstance(expr,str):logger.warning(f"Rule expression is not a string: {expr}");return
		formatted_expr=''
		try:
			cleaned_expr=self._clean_text(expr);formatted_expr=self._evaluate_f_string(cleaned_expr,var)
			try:return eval(formatted_expr,{_BS:{}},{_w:var})
			except Exception as e:logger.error(f"Error evaluating rule expression: '{expr}'. Formatted: '{formatted_expr}'. Error: {e}");return
		except KeyError as e:logger.error(f"Error accessing variable in rule expression: '{expr}'. Missing key: {e}.");return
		except Exception as e:logger.error(f"Error evaluating rule expression: '{expr}'. Formatted: '{formatted_expr}'. Error: {e}");return
	async def _execute_outcome(self,outcome_statement,outcome_type,user_input):
		'\n        Executes an outcome statement.\n\n        An outcome can:\n        1. "Set a variable": Set a variable to a value or another variable.\n        2. "Set a final response": Set a final response to terminate execution.\n        3. "Execute a flow": Trigger an action flow.\n        4. "Set Authorization":  Set self.is_authorized \n\n        Args:\n            statement: An outcome statement dictionary.\n            var: The dictionary of variables.\n\n        Returns:\n            A var and step_response if one is set, otherwise None.\n        ';A='set';step_response=_A
		if outcome_type=='Set a variable'and outcome_statement.get(A):
			set_config=outcome_statement.get(A);variable_to_set=set_config.get('variable');value_to_set=set_config.get(_Ap)
			if variable_to_set and value_to_set:template_str=self._clean_text(value_to_set);resolved_value=self._evaluate_f_string(template_str,self.var);self.var[variable_to_set]=resolved_value
			else:logger.warning(f"Outcome 'set' statement missing 'value'.")
			return self.var,step_response
		elif outcome_type=='Set a response':
			response_template=self._clean_text(outcome_statement.get(_AO,''));step_response=self._evaluate_f_string(response_template,self.var)
			if self.var.get(_H):logger.debug(f"Setting step response: {step_response}")
			return self.var,step_response
		elif outcome_type=='Execute a flow':
			if outcome_statement:
				self.var,action_response=await self._process_routing(self.var,outcome_statement,user_input=user_input)
				if action_response:step_response=action_response
		elif outcome_type=='Set Authentication':
			auth_value=outcome_statement.get(_Ap)
			if auth_value.lower()=='true':self.authorized=_D
			if auth_value.lower()=='false':self.authorized=_G
		return self.var,step_response
	async def _run_delivery_action(self,current_var,delivery_name):
		C='\\s+';B='<[^>]+>';A='email'
		if current_var.get(_H):logger.debug(f"Run Delivery | {delivery_name}")
		delivery_config=self._get_delivery_details(delivery_name)
		if not delivery_config or not delivery_config.get('to'):logger.warning(f"Delivery '{delivery_name}' not configured properly or 'to' field missing.");return current_var,_A
		template_eval_vars=current_var.copy()
		for(key,value)in template_eval_vars.items():
			if self._is_likely_markdown(value):
				try:template_eval_vars[key]=markdown.markdown(value)
				except Exception as e:logger.error(f"Error converting markdown for delivery var['{key}']: {e}")
		to_address=self._evaluate_f_string(self._clean_line(delivery_config['to']),template_eval_vars);html_body_template=self._clean_text(delivery_config.get(_U,''));html_body_content=self._evaluate_f_string(html_body_template,template_eval_vars);plain_text_body=re.sub(B,' ',html_body_content);plain_text_body=re.sub(C,' ',plain_text_body).strip();from_address_template=delivery_config.get('from');from_address=self._evaluate_f_string(self._clean_line(from_address_template),template_eval_vars)if from_address_template else self._email_from_address;subject_template=delivery_config.get(_Ax,'Your AI Delivery');subject=self._evaluate_f_string(self._clean_line(subject_template),template_eval_vars);cc_template=delivery_config.get('cc');cc_address=self._evaluate_f_string(self._clean_line(cc_template),template_eval_vars)if cc_template else _A;bcc_template=delivery_config.get('bcc');bcc_address=self._evaluate_f_string(self._clean_line(bcc_template),template_eval_vars)if bcc_template else _A;reply_to_template=delivery_config.get('replyTo');reply_to_address=self._evaluate_f_string(self._clean_line(reply_to_template),template_eval_vars)if reply_to_template else _A;delivery_type=delivery_config.get(_F);delivery_method=delivery_config.get(_d);final_response_message=_A;token=_A;headers={}
		if delivery_config.get(_T):
			connector_config=self._get_connector_details(delivery_config[_T])
			if connector_config:
				try:
					token=await self._get_token_for_connector(connector_config)
					if token:headers[_L]=token
				except PinionAIAPIError as e:logger.warning(f"Could not get token for connector '{delivery_config[_T]}': {e}. Proceeding without token.")
			else:logger.warning(f"Connector '{delivery_config[_T]}' not found for delivery '{delivery_name}'.")
		if delivery_type==A and delivery_method=='SendGrid':await self._sendgrid_email(plain_text_body,html_body_content,to_address,subject,from_address,cc_address,bcc_address,reply_to_address);logger.info(f"Email sent to {to_address} for delivery '{delivery_name}' via SendGrid.")
		elif delivery_type==A and delivery_method=='infobip':await self._infobip_send_email(plain_text_body,html_body_content,to_address,subject,from_address,token,cc_address,bcc_address,reply_to_address);logger.info(f"Email sent to {to_address} for delivery '{delivery_name}' via Infobip.")
		elif delivery_type==A and delivery_method=='Microsoft Graph API':await self._ms_graph_send_email(plain_text_body,html_body_content,to_address,subject,from_address,token,cc_address,bcc_address,reply_to_address)
		elif delivery_type=='sms'and delivery_method=='Twilio':sms_body_template=self._clean_text(delivery_config.get(_U,''));sms_intermediate_content=self._evaluate_f_string(sms_body_template,template_eval_vars);sms_to_send=re.sub(B,' ',sms_intermediate_content);sms_to_send=re.sub(C,' ',sms_to_send).strip();await self._twilio_sms_message(sms_to_send,to_address,from_address);logger.info(f"Twilio SMS sent to {to_address} for delivery '{delivery_name}'.")
		else:logger.warning(f"Unsupported delivery type/method: {delivery_type}/{delivery_method} for '{delivery_name}'.")
		delivery_response=delivery_config.get('deliveryResponseMessage','')
		if delivery_response:final_response_message=self._evaluate_f_string(delivery_response,template_eval_vars)
		return current_var,final_response_message
	async def _run_journey_action(self,current_var,action_details):
		"Handles a 'journey' type action, from either an intent or an action entity.";B='configuration';A='payment_description';action_key_var_name=action_details.get(_BT);action_key=current_var.get(action_key_var_name)if action_key_var_name else _A
		if not action_key:logger.warning(f"Journey action '{action_details.get(_B)}' requires a value from variable '{action_key_var_name}', but it was not found or is empty in 'var'.");return current_var,'Configuration error for journey action.'
		delivery_method=action_details.get(_Ay);language=action_details.get(_b);_,self.unique_id,self.phone_number=format_phone(self.phone_number);json_payload={_Ai:action_key,_m:{_d:delivery_method,_e:self.phone_number},_Aj:{_Ak:self.unique_id,_e:self.phone_number},_E:{_Al:self._session_id},_b:language}
		if current_var.get(_n):json_payload[_Am]=current_var[_n]
		if action_details.get(_Az)=='credit card payment'and current_var.get(A):json_payload[B]={'credit-card-payment':{'currency':current_var.get('payment_currency'),'lineItems':[{'title':current_var.get(A),'amount':current_var.get('payment_amount'),'quantity':current_var.get('payment_quantity')}]}}
		if action_details.get(_Az)=='one time passcode':json_payload[B]={'random-code':{'code':'6'}}
		if action_details.get(_Ay)=='voice':json_payload[_m]={_d:delivery_method,_e:self.phone_number,'callOperator':'twilio'}
		execution_id,execution_url,error_msg=await self._journey_send_pipeline(current_var,json_payload,delivery_method);final_response=_A
		if error_msg:final_response=error_msg
		elif execution_url:final_response=execution_url
		else:
			logger.info(f"A {action_details.get(_B)} {delivery_method} request has been sent.");is_completed,fulfillment_msg=await self._journey_session_pipeline_status_check(self._session_id,current_var,action_key,120)
			if is_completed:
				response_msg_template=self._clean_text(action_details.get(_f))
				if response_msg_template:final_response=self._evaluate_f_string(response_msg_template,current_var)
				else:final_response=fulfillment_msg
			else:final_response=fulfillment_msg
		return current_var,final_response
	def _run_transfer_action(self,current_var,action_details):
		"Handles a 'transfer' type action."
		if current_var.get(_AW):
			current_time_utc=datetime.datetime.now(tz=zoneinfo.ZoneInfo('UTC'));self.transfer_requested=current_time_utc.isoformat();current_var['transfer_requested']=self.transfer_requested;sms_message=''
			if current_var.get(_AX):passkey=self._generate_password(6);current_var['transferPasskey']=passkey;sms_message=f"Your agent will validate themselves with the following shared passkey: {passkey}"
			response_msg_template=action_details.get(_f)
			if response_msg_template:final_response=self._evaluate_f_string(self._clean_text(response_msg_template),current_var)
			else:final_response=f"You have requested to transfer. Please let the agent know your question. {sms_message}"
		else:final_response='Sorry, I am unable to transfer you.'
		return current_var,final_response
	def _map_to_standard_action_details(self,data):'Maps fields from an intent or action entity to a standard action_details dictionary.';return{_B:data.get(_B),_An:data.get('actionType'),_BT:data.get(_v),_Ay:data.get(_Ae),_b:data.get(_b),_Az:data.get('actionEvent'),_f:data.get('actionResponseMessage'),_Ao:data.get(_Af,{})}
	async def _run_action_action(self,current_var,action_name,final_response_from_caller=_A,user_input=_A):
		if current_var.get(_H):logger.debug(f"Run Action | {action_name}")
		action_entity_data=self._get_action_details(action_name)
		if not action_entity_data:logger.warning(f"Action '{action_name}' not found in agent configuration.");return current_var,_A
		action_details=self._map_to_standard_action_details(action_entity_data);action_type=action_details.get(_An,'general')
		if action_type=='journey':
			if current_var.get(_H):logger.debug(f"Executing journey action '{action_name}'")
			return await self._run_journey_action(current_var,action_details)
		elif action_type=='transfer':
			if current_var.get(_H):logger.debug(f"Executing transfer action '{action_name}'")
			return self._run_transfer_action(current_var,action_details)
		action_flow=action_details.get(_Ao,{});action_produced_final_response=_A
		if action_flow:
			if current_var.get(_H):logger.debug(f"Executing actionFlow for '{action_name}': {action_flow}")
			current_var,action_produced_final_response=await self._process_routing(current_var,action_flow,final_response_from_caller,user_input=user_input)
		else:logger.warning(f"Action '{action_name}' has no 'actionFlow' to execute.")
		if action_details.get(_f):
			response_msg_template=self._clean_text(action_details[_f]);generated_response=self._evaluate_f_string(response_msg_template,current_var);current_var['last_action_response']=generated_response;action_produced_final_response=generated_response
			if current_var.get(_H):logger.debug(f"Action '{action_name}' generated a response and stored it in 'last_action_response': {generated_response}")
		return current_var,action_produced_final_response
	async def _gcs_write(self,bucket_name,file_path,content_bytes,connector_name):
		'Handles writing a file to Google Cloud Storage.'
		if not storage:raise ImportError(_BU)
		gcs_client=_A
		if connector_name:
			conn_config=self._get_connector_details(connector_name)
			if conn_config and conn_config.get(_k)==_Ab:sa_info=json.loads(conn_config.get(_l,'{}'));gcs_client=storage.Client.from_service_account_info(sa_info);logger.info(f"Using GCS service account from connector '{connector_name}'.")
		if not gcs_client:gcs_client=storage.Client();logger.info(_BV)
		bucket=gcs_client.bucket(bucket_name);blob=bucket.blob(file_path);await asyncio.to_thread(blob.upload_from_string,content_bytes);logger.info(f"Successfully wrote to GCS: gs://{bucket_name}/{file_path}")
	async def _gcs_read(self,bucket_name,file_path,connector_name):
		'Handles reading a file from Google Cloud Storage.'
		if not storage:raise ImportError(_BU)
		gcs_client=_A
		if connector_name:
			conn_config=self._get_connector_details(connector_name)
			if conn_config and conn_config.get(_k)==_Ab:sa_info=json.loads(conn_config.get(_l,'{}'));gcs_client=storage.Client.from_service_account_info(sa_info);logger.info(f"Using GCS service account from connector '{connector_name}'.")
		if not gcs_client:gcs_client=storage.Client();logger.info(_BV)
		bucket=gcs_client.bucket(bucket_name);blob=bucket.blob(file_path);read_content_bytes=await asyncio.to_thread(blob.download_as_bytes);logger.info(f"Successfully read from GCS: gs://{bucket_name}/{file_path}");return read_content_bytes
	async def _s3_write(self,bucket_name,file_path,content_bytes,connector_name):
		'Handles writing a file to AWS S3.'
		if not boto3:raise ImportError(_BW)
		s3_client=_A
		if connector_name:
			conn_config=self._get_connector_details(connector_name)
			if conn_config and conn_config.get(_k)=='aws_iam':s3_client=boto3.client('s3',aws_access_key_id=conn_config.get(_A_),aws_secret_access_key=conn_config.get(_l));logger.info(f"Using AWS IAM credentials from connector '{connector_name}'.")
		if not s3_client:s3_client=boto3.client('s3');logger.info(_BX)
		await asyncio.to_thread(s3_client.put_object,Bucket=bucket_name,Key=file_path,Body=content_bytes);logger.info(f"Successfully wrote to S3: s3://{bucket_name}/{file_path}")
	async def _s3_read(self,bucket_name,file_path,connector_name):
		'Handles reading a file from AWS S3.'
		if not boto3:raise ImportError(_BW)
		s3_client=_A
		if connector_name:
			conn_config=self._get_connector_details(connector_name)
			if conn_config and conn_config.get(_k)=='aws_iam':s3_client=boto3.client('s3',aws_access_key_id=conn_config.get(_A_),aws_secret_access_key=conn_config.get(_l));logger.info(f"Using AWS IAM credentials from connector '{connector_name}'.")
		if not s3_client:s3_client=boto3.client('s3');logger.info(_BX)
		response=await asyncio.to_thread(s3_client.get_object,Bucket=bucket_name,Key=file_path);read_content_bytes=response['Body'].read();logger.info(f"Successfully read from S3: s3://{bucket_name}/{file_path}");return read_content_bytes
	async def _local_write(self,file_path,content_bytes):
		'Handles writing a file to the local filesystem.'
		def _sync_write():
			os.makedirs(os.path.dirname(file_path),exist_ok=_D)
			with open(file_path,'wb')as f:f.write(content_bytes)
		await asyncio.to_thread(_sync_write);logger.info(f"Successfully wrote to local path: {file_path}")
	async def _local_read(self,file_path):
		'Handles reading a file from the local filesystem.'
		def _sync_read():
			with open(file_path,'rb')as f:return f.read()
		read_content_bytes=await asyncio.to_thread(_sync_read);logger.info(f"Successfully read from local path: {file_path}");return read_content_bytes
	async def _run_file_action(self,current_var,file_name):
		'\n        Executes a file operation (read/write) for local, GCS, or S3 storage.\n        ';B='binary';A='both'
		if current_var.get(_H):logger.debug(f"Run File Action | {file_name}")
		file_config=self._get_file_details(file_name)
		if not file_config:logger.warning(f"File operation configuration '{file_name}' not found.");return current_var,f"Error: File operation '{file_name}' not found."
		provider=file_config.get('provider');direction=file_config.get('direction');path_template=file_config.get('pathTemplate','');bucket_name=file_config.get('bucketName');source_var=file_config.get(_BQ);dest_var=file_config.get(_BR);connector_name=file_config.get(_T);file_format=file_config.get('format',_P);file_path=self._evaluate_f_string(path_template,current_var)
		if not file_path:logger.error(f"File path template '{path_template}' evaluated to an empty string for file action '{file_name}'.");return current_var,f"Error: File path for '{file_name}' is missing."
		is_write_op=direction in['write',A]and source_var and source_var in current_var and current_var[source_var]is not _A;is_read_op=direction in['read',A]and dest_var
		if not is_read_op and not is_write_op:logger.warning(f"File action '{file_name}' is not actionable. Direction: '{direction}', Source Var: '{source_var}', Dest Var: '{dest_var}'.");return current_var,_A
		try:
			content_bytes_to_write=_A
			if is_write_op:
				content=current_var.get(source_var)
				if file_format==_A4:content_bytes_to_write=json.dumps(content,indent=2).encode(_N)
				elif file_format=='csv':
					if isinstance(content,list)and content and isinstance(content[0],dict):df=pd.DataFrame(content);csv_buffer=StringIO();df.to_csv(csv_buffer,index=_G);content_bytes_to_write=csv_buffer.getvalue().encode(_N)
					else:raise ValueError('For CSV format, the source variable must contain a list of dictionaries.')
				elif file_format=='xml':
					if isinstance(content,dict):content_bytes_to_write=xmltodict.unparse({'root':content},pretty=_D).encode(_N)
					else:raise ValueError('For XML format, the source variable must contain a dictionary.')
				elif file_format==B:
					if not isinstance(content,bytes):raise ValueError('For binary format, the source variable must contain raw bytes.')
					content_bytes_to_write=content
				else:content_bytes_to_write=str(content).encode(_N)
			read_content_bytes=_A
			if provider=='gcs':
				if is_write_op:await self._gcs_write(bucket_name,file_path,content_bytes_to_write,connector_name)
				if is_read_op:read_content_bytes=await self._gcs_read(bucket_name,file_path,connector_name)
			elif provider=='s3':
				if is_write_op:await self._s3_write(bucket_name,file_path,content_bytes_to_write,connector_name)
				if is_read_op:read_content_bytes=await self._s3_read(bucket_name,file_path,connector_name)
			elif provider=='local':
				if is_write_op:await self._local_write(file_path,content_bytes_to_write)
				if is_read_op:read_content_bytes=await self._local_read(file_path)
			else:logger.error(f"Unsupported file provider: '{provider}' for file action '{file_name}'.");return current_var,f"Error: Unsupported file provider '{provider}'."
			if is_read_op and read_content_bytes is not _A:
				try:
					if file_format==_A4:current_var[dest_var]=json.loads(read_content_bytes)
					elif file_format=='csv':csv_io=StringIO(read_content_bytes.decode(_N));current_var[dest_var]=pd.read_csv(csv_io).to_dict('records')
					elif file_format=='xml':current_var[dest_var]=xmltodict.parse(read_content_bytes)
					elif file_format==B:current_var[dest_var]=read_content_bytes
					else:current_var[dest_var]=read_content_bytes.decode(_N)
				except Exception as e:logger.warning(f"Could not deserialize file content for format '{file_format}'. Falling back to raw text. Error: {e}");current_var[dest_var]=read_content_bytes.decode(_N,errors='ignore')
		except(ImportError,ValueError)as e:logger.error(f"Error during file operation '{file_name}': {e}");return current_var,f"Error: {e}"
		except FileNotFoundError:logger.error(f"File not found for read operation: {file_path}");return current_var,f"Error: File not found at {file_path}."
		except Exception as e:logger.error(f"An error occurred during '{provider}' file operation for '{file_name}': {e}",exc_info=_D);return current_var,f"Error during file operation: {e}"
		return current_var,_A
	def _configure_tools_for_request(self,direct_tool_configs,processed_fd_dicts,model_name):
		'\n        Consolidates tool configuration logic for a generation request.\n\n        This helper method prepares the final list of Tool objects by:\n        1. Processing pre-defined tools (like GoogleSearch).\n        2. Creating FunctionDeclaration objects from dictionaries.\n        3. Handling model-specific restrictions, such as mixing tool types.\n\n        Args:\n            direct_tool_configs: A list of pre-defined tool configurations.\n            processed_fd_dicts: A list of dictionaries for function declarations.\n            model_name: The name of the model for the request.\n\n        Returns:\n            A list of Tool objects ready for the API, or None if no tools are configured.\n        ';final_tools_for_config=[]
		if direct_tool_configs:final_tools_for_config.extend(self._prepare_tools_for_genai_config(direct_tool_configs))
		function_declarations=[]
		if processed_fd_dicts:
			for fd_dict in processed_fd_dicts:
				declaration=self._create_function_declaration_from_dict(fd_dict)
				if declaration:function_declarations.append(declaration)
		RESTRICTED_MODELS_FOR_MIXED_TOOLS={_Au};has_functions=bool(function_declarations);has_search=any(t.google_search for t in final_tools_for_config);model_is_restricted=model_name in RESTRICTED_MODELS_FOR_MIXED_TOOLS
		if has_functions and has_search and model_is_restricted:final_tools_for_config=[t for t in final_tools_for_config if not t.google_search]
		if function_declarations:final_tools_for_config.append(Tool(function_declarations=function_declarations))
		return final_tools_for_config if final_tools_for_config else _A
	def _resolve_rag_store(self,store_name):
		'Resolve a rag store by name (case-insensitive, trimmed).\n\n        Returns a tuple: (resource_id, top_k, vector_distance_threshold).\n        Falls back to legacy self.var values when no match or when store_name is None/empty.\n        ';default_resource=self.var.get(_AY,'');default_top_k=self.var.get(_AZ,10);default_vector_distance_threshold=self.var.get(_Aa,.5)
		if not store_name:return default_resource,default_top_k,default_vector_distance_threshold
		normalized=store_name.strip().lower()
		if hasattr(self,'_rag_stores_by_name')and self._rag_stores_by_name:
			if store_name in self._rag_stores_by_name:cfg=self._rag_stores_by_name[store_name];return cfg.get(_s,default_resource),cfg.get(_t,default_top_k),cfg.get(_u,default_vector_distance_threshold)
			for(k,cfg)in self._rag_stores_by_name.items():
				if k.strip().lower()==normalized:return cfg.get(_s,default_resource),cfg.get(_t,default_top_k),cfg.get(_u,default_vector_distance_threshold)
		return default_resource,default_top_k,default_vector_distance_threshold
	def _prepare_tools_for_genai_config(self,tools_list_from_config):
		'Prepares Tool objects for GenerateContentConfig, handling GoogleSearch strings.';B='function_declarations';A='rag_store';prepared_tools=[]
		if not tools_list_from_config:return prepared_tools
		for tool_item in tools_list_from_config:
			if isinstance(tool_item,str)and'GoogleSearch'in tool_item:prepared_tools.append(Tool(google_search=GoogleSearch()))
			elif isinstance(tool_item,str)and'ToolCodeExecution'in tool_item:prepared_tools.append(Tool(code_execution=ToolCodeExecution()))
			elif isinstance(tool_item,str)and'UrlContext'in tool_item:prepared_tools.append(Tool(url_context=UrlContext()))
			elif isinstance(tool_item,str)and'RagStore'in tool_item or isinstance(tool_item,Tool)and getattr(tool_item,'retrieval',_A)and getattr(tool_item.retrieval,A,_A):
				store_name=_A
				if isinstance(tool_item,str):
					try:
						if'('in tool_item and')'in tool_item:start=tool_item.index('(')+1;end=tool_item.index(')',start);store_name=tool_item[start:end].strip()
						elif':'in tool_item:
							parts=tool_item.split(':',1)
							if len(parts)>1:store_name=parts[1].strip()
					except Exception:store_name=_A
				elif isinstance(tool_item,Tool):
					try:
						rs=getattr(tool_item.retrieval,A,_A)or getattr(tool_item.retrieval,'vertex_rag_store',_A)
						if rs:store_name=getattr(rs,_B,_A)or getattr(rs,'store_name',_A)
					except Exception:store_name=_A
				resource_id,top_k,vector_distance_threshold=self._resolve_rag_store(store_name)
				if resource_id:prepared_tools.append(Tool(retrieval=Retrieval(vertex_rag_store=VertexRagStore(rag_resources=[VertexRagStoreRagResource(rag_corpus=resource_id)],similarity_top_k=top_k,vector_distance_threshold=vector_distance_threshold))))
			elif isinstance(tool_item,Tool):prepared_tools.append(tool_item)
			elif isinstance(tool_item,dict):
				try:
					if B in tool_item:
						declarations=[]
						for fd_dict in tool_item[B]:
							declaration=self._create_function_declaration_from_dict(fd_dict)
							if declaration:declarations.append(declaration)
						if declarations:prepared_tools.append(Tool(function_declarations=declarations))
					elif'google_search'in tool_item:prepared_tools.append(Tool(google_search=GoogleSearch()))
					elif'url_context'in tool_item:prepared_tools.append(Tool(url_context=UrlContext()))
					else:logger.warning(f"Invalid tool dictionary format: {tool_item}. Skipping.")
				except Exception as e:logger.warning(f"Could not parse tool dictionary {tool_item}: {e}. Skipping.")
			else:logger.warning(f"Invalid tool format encountered: {tool_item}. Skipping.")
		return prepared_tools
	@staticmethod
	def _is_likely_markdown(text_content):
		'Heuristic to determine if a string is likely Markdown.'
		if not isinstance(text_content,str):return _G
		if re.search('^\\s*#{1,6}\\s+',text_content,re.MULTILINE):return _D
		if re.search('^\\s*[\\*\\-\\+]\\s+',text_content,re.MULTILINE):return _D
		if re.search('^\\s*\\d+\\.\\s+',text_content,re.MULTILINE):return _D
		if re.search('\\*\\*.*?\\*\\*|__.*?__',text_content):return _D
		if re.search('`.*?`',text_content):return _D
		if re.search('!?\\[.*?\\]\\(.*?\\)',text_content):return _D
		return _G
	def _get_gemini_response_sync(self,model_name,contents,config):
		'Synchronous call to Gemini/Vertex AI.'
		if not self._genai_client:logger.error(_BY);return _BZ,[],_A
		try:
			if self._gcp_project_id and self._gcp_region:response=self._genai_client.models.generate_content(contents=contents,model=model_name,config=config)
			else:
				try:model_instance=genai.GenerativeModel(model_name);response=model_instance.generate_content(contents=contents,generation_config=config,tools=config.tools if hasattr(config,_O)and config.tools else _A)
				except Exception as e:logger.error(f"Failed to use direct Gemini API model '{model_name}': {e}",exc_info=_D);return f"Error: AI model '{model_name}' could not be used.",[]
			response_text=_A;function_calls=_A
			if response.candidates and len(response.candidates)>0:
				candidate=response.candidates[0]
				if candidate.content and candidate.content.parts:
					fc_parts=[part.function_call for part in candidate.content.parts if hasattr(part,_Ba)and part.function_call]
					if fc_parts:
						function_calls=[]
						for fc in fc_parts:args_dict={key:value for(key,value)in fc.args.items()};function_calls.append({_B:fc.name,_I:args_dict})
					text_parts=[part.text for part in candidate.content.parts if hasattr(part,_P)and part.text]
					if text_parts:response_text=''.join(text_parts)
			if not response_text and not function_calls and hasattr(response,_P)and response.text:response_text=response.text
			return response_text,list(response.candidates)if hasattr(response,_AF)else[],function_calls
		except Exception as e:logger.error(f"Error getting Gemini response for model {model_name}: {e}",exc_info=_D);return f"There was an error generating this response: {e}",[],_A
	async def _get_gemini_response_async(self,model_name,contents,config):
		'Asynchronous call to Gemini/Vertex AI.'
		if not self._genai_client:logger.error(_BY);return _BZ,[],_A
		try:
			response=await self._genai_client.aio.models.generate_content(contents=contents,model=model_name,config=config);response_text=_A;function_calls=_A
			if response.candidates and len(response.candidates)>0:
				candidate=response.candidates[0]
				if candidate.content and candidate.content.parts:
					fc_parts=[part.function_call for part in candidate.content.parts if hasattr(part,_Ba)and part.function_call]
					if fc_parts:
						function_calls=[]
						for fc in fc_parts:args_dict={key:value for(key,value)in fc.args.items()};function_calls.append({_B:fc.name,_I:args_dict})
					text_parts=[part.text for part in candidate.content.parts if hasattr(part,_P)and part.text]
					if text_parts:response_text=''.join(text_parts)
			if not response_text and not function_calls and hasattr(response,_P)and response.text:response_text=response.text
			return response_text,list(response.candidates)if hasattr(response,_AF)else[],function_calls
		except google_api_exceptions.PermissionDenied as e:logger.error(f"Permission Denied during Gemini API call. Check IAM roles for the service account. Details: {e}",exc_info=_D);return'Error: Permission denied. Please check service account permissions.',[],_A
		except google_api_exceptions.NotFound as e:logger.error(f"Model or endpoint not found: '{model_name}'. Check model name and region. Details: {e}",exc_info=_D);return f"Error: The model '{model_name}' was not found.",[],_A
		except google_api_exceptions.InvalidArgument as e:logger.error(f"Invalid argument passed to Gemini API. Check contents and config. Details: {e}",exc_info=_D);return'Error: Invalid request sent to the model.',[],_A
		except Exception as e:logger.error(f"An unexpected error occurred in _get_gemini_response_async for model {model_name}: {e}",exc_info=_D);return f"There was an unexpected error generating this response: {e}",[],_A
	async def _get_openai_response_async(self,model_name,messages,prompt_config,tools=_A):
		'Asynchronous call to OpenAI API.';A='reasoning_effort'
		if not self._openai_api_key:raise PinionAIConfigurationError('OpenAI API key is not configured.')
		if not AsyncOpenAI:raise PinionAIConfigurationError("OpenAI library is not installed. Please install it with 'pip install openai'.")
		http_client=httpx.AsyncClient();client=AsyncOpenAI(api_key=self._openai_api_key);openai_params={_V:model_name,_x:messages,_A5:prompt_config.get(_AD),_B0:prompt_config.get(_AG),_W:prompt_config.get(_W),'frequency_penalty':prompt_config.get('frequencyPenalty'),'presence_penalty':prompt_config.get('presencePenalty')}
		if prompt_config.get(A):openai_params[A]=prompt_config.get(A)
		if tools:openai_params[_O]=tools;openai_params[_B1]='auto'
		openai_params={k:v for(k,v)in openai_params.items()if v is not _A}
		try:
			response=await client.chat.completions.create(**openai_params);response_message=response.choices[0].message;response_text=response_message.content;function_calls=_A
			if response_message.tool_calls:
				function_calls=[]
				for tool_call in response_message.tool_calls:
					try:arguments=json.loads(tool_call.function.arguments)
					except json.JSONDecodeError:logger.error(f"Failed to decode OpenAI tool arguments: {tool_call.function.arguments}");arguments={}
					function_calls.append({_B:tool_call.function.name,_I:arguments})
			return response_text,function_calls
		except Exception as e:logger.error(f"Error calling OpenAI API for model {model_name}: {e}",exc_info=_D);return f"Error from OpenAI: {e}",_A
	async def _get_anthropic_response_async(self,model_name,system_prompt,messages,prompt_config,tools=_A):
		'Asynchronous call to Anthropic API.';A='tool_use'
		if not self._anthropic_api_key:raise PinionAIConfigurationError('Anthropic API key is not configured.')
		if not AsyncAnthropic:raise PinionAIConfigurationError("Anthropic library is not installed. Please install it with 'pip install anthropic'.")
		client=AsyncAnthropic(api_key=self._anthropic_api_key);anthropic_params={_V:model_name,_z:system_prompt,_x:messages,_A5:prompt_config.get(_AD),_B0:prompt_config.get(_AG,4096),_W:prompt_config.get(_W),_AE:prompt_config.get(_AE)}
		if tools:anthropic_params[_O]=tools;anthropic_params[_B1]={_F:'auto'}
		anthropic_params={k:v for(k,v)in anthropic_params.items()if v is not _A}
		try:
			response=await client.messages.create(**anthropic_params);response_text=_A;function_calls=_A
			if response.stop_reason==A:
				function_calls=[]
				for content_block in response.content:
					if content_block.type==A:function_calls.append({_B:content_block.name,_I:content_block.input})
			else:
				text_blocks=[block.text for block in response.content if block.type==_P]
				if text_blocks:response_text=''.join(text_blocks)
			return response_text,function_calls
		except Exception as e:logger.error(f"Error calling Anthropic API for model {model_name}: {e}",exc_info=_D);return f"Error from Anthropic: {e}",_A
	async def _get_deepseek_response_async(self,model_name,messages,prompt_config,tools):
		'\n        Get response from a DeepSeek model.\n        ';A='max_output_tokens'
		try:from openai import AsyncOpenAI
		except ImportError:logger.error("OpenAI library not installed. Please install it with 'pip install openai'.");return'Error: OpenAI library not installed.',_A
		api_key=self._get_api_key(_AJ)
		if not api_key:logger.error('DeepSeek API key not found.');return'Error: DeepSeek API key not found.',_A
		try:client=AsyncOpenAI(api_key=api_key,base_url='https://api.deepseek.com/v1')
		except Exception as e:logger.error(f"Failed to initialize DeepSeek client: {e}");return f"Error initializing DeepSeek client: {e}",_A
		request_params={_V:model_name,_x:messages}
		if A in prompt_config:request_params[_B0]=prompt_config[A]
		if _A5 in prompt_config:request_params[_A5]=prompt_config[_A5]
		if _W in prompt_config:request_params[_W]=prompt_config[_W]
		if tools:request_params[_O]=tools;request_params[_B1]='auto'
		try:
			logger.info(f"Sending request to DeepSeek model: {model_name}");response=await client.chat.completions.create(**request_params);response_message=response.choices[0].message;llm_response_text=response_message.content or'';function_calls=_A
			if response_message.tool_calls:
				function_calls=[]
				for tool_call in response_message.tool_calls:
					try:arguments=json.loads(tool_call.function.arguments);function_calls.append({_B:tool_call.function.name,'arguments':arguments})
					except json.JSONDecodeError as e:logger.error(f"Failed to decode function arguments from DeepSeek: {tool_call.function.arguments}. Error: {e}");return f"Error decoding tool arguments from DeepSeek: {e}",_A
			return llm_response_text,function_calls
		except Exception as e:logger.error(f"Error getting response from DeepSeek: {e}");return f"Error from DeepSeek: {e}",_A
	def _extract_function_calls_from_llm_response(self,llm_response):
		'Extracts function calls from a Gemini Function Call response.';function_calls_list=[]
		try:
			if llm_response.candidates and llm_response.candidates[0].content.parts:
				for part in llm_response.candidates[0].content.parts:
					if part.function_call:fc=part.function_call;call_dict={fc.name:dict(fc.args.items())};function_calls_list.append(call_dict)
		except(AttributeError,IndexError):logger.debug('No function calls found in LLM response or response structure unexpected.')
		return function_calls_list
	async def _get_token_api(self,host,client_id,client_secret):
		url='/token';headers={_Z:_M};data={_B2:_Bb,_B3:client_id,_B4:client_secret}
		try:response=await self._http_session.post(url,headers=headers,json=data);response.raise_for_status();auth_response=response.json();return f"{auth_response[_Bc]} {auth_response[_Bd]}"
		except httpx.RequestError as e:raise PinionAIAPIError(f"Network error getting token from {e.request.url}",details=str(e))from e
		except(KeyError,json.JSONDecodeError)as e:raise PinionAIAPIError('Invalid token response',details=str(e))from e
	async def _start_session_api(self,host,agent_id_to_start,token):
		url=f"/agent/{agent_id_to_start}";headers={_B5:_AP,_q:_A3,_L:token}
		try:
			response=await self._http_session.get(url,headers=headers);response.raise_for_status();data=response.json();session_uid=data.get(_C,{}).get(_E,{}).get('uid')
			if session_uid:return session_uid,data
			raise PinionAISessionError('Session UID not found in API response.',details=data)
		except httpx.RequestError as e:raise PinionAISessionError(f"Network error starting session from {e.request.url}",details=str(e))from e
		except json.JSONDecodeError as e:raise PinionAISessionError('Invalid JSON response when starting session',details=str(e))from e
	async def _start_version_api(self,host,agent_id_to_start,token,version_str):
		url=f"/version/{agent_id_to_start}/{version_str}";headers={_B5:_AP,_q:_A3,_L:token}
		try:
			response=await self._http_session.get(url,headers=headers);response.raise_for_status();data=response.json();session_uid=data.get(_C,{}).get(_E,{}).get('uid')
			if session_uid:return session_uid,data
			raise PinionAISessionError('Session UID not found in versioned API response.',details=data)
		except httpx.RequestError as e:raise PinionAISessionError(f"Network error starting versioned session from {e.request.url}",details=str(e))from e
		except json.JSONDecodeError as e:raise PinionAISessionError(f"Invalid JSON response when starting versioned session from {url}",details=str(e))from e
	async def _get_session_api(self,host,session_uid,token):
		url=f"/session/{session_uid}";headers={_q:_A3,_L:token,_B5:_AP}
		try:
			response=await self._http_session.get(url,headers=headers);response.raise_for_status();data=response.json()
			if data.get(_C,{}).get(_E,{}).get('uid')==session_uid:return data
			raise PinionAISessionError('GET Session UID not found in API response.',details=data)
		except httpx.RequestError as e:raise PinionAISessionError(f"Network error getting session from {e.request.url}",details=str(e))from e
		except json.JSONDecodeError as e:raise PinionAISessionError(f"Invalid JSON response when getting session from {url}",details=str(e))from e
	async def _get_session_lastmodified_api(self,host,session_uid,token):
		url=f"/session/{session_uid}/lastmodified";headers={_q:_A3,_L:token}
		try:response=await self._http_session.get(url,headers=headers);response.raise_for_status();data=response.json();last_modified=data.get(_C,{}).get(_E,{}).get('lastmodified');return last_modified,'success'
		except httpx.RequestError as e:raise PinionAISessionError(f"Request error getting last modified in session from {e.request.url}",details=str(e))from e;return _A,e
		except(json.JSONDecodeError,KeyError)as e:raise PinionAISessionError(f"Error parsing lastmodified response from {url}",details=str(e))from e;return _A,e
	async def _post_session_api(self,host,token,session_uid,data_payload,transfer_req,transfer_acc):
		url=f"/session";headers={_Z:_M,'Content-Encoding':_AP,_L:token};full_payload={'sessionUid':session_uid,_C:data_payload,'transferRequested':transfer_req,'transferAccepted':transfer_acc}
		try:
			json_string_payload=json.dumps(full_payload,default=_json_datetime_serializer);compressed_data=gzip.compress(json_string_payload.encode(_N));response=await self._http_session.post(url,headers=headers,content=compressed_data)
			if response.status_code==200:return response,response.json()
			else:logger.warning(f"POST to {url} failed with status {response.status_code}: {response.text}");return response,response.text
		except httpx.RequestError as e:logger.error(f"API POST error for {url}: {e}");return _A,e
		except json.JSONDecodeError as e:logger.error(f"JSON decode error on 200 response from {url}: {e}");return response,e
	async def _get_token_for_connector(self,connector_config):
		'Gets auth token for a given connector configuration.';url=connector_config.get(_X);client_id=connector_config.get(_A_);client_secret=connector_config.get(_l);grant_type=connector_config.get(_k,_Bb);content_type=connector_config.get(_Be,_M);use_header_payload=connector_config.get('headerPayload',_G);scope=connector_config.get(_A9,_A)
		if not url or not client_id or not client_secret:logger.warning(f"Connector '{connector_config.get(_B)}' is missing URL, clientId, or clientSecret.");return
		headers={};data_to_send:0
		if use_header_payload:client_keys=f"{client_id}:{client_secret}";client_keys_b64=base64.b64encode(client_keys.encode()).decode();headers[_L]=f"Basic {client_keys_b64}";headers[_Z]='application/x-www-form-urlencoded';data_to_send=f"grant_type={grant_type}"
		else:
			headers[_Z]=content_type
			if _A4 in content_type.lower():
				data_to_send={_B2:grant_type,_B3:client_id,_B4:client_secret}
				if scope:data_to_send[_A9]=scope
			elif'x-www-form-urlencoded'in content_type.lower():
				form_data=[(_B2,grant_type),(_B3,client_id),(_B4,client_secret)]
				if scope:form_data.append((_A9,scope))
				data_to_send='&'.join([f"{k}={quote(str(v))}"for(k,v)in form_data])
			else:logger.warning(f"Unsupported content type for connector token request: {content_type}");return
		try:
			payload=json.dumps(data_to_send)if isinstance(data_to_send,dict)else data_to_send
			async with httpx.AsyncClient()as client:response=await client.post(url,headers=headers,content=payload);response.raise_for_status();auth_response=response.json();token_type=auth_response.get(_Bc,'Bearer').capitalize();return f"{token_type} {auth_response[_Bd]}"
		except httpx.RequestError as e:logger.error(f"Failed to obtain grant token for connector '{connector_config.get(_B)}' from {url}: {e}");raise PinionAIAPIError(f"Network error getting token for connector '{connector_config.get(_B)}'",details=str(e))from e
		except(KeyError,json.JSONDecodeError)as e:logger.error(f"Error parsing token response for connector '{connector_config.get(_B)}' from {url}: {e}");raise PinionAIAPIError(f"Invalid token response for connector '{connector_config.get(_B)}'",details=str(e))from e
	async def _generic_api_post_put(self,current_var,api_config,headers,method):
		'Handles generic POST/PUT API calls.';url_template=self._clean_line(api_config.get(_X,''));url=self._evaluate_f_string(url_template,current_var)
		if not url:logger.error(f"URL could not be evaluated for API '{api_config.get(_B)}'. Template: {url_template}");return current_var,_A,_A,_Bf
		raw_body_template=api_config.get(_U,'');final_data_bytes=_A;content_type=headers.get(_Z,'').lower()
		try:
			if _M in content_type and raw_body_template.strip():parsable_template=raw_body_template.replace('["',"['").replace('"]',"']");json_structure_template=json.loads(parsable_template);evaluated_structure=self._evaluate_vars_in_structure(json_structure_template,current_var);final_data_bytes=json.dumps(evaluated_structure).encode(_N)
			elif raw_body_template.strip():evaluated_string=self._evaluate_f_string(raw_body_template,current_var);final_data_bytes=evaluated_string.encode(_N)
			else:final_data_bytes=b''
		except json.JSONDecodeError as e:logger.error(f"Invalid JSON in API body template for '{api_config.get(_B)}': {raw_body_template}. Error: {e}");return current_var,_A,_A,f"Invalid JSON in API body: {e}"
		except Exception as e:logger.error(f"Error processing body for API '{api_config.get(_B)}': {e}. Template: '{raw_body_template}'");return current_var,_A,_A,f"Error processing API body: {e}"
		if final_data_bytes is _A:return current_var,_A,_A,'Error: API body could not be prepared.'
		logger.debug(f"API {method} Request URL: {url}");logger.debug(f"API {method} Request Headers: {headers}");logger.debug(f"API {method} Request Body: {final_data_bytes.decode(_N)if final_data_bytes else'None'}")
		try:
			async with httpx.AsyncClient()as client:
				if method=='POST':response=await client.post(url,headers=headers,content=final_data_bytes,timeout=120)
				elif method=='PUT':response=await client.put(url,headers=headers,content=final_data_bytes,timeout=120)
				else:return current_var,_A,_A,f"Unsupported method {method} in _generic_api_post_put"
			parsed_response:0
			try:parsed_response=response.json()
			except json.JSONDecodeError:parsed_response=response.text
			if api_config.get(_Y):current_var[api_config[_Y]]=parsed_response
			final_response_message=_A
			if response.status_code>=400 or not parsed_response:
				logger.warning(f"API {method} to {url} failed with status {response.status_code}: {parsed_response}")
				if api_config.get(_AQ):final_response_message=self._evaluate_f_string(api_config[_AQ],current_var)
			return current_var,response,parsed_response,final_response_message
		except httpx.RequestError as e:status_code=e.response.status_code if hasattr(e,_AO)and e.response else _A;error_detail=e.response.text if hasattr(e,_AO)and e.response else str(e);raise PinionAIAPIError(f"API {method} request to {url} failed: {error_detail}",status_code=status_code,details=str(e))from e
	async def _generic_api_get(self,current_var,api_config,headers):
		'Handles generic GET API calls.';url_template=self._clean_line(api_config.get(_X,''));url=self._evaluate_f_string(url_template,current_var)
		if not url:logger.error(f"URL could not be evaluated for API GET '{api_config.get(_B)}'. Template: {url_template}");return current_var,_A,_A,_Bf
		logger.debug(f"API GET Request URL: {url}");logger.debug(f"API GET Request Headers: {headers}")
		try:
			async with httpx.AsyncClient()as client:response=await client.get(url,headers=headers,timeout=120)
			parsed_response:0
			try:parsed_response=response.json()
			except json.JSONDecodeError:parsed_response=response.text
			if api_config.get(_Y):current_var[api_config[_Y]]=parsed_response
			final_response_message=_A
			if response.status_code>=400:
				logger.warning(f"API GET to {url} failed with status {response.status_code}: {parsed_response}")
				if api_config.get(_AQ):final_response_message=self._evaluate_f_string(api_config[_AQ],current_var)
			return current_var,response,parsed_response,final_response_message
		except httpx.RequestError as e:error_detail=e.response.text if hasattr(e,_AO)and e.response else str(e);raise PinionAIAPIError(f"API GET request to {url} failed: {error_detail}")from e
	async def _get_journey_token(self,current_var,user_input=_A):
		'Gets or refreshes Journey client credentials token.'
		if self._journey_bearer_token:return self._journey_bearer_token
		journey_connector=current_var.get('journey_connector_name','')
		if journey_connector:
			connector_config=self._get_connector_details(journey_connector)
			if connector_config:
				try:
					token=await self._get_token_for_connector(connector_config)
					if token:self._journey_bearer_token=token;return self._journey_bearer_token
				except PinionAIAPIError as e:logger.warning(f"Could not get token for connector '{journey_connector}': {e}. Proceeding without token.")
			else:logger.warning(f"Connector '{journey_connector}' not found.")
	async def _journey_lookup(self,unique_id_val,current_var,user_input=_A):
		'Performs a Journey customer lookup.';A='enrollments';account_id=current_var.get('journey_accountId');bearer_token=await self._get_journey_token(current_var)
		if not account_id or not bearer_token:return _A,_G,'error_config'
		headers={_AR:_M,_L:bearer_token};url=f"https://app.journeyid.io/api/system/customers/lookup?account_id={account_id}&unique_id={unique_id_val}"
		try:
			response=await self._http_session.get(url,headers=headers,timeout=60);response.raise_for_status();lookup_data=response.json();logger.debug(f"Journey lookup response: {json.dumps(lookup_data,indent=2)}");customer_id=lookup_data.get('id');enrolled=_G
			if customer_id and lookup_data.get(A):
				for enrollment in lookup_data[A]:
					if enrollment.get(_F)=='webauthn':enrolled=_D;break
			return customer_id,enrolled,'found'if customer_id else'empty'
		except httpx.HTTPStatusError as e:logger.error(f"Journey lookup failed with status {e.response.status_code} for unique_id {unique_id_val}. Response: {e.response.text}")
		except httpx.RequestError as e:logger.error(f"Journey lookup error for unique_id {unique_id_val}: {e}")
		except(json.JSONDecodeError,KeyError)as e:logger.error(f"Error parsing Journey lookup response for {unique_id_val}: {e}")
		return _A,_G,'error_request'
	async def _journey_send_pipeline(self,current_var,json_payload,delivery_method,user_input=_A):
		'Sends a pipeline execution request to Journey.';bearer_token=await self._get_journey_token(current_var)
		if not bearer_token:return _A,_B6
		post_url='https://app.journeyid.io/api/system/executions';headers={_q:_M,_Z:_M,_L:bearer_token}
		try:
			async with httpx.AsyncClient()as client:response=await client.post(post_url,headers=headers,content=json.dumps(json_payload),timeout=120)
			response_data=response.json()
			if 200<=response.status_code<300:
				if delivery_method==_X:
					execution_url=response_data.get(_X);execution_id=response_data.get('id')
					if execution_url and execution_id:return execution_id,execution_url,''
					else:return _A,_A,'Execution URL or ID not found in successful Journey response.'
				else:
					execution_id=response_data.get('id')
					if execution_id:return execution_id,_A,''
					else:return _A,_A,'ExecutionId not found in successful Journey response.'
			else:
				error_msg=response_data.get(_h,response.text)
				if'Token is expired'in str(error_msg):self._journey_bearer_token=_A;return _A,_A,'Your Journey session has expired. Please try again.'
				logger.warning(f"Journey send_pipeline failed ({response.status_code}): {error_msg}");return _A,_A,f"Journey pipeline error: {error_msg} {response.text}"
		except httpx.RequestError as e:logger.error(f"Journey send_pipeline request error: {e}");return _A,_A,'Error sending request to Journey.'
		except json.JSONDecodeError as e:logger.error(f"Error parsing Journey send_pipeline response: {e}");return _A,_A,'Error processing Journey response.'
	async def _journey_execution_status_check(self,execution_id,current_var,max_retries=12,delay_seconds=5,user_input=_A):
		'Checks the status of a Journey execution.';bearer_token=await self._get_journey_token(current_var)
		if not bearer_token:return _G,_B6
		url=f"https://app.journeyid.io/api/system/executions/{execution_id}";headers={_AR:_M,_L:bearer_token}
		for attempt in range(max_retries):
			try:
				async with httpx.AsyncClient()as client:response=await client.get(url,headers=headers,timeout=30)
				response.raise_for_status();status_data=response.json()
				if status_data.get(_Bg):return _D,status_data.get('outcome',{}).get(_i,'Task completed successfully.')
			except httpx.RequestError as e:logger.warning(f"Journey execution status check attempt {attempt+1} failed for {execution_id}: {e}")
			except(json.JSONDecodeError,KeyError)as e:logger.warning(f"Error parsing Journey execution status for {execution_id}: {e}")
			if attempt<max_retries-1:time.sleep(delay_seconds)
		return _G,'The Journey task was not completed in the allotted time or an error occurred.'
	async def _journey_session_pipeline_status_check(self,session_id_val,current_var,pipeline_key_to_check,max_retries=12,delay_seconds=5,user_input=_A):
		'Checks pipeline status within a Journey session.';A='pipeline';bearer_token=await self._get_journey_token(current_var)
		if not bearer_token:return _G,_B6
		url=f"https://app.journeyid.io/api/system/sessions/lookup?external_ref={session_id_val}";headers={_AR:_M,_L:bearer_token}
		for attempt in range(max_retries):
			try:
				async with httpx.AsyncClient()as client:response=await client.get(url,headers=headers,timeout=30)
				response.raise_for_status();session_lookup_data=response.json();executions=session_lookup_data.get('executions',[])
				for exec_item in executions:
					if exec_item.get(A,{}).get('key')==pipeline_key_to_check or exec_item.get(A,{}).get('id')==pipeline_key_to_check:
						if exec_item.get(_Bg):return _D,exec_item.get('outcome',{}).get(_i,'Pipeline completed.')
						break
			except httpx.RequestError as e:logger.warning(f"Journey session pipeline status check attempt {attempt+1} failed for session {session_id_val}, pipeline {pipeline_key_to_check}: {e}")
			except(json.JSONDecodeError,KeyError)as e:logger.warning(f"Error parsing Journey session pipeline status for {session_id_val}: {e}")
			if attempt<max_retries-1:time.sleep(delay_seconds)
		return _G,'The Journey pipeline action was not completed or timed out.'
	@staticmethod
	def _generate_uid():return str(uuid.uuid4())
	@staticmethod
	def _generate_secret(length=32):return secrets.token_urlsafe(length)
	@staticmethod
	def _generate_password(length=12):
		if length<4:length=4
		digits_chars='0123456789';locase_chars='abcdefghijklmnopqrstuvwxyz';upcase_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ';symbols_chars='$%?!';combined_list=list(digits_chars+locase_chars+upcase_chars+symbols_chars);password_chars=[random.choice(digits_chars),random.choice(locase_chars),random.choice(upcase_chars),random.choice(symbols_chars)]
		for _ in range(length-4):password_chars.append(random.choice(combined_list))
		random.shuffle(password_chars);return''.join(password_chars)
	async def _twilio_sms_message(self,sms_body,to_phone,from_phone_twilio=_A):
		if not self._twilio_account_sid or not self._twilio_auth_token:logger.error('Twilio credentials not configured. Cannot send SMS.');return
		_national_digits,_unique_id,to_phone_e164=format_phone(to_phone);twilio_from_number=from_phone_twilio or self._twilio_number
		if not twilio_from_number:logger.error(_Bh);return
		try:twilio_client=TwilioClient(self._twilio_account_sid,self._twilio_auth_token);message=await asyncio.to_thread(twilio_client.messages.create,body=sms_body,from_=twilio_from_number,to=to_phone_e164);logger.info(f"Twilio SMS sent via client. SID: {message.sid}")
		except Exception as e:logger.error(f"Error sending Twilio SMS via client to {to_phone_e164}: {e}")
	async def _sendgrid_email(self,plain_text_body,html_body,to_email,subject,from_email_addr=_A,cc_address=_A,bcc_address=_A,reply_to_address=_A):
		if not self._email_api_key:logger.error('Email API key not configured. Cannot send email.');return
		actual_from_email=from_email_addr or self._email_from_address
		if not actual_from_email:logger.error("Email 'from' address not configured. Cannot send email.");return
		p=Personalization()
		if to_email:
			to_address_list=to_email.split(_S)
			for addr in to_address_list:p.add_to(To(addr.strip()))
		if cc_address:
			cc_address_list=cc_address.split(_S)
			for addr in cc_address_list:p.add_cc(Cc(addr.strip()))
		if bcc_address:
			bcc_address_list=bcc_address.split(_S)
			for addr in bcc_address_list:p.add_bcc(Bcc(addr.strip()))
		if reply_to_address:
			reply_to_list=reply_to.split(_S)
			for addr in reply_to_list:p.add_reply_to(ReplyTo(addr.strip()))
		try:sg=sendgrid.SendGridAPIClient(self._email_api_key);message=Mail(from_email=From(actual_from_email),subject=subject,plain_text_content=plain_text_body,html_content=html_body);message.add_personalization(p);response=await asyncio.to_thread(sg.send,message)
		except Exception as e:logger.error(f"Error sending email to {to_email} via SendGrid: {e}")
	async def _infobip_send_email(self,plain_text_body,html_body_content,to_address,subject,from_address=_A,token=_A,cc_address=_A,bcc_address=_A,reply_to_address=_A):
		'Sends an email using the Infobip API.'
		if not token:logger.error('Infobip token not provided. Cannot send email.');return
		infobip_url='https://g9egk8.api.infobip.com/email/4/messages';headers={_L:token,_Z:_M,_AR:_M};payload={_x:[{'sender':from_address,'destinations':[{'to':[{'destination':to_address}]}],_Q:{_Ax:subject,_P:plain_text_body,'html':html_body_content}}]}
		try:
			async with httpx.AsyncClient()as client:response=await client.post(infobip_url,headers=headers,json=payload);response.raise_for_status();logger.info(f"Email sent to {to_address} via Infobip. Response: {response.text}")
		except httpx.HTTPStatusError as http_err:logger.error(f"HTTP error occurred sending email via Infobip: {http_err} - {http_err.response.text}")
		except Exception as e:logger.error(f"An unexpected error occurred sending email via Infobip: {e}")
	async def _ms_graph_send_email(self,plain_text_body,html_body_content,to_address,subject,from_address=_A,token=_A,cc_address=_A,bcc_address=_A,reply_to_address=_A):
		'Sends an email using the Microsoft Graph API.';B='address';A='emailAddress'
		if not token:logger.error('Microsoft Graph API token not provided. Cannot send email.');return
		if not from_address:logger.error("Microsoft Graph API 'from' address not provided. Cannot send email.");return
		graph_api_endpoint='https://graph.microsoft.com/v1.0';url=f"{graph_api_endpoint}/users/{from_address}/sendMail";headers={_L:token,_Z:_M};email_payload={_i:{_Ax:subject,_U:{_Be:'HTML',_Q:html_body_content}},'saveToSentItems':'true'}
		if to_address:to_address_list=to_address.split(_S);email_payload[_i]['toRecipients']=[{A:{B:addr.strip()}}for addr in to_address_list]
		if cc_address:cc_address_list=cc_address.split(_S);email_payload[_i]['ccRecipients']=[{A:{B:addr.strip()}}for addr in cc_address_list]
		if bcc_address:bcc_address_list=bcc_address.split(_S);email_payload[_i]['bccRecipients']=[{A:{B:addr.strip()}}for addr in bcc_address_list]
		if reply_to_address:reply_to_list=reply_to.split(_S);email_payload[_i]['replyTo']=[{A:{B:addr.strip()}}for addr in reply_to_list]
		try:
			async with httpx.AsyncClient()as client:response=await client.post(url,headers=headers,json=email_payload);response.raise_for_status();logger.info(f"Email sent to {to_address} via Microsoft Graph API. Response status: {response.status_code}")
		except httpx.HTTPStatusError as http_err:logger.error(f"HTTP error occurred sending email via Microsoft Graph API: {http_err} - {http_err.response.text}")
		except Exception as e:logger.error(f"An unexpected error occurred sending email via Microsoft Graph API: {e}")
	@staticmethod
	def _clean_line(text):
		if not text:return''
		return text.strip('\n')
	@staticmethod
	def _clean_text(text):
		if not text:return''
		return text.replace('\n','').replace('\r','').replace('\t','')
	def _evaluate_vars_in_structure(self,data_structure,context_vars,user_input=_A):
		'\n        Recursively traverses a dict or list, evaluating string templates like f"var[\'key\']".\n        Uses a provided context_vars for evaluation, not necessarily self.var.\n        ';D='context_vars';C='current_var';B='{current_var[';A='{var['
		if isinstance(data_structure,dict):
			for(key,value)in list(data_structure.items()):
				if isinstance(value,str):
					if A in value or B in value:
						try:eval_globals={_w:context_vars,C:context_vars,D:context_vars,_B7:user_input};data_structure[key]=eval(f"f'''{value}'''",eval_globals,{})
						except Exception as e:logger.warning(f"Could not evaluate template for key '{key}': '{value}'. Error: {e}")
				elif isinstance(value,(dict,list)):self._evaluate_vars_in_structure(value,context_vars,user_input)
		elif isinstance(data_structure,list):
			for(i,item)in enumerate(data_structure):
				if isinstance(item,str):
					if A in item or B in item or user_input is not _A and'{user_input}'in item:
						try:eval_globals={_w:context_vars,C:context_vars,D:context_vars,_B7:user_input};data_structure[i]=eval(f"f'''{item}'''",eval_globals,{})
						except Exception as e:logger.warning(f"Could not evaluate template in list item: '{item}'. Error: {e}")
				elif isinstance(item,(dict,list)):self._evaluate_vars_in_structure(item,context_vars,user_input)
		return data_structure
	def _evaluate_f_string(self,template_string,context_vars,user_input=_A):
		'Safely evaluates an f-string like template using provided context variables.'
		try:eval_namespace={_w:context_vars,_B7:user_input};return eval(f"f'''{template_string}'''",eval_namespace,{})
		except Exception as e:logger.error(f"Error evaluating f-string template: '{template_string}'. Error: {e}");return template_string
	def _create_function_declaration_from_dict(self,declaration_dict):
		"\n        Safely creates a FunctionDeclaration object from a dictionary.\n\n        This function takes a dictionary that mirrors the structure of a JSON\n        function declaration and converts it into a valid FunctionDeclaration\n        object that can be used with the Vertex AI SDK.\n\n        Args:\n            declaration_dict: A dictionary with 'name', 'description', and\n                              'parameters' keys.\n\n        Returns:\n            A FunctionDeclaration object if the input is valid, otherwise None.\n        "
		if not isinstance(declaration_dict,dict):logger.error('Input must be a dictionary to create a FunctionDeclaration.');return
		name=declaration_dict.get(_B);description=declaration_dict.get(_K);parameters=declaration_dict.get(_AS)
		if not all([name,description,isinstance(parameters,dict)]):logger.error(f"The provided dictionary is missing required keys ('name', 'description') or 'parameters' is not a dictionary. Got: {declaration_dict}");return
		try:return FunctionDeclaration(name=name,description=description,parameters=parameters)
		except Exception as e:logger.error(f"Failed to instantiate FunctionDeclaration from dict {declaration_dict}: {e}");return
	def _translate_tools_for_provider(self,provider,direct_tool_configs,processed_fd_dicts):
		'Translates internal tool configuration to a model provider-specific format.'
		if not processed_fd_dicts:return
		translated_tools=[]
		if provider==_g:
			for fd in processed_fd_dicts:translated_tools.append({_F:_Aw,_Aw:{_B:fd.get(_B),_K:fd.get(_K),_AS:fd.get(_AS)}})
		elif provider==_y:
			for fd in processed_fd_dicts:translated_tools.append({_B:fd.get(_B),_K:fd.get(_K),'input_schema':fd.get(_AS)})
		return translated_tools if translated_tools else _A
	def get_chat_messages_for_display(self):'Returns chat messages, suitable for display by an application.';return self.chat_messages
	def add_message_to_history(self,role,content):'Adds a message to the internal chat history.';self.chat_messages.append({_R:role,_Q:content})
	@property
	def session_id(self):return self._session_id
	@property
	def current_var_data(self):return self.var.copy()
	def __repr__(self):return f"<PinionAIClient(agent_id='{self._agent_id}', session_id='{self._session_id}', host='{self._host_url}')>"
def format_phone(number_str):
	'\n    Formats a phone number to a consistent E.164 format.\n\n    This is a standalone utility function.\n\n    Args:\n        number_str: The phone number as a string.\n\n    Returns:\n        A tuple containing (national_digits, unique_id, e164_format).\n    ';A='1'
	if not isinstance(number_str,str):number_str=str(number_str)
	digits=re.sub('[^0-9]','',number_str)
	if digits.startswith(A)and len(digits)==11:0
	elif len(digits)==10:
		is_likely_us_short=_D
		if 650<=int(digits[0:3])<=659 and int(digits[0:3])!=657:is_likely_us_short=_G
		if is_likely_us_short:digits=f"1{digits}"
	unique_id=digits;phone_number_e164=f"+{digits}";national_digits=digits.removeprefix(A)if digits.startswith(A)and len(digits)>10 else digits;return national_digits,unique_id,phone_number_e164
def twilio_sms_message(sms_body,to_phone,from_phone_twilio=_A):
	'Sends an SMS using Twilio, reading credentials from environment variables.';twilio_account_sid=os.environ.get(_AT);twilio_auth_token=os.environ.get(_AU)
	if not twilio_account_sid or not twilio_auth_token:logger.error('Twilio credentials not configured in environment. Cannot send SMS.');return
	_national_digits,_unique_id,to_phone_e164=format_phone(to_phone);twilio_from_number=from_phone_twilio or os.environ.get(_AV)
	if not twilio_from_number:logger.error(_Bh);return
	try:client=Client(twilio_account_sid,twilio_auth_token);message=client.messages.create(body=sms_body,from_=twilio_from_number,to=to_phone_e164);logger.info(f"Twilio SMS sent. SID: {message.sid}")
	except Exception as e:logger.error(f"Error sending Twilio SMS to {to_phone_e164}: {e}")