from flask import Flask, request, jsonify
import requests
import logging
import concurrent.futures
from functools import partial

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

        write_concern = int(request.args.get('concern'))

        if write_concern == 1:
            messages.append(msg)
            app.logger.info(f"Message - '{msg}' - was saved on Master")
            return jsonify({"message": f"Master's POST request finished. Message - '{msg}' - was saved on Master"})
        else:
            # Replicate the log to all secondary servers and wait for acknowledgments
            app.logger.info("Master's POST request started")
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            the_futures = [
                executor.submit(partial(replicate_to_secondary, msg=msg), link)
                for link in secondaries
            ]
            if write_concern == 2:
                done_futures, not_done_futures = concurrent.futures.wait(
                    the_futures,
                    return_when=concurrent.futures.FIRST_COMPLETED
                )
                executor.shutdown(cancel_futures=True, wait=False)
            elif write_concern == 3:
                done_futures, not_done_futures = concurrent.futures.wait(
                    the_futures,
                    return_when=concurrent.futures.ALL_COMPLETED
                )
                executor.shutdown(cancel_futures=False, wait=True)

            acks = 0
            for future in done_futures:
                result = future.result()
                if result:
                    acks += 1

            if write_concern == 2:
                if acks == 1:
                    messages.append(msg)
                    app.logger.info(f"Master's POST request finished")
                    return jsonify({"message": "New message added and replicated successfully"})
            elif write_concern == 3:
                if acks == len(secondaries):
                    messages.append(msg)
                    app.logger.info(f"Master's POST request finished")
                    return jsonify({"message": "New message added and replicated successfully"})
            else:
                app.logger.info("Missing JSON in request")
                return jsonify({"message": "Missing JSON in request"})


def replicate_to_secondary(url, msg):
    try:
        app.logger.info(f"Sent message - '{msg}' - from Master to Secondary server {url}")
        response = requests.post(f"{url}/replicate-log", json={"entry": msg})
        if response.ok:
            app.logger.info(f"Message - '{msg}' - received by Secondary server {url}")
            return True
        else:
            app.logger.info(
                f"Message - '{msg}' - failed for Secondary server {url}. {response.status_code} status response ")
            return False
    except requests.exceptions.RequestException as e:
        app.logger.info(f"Error sending request with message - '{msg}' - for Secondary server {url} - {str(e)}")
        return False


@app.route('/get-message', methods=['GET'])
def get_log():
    app.logger.info(f"ALl messages on Master server - {messages}")
    return jsonify({"messages": messages})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)