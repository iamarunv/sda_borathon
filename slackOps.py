import os, time
from slackclient import SlackClient

# debug mode
DEBUG = True
def log(s):
    if DEBUG:
        print(s)

# default slack channel
slackChannel = "admin-queue"

# get the token from os environment
def getSlackToken ():
    # hard code the token as of now
    slack_token = None
    try:
        slack_token = os.environ["SLACK_API_TOKEN"]
    except KeyError:
        slack_token = None
        pass
    return slack_token

# establish slack connection
def connectToSlack():
    uToken = getSlackToken()
    if uToken:
        log("Received token:%s" % uToken)
    else:
        uToken = input("No token found, please enter a Slack token:")

    sc = SlackClient(uToken)
    if sc.rtm_connect():
        log("Successfully connected to Slack service...")
        return sc
    else:
        print("Connection failed, invalid token.")
        exit(1)

recId = 0
policyCreate_json =[
    {
        "text": "Choose an action to perform",
        "fallback": "You are unable to choose an action",
        "callback_id": recId,
        "color": "#3AA3E3",
        "attachment_type": "default",
        "actions": [
            {
                "name": "accept",
                "text": "Yes",
                "style": "primary",
                "type": "button",
                "value": 1
            },
            {
                "name": "policy",
                "text": "Yes and Remember",
                "type": "button",
                "value": 1
            },
            {
                "name": "ignore",
                "text": "Ignore",
                "style": "danger",
                "type": "button",
                "value": 0
            }
        ]
    }
]

def sendMsg (group, msg):
    sc = connectToSlack()
    sc.rtm_send_message(group, msg)
    return 0

# prompt the user to take an action on recommendation
def promptRec(recId, msg):
    recId = recId
    sc = connectToSlack()
    log("recID=%d, msg=%s" % (recId, msg))
    sc.api_call(
        "chat.postMessage",
        channel=slackChannel,
        text=msg,
        attachments=policyCreate_json
    )
