; example service for systemd
; cp notify_incoming_call.service.tpl /etc/systemd/system/notify_incoming_call.service
; systemctl enable notify_incoming_call.service && systemctl start notify_incoming_call.service

[Unit]
After=asterisk.service

[Service]
EnvironmentFile=-/etc/default/locale
WorkingDirectory=/home/notifycall/pbxutils
ExecStart=/home/notifycall/pbxutils/notify_incoming_call.py
User=notifycall
Restart=on-failure

[Install]
WantedBy=multi-user.target
