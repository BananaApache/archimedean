
import sys
import os
import json
import requests
from bs4 import BeautifulSoup as bs
import smtplib
import datetime

home = os.getenv('HOME')
archimedean_file_path = os.path.join(home, '.archimedean')
creds_file_path = os.path.join(home, '.archimedean', 'creds.json')
hw_file_path = os.path.join(home, '.archimedean', 'homework_file.txt')


class styles:
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    cyan = '\u001b[36m'
    white = '\u001b[37m'
    clear = '\x1b[2K'
    line_up = '\033[1A'


if not os.path.isdir(os.path.join(home, '.archimedean')):
    os.makedirs(os.path.join(home, '.archimedean'))


def read_json():
    creds = json.load(open(creds_file_path, 'r'))
    print(creds['username'])
    print(creds['password'])


def write_json():
    creds = {
        "username": "1",
        "password": "2"
    }

    open(creds_file_path, 'w+').write(json.dumps(creds, indent=4))


def login():
    "Login to Archie"
    print()

    username = input("Enter Archie's username: ")
    password = input("Enter Archie's password: ")

    if not os.path.isdir(archimedean_file_path):
        os.makedirs(archimedean_file_path)

    creds = {
        "username": username,
        "password": password
    }

    open(creds_file_path, 'w+').write(json.dumps(creds, indent=4))

    print(styles.green + "\nSaved credentials. You can now login to Archie.\n")


def get_creds():
    "Get user's credentials from ~/.archimedean/creds.txt"
    creds = json.load(open(creds_file_path, 'r'))
    return creds['username'], creds['password']


def cinemath():
    "Download all of a class's cinemath files"
    if not os.path.isfile(creds_file_path):
        print(
            styles.red + "\nRun 'archimedean login' first to save your credentials.\n")
        exit()

    usr = tuple(get_creds())[0]
    pswd = tuple(get_creds())[1]

    payload = {
        "username": usr,
        "password": pswd
    }

    with requests.Session() as s:
        r = s.post("http://cinemath.archimedean.org/index.php", data=payload)
        r = s.get("http://cinemath.archimedean.org/menu.php?school=auc")
        soup = bs(r.content, 'html.parser')

        classes = {}

        for a in soup.findAll("a"):
            if str(a).split()[2].startswith("onclick=\"load_lesson("):
                classes.update({a.text: a['onclick'].split("'")[1]})

    print()

    i = 1
    for cls in classes:
        print(styles.yellow, i, " = ", cls)
        i += 1

    print()
    usr_num = int(
        input(styles.green + "Which class to choose? " + styles.white))
    class_name = list(classes.items())[usr_num - 1][1]

    r = requests.get(
        f"http://cinemath.archimedean.org/toc_generic.php?class_name={class_name}")
    soup = bs(r.content, 'html.parser')

    total_lessons = soup.findAll('a')[-1].text.split()[-1]

    for i in range(2, int(total_lessons) + 1):
        r = requests.get(
            f"http://cinemath.archimedean.org/load_jpeg.php?class_name={class_name}&lesson_number={i}")
        soup = bs(r.content, 'html.parser')

        if soup.prettify().strip() != "There is no teacher notes for this lesson":
            for img in soup.findAll('img'):
                src = img['src']
                img_data = requests.get(src).content
                lesson = src.split("/")[7]

                if not os.path.isdir(os.path.join(home, 'Downloads', str(list(classes.items())[usr_num - 1][0]))):
                    os.makedirs(os.path.join(home, 'Downloads', str(
                        list(classes.items())[usr_num - 1][0])))

                with open(os.path.join(home, 'Downloads', str(list(classes.items())[usr_num - 1][0]), f"{str(lesson)}.jpg"), 'wb') as handler:
                    handler.write(img_data)

                print(
                    str(styles.cyan),
                    f"\nDownloading files to '{os.path.join(home, 'Downloads', str(list(classes.items())[usr_num - 1][0]))}'. Lessons left:" + str(
                        styles.yellow), str(int(total_lessons) - i),
                    end="")
                print(styles.line_up, end=styles.clear)


def email():
    "Set up email to notify when there is new homeworks"
    if not os.path.isfile(creds_file_path):
        print(
            styles.red + "\nRun 'archimedean login' first to save your credentials.\n")
        exit()

    user_email = input(
        "Enter the email account that will receive new homework messages: ")

    usr = tuple(get_creds())[0]
    pswd = tuple(get_creds())[1]

    login_data = {"login_name": usr,
                  "passwd": pswd, "submit": "Login"}

    url = "https://sis.archimedean.org/sis/default.php"

    with requests.Session() as s:
        r = s.post(url, data=login_data)
        soup = bs(r.content, 'html.parser')
        # print(soup.prettify())
        hw_url = "https://sis.archimedean.org/sis/course_wall.php"
        r = s.get(hw_url)
        soup = bs(r.content, 'html.parser')

    html_hw_lst = soup.findAll('td', nowrap='nowrap')
    html_duedate_lst = soup.findAll('td', nowrap='nowrap')
    html_teacher_lst = soup.findAll('td', nowrap='nowrap')
    duedate_lst_unf = []
    hw_lst = []
    teacher_lst = []
    duedate_lst = []

    for duedate in html_duedate_lst:
        duedate.findNext('td')
        duedate = duedate.findNext('td')
        duedate = duedate.findNext('td')
        duedate = duedate.findNext('td')
        duedate_lst_unf.append(duedate.get_text())

    for date_f in duedate_lst_unf:
        date_f = date_f.split("-")
        duedate_lst.append(str(date_f[1]) + "/" +
                           str(date_f[2] + "/" + str(date_f[0])))

    for hw in html_hw_lst:
        hw_lst.append(hw.get_text())

    for teacher in html_teacher_lst:
        teacher = teacher.findNext('td')
        teacher = teacher.findNext('td')
        teacher = teacher.findNext('td')
        teacher = teacher.findNext('td')
        teacher = teacher.findNext('td')
        teacher_lst.append(teacher.get_text())

    if os.path.isfile(hw_file_path):
        file_hw = open(hw_file_path, "r")

        check_prev = ''
        check_prev += ''.join(hw_lst)

        hw_str = file_hw.read()

        if hw_str == check_prev:
            print("\n", styles.green, "No changes in homework", styles.white, "\n")
        else:
            print("\nNew Homework")
            print("\n", styles.cyan, "Changes in homework detected", styles.white)
            print("\n", styles.green, "Sending mail...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('anotheroneofmyemailacc@gmail.com',
                         'aedsspcvcmoymnvs')

            current_time = datetime.datetime.now()
            current_time = current_time.strftime("%-I:%M %p")

            current_date = datetime.datetime.now()
            current_date = current_date.strftime("%B %d")

            homework = ' '.join(hw_lst)

            homework = ''

            for i in range(len(hw_lst)):
                homework += '' + \
                    hw_lst[i] + " for " + teacher_lst[i] + \
                    " is due on " + duedate_lst[i] + "\n\n"

            mail = 'Subject: {}\n\n{}'.format(
                "New Archie HW | " + str(current_date) + " " + str(current_time), homework)

            server.sendmail('anotheroneofmyemailacc@gmail.com',
                            user_email, mail)
            print("\n", styles.red, "Mail sent!\n", styles.white)

            for i in range(len(hw_lst)):
                print(styles.green + hw_lst[i] + styles.white + " for " + styles.cyan + teacher_lst[i] +
                      styles.white + " is due at " + styles.yellow + duedate_lst[i] + styles.white)

            file_hw = open(hw_file_path, "w")

            for write in hw_lst:
                file_hw.write(write)

    else:
        file_hw = open(hw_file_path, "w+")

        for write in hw_lst:
            file_hw.write(write)

        print("\nNew Homework")
        print("\n", styles.cyan, "Changes in homework detected", styles.white)
        print("\n", styles.green, "Sending mail...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('anotheroneofmyemailacc@gmail.com',
                     'aedsspcvcmoymnvs')

        current_time = datetime.datetime.now()
        current_time = current_time.strftime("%-I:%M %p")

        current_date = datetime.datetime.now()
        current_date = current_date.strftime("%B %d")

        homework = ' '.join(hw_lst)

        homework = ''

        for i in range(len(hw_lst)):
            homework += '' + \
                hw_lst[i] + " for " + teacher_lst[i] + \
                " is due on " + duedate_lst[i] + "\n\n"

        mail = 'Subject: {}\n\n{}'.format(
            "New Archie HW | " + str(current_date) + " " + str(current_time), homework)

        server.sendmail('anotheroneofmyemailacc@gmail.com', user_email, mail)

        print("\n", styles.red, "Mail sent!\n", styles.white)
