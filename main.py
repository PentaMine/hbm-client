import configparser
import datetime
import os
from datetime import *
from dataclasses import dataclass
import threading
from colorama import Fore
import spyl
import time as tm


class TerminalSession(threading.Thread):
    def run(self) -> None:
        run_executable(self.executable)
        logger.log(F"PROCESS \"{self.executable.name}\" FINISHED", SuccessLevel)
        logger.log_info(F"CLOSING THREAD FOR PROCESS \"{self.executable.name}\"")


@dataclass
class Executable:
    key: str
    command: str
    path: str
    runTime: time
    name: str
    didRun: bool = False


def validate_ini_file(conf: dict):
    try:
        commands = conf["commands"]
        paths = conf["paths"]
        times = conf["times"]
        names = conf["names"]
        if not (commands.keys() == paths.keys() == times.keys() == names.keys()):
            raise Exception
        for i in paths:
            if not os.path.exists(paths[i]):
                raise Exception
    except KeyError as e:
        return False
    except Exception as e:
        return False
    return True


def get_values_form_config(conf):
    keys = conf["commands"].keys()
    commands = [conf["commands"][i] for i in conf["commands"]]
    paths = [conf["paths"][i] for i in conf["paths"]]
    times = [conf["times"][i] for i in conf["times"]]
    names = [conf["names"][i] for i in conf["names"]]
    execs = []
    for key, command, path, time, name in zip(keys, commands, paths, times, names):
        run_time = datetime.strptime(time, '%H:%M:%S').time()
        execs.append(Executable(key, command.replace("$1", datetime.now().strftime("%x")), path, run_time, name))

    return execs


def run_executable(executable: Executable):
    os.chdir(executable.path)
    os.system(executable.command)
    os.chdir(os.path.dirname(os.path.realpath(__file__)))


config = configparser.ConfigParser()
config.read("config.ini")

logger = spyl.Logger(quitWhenLogFatal=True)

SuccessLevel = spyl.LogLevel("DONE", Fore.GREEN)

if not validate_ini_file(config):
    logger.log_fatal("CONFIG.INI IS INVALID")

executables = get_values_form_config(config)

while True:

    if time(hour=0, minute=0, second=0) < datetime.now().time() < time(hour=0, minute=0, second=10):
        for executable in executables:
            executable.didRun = False

        new_config = configparser.ConfigParser()
        new_config.read("config.ini")

        if not validate_ini_file(new_config):
            logger.log_error("CONFIG.INI IS INVALID, CHANGES TO IT WILL BE IGNORED")
        elif config != new_config:
            config = new_config
            logger.log_info("UPDATING CONFIG.INI FILE")
            executables = get_values_form_config(config)
        else:
            logger.log_info("NO CHANGES TO THE CONFIG.INI FILE")
        tm.sleep(10)

    for executable in executables:
        # print(executable.runTime, datetime.now().time(), executable.runTime > datetime.now().time())
        if executable.runTime < datetime.now().time() and not executable.didRun:
            logger.log_info(F"STARTING A THREAD FOR PROCESS \"{executable.name}\"")
            thread = TerminalSession()
            thread.executable = executable
            thread.start()
            executable.didRun = True
