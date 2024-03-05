import subprocess
import readline
import random
import getpass

cmd = "timedatectl | grep -i 'Time zone' | tr -s ' ' | cut -d ' ' -f4"
output = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
stdout, stderr = output.communicate()
timezone = stdout.decode("utf-8")[:-1]

answers = ["oui", "non"]
answer = "maybe"

if timezone != "Europe/Paris":
    print(
        "Le fuseau horaire de votre box IPTV est {timezone}. Le fuseau horaire qui "
        "doit être configuré est 'Europe/Paris'. Si vous ne voulez pas changer de "
        "fuseau horaire, contactez-nous pour configurer votre box TV afin de "
        "pouvoir l'utiliser avec un fuseau horaire différent "
        "de 'Europe/Paris'.".format(timezone=timezone)
    )
    while answer.lower() not in answers:
        answer = input(
            "Voulez-vous changer le fuseau horaire pour 'Europe/Paris'?"
            " (répondre oui ou non): "
        )
    if answer.lower() == "oui":
        cmd = "sudo timedatectl set-timezone Europe/Paris"
        timezo = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        timezo.wait()
        print(
            "\nImportant: Veuillez rédemarrer la box IPTV puis relancer le programme install.py\n"
        )
        exit()
    else:
        exit()

cmd = "ls ~ | grep ^videos_select$"
output = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
stdout, stderr = output.communicate()
ls_directory = stdout.decode("utf-8")[:-1]

if ls_directory == "":
    cmd = "mkdir ~/videos_select"
    directory = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    directory.wait()
    print("Le dossier videos_select a été créé dans votre dossier home.\n")

cmd = "mkdir -p ~/.local/share/iptv_box ~/.config/iptv_box"
directories = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
directories.wait()
print("Les dossiers ~/.config/iptv_box et ~/.local/share/iptv_box ont "
      "été créés.\n")


print("Configuration des tâches cron du programme IPTV-select:\n")

cmd = 'curl -I https://iptv-select.fr | grep HTTP | tail -1 | cut -d " " -f 2'
http = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
stdout, stderr = http.communicate()
http_response = stdout.decode("ascii")[:-1]

if http_response != "200":
    print(
        "\nLa box IPTV-select n'est pas connectée à internet. Veuillez "
        "vérifier votre connection internet et relancer le programme "
        "d'installation.\n\n"
    )
    exit()

username = input(
    "Veuillez saisir votre identifiant de connexion (adresse "
    "email) sur IPTV-select.fr: "
)
password_iptvrecord = getpass.getpass(
    "Veuillez saisir votre mot de passe sur IPTV-select.fr: "
)

cmd = "ls -a ~ | grep ^.netrc$"
output = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
stdout, stderr = output.communicate()
ls_netrc = stdout.decode("utf-8")[:-1]

if ls_netrc == "":
    cmd = "touch ~/.netrc"
    touch = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    touch.wait()
    cmd = "chmod go= ~/.netrc"
    chmod = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )

cmd = "echo $USER"
echo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
stdout, stderr = echo.communicate()
user = stdout.decode("utf-8")[:-1]

authprog_response = "403"

with open("/home/" + user + "/.netrc", "r") as file:
    lines_origin = file.read().splitlines()

while authprog_response != "200":
    with open("/home/" + user + "/.netrc", "r") as file:
        lines = file.read().splitlines()

    try:
        position = lines.index("machine www.iptv-select.fr")
        lines[position + 1] = "  login {username}".format(username=username)
        lines[position + 2] = "  password {password_iptvrecord}".format(
            password_iptvrecord=password_iptvrecord
        )
    except ValueError:
        lines.append("machine www.iptv-select.fr")
        lines.append("  login {username}".format(username=username))
        lines.append(
            "  password {password_iptvrecord}".format(
                password_iptvrecord=password_iptvrecord
            )
        )

    with open("/home/" + user + "/.netrc", "w") as file:
        for line in lines:
            file.write(line + "\n")

    cmd = (
        'curl -iSn https://www.iptv-select.fr/api/v1/prog | grep HTTP | cut -d " " -f 2'
    )

    authprog = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    stdout, stderr = authprog.communicate()
    authprog_response = stdout.decode("ascii")[:-1]

    if authprog_response != "200":
        try_again = input(
            "Le couple identifiant de connexion et mot de passe "
            "est incorrect.\nVoulez-vous essayer de nouveau?(oui ou non): "
        )
        answer_hide = "maybe"
        if try_again.lower() == "oui":
            username = input(
                "Veuillez saisir de nouveau votre identifiant de connexion (adresse email) sur IPTV-select.fr: "
            )
            while answer_hide.lower() not in answers:
                answer_hide = input(
                    "Voulez-vous afficher le mot de passe que vous saisissez "
                    "pour que cela soit plus facile? (répondre par oui ou non): "
                )
            if answer_hide.lower() == "oui":
                password_iptvrecord = input(
                    "Veuillez saisir de nouveau votre mot de passe sur IPTV-select.fr: "
                )
            else:
                password_iptvrecord = getpass.getpass(
                    "Veuillez saisir de nouveau votre mot de passe sur IPTV-select.fr: "
                )
        else:
            with open("/home/" + user + "/.netrc", "w") as file:
                for line in lines_origin:
                    file.write(line + "\n")
            exit()


heure = random.randint(6, 23)
minute = random.randint(0, 58)
minute_2 = minute + 1

cmd = "crontab -l > cron_tasks.sh"
crontab_init = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
)
crontab_init.wait()

with open("cron_tasks.sh", "r") as crontab_file:
    cron_lines = crontab_file.readlines()

curl = (
    "{minute} {heure} * * * export USER='{user}' && "
    "curl -H 'Accept: application/json;"
    "indent=4' -n "
    "https://www.iptv-select.fr/api/v1/prog > /home/$USER/.local/share"
    "/iptv_box/info_progs.json 2>> /var/tmp/cron_curl.log\n".format(
        user=user,
        minute=minute,
        heure=heure,
    )
)

cron_launch = (
    "{minute_2} {heure} * * * export USER='{user}' && "
    "cd /home/$USER/iptv_box && "
    "bash cron_launch_record.sh\n".format(user=user, minute_2=minute_2, heure=heure)
)

cron_lines = [curl if "iptv_box/info_progs.json" in cron else cron for cron in cron_lines]
cron_lines = [cron_launch if "iptv_box &&" in cron else cron for cron in cron_lines]

cron_lines_join = "".join(cron_lines)

if "iptv_box/info_progs.json" not in cron_lines_join:
    cron_lines.append(curl)
if "cd /home/$USER/iptv_box &&" not in cron_lines_join:
    cron_lines.append(cron_launch)

with open("cron_tasks.sh", "w") as crontab_file:
    for cron_task in cron_lines:
        crontab_file.write(cron_task)

cmd = "crontab cron_tasks.sh"
cron = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
cron.wait()
cmd = "rm cron_tasks.sh"
rm = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

print("\nLes tâches cron de votre box IPTV-select sont maintenant configurés!\n")
