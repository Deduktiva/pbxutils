# asterisk manager utility scripts

## General

`watched_channels` is a space separated list.

The manager user does not need any write rights, and only needs `read=call` rights.

Example `manager.conf` entry:

    [pbxnotify]
    secret=pbxnotify
    deny=0.0.0.0/0.0.0.0
    permit=127.0.0.1/255.255.255.255
    read=call


## notify_incoming_call

Notify pushover.net client on call ringing.

## pbxmute

Mutes ALSA channel on call pickup (and unmutes on hang up).

