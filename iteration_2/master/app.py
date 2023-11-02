from flask import Flask, request, jsonify
from collections import OrderedDict
from functools import partial
import requests
import logging
import concurrent.futures
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')
app = Flask(__name__)

# Initialize messages as an empty dict
messages = {}
idx = 0


@app.route('/add-message', methods=['POST'])
def add_log():
    global idx
    # app.logger.info(f"Current value idx: {idx}")

    idx += 1
    # app.logger.info(f"Updated value idx: {idx}")

    try:
        secondaries = request.args.getlist('secondary')
    except KeyError as e:
        app.logger.info(f"Error - {e}. Please set 'secondary' parameter in POST request url")
        return jsonify({"message": "Please set 'secondary' parameter in POST request url"})

    try:
        write_concern = int(request.args.get('concern'))
    except KeyError as e:
        app.logger.info(f"Error - {e}. Please set 'concern' parameter in POST request url")
        return jsonify({"message": "Please set 'concern' parameter in POST request url"})

    if request.is_json:
        data = request.json
        try:
            msg = data['entry']
            app.logger.info(f"New message - '{msg}' - was created in correct JSON format")

            tmp_msg_info = {idx: msg}
            # app.logger.info(f"Current dict msg: {tmp_msg_info}")

            # avoid message deduplication
            if msg not in messages.values():
                if write_concern < 1 or write_concern > 3:
                    app.logger.info("'concern' parameter has an invalid value.Please set the value between 1 and 3.")
                    return jsonify({"message": "Please set 'concern' parameter to value between 1 and 3."})
                elif write_concern == 1:
                    messages.update(tmp_msg_info)
                    app.logger.info(f"Message - '{msg}' - was saved on Master. Master's POST request started")
                    post_request_results = [replicate_to_secondary(url=url_secondary,
                                                                   msg=msg,
                                                                   msg_idx=idx)
                                            for url_secondary in secondaries]
                    if False in post_request_results:
                        return jsonify({"message": f"Error sending request with message - '{msg}' "})
                    else:
                        return jsonify({"message": f"Message - '{msg}' - was saved on all servers"})
                else:
                    app.logger.info("Master's POST request started")
                    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
                    the_futures = [
                        executor.submit(partial(replicate_to_secondary, msg=msg, msg_idx=idx), link)
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
                        # app.logger.info(f"Added dict msg to Master messages: {tmp_msg_info}")
                        messages.update(tmp_msg_info)
                        app.logger.info("Master's POST request finished")
                        return jsonify({"message": "New message added and replicated successfully"})
            else:
                app.logger.info(f"Message - '{msg}' - already exists on Master")
                return jsonify({"message": f"Message - '{msg}' - already exists on Master"})
        except KeyError as e:
            app.logger.info(f"Error - {e}. Please set 'entry' key to JSON file")
            return jsonify({"message": "Please set 'entry' key to JSON file"})
    else:
        app.logger.info("Missing JSON in request")
        return jsonify({"message": "Missing JSON in request"})


def replicate_to_secondary(url, msg, msg_idx):
    try:
        app.logger.info(f"Sent message - '{msg}' - from Master to Secondary server {url}")
        response = requests.post(f"{url}/replicate-log", json={"id": msg_idx, "entry": msg})
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
    if not messages:
        app.logger.info(f"No messages saved on Master yet")
        return jsonify({"message": "No messages saved on Master yet"})
    else:
        ord_msgs = OrderedDict(sorted(messages.items()))
        app.logger.info(f"Ordered list of messages: {ord_msgs}")
        if list(ord_msgs.keys()) == [k for k in range(1, len(ord_msgs.keys()) + 1)]:
            app.logger.info(f"List of messages on Master server - {ord_msgs}")
            return jsonify({"messages": ord_msgs})
        else:
            app.logger.info(f"Wait until all messages are saved on Master server {request.host_url}")
            return jsonify({"messages": "Wait until all messages are saved on Master server"})


if __name__ == '__main__':
    app.run(host=os.getenv('HOST'), port=int(os.getenv('PORT')), debug=False)
