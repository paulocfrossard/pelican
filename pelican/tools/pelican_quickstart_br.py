#!/usr/bin/env python

import argparse
import locale
import os
from typing import Mapping

from jinja2 import Environment, FileSystemLoader

try:
    import zoneinfo
except ModuleNotFoundError:
    from backports import zoneinfo

try:
    import readline  # NOQA
except ImportError:
    pass

try:
    import tzlocal

    if hasattr(tzlocal.get_localzone(), "zone"):
        _DEFAULT_TIMEZONE = tzlocal.get_localzone().zone
    else:
        _DEFAULT_TIMEZONE = tzlocal.get_localzone_name()
except ModuleNotFoundError:
    _DEFAULT_TIMEZONE = "America/Fortaleza"

from pelican import __version__

locale.setlocale(locale.LC_ALL, "")
try:
    _DEFAULT_LANGUAGE = locale.getlocale()[0]
except ValueError:
    # Don't fail on macosx: "unknown locale: UTF-8"
    _DEFAULT_LANGUAGE = None
if _DEFAULT_LANGUAGE is None:
    _DEFAULT_LANGUAGE = "pt"
else:
    _DEFAULT_LANGUAGE = _DEFAULT_LANGUAGE.split("_")[0]

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    trim_blocks=True,
    keep_trailing_newline=True,
)


_GITHUB_PAGES_BRANCHES = {"personal": "main", "project": "gh-pages"}

CONF = {
    "pelican": "pelican",
    "pelicanopts": "",
    "basedir": os.curdir,
    "ftp_host": "localhost",
    "ftp_user": "anonymous",
    "ftp_target_dir": "/",
    "ssh_host": "localhost",
    "ssh_port": 22,
    "ssh_user": "root",
    "ssh_target_dir": "/var/www",
    "s3_bucket": "my_s3_bucket",
    "cloudfiles_username": "my_rackspace_username",
    "cloudfiles_api_key": "my_rackspace_api_key",
    "cloudfiles_container": "my_cloudfiles_container",
    "dropbox_dir": "~/Dropbox/Public/",
    "github_pages_branch": _GITHUB_PAGES_BRANCHES["project"],
    "default_pagination": 10,
    "siteurl": "",
    "lang": _DEFAULT_LANGUAGE,
    "timezone": _DEFAULT_TIMEZONE,
}

# url for list of valid timezones
_TZ_URL = "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"


# Create a 'marked' default path, to determine if someone has supplied
# a path on the command-line.
class _DEFAULT_PATH_TYPE(str):
    is_default_path = True


_DEFAULT_PATH = _DEFAULT_PATH_TYPE(os.curdir)


def ask(question, answer=str, default=None, length=None):
    if answer == str:
        r = ""
        while True:
            if default:
                r = input(f"> {question} [{default}] ")
            else:
                r = input(f"> {question} ")

            r = r.strip()

            if len(r) <= 0:
                if default:
                    r = default
                    break
                else:
                    print("Deve ser inserido um valor")
            else:
                if length and len(r) != length:
                    print(f"A inserção de dados deve ter {length} caracteres")
                else:
                    break

        return r

    elif answer == bool:
        r = None
        while True:
            if default is True:
                r = input(f"> {question} (Y/n) ")
            elif default is False:
                r = input(f"> {question} (y/N) ")
            else:
                r = input(f"> {question} (y/n) ")

            r = r.strip().lower()

            if r in ("y", "yes / sim"):
                r = True
                break
            elif r in ("n", "no / nao"):
                r = False
                break
            elif not r:
                r = default
                break
            else:
                print("Responda as perguntas com 'y' para Sim e 'n' para Não")
        return r
    elif answer == int:
        r = None
        while True:
            if default:
                r = input(f"> {question} [{default}] ")
            else:
                r = input(f"> {question} ")

            r = r.strip()

            if not r:
                r = default
                break

            try:
                r = int(r)
                break
            except ValueError:
                print("Deve ser um numero inteiro")
        return r
    else:
        raise NotImplementedError("a variavel `answer` deve ser uma str, bool, ou integer")


def ask_timezone(question, default, tzurl):
    """Prompt for time zone and validate input"""
    tz_dict = {tz.lower(): tz for tz in zoneinfo.available_timezones()}
    while True:
        r = ask(question, str, default)
        r = r.strip().replace(" ", "_").lower()
        if r in tz_dict.keys():
            r = tz_dict[r]
            break
        else:
            print("Por favor defina um 'time zone' valido:\n" " (check [{}])".format(tzurl))
    return r


def render_jinja_template(tmpl_name: str, tmpl_vars: Mapping, target_path: str):
    try:
        with open(
            os.path.join(CONF["basedir"], target_path), "w", encoding="utf-8"
        ) as fd:
            _template = _jinja_env.get_template(tmpl_name)
            fd.write(_template.render(**tmpl_vars))
    except OSError as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="O kickstarter do projeto Pelican",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-p", "--path", default=_DEFAULT_PATH, help="O local para gerar o blog"
    )
    parser.add_argument(
        "-t", "--title", metavar="title", help="Defina o titulo do seu website"
    )
    parser.add_argument(
        "-a", "--author", metavar="author", help="Defina o autor do website"
    )
    parser.add_argument(
        "-l", "--lang", metavar="lang", help="Defina a lingua padrao"
    )

    args = parser.parse_args()

    print(
        """Bem vindo ao Pelican-quickstartv{v}

Este script vai te ajudar a criar um novo blog/website baseado no Pelican

Por favor responda as questões para que possamos gerar os arquivos necessarios
para o Pelican.

    """.format(v=__version__)
    )

    project = os.path.join(os.environ.get("VIRTUAL_ENV", os.curdir), ".project")
    no_path_was_specified = hasattr(args.path, "is_default_path")
    if os.path.isfile(project) and no_path_was_specified:
        CONF["basedir"] = open(project).read().rstrip("\n")
        print(
            "Usando o projeto jã associado a esse virtual environment. "
            "Will save to:\n%s\n" % CONF["basedir"]
        )
    else:
        CONF["basedir"] = os.path.abspath(
            os.path.expanduser(
                ask(
                    "Onde deseja criar seu novo site?",
                    answer=str,
                    default=args.path,
                )
            )
        )

    CONF["sitename"] = ask(
        "Qual o titulo de seu novo site?", answer=str, default=args.title
    )
    CONF["author"] = ask(
        "Quem é o autor desse site?", answer=str, default=args.author
    )
    CONF["lang"] = ask(
        "Qual a lingua padrão desse site?",
        str,
        args.lang or CONF["lang"],
        2,
    )

    if ask(
        "Deseja especificar um prefixo para URL? e.g., https://exemplo.com  ",
        answer=bool,
        default=True,
    ):
        CONF["siteurl"] = ask(
            "Qual é o prefixo da URL? (Veja " "o exemplo acima; nao coloque a barra final)",
            str,
            CONF["siteurl"],
        )

    CONF["with_pagination"] = ask(
        "Deseja ativar a numeração das paginas dos artigos?",
        bool,
        bool(CONF["default_pagination"]),
    )

    if CONF["with_pagination"]:
        CONF["default_pagination"] = ask(
            "Quantos artigos por página  " " você quer que apareça?",
            int,
            CONF["default_pagination"],
        )
    else:
        CONF["default_pagination"] = False

    CONF["timezone"] = ask_timezone(
        "Qual a sua time zone?", CONF["timezone"], _TZ_URL
    )

    automation = ask(
        "Você deseja gerar um task.py/Makefile "
        "para autoamtizar a geração e publicação?",
        bool,
        True,
    )

    if automation:
        if ask(
            "Usar o FTP para o upload de seu site?", answer=bool, default=False
        ):
            CONF["ftp"] = (True,)
            CONF["ftp_host"] = ask(
                "Qual é o endereço de seu servidor FTP?", str, CONF["ftp_host"]
            )
            CONF["ftp_user"] = ask(
                "Qual é seu usuario de login?", str, CONF["ftp_user"]
            )
            CONF["ftp_target_dir"] = ask(
                "Onde você quer que seu " "site fique em seu servidor?",
                str,
                CONF["ftp_target_dir"],
            )
        if ask(
            "Você quer fazer upload de seu site usando SSH?", answer=bool, default=False
        ):
            CONF["ssh"] = (True,)
            CONF["ssh_host"] = ask(
                "Qaul é o endereço de seu servidor SSH?", str, CONF["ssh_host"]
            )
            CONF["ssh_port"] = ask(
                "Qual é a porta do seu servidor SSH?", int, CONF["ssh_port"]
            )
            CONF["ssh_user"] = ask(
                "Qual é seu nome de usuario nesse servidor?", str, CONF["ssh_user"]
            )
            CONF["ssh_target_dir"] = ask(
                "Onde quer colocar o seu" " site nesse servidor?",
                str,
                CONF["ssh_target_dir"],
            )

        if ask(
            "Você quer fazer o upload para o dropbox?",
            answer=bool,
            default=False,
        ):
            CONF["dropbox"] = (True,)
            CONF["dropbox_dir"] = ask(
                "Qual é a pasta do seu projeto no dropbox?", str, CONF["dropbox_dir"]
            )

        if ask(
            "Você quer fazer o upload usando S3?", answer=bool, default=False
        ):
            CONF["s3"] = (True,)
            CONF["s3_bucket"] = ask(
                "Qual é o nome de seu S3 bucket?", str, CONF["s3_bucket"]
            )

        if ask(
            "Quer fazer upload usando o serviço " "Rackspace Cloud Files?",
            answer=bool,
            default=False,
        ):
            CONF["cloudfiles"] = (True,)
            CONF["cloudfiles_username"] = ask(
                "Qual é seu usuario de nuvem Rackspace " "Cloud username?",
                str,
                CONF["cloudfiles_username"],
            )
            CONF["cloudfiles_api_key"] = ask(
                "Qual é seu Rackspace " "Cloud API key?",
                str,
                CONF["cloudfiles_api_key"],
            )
            CONF["cloudfiles_container"] = ask(
                "Qual é o nome do seu " "Cloud Files conteiner?",
                str,
                CONF["cloudfiles_container"],
            )

        if ask(
            "Quer fazer upload do seu site usando GitHub Pages?",
            answer=bool,
            default=False,
        ):
            CONF["github"] = (True,)
            if ask(
                "Qual é sua pagina pessoal (username.github.io)?",
                answer=bool,
                default=False,
            ):
                CONF["github_pages_branch"] = _GITHUB_PAGES_BRANCHES["personal"]
            else:
                CONF["github_pages_branch"] = _GITHUB_PAGES_BRANCHES["project"]

    try:
        os.makedirs(os.path.join(CONF["basedir"], "content"))
    except OSError as e:
        print(f"Error: {e}")

    try:
        os.makedirs(os.path.join(CONF["basedir"], "output"))
    except OSError as e:
        print(f"Error: {e}")

    conf_python = dict()
    for key, value in CONF.items():
        conf_python[key] = repr(value)
    render_jinja_template("pelicanconf.py.jinja2", conf_python, "pelicanconf.py")

    render_jinja_template("publishconf.py.jinja2", CONF, "publishconf.py")

    if automation:
        render_jinja_template("tasks.py.jinja2", CONF, "tasks.py")
        render_jinja_template("Makefile.jinja2", CONF, "Makefile")

    print("Pronto. seu novo projeto está disponível em %s" % CONF["basedir"])


if __name__ == "__main__":
    main()
