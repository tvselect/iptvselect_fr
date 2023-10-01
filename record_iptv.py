import logging
import subprocess
import argparse
import time
from datetime import datetime
from configparser import ConfigParser

parser = argparse.ArgumentParser()
parser.add_argument("title")
parser.add_argument("provider")
parser.add_argument("recorder")
parser.add_argument("m3u8_link")
parser.add_argument("duration")
parser.add_argument("save")
args = parser.parse_args()

config_iptv_select = ConfigParser()
config_iptv_select.read("iptv_select_conf.ini")

logging.basicConfig(
    filename="/var/tmp/record_{title}_{save}.log".format(
        title=args.title, save=args.save
    ),
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)


date_now_epoch = datetime.now().timestamp()
end_video = date_now_epoch + int(args.duration)

record_position = 0

cmd = "echo $USER"
echo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
stdout, stderr = echo.communicate()
user = stdout.decode("utf-8")[:-1]


def start_or_kill():
    """
    Write time recording beginning in start_time files or kill
    recorder command"
    """
    cmd = (
        "ls /home/$USER/videos_select/{title}-save/{title}"
        "_{provider}_{record_position}_{save}.ts".format(
            title=args.title,
            provider=args.provider,
            record_position=record_position,
            save=args.save,
        )
    )
    ls_file = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    stdout, stderr = ls_file.communicate()
    ls_video = stdout.decode("utf-8")[:-1]

    if (
        ls_video
        == "/home/"
        + user
        + "/videos_select/{title}-save/{title}_{provider}_{record_position}_{save}.ts".format(
            title=args.title,
            provider=args.provider,
            record_position=record_position,
            save=args.save,
        )
    ):
        time_now_epoch = datetime.now().timestamp()
        time_movie = round(time_now_epoch - 30)

        logging.info("Started!!!!")

        with open(
            "/home/" + user + "/videos_select/{title}-save/start_time_{title}_"
            "{provider}_{save}.txt".format(
                title=args.title, provider=args.provider, save=args.save
            ),
            "a",
        ) as file:
            file.write(str(time_movie) + "\n")
    else:
        cmd = (
            "ps -ef | grep {title}_{provider}_{record_position}_"
            "{save}.ts | tr -s ' ' | cut -d ' ' -f2 | head -n 2".format(
                title=args.title,
                provider=args.provider,
                record_position=record_position,
                save=args.save,
            )
        )
        stdout = subprocess.check_output(cmd, shell=True)
        pid_stream = int(stdout.decode("utf-8").split("\n")[:-1][1])

        cmd = "kill {pid_stream}".format(pid_stream=pid_stream)
        kill = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )

        logging.info("killed!!!")


"""
    Check if the number of process belonging to the
    iptv provider is below the maximum allowed:
"""

max_iptv_provider = 0
config_iptv_select_keys = ["iptv_provider", "iptv_backup", "iptv_backup_2"]

for key in config_iptv_select.keys():
    if str(key) != "DEFAULT":
        for iptv_function in config_iptv_select_keys:
            if config_iptv_select[str(key)][iptv_function] == args.provider:
                max_iptv_provider += 1

cmd = "ps aux | grep -wc 'record_iptv.py .* {provider}'".format(provider=args.provider)
pid_record = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
stdout, stderr = pid_record.communicate()
proc_count_provider = stdout.decode("utf-8")[:-1]

if int(proc_count_provider) - 2 > max_iptv_provider:
    logging.info("max_iptv_provider:" + str(max_iptv_provider))
    logging.info("proc_count_provider:" + str(proc_count_provider))
    logging.info(
        "La vidéo {title} ne sera pas enregistrée car vous n'avez pas assez de lignes"
        " de fournisseurs d'IPTV pour cet enregistrement".format(title=args.title)
    )
    exit()

date_now = datetime.now().timestamp()

cmd = "mkdir -p /home/$USER/videos_select/{title}-save/{title}-to-watch".format(
    title=args.title
)
mk_dir = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
mk_dir.wait()


file_size = 0
new_file_size = 1

while date_now < end_video:
    if args.recorder == "ffmpeg":
        cmd = (
            "ps aux | grep -c 'ffmpeg -i {m3u8_link} -c:v copy'".format(
                m3u8_link=args.m3u8_link,
            )
        )
        pid_record = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        stdout, stderr = pid_record.communicate()
        proc_count = stdout.decode("utf-8")[:-1]

    elif args.recorder == "streamlink":
        cmd = (
            "ps aux | grep -c '{title}_{provider}_{record_position}"
            "_{save}.ts -f {m3u8_link}'".format(
                title=args.title,
                provider=args.provider,
                record_position=record_position,
                save=args.save,
                m3u8_link=args.m3u8_link,
            )
        )
        pid_record = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        stdout, stderr = pid_record.communicate()
        proc_count = stdout.decode("utf-8")[:-1]

    elif args.recorder == "vlc":
        cmd = (
            "ps aux | grep -c '\-v {m3u8_link} --sout="
            "file/ts:/home/.*/videos_select/{title}-save/{title}_"
            "{provider}_{record_position}_{save}.ts'".format(
                m3u8_link=args.m3u8_link,
                title=args.title,
                provider=args.provider,
                record_position=record_position,
                save=args.save,
            )
        )
        pid_record = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        stdout, stderr = pid_record.communicate()
        proc_count = stdout.decode("utf-8")[:-1]
        cmd = (
            "du /home/$USER/videos_select/{title}-save/{title}_{provider}_{record_position}"
            "_{save}.ts | cut -f1".format(
                title=args.title,
                provider=args.provider,
                record_position=record_position,
                save=args.save,
            )
        )
        du_cmd = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        stdout, stderr = du_cmd.communicate()
        try:
            new_file_size = int(stdout.decode("utf-8")[:-1])
        except ValueError:
            new_file_size = 0

    elif args.recorder == "mplayer":
        cmd = "ps aux | grep -c 'mplayer {m3u8_link} -dumpstream'".format(
            m3u8_link=args.m3u8_link
        )
        pid_record = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        stdout, stderr = pid_record.communicate()
        proc_count = stdout.decode("utf-8")[:-1]

    date_now = datetime.now().timestamp()
    left_time = round(end_video - date_now)

    if left_time <= 0:
        if args.recorder == "vlc":
            cmd = (
                "ps -ef | grep '\-v {m3u8_link} --sout="
                "file/ts:/home/.*/videos_select/{title}-save/{title}' "
                "| tr -s ' ' | cut -d ' ' -f2".format(
                    m3u8_link=args.m3u8_link, title=args.title
                )
            )
        elif args.recorder == "mplayer":
            cmd = (
                "ps -ef | grep 'mplayer {m3u8_link} -dumpstream "
                "-dumpfile /home/.*/videos_select/{title}-save' "
                "| tr -s ' ' | cut -d ' ' -f2".format(
                    m3u8_link=args.m3u8_link, title=args.title
                )
            )
        pid_range = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        stdout, stderr = pid_range.communicate()
        pid_list = stdout.decode("utf-8").split("\n")[:-1]

        for pid in pid_list:
            cmd = "kill {pid_stream}".format(pid_stream=int(pid))
            kill = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            logging.info("kill last process")
        break

    new_file = False

    if int(proc_count) < 3 or (args.recorder == "vlc" and file_size == new_file_size):
        logging.info("!!!! New file !!!!!!!")

        record_position += 1

        if args.recorder == "ffmpeg":
            cmd = (
                "ffmpeg -i {m3u8_link} -c:v copy -c:a copy -t {left_time} "
                "-f mpegts -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 1"
                " -reconnect_at_eof -y /home/$USER/videos_select/"
                "{title}-save/{title}_{provider}_{record_position}_{save}.ts"
                " >> /var/tmp/infos_{title}_{provider}_{record_position}_{save}.log "
                "2>&1".format(
                    m3u8_link=args.m3u8_link,
                    left_time=left_time,
                    title=args.title,
                    provider=args.provider,
                    record_position=record_position,
                    save=args.save,
                )
            )
            record = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )

            time.sleep(30)

            start_or_kill()


        if args.recorder == "streamlink":
            cmd = (
                "streamlink --http-no-ssl-verify --hls-live-restart "
                "--hls-segment-threads 10 --hls-segment-timeout 10 --stream-segment-attempts 100 "
                "--retry-streams 1 --retry-max 100 --hls-duration 00:{left_time} -o "
                "/home/$USER/videos_select/{title}-save/{title}_{provider}_{record_position}"
                "_{save}.ts -f {m3u8_link} best >> "
                "/var/tmp/infos_{title}_{provider}_{record_position}_{save}.log "
                "2>&1".format(
                    left_time=left_time,
                    title=args.title,
                    provider=args.provider,
                    record_position=record_position,
                    save=args.save,
                    m3u8_link=args.m3u8_link,
                )
            )
            record = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )

            time.sleep(30)

            start_or_kill()

        elif args.recorder == "vlc":
            record_position_last = record_position - 1

            cmd = (
                "ps -ef | grep {title}_{provider}_{record_position}_"
                "{save}.ts | tr -s ' ' | cut -d ' ' -f2 | "
                "head -n 2".format(
                    title=args.title,
                    provider=args.provider,
                    record_position=record_position_last,
                    save=args.save,
                )
            )
            stdout = subprocess.check_output(cmd, shell=True)
            pid_vlc = int(stdout.decode("utf-8").split("\n")[:-1][1])
            cmd = "kill {pid_vlc}".format(pid_vlc=pid_vlc)
            kill = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )

            cmd = (
                "cvlc -v --run-time={left_time} {m3u8_link} --sout=file/ts:/home/$USER/videos_select"
                "/{title}-save/{title}_{provider}"
                "_{record_position}_{save}.ts "
                ">> /var/tmp/infos_{title}_{provider}"
                "_{record_position}_{save}.log 2>&1".format(
                    left_time=left_time,
                    m3u8_link=args.m3u8_link,
                    title=args.title,
                    provider=args.provider,
                    save=args.save,
                    record_position=record_position,
                )
            )
            record = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )

            time.sleep(30)

            cmd = (
                "du /home/$USER/videos_select/{title}-save/{title}"
                "_{provider}_{record_position}"
                "_{save}.ts | cut -f1".format(
                    title=args.title,
                    provider=args.provider,
                    record_position=record_position,
                    save=args.save,
                )
            )
            logging.info("cmd:" + cmd)
            du_cmd = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            stdout, stderr = du_cmd.communicate()

            try:
                logging.info("stdout:" + stdout.decode("utf-8")[:-1])
                file_size = int(stdout.decode("utf-8")[:-1])
                new_file = True
            except ValueError:
                file_size = 0
                new_file = False

            start_or_kill()

        elif args.recorder == "mplayer":
            cmd = (
                "mplayer {m3u8_link} -dumpstream -dumpfile "
                "/home/$USER/videos_select/{title}-save/{title}_{provider}"
                "_{record_position}_{save}.ts >> /var/tmp/infos_{title}_{provider}"
                "_{record_position}_{save}.log 2>&1".format(
                    m3u8_link=args.m3u8_link,
                    title=args.title,
                    provider=args.provider,
                    save=args.save,
                    record_position=record_position,
                )
            )
            record = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )

            time.sleep(30)

            start_or_kill()

    if new_file is False and args.recorder == "vlc":
        logging.info("new_file:" + str(new_file))
        file_size = new_file_size

    time.sleep(40)
