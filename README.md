# server_stats
script to collect some stats

# INSTALL
```
cd /root/
git clone git@github.com:evgenypim/server_stats.git
cd ./server_stats/etc
cp ./stats.yaml.example ./stats.yaml
vi ./stats.yaml
ln -sf /root/server_stats/etc/stats.yaml /etc/
```
# Dependencies
apt-get install python-yaml python-psutil

# Config description
Config file path: /etc/stats.yaml - regular yaml file.
```
#API key and URL
api_key: abc123
api_url: https://api.url.com

# For disks subsystem stats
disks:
        # Mount points for free/used stats per mountpoint
        mount_points:
                - /home
                - /

        # Block devs fo o|i stats
        block_devs:
                - sda1
                - dm-0

        # full paths to dirs for dir size stats
        dirs_size:
                - /mnt/media/
                - /tmp/

# For network subsystem
networking:
        interfaces:
                - enp3s0
                - br0

apache_logs:
# List of keys. The key is the value used in dim2
        - website1:
                # The glob of the files to scan for
                file: /var/log/apache2/log_website1*.log
                # The optional regex of the URI to process. This only processes php files.
                # It is regular Python regular expr.
                # see https://docs.python.org/2/library/re.html#regular-expression-syntax
                url_filter: .php
        - website2:
                file: /var/log/apache2/log_website2*.log
```
