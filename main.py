
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import time, datetime
import sys
import schedule

global is_test
is_test = False

def check_crypto(config_json, last_sent):
	print("Debug: Job Started " + str(datetime.datetime.utcnow()))
	total_message = ""
	special_message = ""
	data = get_cmcprices(config_json)
	if not data:
		return
	if not "data" in data:
		return
	for crypto in data["data"].values():
		for quote_key in crypto["quote"]:
			if quote_key != "USD":
				continue
			quote = crypto["quote"][quote_key]
			total_message += crypto["symbol"] + ": " + str(quote["price"]) + "\n"
			if not "checks" in config_json:
				continue
			for checker in config_json["checks"]:
				if crypto["symbol"] != checker["symbol"]:
					continue
				if crypto["symbol"] != checker["symbol"]:
					continue
				if checker["type"] == "lowerthan" and quote["price"] < checker["value"]:
					if not checker["name"] in last_sent or not last_sent[checker["name"]]:
						special_message += "{0} price has plummeted below {1}.\n".format(checker["symbol"], checker["value"])
					last_sent[checker["name"]] = True
				elif checker["type"] == "greaterthan" and quote["price"] > checker["value"]:
					if not checker["name"] in last_sent or not last_sent[checker["name"]]:
						special_message += "{0} price has risen above {1}.\n".format(checker["symbol"], checker["value"])
					last_sent[checker["name"]] = True
				else:
					last_sent[checker["name"]] = False
	print(total_message)
	if special_message != "":
		if is_test:
			print("message (not sent):" + special_message)
		else:
			message_pushover(special_message, config_json)
	sys.stdout.flush()
	sys.stderr.flush()

def get_cmcprices(config_json):
	url = config_json["cmcurl"]
	parameters = {
		'symbol':'BTC,ETH,BNB,USDT,ADA,DOGE'
	}
	headers = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': config_json["cmckey"],
	}
	session = Session()
	session.headers.update(headers)
	try:
		data = {}
		if is_test:
			with open("test.json", "r") as check_file:
				data = json.loads(check_file.read())
		else:
			response = session.get(url, params=parameters)
			data = json.loads(response.text)
		return data
	except (ConnectionError, Timeout, TooManyRedirects) as e:
		print(e)
		return None

def message_pushover(message, config_json):
	url = config_json["pushoverurl"]
	parameters = {
		'token': config_json["pushovertoken"],
		'user': config_json["pushoveruser"],
		'message': message
	}
	headers = {
		'Accepts': 'application/json'
	}
	session = Session()
	session.headers.update(headers)
	try:
		response = session.post(url, params=parameters)
		data = json.loads(response.text)
	except (ConnectionError, Timeout, TooManyRedirects) as e:
		print(e)

def main():
	args = sys.argv[1:]
	if "-test" in args:
		global is_test
		is_test = True
	config_json = {}
	last_sent = {}
	with open("config.json", "r") as check_file:
		config_json = json.loads(check_file.read())
	check_crypto(config_json, last_sent)

	if is_test:
		schedule.every(5).seconds.do(lambda: check_crypto(config_json, last_sent))
	else:
		schedule.every(20).minutes.do(lambda: check_crypto(config_json, last_sent))

	while True:
		schedule.run_pending()
		time.sleep(1)

if __name__ == "__main__":
	main()
