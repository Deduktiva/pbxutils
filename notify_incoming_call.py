#!/usr/bin/env python3

import pbxutils
import requests


config = pbxutils.read_config('notify_incoming_call.conf')

WATCHED_CHANNELS = config['watched_channels'].split(' ')
PUSHOVER_TOKEN = config['pushover_token']
PUSHOVER_USER = config['pushover_user']
MANAGER_HOSTNAME = config['manager_hostname']
MANAGER_PORT = int(config.get('manager_port', '5038'))
MANAGER_USERNAME = config['manager_username']
MANAGER_PASSWORD = config['manager_password']
NOTIFY_TITLE = config['notify_title']

PUSHOVER_URL = 'https://api.pushover.net/1/messages.json'


def concerns_watched_channel(block):
    for channel in WATCHED_CHANNELS:
        if block['Channel'].startswith(channel + '-'):
            return channel
    return False


def notify(title, message):
    data = {
        'token': PUSHOVER_TOKEN,
        'user': PUSHOVER_USER,
        'title': title,
        'message': message,
    }
    print('notify:', data)
    requests.post(PUSHOVER_URL, data=data)


def run():
    t = pbxutils.connect(MANAGER_HOSTNAME, MANAGER_PORT, MANAGER_USERNAME, MANAGER_PASSWORD)
    print("Logged in, waiting for events...")
    while True:
        event = pbxutils.read_block(t, 'Event')
        eventtype = event['Event']
        if eventtype == 'Newstate':
            channel = concerns_watched_channel(event)
            if channel and event['ChannelStateDesc'] == 'Ringing':
                print(event)
                if ('+' + event['CallerIDNum']) != event['CallerIDName']:
                    message = '%s %s' % (event['CallerIDName'], event['CallerIDNum'])
                else:
                    message = '%s' % (event['CallerIDName'], )
                notify(NOTIFY_TITLE, message)


if __name__ == '__main__':
    run()
