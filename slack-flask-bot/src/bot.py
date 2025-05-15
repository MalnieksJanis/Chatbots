from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

class SlackBot:
    def __init__(self, token):
        self.client = WebClient(token=token)

    def send_message(self, channel, text, blocks=None):
        try:
            self.client.chat_postMessage(channel=channel, text=text, blocks=blocks)
        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")