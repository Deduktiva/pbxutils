#!/usr/bin/env python3

# Needs python 3.4+

import sys
import telnetlib


LOGIN_TPL = """Action: Login
Username: %s
Secret: %s

"""


def read_config(filename):
    with open(filename, 'r', encoding='utf-8') as c:
        config_items = [l.split('=', 1) for l in c.read().splitlines() if not l.startswith('#') and '=' in l]
        config = {k.strip(): v.strip() for (k, v) in config_items}
    return config


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


def read_block(tn, blocktype):
    wait_until(tn, blocktype.encode('utf-8') + b": ")
    v = wait_newline(tn).decode('utf-8')
    block = {blocktype: v}
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


def connect(hostname, port, username, password):
    print("Connecting...")
    t = telnetlib.Telnet(hostname, port)
    wait_until(t, b"Asterisk Call Manager/1")
    print("Connected.")
    t.write((LOGIN_TPL % (username, password)).encode('utf-8'))
    wait_until(t, b"Message: ")
    expect_string(t, b"Authentication accepted")
    return t
