; example service for systemd
; cp pbxmute.service.tpl /etc/systemd/system/pbxmute.service
; systemctl enable pbxmute.service && systemctl start pbxmute.service

[Unit]
After=asterisk.service

[Service]
EnvironmentFile=-/etc/default/locale
WorkingDirectory=/home/pbxmute/pbxutils
ExecStart=/home/pbxmute/pbxutils/pbxmute.py
User=pbxmute
Restart=on-failure

[Install]
WantedBy=multi-user.target
