from flask import Flask, request, jsonify
import requests
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')
app = Flask(__name__)

# Initialize messages as an empty list
messages = []


@app.route('/add-message', methods=['POST'])
def add_log():
    if request.is_json:
        data = request.json
        msg = data['entry']

        secondaries = request.args.getlist('secondaries')
        app.logger.info(f"New message - '{msg}' - was created in correct JSON format")

        # Replicate the log to all secondary servers and wait for acknowledgments
        app.logger.info("Master's POST request started")
        acks = replicate_log_to_secondaries(msg, secondaries)
        app.logger.info("Master's POST request finished")

        if len(acks) == len(secondaries):
            # Append a new message to messages list
            messages.append(msg)

            app.logger.info(f"Message - '{msg}' - replicated successfully to Secondary servers")
            return jsonify({"message": "New message added and replicated successfully"})
        else:
            app.logger.info(f"Message - '{msg}' - failed to replicate")
            return jsonify({"message": "Failed to replicate new message"})

    else:
        app.logger.info("Missing JSON in request")
        return jsonify({"message": "Missing JSON in request"})


def replicate_log_to_secondaries(msg, secondaries):
    acks = []

    for url in secondaries:
        try:
            response = requests.post(f"{url}/replicate-log", json={"entry": msg})
            app.logger.info(f"Sent message - '{msg}' - from Master to Secondary server {url}")
            if response.ok:
                acks.append(url)
                app.logger.info(f"Message - '{msg}' - received by Secondary server {url}")
            else:
                app.logger.info(f"Message - '{msg}' - failed for Secondary server {url}. {response.status_code} status response ")
        except requests.exceptions.RequestException as e:
            app.logger.info(f"Error sending request with message - '{msg}' - for Secondary server {url} - {str(e)}")

    return acks


@app.route('/get-message', methods=['GET'])
def get_log():
    app.logger.info(f"ALl messages on Master server - {messages}")
    return jsonify({"messages": messages})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
