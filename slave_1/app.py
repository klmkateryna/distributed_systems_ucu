from flask import Flask, request, jsonify
import time
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')

app = Flask(__name__)

# Initialize the replication log as an empty list
replicated_logs = []


@app.route('/replicate-log', methods=['POST', 'GET'])
def replicate_log():
    if request.method == 'POST':
        data = request.json
        msg = data['entry']

        sec_sleep = 10

        app.logger.info(f"Sleep time for Secondary server - {sec_sleep} sec")
        # Introduce a sleep to simulate replication delay
        time.sleep(sec_sleep)

        # Append a new message to the replication log
        replicated_logs.append(msg)
        app.logger.info(f"Received message - '{msg}'")

        return jsonify({"message": "Log entry replicated successfully"})
    else:
        if not replicated_logs:
            app.logger.info("No messages received by Secondary server")
            return jsonify({"message": "No messages received yet"})
        else:
            app.logger.info(f"ALl messages on Secondary server - {replicated_logs}")
            return jsonify({"messages": replicated_logs})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
