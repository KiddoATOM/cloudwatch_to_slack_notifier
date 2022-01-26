#!/usr/bin/env python3

import boto3
import json
import logging
import os

from botocore.exceptions import ClientError

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)



def send_to_slack(slack_message, slack_webhook_url):
    status = True
    LOGGER.info("sending slack message")

    req = Request(slack_webhook_url, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        LOGGER.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        LOGGER.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        LOGGER.error("Server connection failed: %s", e.reason)

    return status


def get_slack_webhook_url(ssm_parm):
    ssm_client = boto3.client('ssm')
    slack_url = None

    try:
        response = ssm_client.get_parameter(Name=ssm_parm, WithDecryption=True)
        slack_url = response['Parameter']['Value']

    except ClientError as e:
        print("Unexpected error getting SSM param: "+ e.response['Error']['Code'])
    
    return slack_url


def lambda_handler(event, context):
    LOGGER.info('REQUEST RECEIVED: {}'.format(json.dumps(event, default=str)))

    message = json.loads(event['Records'][0]['Sns']['Message'])
    LOGGER.info("Message: " + str(message))

    slack_channel = os.environ['SLACK_CHANNEL']
    slack_webhook_ssm_parm = os.environ['SSM_SLACK_WEBHOOK']
    region = os.environ['AWS_REGION']

    slack_webhook_url = get_slack_webhook_url(slack_webhook_ssm_parm)
    environment = os.environ['ENVIRONMENT'].title()

    # Pull data out of the alarm message
    alarm_name = message['AlarmName']
    new_state = message['NewStateValue']
    reason = message['NewStateReason']
    region_str = message['Region']
    metric_namespace = message['Trigger']['Namespace']
    metric_name = message['Trigger']['MetricName']

    if 'Statistic' in message['Trigger']:
        metric_statistic = message['Trigger']['Statistic']
    elif 'StatisticType' in message['Trigger']:
        metric_statistic = message['Trigger']['StatisticType'] + "(" + message['Trigger']['ExtendedStatistic'] + ")"

    if 'Threshold' in message['Trigger']:
        alarm_threshold = message['Trigger']['Threshold']
        alarm_threshold = format(alarm_threshold,",")
    else:
        alarm_threshold = "n/a"

    if 'EvaluationPeriods' in message['Trigger']:
        eval_periods = message['Trigger']['EvaluationPeriods']
    else:
        eval_periods = "n/a"
    if new_state == "OK":
        color = "#16C616"
    else:
        color = "#EC0030"

    alarm_console_link = "https://console.aws.amazon.com/cloudwatch/home?region=" + region + "#alarm:alarmFilter=ANY;name=" + alarm_name
    slack_message = "[*" + environment + "*]Cloudwatch Alarm `" + alarm_name + "` is in state _" + new_state + "_ in " + region_str

    slack_attachment = [
        {
            "fallback": "Check the Cloudwatch console for details.",
            "color": color,
            "title": "View Alarm Details in the AWS Console",
            "text": reason,
            "title_link": alarm_console_link,
            "fields": [
                {
                    "title": "Threshold",
                    "value": str(alarm_threshold),
                    "short": 'false'
                },
                {
                    "title": "Evals Over/Lower Threshold",
                    "value": str(eval_periods),
                    "short": 'false'
                },
                {
                    "title": "Namespace",
                    "value": metric_namespace,
                    "short": 'false'
                },
                {
                    "title": "Metric",
                    "value": metric_name,
                    "short": 'false'
                }
            ]
        }
    ]

    slack_body = {
        'username': "",
        'icon_url': "https://upload-icon.s3.us-east-2.amazonaws.com/uploads/icons/png/1349651671536126578-512.png",
        'channel': slack_channel,
        'attachments': slack_attachment,
        'text': slack_message
    }

    if slack_webhook_url:
        status = send_to_slack(slack_body, slack_webhook_url)
    else:
        logger.error("Unable to obtain the Slack webhook URL to post to")

    return status

