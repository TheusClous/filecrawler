import os
import importlib
import pkgutil
import random
import sqlite3
import string
import sys
from argparse import _ArgumentGroup, ArgumentParser, Namespace
from pathlib import Path

from filecrawler.libs.module import Module
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.libs.crawlerdb import CrawlerDB
from filecrawler.util.logger import Logger


class CrawlerBase(object):
    _stdout = None
    _stderr = None

    help_show = True
    check_database = True
    name = ''
    description = ''
    verbose = 0

    def __init__(self, name, description, help_show=True):
        self.name = name
        self.description = description
        self.help_show = help_show
        CrawlerBase.get_system_defaults()
        pass

    @classmethod
    def write_status(cls, text):
        print(text, file=CrawlerBase._stderr, end='\r', flush=True)

    @classmethod
    def clear_line(cls):
        try:
            size = os.get_terminal_size(fd=os.STDOUT_FILENO)
        except:
            size = 80

        print((" " * size), end='\r', flush=True)
        print((" " * size), file=CrawlerBase._stderr, end='\r', flush=True)

    @staticmethod
    def get_system_defaults():
        if CrawlerBase._stdout is None:
            CrawlerBase._stdout = sys.stdout

        if CrawlerBase._stderr is None:
            CrawlerBase._stderr = sys.stderr

    @classmethod
    def get_base_module(cls) -> str:
        file = Path(__file__).stem

        parent_module = f'.{cls.__module__}.'.replace(f'.{file}.', '').strip(' .')

        return '.'.join((parent_module, 'cmd'))

    @classmethod
    def list_modules(cls, help_show=True, verbose=False) -> dict:
        try:

            base_module = CrawlerBase.get_base_module()

            modules = {}

            base_path = os.path.join(
                Path(__file__).resolve().parent, 'cmd'
            )

            for loader, modname, ispkg in pkgutil.walk_packages([base_path]):
                if not ispkg:
                    if verbose:
                        Color.pl('{?} Importing module: %s' % f'{base_module}.{modname}')
                    importlib.import_module(f'{base_module}.{modname}')

            if verbose:
                Logger.pl('')

            for iclass in CrawlerBase.__subclasses__():
                t = iclass()
                if t.name in modules:
                    raise Exception(f'Duplicated Module name: {iclass.__module__}.{iclass.__qualname__}')

                if t.help_show is True or help_show is True:
                    modules[t.name] = Module(
                        name=t.name.lower(),
                        description=t.description,
                        module=str(iclass.__module__),
                        qualname=str(iclass.__qualname__),
                        class_name=iclass
                    )

            return modules

        except Exception as e:
            raise Exception('Error listing command modules', e)

    def open_db(self, args: Namespace, check: bool = False) -> CrawlerDB:
        db_name = os.path.abspath(args.dbfile.strip())

        if not os.path.isfile(db_name):
            Color.pl('{!} {R}error: database file not found {O}%s{R}{W}\r\n' % db_name)
            exit(1)

        try:
            db = CrawlerDB(auto_create=False,
                           db_name=db_name)

            if check:
                db.check_open()

            return db

        except sqlite3.OperationalError as e:
            Logger.pl(
                '{!} {R}error: the database file exists but is not an SQLite or table structure was not created. Use parameter {O}--create-db{R} command to create.{W}\r\n')
            exit(1)
        except Exception as e:
            raise e

    def print_verbose(self, text: str, min_level: int = 1):
        if self.verbose <= min_level:
            return

        Logger.pl('{?} {W}{D}%s{W}' % text)

    def get_config_sample(self) -> list:
        return []

    def add_flags(self, flags: _ArgumentGroup):
        pass

    def add_commands(self, cmds: _ArgumentGroup):
        pass

    def add_groups(self, parser: ArgumentParser):
        pass

    def load_from_arguments(self, args: Namespace) -> bool:
        raise Exception('Method "load_from_arguments" is not yet implemented.')

    def load_config(self, config: dict) -> bool:
        raise Exception('Method "load_config" is not yet implemented.')

    def run(self):
        raise Exception('Method "run" is not yet implemented.')

    def get_temp_directory(self) -> Path:
        path = os.path.join(
            os.getcwd(),
            ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase) for i in range(20))
        )
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)

        return p

    def get_files(self, path):
        for file in os.listdir(path):
            p1 = os.path.join(path, file)
            if os.path.isfile(p1):
                yield p1
            elif os.path.isdir(p1):
                yield from self.get_files(p1)
