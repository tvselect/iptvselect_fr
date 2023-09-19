echo --- crontab start: $(date) >> /var/tmp/cron_launch_record.log

python3 launch_record.py >> /var/tmp/cron_launch_record.log 2>&1

echo --- crontab end: $(date) >> /var/tmp/cron_launch_record.log
