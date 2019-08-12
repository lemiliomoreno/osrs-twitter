
import os

CONSUMER_KEY = os.environ['TWITTER_API_CONSUMER_KEY']
CONSUMER_SECRET = os.environ['TWITTER_API_CONSUMER_SECRET']
ACCESS_KEY = os.environ['TWITTER_API_ACCESS_KEY']
ACCESS_SECRET = os.environ['TWITTER_API_ACCESS_SECRET']
ACCOUNT_ID = os.environ['TWITTER_API_ACCOUNT_ID']

EOL = '\n'

class message_control:

	filter_msg_list = []
	msg_list = []
	messages = []
	to_read = None

	def __init__(self, file_name='/home/osrs_manager/osrs_ge/last_msg_id.txt', *args, **kwargs):
		import twitter

		self.file_name = file_name
		self.auth = twitter.Api(
			consumer_key=CONSUMER_KEY, 
			consumer_secret=CONSUMER_SECRET, 
			access_token_key=ACCESS_KEY,
			access_token_secret=ACCESS_SECRET)
		self.last_seen_id = None
		self.get_last_seen_id()

	def get_msgs(self):
		self.messages = self.auth.GetDirectMessages(return_json=True)
		self.to_read = self.not_read_msgs()

	def not_read_msgs(self):
		for item in self.messages['events']:
			if item['id'] == self.last_seen_id:
				return len(self.filter_msg_list)
			elif '#osrs_ge' in item['message_create']['message_data']['text'] and item['message_create']['sender_id'] != ACCOUNT_ID:
				self.filter_msg_list.append(item)

	def get_last_seen_id (self):
		with open(self.file_name, 'r') as file_content:
			self.last_seen_id = file_content.read().strip()

	def save_last_seen_id(self):
		with open(self.file_name, 'w') as file_content:
			file_content.write(self.last_seen_id)

	def get_msgs_info(self):
		parameters = {}
		message_info = {
			'msg_id' : '',
			'sender_id' : '',
			'text' : '',
			}
		for message in self.filter_msg_list:
			message_info['msg_id'] = message['id']
			message_info['text'] = message['message_create']['message_data']['text'].encode('utf-8').decode('utf-8').lower()
			message_info['sender_id'] = message['message_create']['sender_id']
			self.msg_list.append(message_info)
			message_info = {}
		return self.msg_list
	
	def reply_msgs(self, msgs_info):
		msg_sent = None
		for item in msgs_info:
			msg_sent = self.auth.PostDirectMessage(text=item['reply'], user_id=item['sender_id'], return_json=True)
			print(msg_sent)
		if self.to_read > 0:
			self.last_seen_id = msgs_info[self.to_read - 1]['msg_id']
			self.save_last_seen_id()


class api_data_control:

	def __init__(self, api='https://storage.googleapis.com/osbuddy-exchange/summary.json', *args, **kwargs):
		self.data = None
		self.raw_data = None
		self.encoding = None
		self.api = api
		self.do_connection()
		
	def do_connection(self):
		import json
		import urllib.request
		
		data_request = urllib.request.urlopen(self.api)
		self.raw_data = data_request.read()
		self.encoding = data_request.info().get_content_charset('utf-8')
		self.data = json.loads(self.raw_data.decode(self.encoding))
		
	def get_data(self):
		return self.data
	
	
class filter_control:

	def __init__(self, msgs_info, api_info, *args, **kwargs):
		self.msgs_info = msgs_info
		self.api_info = api_info
		self.total_msgs = len(msgs_info)
		
		super().__init__(*args, **kwargs)
		
		self.filter_params = [
			{
				'name' : '#profit_func()',
				'nickname' : 'profit',
				'params' : [['profit_min', 1], ['profit_max', 1000000], ['max_items', 20]],
				'callable' : self.filter_profit,
			},
			{
				'name' : '#testing_func()',
				'nickname' : 'testing',
				'params' : [['test_min', 1], ['test_max', 1000000]],
			},
		]
		
	
	def filter_profit(self, list_index):
		result = []
		max_result = None
		for item in self.api_info.keys():
			if self.api_info[item]['buy_average'] != 0:
				item_diff = int(self.api_info[item]['sell_average']) - int(self.api_info[item]['buy_average'])
				if (item_diff >= int(self.msgs_info[list_index]['filters']['profit']['profit_min']) and item_diff <= int(self.msgs_info[list_index]['filters']['profit']['profit_max'])):
					self.api_info[item]['difference'] = item_diff
					result.append(self.api_info[item])
				
		sorted_result = sorted(result, key=lambda item : item['difference'], reverse=True)

		if len(sorted_result) >= int(self.msgs_info[list_index]['filters']['profit']['max_items']) and int(self.msgs_info[list_index]['filters']['profit']['max_items']) <= 200:
			max_result = int(self.msgs_info[list_index]['filters']['profit']['max_items'])
		else:
			max_result = len(sorted_result)
		
		self.msgs_info[list_index]['result'] = []
		
		for item in range(0, max_result):
			self.msgs_info[list_index]['result'].append(sorted_result[item])
	
	def messages_to_reply(self):
		for msg in self.msgs_info:
			msg['reply'] = ''
			msg['reply'] += '*' * 10 + EOL
			msg['reply'] +=  'msg_id: {0}'.format(msg['msg_id']) + EOL
			msg['reply'] +=  'sender_id: {0}'.format(msg['sender_id']) + EOL
			if 'result' in msg:
				msg['reply'] += 'result_len: {0}'.format(len(msg['result'])) + EOL
				msg['reply'] += '{0:30}|{1:15}|{2:15}|{3:15}'.format(
                                            'Item name',
                                            'Sell Average',
                                            'Buy average',
                                            'Profit',) + EOL
				for result in msg['result']:
                                    msg['reply'] += '{0:30}|{1:15}|{2:15}|{3:15}'.format(
						result['name'],
						result['sell_average'],
						result['buy_average'],
						result['difference'],)  + EOL
	
	def retrieve_messages(self):
		return self.msgs_info
		
	def create_list_filters(self):
		filter_count = 0
		for index in range(0, self.total_msgs):
			self.msgs_info[index]['filters'] = {}
			for func_dict in self.filter_params:
				if func_dict['name'] in self.msgs_info[index]['text']:
					self.fill_filter(func_dict, index)
					self.filter_params[filter_count]['callable'](list_index=index)
				filter_count += 1
			filter_count = 0
				
	def fill_filter(self, func, list_index):
		self.msgs_info[list_index]['filters'][func['nickname']] = {}
		for msg_text_param in self.msgs_info[list_index]['text'].splitlines():
			for filter_param in func['params']:
				if filter_param[0] in msg_text_param:
					self.msgs_info[list_index]['filters'][func['nickname']][filter_param[0]] = msg_text_param.split(':')[1]
				else: 
					self.msgs_info[list_index]['filters'][func['nickname']][filter_param[0]] = str(filter_param[1])
		
msg_controller = message_control()
msg_controller.get_msgs()
msg = msg_controller.get_msgs_info()

ge_controller = api_data_control()
ge = ge_controller.get_data()

filters = filter_control(msgs_info=msg, api_info=ge)
filters.create_list_filters()
filters.messages_to_reply()

msg_controller.reply_msgs(msgs_info=filters.retrieve_messages())		

