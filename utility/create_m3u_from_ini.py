import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("provider")
parser.add_argument("m3u_file")
args = parser.parse_args()

cmd = "echo $USER"
echo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
stdout, stderr = echo.communicate()
user = stdout.decode("utf-8")[:-1]

try:
    with open(
        "/home/{user}/.config/iptv_box/iptv_providers/{provider}.ini".format(
            user=user, provider=args.provider
        ),
        "r",
    ) as ini:
        first_line = ini.readline()
        lines = ini.read().splitlines()
except FileNotFoundError:
    print(
        "Le fichier {provider}.ini n'est pas présent dans le dossier "
        "~/.config/iptv_box/iptv_providers. Vous devez renseigner "
        "comme premier argument le fichier avec l'extension .ini puis "
        "en 2ème argument celui avec l'extension .m3u. Les noms des fichiers "
        "doivent être renseignés sans les extensions.".format(provider=args.provider)
    )
    exit()

try:
    with open(
        "/home/{user}/.config/iptv_box/iptv_providers/{m3u_file}.m3u".format(
            user=user, m3u_file=args.m3u_file
        ),
        "r",
    ) as ini:
        first_line = ini.readline()
        lines_m3u = ini.read().splitlines()
except FileNotFoundError:
    print(
        "Le fichier {m3u_file}.m3u n'est pas présent dans le dossier "
        "~/.config/iptv_box/iptv_providers. Vous devez renseigner comme "
        "premier argument le fichier avec l'extension .ini puis en 2ème "
        "argument celui avec l'extension .m3u. Les noms des fichiers doivent "
        "être renseignés sans les extensions.".format(m3u_file=args.m3u_file)
    )
    exit()

with open(
    "/home/{user}/videos_select/{provider}_testvlc.m3u".format(
        user=user, provider=args.provider
    ),
    "w",
) as outfile:
    for line in lines:
        chan_info = line.split(" = ")
        if len(chan_info) > 1 and chan_info[1] != "":
            for n in range(len(lines_m3u)):
                if lines_m3u[n] == chan_info[1]:
                    outfile.write(lines_m3u[n - 1] + "---" + chan_info[0] + "\n")
                    outfile.write(chan_info[1] + "\n")
                    break
