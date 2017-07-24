from flask import Flask, request, make_response
from slackclient import SlackClient

# bot user token
<<<<<<< HEAD:src/restBot.py
SLACK_BOT_TOKEN = "xoxb-216284053943-MgI9cATVnvLRB4tby0OiELpB"
=======
SLACK_BOT_TOKEN = os.environ["SLACK_API_TOKEN"]
>>>>>>> f5b242c8973d57f8aae77a31edd697f074af96ab:restBot.py
sc = SlackClient(SLACK_BOT_TOKEN)

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)

@app.route("/slack/message_actions", methods=["POST"])
def message_actions():

    # Parse the request payload
    from_json = json.loads(request.form["payload"])
    user = from_json["user"]["name"]
    orgMsg = from_json["original_message"]["text"]

    # Check to see what the user's selection was and update the message
    select = from_json["actions"][0]["name"]

    if select == "accept":
        msgText = "The recommendation is accepted successfully!"
    elif select == "policy":
        msgText = "The policy has been added successfully!"
    else:
        msgText = "No action to perform"

    response = sc.api_call(
      "chat.update",
      channel=from_json["channel"]["id"],
      ts=from_json["message_ts"],
      text=orgMsg,
      attachments=[
          {
           "replace_original": "true",
           "color": "#36a64f",
           "text": "`@%s`:%s" %(user, msgText),
           "mrkdwn_in": ["text"]
           }

      ]
    )

    return make_response("", 200)

if __name__ == "__main__":
    app.run()
