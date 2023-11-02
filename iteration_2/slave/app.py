from flask import Flask, request, jsonify
from collections import OrderedDict
import time
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')

app = Flask(__name__)

# Initialize the replication log as an empty list
# replicated_logs = []
replicated_logs = {}
global idx
idx = 0

@app.route('/replicate-log', methods=['POST', 'GET'])
def replicate_log():
    if request.method == 'POST':
        data = request.json
        msg = data['entry']
        msg_id = data['id']
        app.logger.info(f"Message: {msg}, message ID: {msg_id}")

        sec_sleep = int(os.getenv('TIME_SLEEP_IN_SEC'), 0)

        app.logger.info(f"Secondary server - {request.host_url}, sleep time - {sec_sleep} sec")
        # Introduce a sleep to simulate replication delay
        time.sleep(sec_sleep)

        if msg_id in replicated_logs.keys():
            app.logger.info(f"Message - '{msg}' - already exists on Secondary server - {request.host_url}")
            return jsonify({"message": f"Message - '{msg}' - already exists on Secondary server - {request.host_url}"})
        else:
            # Append a new message to the replication log
            replicated_logs.update({msg_id: msg})
            app.logger.info(f"List of messages on POST stage Secondary server - {request.host_url} - {replicated_logs}")
            return jsonify({"message": "Log entry replicated successfully"})
    else:
        if not replicated_logs:
            app.logger.info(f"No messages received by Secondary server {request.host_url}")
            return jsonify({"message": "No messages received yet"})
        else:
            app.logger.info(f"List of messages on GET stage Secondary server - {request.host_url} - {replicated_logs}")
            ord_replicated_logs = OrderedDict(sorted(replicated_logs.items()))
            if list(ord_replicated_logs.keys()) == [idx for idx in range(1, len(ord_replicated_logs.keys()) + 1)]:
                app.logger.info(f"List of messages on Secondary server {request.host_url} - {ord_replicated_logs}")
                return jsonify({"messages": ord_replicated_logs})
            else:
                app.logger.info(f"Wait until all messages are saved on Secondary server {request.host_url}")
                return jsonify({"messages": "Wait until all messages are saved on Secondary server"})

            # while list(ord_replicated_logs.keys()) != [idx for idx in range(1, len(ord_replicated_logs.keys())+1)]:
            #     continue




if __name__ == '__main__':
    app.run(host=os.getenv('HOST'), port=int(os.getenv('PORT')))