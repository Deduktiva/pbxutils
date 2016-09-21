#!/usr/bin/env python3

# Needs python 3.4+

MUTE_STATE = {}

import sys
import configparser
import telnetlib
import subprocess

with open('pbxmute.conf', 'r', encoding='utf-8') as c:
    config_items = [l.split('=', 1) for l in c.read().splitlines() if not l.startswith('#') and '=' in l]
    config = {k.strip(): v.strip() for (k, v) in config_items}

WATCHED_CHANNELS = config['watched_channels'].split(' ')
MUTE_SWITCH = config['mute_switch']
MANAGER_HOSTNAME = config['manager_hostname']
MANAGER_PORT = int(config.get('manager_port', '5038'))
MANAGER_USERNAME = config['manager_username']
MANAGER_PASSWORD = config['manager_password']
RESTART_ON_ERROR = bool(config.get('restart_on_error', 'true'))

LOGIN_MSG = """Action: Login
Username: %s
Secret: %s

""" % (MANAGER_USERNAME, MANAGER_PASSWORD)


def expect_string(tn, s):
    result = wait_newline(tn)
    if result != s:
        print("Expected %r, got %r instead" % (s, result))
        sys.exit(1)


def wait_until(tn, s):
    while True:
        result = tn.read_until(s, timeout=1)
        if result != b'':
            return result


def wait_newline(tn):
    return wait_until(tn, b"\r\n").rstrip(b"\r\n")


def print_block(tn):
    while True:
        result = wait_newline(tn)
        if result == b"":
            break
        print(result)


def read_block(tn):
    block = {}
    while True:
        result = wait_newline(tn)
        if result == b"":
            break
        entry = result.decode('utf-8').split(': ', 1)
        if len(entry) == 1:
            block[entry[0]] = ''
        else:
            block[entry[0]] = entry[1]
    return block


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
    print("Connecting...")
    t = telnetlib.Telnet(MANAGER_HOSTNAME, MANAGER_PORT)
    wait_until(t, b"Asterisk Call Manager/1")
    print("Connected.")
    t.write(LOGIN_MSG.encode('utf-8'))
    wait_until(t, b"Message: ")
    expect_string(t, b"Authentication accepted")

    connected_channels = {}
    print("Logged in, waiting for events...")
    while True:
        wait_until(t, b"Event: ")
        eventtype = wait_newline(t)
        event = read_block(t)
        if eventtype in [b'Newstate', b'Hangup']:
            channel = concerns_watched_channel(event)
            if channel:
                uniqueid = event['Uniqueid']
                connected_channels.setdefault(channel, [])
                if eventtype == b'Newstate' and event['ChannelStateDesc'] == 'Up':
                    connected_channels[channel].append(uniqueid)
                    print("Channel %s now connected on call %s" % (channel, uniqueid))
                elif eventtype == b'Hangup':
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
