from configparser import RawConfigParser
from os import path, environ
import os
import traceback
from typing import Dict, List
from enum import Enum
import logging
from ..util.config_exception import ConfigurationException
from ..util.log_utility import LogUtility as lout
from .config_env import ConfigEnv

#
#   1 csvpaths & csvpath own their own config
#   2 start up to sensible defaults in config.ini
#   3 reloading is easy
#   4 programmatically changing values is easy
#   5 config validation is easy
#


class OnError(Enum):
    RAISE = "raise"
    QUIET = "quiet"
    COLLECT = "collect"
    STOP = "stop"
    FAIL = "fail"
    PRINT = "print"


class LogLevels(Enum):
    INFO = "info"
    DEBUG = "debug"
    WARN = "warn"
    ERROR = "error"


class LogFile(Enum):
    LOG_FILE = "log_file"
    LOG_FILES_TO_KEEP = "log_files_to_keep"
    LOG_FILE_SIZE = "log_file_size"


class Sections(Enum):
    CSVPATH_FILES = "csvpath_files"
    CSV_FILES = "csv_files"
    ERRORS = "errors"
    LOGGING = "logging"
    FUNCTIONS = "functions"
    CACHE = "cache"


#
# main external methods:
#  - load
#  - save
#  - refresh
#  - reload
#  - add_to_config
#  - get
#
class Config:
    """by default finds config files at ./config/config.ini.
    To set a different location:
     - set a CSVPATH_CONFIG_FILE env var
     - create a Config instance set its CONFIG member and call reload
     - or set Config.CONFIG and reload to reset all instances w/o own specific settings
    Also, you can pass Config(load=False) to give you the opportunity to set some/all
    properties programmatically.
    """

    CONFIG: str = f"config{os.sep}config.ini"
    CSVPATH_CONFIG_FILE_ENV: str = "CSVPATH_CONFIG_PATH"

    DEFAULT_CONFIG = f"""
[extensions]
csvpath_files = csvpath, csvpaths
csv_files = csv, tsv, dat, tab, psv, ssv

[errors]
csvpath = collect, fail, print
csvpaths = print, collect
use_format = full
pattern = {{time}}:{{file}}:{{line}}:{{paths}}:{{instance}}:{{chain}}:  {{message}}

[logging]
csvpath = info
csvpaths = info
log_file = logs{os.sep}csvpath.log
log_files_to_keep = 100
log_file_size = 50000000
# file or rotating
handler = file

[config]
path = XXXXXXXXXXX
allow_var_sub = True
var_sub_source = env

[functions]
imports =

[cache]
path =

[results]
archive = archive
transfers = transfers

[inputs]
files = inputs{os.sep}named_files
csvpaths = inputs{os.sep}named_paths
on_unmatched_file_fingerprints = halt
allow_http_files=True
allow_local_files=True

[listeners]
# add listener group names to send events to the channel they represent
groups = default
#slack, openlineage, ckan, sftp, sftpplus, otlp, sqlite, sql

# general purpose webhook caller
webhook.results = from csvpath.managers.integrations.webhook.webhook_results_listener import WebhookResultsListener

# add a listener to exec scripts at the end of named-paths group runs
scripts.results = from csvpath.managers.integrations.scripts.scripts_results_listener import ScriptsResultsListener

# add sql to capture results in mysql, postgres, ms sql server, or sqlite
sql.file = from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
sql.paths = from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
sql.result = from csvpath.managers.integrations.sql.sql_result_listener import SqlResultListener
sql.results = from csvpath.managers.integrations.sql.sql_results_listener import SqlResultsListener

# add sqlite to capture results in a local sqlite file
sqlite.results = from csvpath.managers.integrations.sqlite.sqlite_results_listener import SqliteResultsListener
sqlite.result = from csvpath.managers.integrations.sqlite.sqlite_result_listener import SqliteResultListener

# add to capture a history of all named-file stagings and all named-paths loads in
# an [inputs] files and an[inputs] paths root manifest.json
default.file = from csvpath.managers.files.files_listener import FilesListener
default.paths = from csvpath.managers.paths.paths_listener import PathsListener

# add otlp to the list of groups above to push observability metrics to an OpenTelemetry endpoint
otlp.result = from csvpath.managers.integrations.otlp.otlp_result_listener import OpenTelemetryResultListener
otlp.results = from csvpath.managers.integrations.otlp.otlp_results_listener import OpenTelemetryResultsListener
otlp.errors = from csvpath.managers.integrations.otlp.otlp_error_listener import OpenTelemetryErrorListener
otlp.paths = from csvpath.managers.integrations.otlp.otlp_paths_listener import OpenTelemetryPathsListener
otlp.file = from csvpath.managers.integrations.otlp.otlp_file_listener import OpenTelemetryFileListener

# add sftp to the list of groups above to push content and metadata to an SFTP account
sftp.results = from csvpath.managers.integrations.sftp.sftp_sender import SftpSender

# add sftpplus to the list of groups above to automate registration and named-paths group runs on file arrival at an SFTPPlus server
sftpplus.paths = from csvpath.managers.integrations.sftpplus.sftpplus_listener import SftpPlusListener

# add ckan to the list of groups above to push content and metadata to CKAN
ckan.results = from csvpath.managers.integrations.ckan.ckan_listener import CkanListener

#add openlineage to the list of groups above for OpenLineage events to a Marquez server
openlineage.file = from csvpath.managers.integrations.ol.file_listener_ol import OpenLineageFileListener
openlineage.paths = from csvpath.managers.integrations.ol.paths_listener_ol import OpenLineagePathsListener
openlineage.result = from csvpath.managers.integrations.ol.result_listener_ol import OpenLineageResultListener
openlineage.results = from csvpath.managers.integrations.ol.results_listener_ol import OpenLineageResultsListener

# add slack to the list of groups above for alerts to slack webhooks
slack.file = from csvpath.managers.integrations.slack.sender import SlackSender
slack.paths = from csvpath.managers.integrations.slack.sender import SlackSender
slack.result = from csvpath.managers.integrations.slack.sender import SlackSender
slack.results = from csvpath.managers.integrations.slack.sender import SlackSender

[otlp]
# add OTLP config here if not relying directly on the env vars

[aws]
#

[azure]
#

[gcs]
#

[sqlite]
db = archive/csvpath.db

[sql]
# mysql, postgres, sql_server, or sqlite
dialect = sqlite
connection_string = sqlite:///archive/csvpath-sqlite.db

[sftp]
server =
port =
username =
password =

[sftpplus]
# these are only needed on the server
admin_username = SFTPPLUS_ADMIN_USERNAME
admin_password = SFTPPLUS_ADMIN_PASSWORD
api_url = https://. . . :10020/json
scripts_dir =
execute_timeout = 300

# these are only needed by the csvpath writer
mailbox_user = mailbox
mailbox_password = SFTPPLUS_MAILBOX_PASSWORD
server = SFTPPLUS_SERVER
port = SFTPPLUS_PORT

[ckan]
server = http://. . . :80
api_token =

[openlineage]
base_url = http://. . . :5000
endpoint = api/v1/lineage
api_key = "none"
timeout = 5
verify = False

[slack]
# add your main webhook here. to set webhooks on a csvpath-by-csvpath basis add
# on-valid-slack: webhook-minus-'https://' and/or
# on-invalid-slack: webhook-minus-'https://'
webhook_url =

[scripts]
run_scripts = no
shell = /bin/bash
"""

    def __init__(self, *, load=True, config_env: ConfigEnv = None):
        #
        # when config is loaded it reads from config/config.ini. if that location says config lives
        # somewhere else, config reloads from that place. that works fine.
        #
        # where I get paranoid is cycles. in principle, the second config could have a [config] path
        # pointing back to the first, most likely "config/config.ini", which would then reload and
        # repoint to the 2nd file in an infinite loop. if we see a small number of loops we raise an
        # exception. it isn't airtight because you could have a lengthy chain of configs that
        # eventually loop. but that would be a very unlikely unforced err. note that this var is no
        # longer static and should never have been. cycles are only meaningful in a single instance.
        # we expect one or even two cycles per instance in the usual case in any complex env, e.g. in
        # FlightPath. if we counted all the cycles ever for all instances the number would go nuts.
        #
        self.config_path_cycle = 0
        self.load = load
        self._config_env = config_env
        self._config = RawConfigParser()
        self._configpath = None
        #
        # if env is set it is over anything else. However, the config.ini
        # found by env var or any other way has its configpath evaluated and
        # will be reloaded if it is found to be different. this could result
        # an infinite loop, but that would be an unlikely user error easily
        # corrected.
        #
        # pass in None to trigger a configpath load
        self.configpath = None

    def __del__(self) -> None:
        try:
            lout.release_logger(self)
        except Exception:
            print(traceback.format_exc())

    @property
    def config_env(self) -> ConfigEnv:
        if self._config_env is None:
            self._config_env = ConfigEnv(config=self)
        return self._config_env

    @config_env.setter
    def config_env(self, e: ConfigEnv) -> None:
        self._config_env = e

    @property
    def config_parser(self) -> RawConfigParser:
        return self._config

    @property
    def configpath(self) -> str:
        if self._configpath is None:
            self.configpath = None
        return self._configpath

    #
    # setting configpath triggers a reload
    #
    @configpath.setter
    def configpath(self, path: str) -> None:
        #
        # if None passed in, check Env vars, if None, use default
        #
        if path is not None:
            path = path.strip()
        if path == "":
            path = None
        if path is None:
            path = environ.get(Config.CSVPATH_CONFIG_FILE_ENV)
            if path is not None:
                path = path.strip()
            if path == "":
                path = None
            if path is None:
                path = Config.CONFIG
        self._configpath = path
        self._load_config()
        # if newly loaded config path doesn't match where it was loaded from, reload w/it.
        path = self._get(section="config", name="path", no_list=True)
        if path is not None:
            path = path.strip()
        if path == "":
            path = None
        if path is not None and path != self._configpath:
            # if recurse, could loop. but probably won't and not looping is user's responsibility.
            self.configpath = path

    @property
    def load(self) -> bool:
        return self._load

    @load.setter
    def load(self, lo: bool) -> None:
        self._load = lo

    def reload(self):
        self._config = RawConfigParser()
        self._load = True
        self._load_config()

    def set_config_path_and_reload(self, path: str) -> None:
        self.configpath = path
        self.reload()

    @property
    def config_path(self) -> str:
        return self.configpath

    @property
    def sections(self) -> list[str]:
        return self._config.sections()

    def get(self, *, section: str = None, name: str, default=None):
        #
        # go-agent on Mac via Brew can have commas in paths. must be true in other cases
        # as well. finding configpath is the only place we've seen the problem of finding
        # a list when we expect a string. adding no_list=True is a stop-gap. a bit hacky
        # and odd that it only shows up after months of working fine. but there it is.
        #
        no_list = False
        if section == "config" and name == "path":
            no_list = True
        return self._get(section, name, default, no_list=no_list)

    def _get(self, section: str, name: str, default=None, no_list=False):
        #
        # TODO: we should swap all uppercase values for env var values if we find a
        # matching env var. same as we do for metadata values
        #
        if name is None:
            raise ConfigurationException("Name cannot be None")
        if section is None:
            #
            # if section is none we're just looking at the OS env vars or the project
            # env vars, if the project is configured to hold vars in a JSON file.
            #
            ret = self.config_env.get(name=name, default=default)
            return ret
        if self._config is None:
            raise ConfigurationException("No config object available")
        try:
            s = self._config[section][name]
            ret = None
            if no_list is False and s and isinstance(s, str) and s.find(",") > -1:
                ret = [s.strip() for s in s.split(",")]
            elif isinstance(s, str):
                ret = s.strip()
            else:
                ret = s
            if ret and isinstance(ret, str) and ret.isupper():
                v2 = self.config_env.get(name=ret, default=default)
                if v2 is not None:
                    ret = v2.strip()
            return ret
        except KeyError:
            return default

    @property
    def _logger(self):
        name = lout.logger_name(self)
        return lout.config_logger(config=self, name=name, level="debug")

    #
    # set() and _set() do not call refresh(). add_to_config() calls _set() and refresh().
    # using "name" as the key param because get() uses name and that method is used everywhere.
    #
    def set(self, *, section, name, value) -> None:
        self._set(section, name, value)

    def _set(self, section, key, value) -> None:
        if isinstance(value, list):
            value = ",".join(value)
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, value)

    #
    # adds the value to the internal configparser object. doesn't save.
    # does a refresh to make sure any lists or other interpreted values
    # are up to date. if you want to save you need to call the save
    # method.
    #
    def add_to_config(self, section, key, value) -> None:
        if not self._config.has_section(section):
            self._config.add_section(section)
        #
        # values must be strings
        #
        if value is None:
            value = ""
        #
        # why would we not use _set(section, key, value)?
        #
        self._set(section, key, value)
        self.refresh()

    def save_config(self) -> None:
        with open(self.configpath, "w", encoding="utf-8") as f:
            self._config.write(f)

    def _create_default_config(self) -> None | str:
        directory = ""
        name = ""
        cp = self._configpath
        if cp is None or cp.strip() == "":
            cp = os.path.join("config", "config.ini")
        name = os.path.basename(cp)
        directory = os.path.dirname(cp)
        if directory == "":
            directory = "config"
        if not directory.strip().startswith(os.sep):
            directory = os.path.join(os.getcwd(), directory)
        if directory != "":
            if not path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception:
                    print(traceback.format_exc())
        self._configpath = os.path.join(directory, name)
        cfg = Config.DEFAULT_CONFIG
        cfg = cfg.replace("XXXXXXXXXXX", self._configpath)
        with open(self._configpath, "w", encoding="utf-8") as file:
            file.write(cfg)
            #
            # writing a new config means we want to immediately load it?
            # possibly not.
            #
            try:
                self._assure_logs_path()
            except Exception:
                print(traceback.format_exc())
            try:
                self._assure_archive_path()
            except Exception:
                print(traceback.format_exc())
            try:
                self._assure_transfer_root()
            except Exception:
                print(traceback.format_exc())
            try:
                self._assure_inputs_files_path()
            except Exception:
                print(traceback.format_exc())
            try:
                self._assure_cache_path()
            except Exception:
                print(traceback.format_exc())
            try:
                self._assure_inputs_csvpaths_path()
            except Exception:
                print(traceback.format_exc())

            print("Created a default config file at: ")
            print(f"  {self._configpath}.")
            print("If you want your config somewhere else remember to")
            print("update the [config] path key in the default config.ini")

    def _assure_logs_path(self) -> None:
        if self.load:
            filepath = self.log_file
            if not filepath or filepath.strip() == "":
                filepath = f"logs{os.sep}csvpath.log"
                self.log_file = filepath
            dirpath = self._get_dir_path(filepath)
            if dirpath and not path.exists(dirpath):
                os.makedirs(dirpath)

    def _get_dir_path(self, filepath):
        p = os.path.dirname(filepath)
        return p if not p == "" else None

    def _assure_archive_path(self) -> None:
        if self.load:
            if self.archive_path is None or self.archive_path.strip() == "":
                self.archive_path = "archive"
            if self.archive_path.strip().lower().startswith("s3://"):
                return
            if self.archive_path.strip().lower().startswith("azure://"):
                return
            if self.archive_path.strip().lower().startswith("sftp://"):
                return
            if not path.exists(self.archive_path):
                os.makedirs(self.archive_path)

    @property
    def archive_sep(self) -> None:
        if self.archive_path is None or self.archive_path.strip() == "":
            return os.sep
        a = self.archive_path.strip().lower()
        if a.find("://") > -1:
            return "/"
        return os.sep

    @property
    def files_sep(self) -> None:
        if self.inputs_files_path is None or self.inputs_files_path.strip() == "":
            return os.sep
        a = self.inputs_files_path.strip().lower()
        if a.find("://") > -1:
            return "/"
        return os.sep

    @property
    def csvpaths_sep(self) -> None:
        if (
            self._assure_inputs_csvpaths_path is None
            or self._assure_inputs_csvpaths_path.strip() == ""
        ):
            return os.sep
        a = self._assure_inputs_csvpaths_path.strip().lower()
        if a.find("://") > -1:
            return "/"
        return os.sep

    def _assure_transfer_root(self) -> None:
        if self.load:
            if self.transfer_root is None or self.transfer_root.strip() == "":
                self.transfer_root = "transfers"
            if not path.exists(self.transfer_root):
                os.makedirs(self.transfer_root)

    def _assure_inputs_files_path(self) -> None:
        if self.load:
            if self.inputs_files_path is None or self.inputs_files_path.strip() == "":
                self.inputs_files_path = f"inputs{os.sep}named_files"
            if self.inputs_files_path.strip().lower().startswith("s3://"):
                return
            if self.inputs_files_path.strip().lower().startswith("azure://"):
                return
            if self.inputs_files_path.strip().lower().startswith("sftp://"):
                return
            if self.inputs_files_path.strip().lower().startswith("gs://"):
                return
            if not path.exists(self.inputs_files_path):
                os.makedirs(self.inputs_files_path)

    def _assure_inputs_csvpaths_path(self) -> None:
        if self.load:
            if (
                self.inputs_csvpaths_path is None
                or self.inputs_csvpaths_path.strip() == ""
            ):
                self.inputs_csvpaths_path = f"inputs{os.sep}named_paths"
            if self.inputs_csvpaths_path.strip().lower().startswith("s3://"):
                return
            if self.inputs_csvpaths_path.strip().lower().startswith("azure://"):
                return
            if self.inputs_csvpaths_path.strip().lower().startswith("sftp://"):
                return
            if self.inputs_csvpaths_path.strip().lower().startswith("gs://"):
                return
            if not path.exists(self.inputs_csvpaths_path):
                try:
                    os.makedirs(self.inputs_csvpaths_path)
                except Exception:
                    print(traceback.format_exc())

    """
    def _assure_cache_path(self) -> None:
        if self.load:
            p = self._get("cache", "path", "cache")
            if p:
                p = p.strip()
            if not p or p == "":
                uc = self.get(section="cache", name="use_cache")
                if uc and uc.strip().lower() == "no":
                    return
                self._set("cache", "use_cache", "no")
                return
            if p.find("://") > -1:
                raise ConfigurationException(
                    f"Cache dir must be on the local drive, not {p}"
                )
            if not os.path.exists(p):
                try:
                    os.makedirs(p)
                except Exception:
                    print(traceback.format_exc())
    """

    def _assure_cache_path(self) -> None:
        if self.load:
            p = self._get("cache", "path", "cache")
            if p:
                p = p.strip()
            if not p or p == "":
                #
                # the default is the relative path 'cache'
                #
                p = "cache"
                uc = self.get(section="cache", name="use_cache")
                #
                # if we aren't using cache we shouldn't create the unused dir, if it doesn't exist.
                #
                if uc and uc.strip().lower() in ["no", "false"]:
                    return
                else:
                    self._set("cache", "path", "cache")
            if p.find("://") > -1:
                raise ConfigurationException(
                    f"Cache dir must be on the local drive, not {p}"
                )
            if not os.path.exists(p):
                try:
                    os.makedirs(p)
                except Exception:
                    print(traceback.format_exc())

    def _assure_config_file_path(self) -> None:
        if self.load:
            if not self.configpath or self.configpath.strip() == "":
                self.configpath = Config.CONFIG
            if not os.path.isfile(self.configpath):
                self._create_default_config()

    def _load_config(self, norecurse=False):
        if self._load is False:
            return
        self._assure_config_file_path()
        path = self.configpath
        print(f"Config_loadcf: path {path}")
        self._config.read(path)
        self.refresh()

    def refresh(self) -> None:
        #
        # the sections: csv_files and csvpath_files are deprecated in favor of
        # a single extensions section with csv_files and csvpath_files as keys.
        # is is a simpler way to go and will UI better. the old way can hang about
        # for a release or two, but should be retired soon.
        #
        #
        self.csvpath_log_level = self._get(Sections.LOGGING.value, "csvpath")
        self.csvpaths_log_level = self._get(Sections.LOGGING.value, "csvpaths")

        self.log_file = self._get(Sections.LOGGING.value, LogFile.LOG_FILE.value)
        self.log_files_to_keep = self._get(
            Sections.LOGGING.value, LogFile.LOG_FILES_TO_KEEP.value, 10
        )
        self.log_file_size = self._get(
            Sections.LOGGING.value, LogFile.LOG_FILE_SIZE.value, 12800000
        )
        #
        # test file system paths in context of go-agent can have commas due to brew
        # so we pass a flag to prevent comma parsing. why this didn't come up ages ago
        # i'm not sure. puzzling.
        #
        path = self._get("config", "path", no_list=True)
        #
        # maybe? here if we load from self.configpath = xyz.ini and xyz.ini has [config] path=
        # we stay with self.configpath = xyz
        #
        path = path.strip().lower() if path else ""
        #
        # current
        # in the current case if we load from self.configpath = xyz.ini and xyz.ini has [config] path=
        # [config] path is set to config/config.ini and we reload, which isn't what we want.
        #
        # path = path.strip().lower() if path else Config.CONFIG
        #
        if path != "" and path != self.configpath.strip().lower():
            self.config_path_cycle += 1
            #
            # see note at top of class. 3 would probably do it. but 6 is fine.
            #
            if self.config_path_cycle > 6:
                raise Exception(
                    f"Config cycle: {self.config_path_cycle}. Check [config] path {path} and {self.configpath} for cycles"
                )
            self.configpath = path
            self.reload()
            return
        self.config_path_cycle = 0
        self.validate_config()

    def validate_config(self) -> None:
        #
        # error policies
        #
        if (
            self.csvpath_errors_policy is None
            or not isinstance(self.csvpath_errors_policy, list)
            or not len(self.csvpath_errors_policy) > 0
        ):
            raise ConfigurationException(
                f"CsvPath error policy is wrong: {self.csvpath_errors_policy}"
            )
        for _ in self.csvpath_errors_policy:
            if _ not in [s.value for s in OnError]:
                raise ConfigurationException(f"CsvPath error policy {_} is wrong")
        if (
            self.csvpaths_errors_policy is None
            or not isinstance(self.csvpaths_errors_policy, list)
            or not len(self.csvpaths_errors_policy) > 0
        ):
            raise ConfigurationException("CsvPaths error policy is wrong")
        for _ in self.csvpaths_errors_policy:
            if _ not in [s.value for s in OnError]:
                raise ConfigurationException(f"CsvPaths error policy {_} is wrong")
        #
        # log levels
        #
        if self.csvpath_log_level is None or not isinstance(
            self.csvpath_log_level, str
        ):
            raise ConfigurationException(
                f"CsvPath log level is wrong: {self.csvpath_log_level}"
            )
        if self.csvpath_log_level not in [s.value for s in LogLevels]:
            raise ConfigurationException(f"CsvPath log level {_} is wrong")
        if self.csvpaths_log_level is None or not isinstance(
            self.csvpaths_log_level, str
        ):
            raise ConfigurationException("CsvPaths log level is wrong")
        if self.csvpaths_log_level not in [s.value for s in LogLevels]:
            raise ConfigurationException(f"CsvPaths log level {_} is wrong")
        #
        # log files config
        #
        if self.log_file is None or not isinstance(self.log_file, str):
            raise ConfigurationException(f"Log file path is wrong: {self.log_file}")
        #
        # make sure the log dir exists
        #
        self._assure_logs_path()
        if self.log_files_to_keep is None or not isinstance(
            self.log_files_to_keep, int
        ):
            raise ConfigurationException(
                f"Log files to keep is wrong: {type(self.log_files_to_keep)}"
            )
        if self.log_file_size is None or not isinstance(self.log_file_size, int):
            raise ConfigurationException("Log files size is wrong")
        #
        # make sure a cache dir exists. the default should be chosen in the
        # default config, but regardless, we create the dir.
        #
        self._assure_cache_path()
        #
        # make sure a inputs dirs exist.
        #
        self._assure_inputs_files_path()
        self._assure_inputs_csvpaths_path()

    # ======================================

    def additional_listeners(self, listener_type) -> list[str]:
        # pull type for group names
        # for each group name find:
        #    listener_type.groupname=listner
        listeners = []
        groups = self._get("listeners", "groups")
        if groups is None:
            groups = []
        if isinstance(groups, str):
            groups = [groups]
        for group in groups:
            lst = f"{group}.{listener_type}"
            listener = self._get("listeners", lst)
            if listener is not None:
                listeners.append(listener)
        return listeners

    @property
    def cache_dir_path(self) -> str:
        return self._get("cache", "path")

    @cache_dir_path.setter
    def cache_dir_path(self, p) -> None:
        self._set("cache", "path", p)

    def halt_on_unmatched_file_fingerprints(self) -> bool:
        houf = self._get("inputs", "on_unmatched_file_fingerprints")
        if houf == "halt":
            return True
        elif houf == "continue":
            return False
        return None

    @property
    def transfer_root(self) -> str:
        return self._get("results", "transfers", "transfers")

    @transfer_root.setter
    def transfer_root(self, p) -> None:
        self._set("results", "transfers", p)

    @property
    def archive_path(self) -> str:
        return self._get("results", "archive", "archive")

    @archive_path.setter
    def archive_path(self, p) -> None:
        self._set("results", "archive", p)

    @property
    def archive_name(self) -> str:
        p = self.archive_path
        if p.find(self.archive_sep) > -1:
            p = p[p.rfind(os.sep) + 1 :]
        return p

    @property
    def inputs_files_path(self) -> str:
        return self._get("inputs", "files", f"inputs{os.sep}named_files")

    @inputs_files_path.setter
    def inputs_files_path(self, p) -> None:
        self._set("inputs", "files", p)

    @property
    def inputs_csvpaths_path(self) -> str:
        return self._get("inputs", "csvpaths", f"inputs{os.sep}named_paths")

    @inputs_csvpaths_path.setter
    def inputs_csvpaths_path(self, p) -> None:
        self._set("inputs", "csvpaths", p)

    @property
    def function_imports(self) -> str:
        return self._get(Sections.FUNCTIONS.value, "imports", "imports")

    @function_imports.setter
    def function_imports(self, path: str) -> None:
        self._set(Sections.FUNCTIONS.value, "imports", path)

    @property
    def csvpath_errors_policy(self) -> list[str]:
        p = self._get(
            Sections.ERRORS.value,
            "csvpath",
            ["print", "stop", "fail", "collect"],
        )
        if not isinstance(p, list):
            return [p]
        return p
        # return self._csvpath_errors_policy

    @csvpath_errors_policy.setter
    def csvpath_errors_policy(self, ss: list[str]) -> None:
        if isinstance(ss, str):
            ss = [ss]
        self._set(Sections.ERRORS.value, "csvpath", ss)
        # self._csvpath_errors_policy = ss

    @property
    def csvpaths_errors_policy(self) -> list[str]:
        p = self._get(
            Sections.ERRORS.value,
            "csvpaths",
            ["print", "stop", "fail", "collect"],
        )
        if isinstance(p, str):
            return [p]
        return p
        # return self._csvpaths_errors_policy

    @csvpaths_errors_policy.setter
    def csvpaths_errors_policy(self, ss: list[str]) -> None:
        if isinstance(ss, str):
            ss = [ss]
        self._set(Sections.ERRORS.value, "csvpaths", ss)
        # self._csvpaths_errors_policy = ss

    @property
    def csvpath_log_level(self) -> str:
        return self._get("logging", "csvpath")

    @csvpath_log_level.setter
    def csvpath_log_level(self, s: str) -> None:
        self._set("logging", "csvpath", s)

    @property
    def csvpaths_log_level(self) -> str:
        return self._get("logging", "csvpaths")

    @csvpaths_log_level.setter
    def csvpaths_log_level(self, s: str) -> None:
        self._set("logging", "csvpaths", s)

    @property
    def log_file(self) -> str:
        return self.get(section="logging", name="log_file")

    @log_file.setter
    def log_file(self, s: str) -> None:
        self._set("logging", "log_file", s)

    @property
    def log_files_to_keep(self) -> int:
        fs = self._get(Sections.LOGGING.value, LogFile.LOG_FILES_TO_KEEP.value, 10)
        try:
            fs = int(fs)
        except ValueError:
            return 10
        return fs

    @log_files_to_keep.setter
    def log_files_to_keep(self, i: int) -> None:
        try:
            i = int(i)
        except (ValueError, TypeError):
            i = 10
        self._set(Sections.LOGGING.value, LogFile.LOG_FILES_TO_KEEP.value, i)

    @property
    def log_file_size(self) -> int:
        fs = self._get(Sections.LOGGING.value, LogFile.LOG_FILE_SIZE.value, 12800000)
        try:
            fs = int(fs)
        except ValueError:
            fs = 12800000
        return fs

    @log_file_size.setter
    def log_file_size(self, i: int) -> None:
        try:
            i = int(i)
        except (TypeError, ValueError):
            i = 12800000
        self._set(Sections.LOGGING.value, LogFile.LOG_FILE_SIZE.value, i)
