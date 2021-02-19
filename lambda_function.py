from json import dumps
from os import environ
from botocore.vendored import requests

SLACK_TOKEN = environ['SLACK_TOKEN']
CHANNEL = environ['SLACK_CHANNEL']
SlackEmoji = ':warning:'
DisplayName = 'AWS-SG-Change-Alert'
AlertColor = '#FF8C00'


def get_changes(event):
    """ Function to extract details from Cloudtrail event """
    #print('Event-Received:', event)
    change_type = event.get("detail").get("eventName")
    user_account = (event.get("detail").get("userIdentity").get("userName") if event.get("detail").get(
        "userIdentity").get("userName") else event.get("detail").get("userIdentity").get("type"))

    sg_id = [val for key, val in event.get("detail").get("requestParameters").items() if 'Id' in key]
    if not sg_id:
        sg_id = event.get("detail").get("requestParameters").get("groupName")
    else:
        sg_id = sg_id[0]
    changes = dumps((event.get("detail").get("requestParameters").get("ipPermissions") if event.get("detail").get(
        "requestParameters").get("ipPermissions") else event.get("detail").get("requestParameters")), indent=1)
    timestamp = event.get("detail").get("eventTime")
    region = event.get("detail").get("awsRegion")
    return change_type, user_account, sg_id, changes, timestamp, region


def send_slack_alert(change_type, user_account, sg_id, changes, timestamp, region):
    """ Function to send Slack alert """
    if changes == "None":
        slack_data = {"channel": CHANNEL, "icon_emoji": SlackEmoji, "username": DisplayName, "attachments": [
            {"color": AlertColor, "title": 'Change-type: '+change_type+'\n AWS-Region: '+region+'\n ID/Name: '+sg_id+'\n Timestamp: '+timestamp+'\n AWS-User: '+user_account, "text": 'Rule-Changes: ```'+change_type+'```'}]}
    else:
        slack_data = {"channel": CHANNEL, "icon_emoji": SlackEmoji, "username": DisplayName, "attachments": [
            {"color": AlertColor, "title": 'Change-type: '+change_type+'\n AWS-Region: '+region+'\n ID/Name: '+sg_id+'\n Timestamp: '+timestamp+'\n AWS-User: '+user_account, "text": 'Rule-Changes: ```'+changes+'```'}]}
    response = requests.post(SLACK_TOKEN, data=dumps(slack_data), headers={
                             'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError('Slack Error Code: %s \nError Detail -\n%s' %
                         (response.status_code, response.text))


def lambda_handler(event, context):
    """ AWS Lambda function handler to get Cloudtrail event """
    change_type, user_account, sg_id, changes, timestamp, region = get_changes(
        event)
    send_slack_alert(change_type, user_account, sg_id,
                     changes, timestamp, region)
    return event