#!/usr/bin/env python3

# Needs python 3.4+

MUTE_STATE = {}

import pbxutils
import subprocess


config = pbxutils.read_config('pbxmute.conf')

WATCHED_CHANNELS = config['watched_channels'].split(' ')
MUTE_SWITCH = config['mute_switch']
MANAGER_HOSTNAME = config['manager_hostname']
MANAGER_PORT = int(config.get('manager_port', '5038'))
MANAGER_USERNAME = config['manager_username']
MANAGER_PASSWORD = config['manager_password']
RESTART_ON_ERROR = bool(config.get('restart_on_error', 'true'))


def concerns_watched_channel(block):
    for channel in WATCHED_CHANNELS:
        if block['Channel'].startswith(channel + '-'):
            return channel
    return False


def any_connected(connected_channels):
    for (channel, connections) in connected_channels.items():
        if connections != []:
            return True
    return False


def amixer_cset(on):
    cmd = ['amixer', 'cset', MUTE_SWITCH, 'on' if on else 'off']
    print('Running: %s' % cmd)
    subprocess.Popen(cmd).communicate()


def amixer_cget():
    cmd = ['amixer', 'cget', MUTE_SWITCH]
    print('Running: %s' % cmd)
    (stdout, _) = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True).communicate()
    lines = stdout.splitlines()
    for line in lines:
        if line.startswith('  : '):
            _, on = line.lstrip('  : ').split('=')
            return on == 'on'
    print("E: could not get amixer state from stdout: %r" % lines)
    return False


def update_mute_state(mute_required):
    print("Should set mute state to %s" % mute_required)
    MUTE_STATE.setdefault('was_mute_required', False)
    if MUTE_STATE['was_mute_required'] == mute_required:
        print("Mute state was not changed")
        return
    MUTE_STATE['was_mute_required'] = mute_required
    if mute_required:
        print('MUTE')
        MUTE_STATE['was_externally_muted'] = amixer_cget()
        amixer_cset(not mute_required)
    else:
        print('UNMUTE')
        amixer_cset(not mute_required)


def run():
    t = pbxutils.connect(MANAGER_HOSTNAME, MANAGER_PORT, MANAGER_USERNAME, MANAGER_PASSWORD)
    connected_channels = {}
    print("Logged in, waiting for events...")
    while True:
        event = pbxutils.read_block(t, 'Event')
        eventtype = event['Event']
        if eventtype in ['Newstate', 'Hangup']:
            channel = concerns_watched_channel(event)
            if channel:
                uniqueid = event['Uniqueid']
                connected_channels.setdefault(channel, [])
                if eventtype == 'Newstate' and event['ChannelStateDesc'] == 'Up':
                    connected_channels[channel].append(uniqueid)
                    print("Channel %s now connected on call %s" % (channel, uniqueid))
                elif eventtype == 'Hangup':
                    connected_channels[channel].remove(event['Uniqueid'])
                    print("Channel %s now disconnected from call %s" % (channel, uniqueid))
                update_mute_state(any_connected(connected_channels))
            print()


if __name__ == '__main__':
    if RESTART_ON_ERROR:
        while True:
            try:
                run()
            except Exception as except_inst:
                print("\n\n\nRestarting, Crashed with:", except_inst)
    else:
        run()
