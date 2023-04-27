import logging
import os
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import csv
load_dotenv()
app = Flask(__name__)
slack_client = WebClient(token=os.environ['SLACK_APP_TOKEN'])
csv_file = 'messages.csv'


def save_message_to_csv(sender_id, receiver_id, message):
    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([sender_id, receiver_id, message])


@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        user_id, message = request.form.get('text').split(' ', 1)
    except Exception as e:
        logging.error(f"Error parsing text parameter: {e}")
        return jsonify({'error': 'Failed to parse user_id and message'}), 400

    try:
        response = slack_client.users_info(user=user_id)
        user = response['user']
    except SlackApiError as e:
        logging.error(f"Failed to get user info: {e}")
        return jsonify({'error': f"Failed to get user info: {e}"}), 500

    try:
        response = slack_client.conversations_open(users=[user_id])
        channel_id = response['channel']['id']
    except SlackApiError as e:
        logging.error(f"Failed to open a conversation: {e}")
        return jsonify({'error': f"Failed to open a conversation: {e}"}), 500

    try:
        slack_client.chat_postMessage(channel=channel_id, text=message)
        save_message_to_csv(user['id'], user_id, message)
        return jsonify({'status': 'ok'})
    except SlackApiError as e:
        logging.error(f"Failed to send the message: {e}")
        return jsonify({'error': f"Failed to send the message: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
