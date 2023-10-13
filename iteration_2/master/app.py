from flask import Flask, request, jsonify
import requests
import logging
import concurrent.futures
from functools import partial
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')
app = Flask(__name__)

# Initialize messages as an empty list
messages = []


@app.route('/add-message', methods=['POST'])
def add_log():
    if request.is_json:
        data = request.json
        try:
            msg = data['entry']

            secondaries = request.args.getlist('secondary')
            app.logger.info(f"New message - '{msg}' - was created in correct JSON format")

            write_concern = int(request.args.get('concern'))

            if write_concern < 1 or write_concern > 3:
                app.logger.info("'concern' parameter has an invalid value.Please set the value between 1 and 3.")
                return jsonify({"message": "Please set 'concern' parameter to value between 1 and 3."})
            elif write_concern == 1:
                messages.append(msg)
                app.logger.info(f"Message - '{msg}' - was saved on Master")
                return jsonify({"message": f"Message - '{msg}' - was saved on Master"})
            else:
                if secondaries:
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

                    if (write_concern == 2 and acks == 1) or (write_concern == 3 and acks == len(secondaries)):
                        messages.append(msg)
                        app.logger.info("Master's POST request finished")
                        return jsonify({"message": "New message added and replicated successfully"})
                    # if write_concern == 2:
                    #     if acks == 1:
                    #         messages.append(msg)
                    #         app.logger.info(f"Master's POST request finished")
                    #         return jsonify({"message": "New message added and replicated successfully"})
                    # elif write_concern == 3:
                    #     if acks == len(secondaries):
                    #         messages.append(msg)
                    #         app.logger.info(f"Master's POST request finished")
                    #         return jsonify({"message": "New message added and replicated successfully"})
                else:
                    app.logger.info(f"Message - '{msg}' - failed to replicate. "
                                    "Please set the correct name for 'secondary' parameter in POST request url")
                    return jsonify({"message": "Failed to replicate new message."
                                               "Please set the correct name for 'secondary' parameter in POST request "
                                               "url"})
        except KeyError as e:
            app.logger.info(f"Error - {e}. Please set 'entry' key to JSON file")
            return jsonify({"message": "Please set 'entry' key to JSON file"})
    else:
        app.logger.info("Missing JSON in request")
        return jsonify({"message": "Missing JSON in request"})


def replicate_to_secondary(url, msg):
    try:
        app.logger.info(f"Sent message - '{msg}' - from Master to Secondary server {url}")
        response = requests.post(f"{url}/replicate-log", json={"entry": msg})
        if response.ok:
            app.logger.info(f"Master got ACK from Secondary server {url} : message '{msg}' received")
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
    app.run(host=os.getenv('HOST_MASTER'), port=int(os.getenv('PORT_MASTER')), debug=False)
