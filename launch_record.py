import logging
import json
import subprocess
from configparser import ConfigParser
from datetime import datetime, timedelta

config_iptv_select = ConfigParser()
config_iptv_select.read("iptv_select_conf.ini")

logging.basicConfig(
    filename="/var/tmp/cron_launch_record.log",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)


def start_fusion_calcul(start_f):
    minutes = ["58", "59"]
    if start_f[-2:] not in minutes:
        if int(start_f[-2:]) > 7:
            return start_f[:-2] + str(int(start_f[-2:]) + 2)
        else:
            return start_f[:-2] + "0" + str(int(start_f[-2:]) + 2)
    else:
        return start_f[:-2] + str(int(start_f[-2:]) - 2)


config_iptv_select_keys = ["iptv_provider", "iptv_backup", "iptv_backup_2"]


class Provider:
    """Define a provider"""

    def __init__(self, iptv_provider, time_last):
        self.iptv_provider = iptv_provider
        self.time_last = time_last

    def max_iptv(self, config_iptv_select):
        """
        Calcul the maximum number of process allowed for an
        iptv provider.
        """
        self.config_iptv_select = config_iptv_select

        max_iptv_provider = 0

        for key in self.config_iptv_select.keys():
            if str(key) != "DEFAULT":
                for iptv_function in config_iptv_select_keys:
                    if (
                        self.config_iptv_select[str(key)][iptv_function]
                        == self.iptv_provider
                    ):
                        max_iptv_provider += 1

        return max_iptv_provider


providers = {}

for key in config_iptv_select.keys():
    if str(key) != "DEFAULT":
        for iptv_function in config_iptv_select_keys:
            iptv_prov = config_iptv_select[str(key)][iptv_function]
            if iptv_prov not in providers.keys():
                providers[iptv_prov] = Provider(iptv_prov, {})


with open("info_progs.json", "r") as jsonfile:
    data = json.load(jsonfile)

try:
    with open("info_progs_last.json", "r") as jsonfile:
        data_last = json.load(jsonfile)
except FileNotFoundError:
    data_last = []

dates_late = []

for video in data_last:
    date_video = datetime(
        year=int(video["start"][:4]),
        month=int(video["start"][4:6]),
        day=int(video["start"][6:8]),
        hour=int(video["start"][8:10]),
        minute=int(video["start"][10:]),
    ) + timedelta(seconds=int(video["duration"]))
    if date_video > datetime.now():
        dates_late.append(date_video)

provider_rank = 1

while provider_rank < 5:
    try:
        provider = config_iptv_select["PROVIDER_" + str(provider_rank)]
    except KeyError:
        logging.warning(
            "Le fichier iptv_select_conf.ini n'est pas configuré. "
            "Assurez-vous de le configurer au moyen du script configparser_iptv.py."
        )
        exit()
    if provider["iptv_provider"] != "":
        provider_iptv_recorded = provider["iptv_provider"]
        rank_provider_iptv_recorded = str(provider_rank) + provider_iptv_recorded
        if len(dates_late) > 0:
            providers[provider_iptv_recorded].time_last[
                rank_provider_iptv_recorded
            ] = dates_late[0]
            dates_late.pop(0)
        else:
            providers[provider_iptv_recorded].time_last[
                rank_provider_iptv_recorded
            ] = datetime.now()
    provider_rank += 1


start_records = []
start_records_fusion = []

for video in data:
    start_records.append(video["start"])
    start_records_fusion.append(video["start_fusion"])

title_last = "kjgfsdkjfghl"
start_last = 202212080820

for video in data:
    provider_rank = 1
    iptv_provider_set = False
    iptv_backup_set = False
    iptv_backup_2_set = False
    video_start = video["start"]
    video_start_datetime = datetime(
        year=int(video_start[:4]),
        month=int(video_start[4:6]),
        day=int(video_start[6:8]),
        hour=int(video_start[8:10]),
        minute=int(video_start[10:]),
    )
    provider_iptv_recorded = "no_provider"
    provider_iptv_backup = "no_backup"
    provider_iptv_backup_2 = "no_backup_2"

    if title_last == video["title"][:10] and video_start == start_last:
        continue

    title_last = video["title"][:10]
    start_last = video_start

    while provider_rank < 5:
        try:
            provider = config_iptv_select["PROVIDER_" + str(provider_rank)]
        except KeyError:
            logging.warning(
                "Le fichier iptv_select_conf.ini n'est pas configuré. "
                "Assurez-vous de le configurer au moyen du script configparser_iptv.py."
            )
            exit()

        if provider["iptv_provider"] != "" and iptv_provider_set is False:
            config_iptv_provider = ConfigParser()
            config_iptv_provider.read(
                "iptv_providers/" + provider["iptv_provider"] + ".ini"
            )
            if len(config_iptv_provider) < 2:
                logging.warning(
                    "Le fichier iptv_select_conf.ini n'est pas configuré correctement "
                    " car le fournisseur d'IPTV renseigné {iptv_provider} ne correspond pas "
                    "à un fichier de configuration du fournisseur se terminant par "
                    "l'extension .ini".format(iptv_provider=provider["iptv_provider"])
                )
                exit()
            try:
                time_last = providers[provider["iptv_provider"]].time_last[
                    str(provider_rank) + provider["iptv_provider"]
                ]
            except KeyError:
                time_last = datetime.now()
            if time_last < video_start_datetime:
                try:
                    m3u8_link = config_iptv_provider["CHANNELS"][
                        video["channel"].lower()
                    ]
                    if m3u8_link != "":
                        cmd = (
                            "echo 'python3 record_iptv.py {title} {provider} {recorder} "
                            "{m3u8_link} {duration} {save} >> /var/tmp/record_{title}_original.log 2>&1' "
                            "| at -t {start_record} >> /var/tmp/cron_launch_record.log "
                            "2>&1".format(
                                title=video["title"],
                                provider=provider["iptv_provider"],
                                recorder=provider["provider_recorder"],
                                m3u8_link=m3u8_link,
                                save="original",
                                duration=video["duration"],
                                start_record=video_start,
                            )
                        )
                        launch = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                        )
                        launch.wait()
                        iptv_provider_set = True
                        provider_iptv_recorded = provider["iptv_provider"]
                        rank_provider_iptv_recorded = (
                            str(provider_rank) + provider_iptv_recorded
                        )
                        providers[provider_iptv_recorded].time_last[
                            rank_provider_iptv_recorded
                        ] = video_start_datetime + timedelta(
                            seconds=int(video["duration"])
                        )
                    else:
                        logging.info(
                            "La chaîne {channel} ne comporte pas de lien m3u dans le fichier "
                            "{file} pour réaliser l'enregistrement de ce programme. "
                            "Le fournisseur d'IPTV {provider_iptv} ne sera donc pas utilisé pour "
                            "enregistrer la vidéo {title}.".format(
                                channel=video["channel"],
                                file=provider["iptv_provider"] + ".ini",
                                provider_iptv=provider["iptv_provider"],
                                title=video["title"],
                            )
                        )
                except KeyError:
                    logging.warning(
                        "La chaîne {channel} n'est pas présente dans le fichier "
                        "{file}. Le fournisseur d'IPTV {provider_iptv} ne sera donc pas utilisé pour "
                        "enregistrer la vidéo {title} .".format(
                            channel=video["channel"],
                            file=provider["iptv_provider"] + ".ini",
                            provider_iptv=provider["iptv_provider"],
                            title=video["title"],
                        )
                    )
            else:
                logging.info(
                    "La position {provider_rank} du fichier "
                    "iptv_select_conf.ini pour le founisseur d'IPTV "
                    "{provider_iptv} n'est pas libre pour enregistrer "
                    "le film {title}.".format(
                        provider_rank=str(provider_rank),
                        provider_iptv=provider["iptv_provider"],
                        title=video["title"],
                    )
                )
                provider_rank += 1
                continue
        else:
            provider_rank += 1
            continue

        if provider["iptv_backup"] != "" and iptv_backup_set is False:
            config_iptv_backup = ConfigParser()
            config_iptv_backup.read(
                "iptv_providers/" + provider["iptv_backup"] + ".ini"
            )
            if len(config_iptv_backup) < 2:
                logging.warning(
                    "Le fichier iptv_select_conf.ini n'est pas configuré correctement "
                    " car le fournisseur d'IPTV renseigné {iptv_backup} ne correspond pas "
                    "à un fichier de configuration du fournisseur se terminant par "
                    "l'extension .ini".format(iptv_backup=provider["iptv_backup"])
                )
                exit()

            try:
                if video_start[-2:] != "59":
                    if int(video_start[-2:]) > 8:
                        video_start_backup = video_start[:-2] + str(
                            int(video_start[-2:]) + 1
                        )
                    else:
                        video_start_backup = (
                            video_start[:-2] + "0" + str(int(video_start[-2:]) + 1)
                        )
                else:
                    video_start_backup = video_start[:-2] + str(
                        int(video_start[-2:]) - 1
                    )
                m3u8_link = config_iptv_backup["CHANNELS"][video["channel"].lower()]
                if m3u8_link != "":
                    cmd = (
                        "echo 'python3 record_iptv.py {title} {provider} {recorder} "
                        "{m3u8_link} {duration} {save} >> /var/tmp/record_{title}_"
                        "backup.log 2>&1' | at -t {start_record} >> /var/tmp/cron"
                        "_launch_record.log 2>&1".format(
                            title=video["title"],
                            provider=provider["iptv_backup"],
                            recorder=provider["backup_recorder"],
                            m3u8_link=m3u8_link,
                            save="backup",
                            duration=video["duration"],
                            start_record=video_start_backup,
                        )
                    )
                    launch = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                    )
                    launch.wait()
                    iptv_backup_set = True
                    provider_iptv_backup = provider["iptv_backup"]
                    if iptv_provider_set is True and provider["iptv_backup_2"] == "":
                        break
                else:
                    logging.info(
                        "La chaîne {channel} ne comporte pas de lien m3u "
                        "dans le fichier {file} pour réaliser l'enregistrement"
                        " de ce programme. Le fournisseur d'IPTV "
                        "{provider_iptv} ne sera donc pas utilisé pour "
                        "enregistrer la 1ère sauvegarde de la vidéo {title} .".format(
                            channel=video["channel"],
                            file=provider["iptv_backup"] + ".ini",
                            provider_iptv=provider["iptv_backup"],
                            title=video["title"],
                        )
                    )

            except KeyError:
                logging.warning(
                    "La chaîne {channel} n'est pas présente dans le fichier "
                    "{file}. Le fournisseur d'IPTV {provider_iptv} ne sera donc pas utilisé pour "
                    "enregistrer la 1ère sauvegarde de la vidéo {title}".format(
                        channel=video["channel"],
                        file=provider["iptv_backup"] + ".ini",
                        provider_iptv=provider["iptv_backup"],
                        title=video["title"],
                    )
                )
        else:
            provider_rank += 1
            continue

        if provider["iptv_backup_2"] != "" and iptv_backup_2_set is False:
            config_iptv_backup_2 = ConfigParser()
            config_iptv_backup_2.read(
                "iptv_providers/" + provider["iptv_backup_2"] + ".ini"
            )
            if len(config_iptv_backup_2) < 2:
                logging.warning(
                    "Le fichier iptv_select_conf.ini n'est pas configuré correctement "
                    " car le fournisseur d'IPTV renseigné {iptv_backup_2} ne correspond pas "
                    "à un fichier de configuration du fournisseur se terminant par "
                    "l'extension .ini".format(iptv_backup_2=provider["iptv_backup_2"])
                )
                exit()

            try:
                if int(video_start[-2:]) < 58:
                    if int(video_start[-2:]) > 7:
                        video_start_backup_2 = video_start[:-2] + str(
                            int(video_start[-2:]) + 2
                        )
                    else:
                        video_start_backup_2 = (
                            video_start[:-2] + "0" + str(int(video_start[-2:]) + 2)
                        )
                else:
                    video_start_backup_2 = video_start[:-2] + str(
                        int(video_start[-2:]) - 2
                    )
                m3u8_link = config_iptv_backup_2["CHANNELS"][video["channel"].lower()]
                if m3u8_link != "":
                    cmd = (
                        "echo 'python3 record_iptv.py {title} {provider} {recorder} "
                        "{m3u8_link} {duration} {save} >> /var/tmp/record_{title}_backup_2.log 2>&1' "
                        "| at -t {start_record} >> /var/tmp/cron_launch_record.log "
                        "2>&1".format(
                            title=video["title"],
                            provider=provider["iptv_backup_2"],
                            recorder=provider["backup_2_recorder"],
                            m3u8_link=m3u8_link,
                            save="backup_2",
                            duration=video["duration"],
                            start_record=video_start_backup_2,
                        )
                    )
                    launch = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                    )
                    launch.wait()
                    iptv_backup_2_set = True
                    provider_iptv_backup_2 = provider["iptv_backup_2"]
                    if iptv_provider_set is True:
                        break
                    else:
                        provider_rank += 1
                else:
                    logging.info(
                        "La chaîne {channel} ne comporte pas de lien m3u dans le fichier "
                        "{file} pour réaliser l'enregistrement de ce programme. "
                        "Le fournisseur d'IPTV {provider_iptv} ne sera donc pas utilisé pour "
                        "enregistrer la 2ème sauvegarde de la vidéo {title} .".format(
                            channel=video["channel"],
                            file=provider["iptv_backup_2"] + ".ini",
                            provider_iptv=provider["iptv_backup_2"],
                            title=video["title"],
                        )
                    )
                    provider_rank += 1
                    continue

            except KeyError:
                logging.warning(
                    "La chaîne {channel} n'est pas présente dans le fichier "
                    "{file}. Le fournisseur d'IPTV {provider_iptv} ne sera donc pas utilisé pour "
                    "enregistrer la 2ème sauvegarde de la vidéo {title}.".format(
                        channel=video["channel"],
                        file=provider["iptv_backup_2"] + ".ini",
                        provider_iptv=provider["iptv_backup_2"],
                        title=video["title"],
                    )
                )
                provider_rank += 1
                continue
        else:
            provider_rank += 1
            continue

    if iptv_provider_set:
        start_fusion_origin = video["start_fusion"]
        if video["start_fusion"] in start_records:
            video["start_fusion"] = start_fusion_calcul(video["start_fusion"])
        if start_records_fusion.count(video["start_fusion"]) > 1:
            if video["start_fusion"] == start_fusion_origin:
                start_records_fusion.remove(video["start_fusion"])
            video["start_fusion"] = start_fusion_calcul(video["start_fusion"])
        cmd = (
            "echo 'python3 fusion_script.py {title} "
            "{provider_iptv_recorded} {provider_iptv_backup} "
            "{provider_iptv_backup_2} >> "
            "/var/tmp/fusion.log 2>&1' | at -t "
            "{start_fusion} >> /var/tmp/cron_launch_record.log "
            "2>&1".format(
                title=video["title"],
                provider_iptv_recorded=provider_iptv_recorded,
                provider_iptv_backup=provider_iptv_backup,
                provider_iptv_backup_2=provider_iptv_backup_2,
                start_fusion=video["start_fusion"],
            )
        )
        fusion = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )


cmd = "cp info_progs.json info_progs_last.json"
cp_info = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
