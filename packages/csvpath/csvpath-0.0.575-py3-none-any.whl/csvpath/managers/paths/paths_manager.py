# pylint: disable=C0114
import os
import json
from typing import NewType
from json import JSONDecodeError
from csvpath import CsvPath
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.metadata_parser import MetadataParser
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.box import Box
from csvpath.util.nos import Nos
from .paths_registrar import PathsRegistrar
from .paths_metadata import PathsMetadata
from csvpath.util.template_util import TemplateUtility as temu
from csvpath.matching.util.expression_utility import ExpressionUtility as expu

# types for clarity
NamedPathsName = NewType("NamedPathsName", str)
"""@private"""
Csvpath = NewType("Csvpath", str)
"""@private"""
Identity = NewType("Identity", str)
"""@private"""


class PathsManager:
    MARKER: str = "---- CSVPATH ----"
    SCRIPT_TYPES: list[str] = [
        "on_complete_all_script",
        "on_complete_errors_script",
        "on_complete_valid_script",
        "on_complete_invalid_script",
    ]

    def __init__(self, *, csvpaths, named_paths=None):
        """@private"""
        self.csvpaths = csvpaths
        """@private"""
        self._registrar = None
        # self._nos = None
        #
        # this property is set after a metadata update is distributed from adding
        # a named-paths group. it is only reset at the next add. if the next add
        # fails before completing this value will be None.
        #
        self._last_add_metadata = None

    @property
    def last_add_metadata(self) -> PathsMetadata:
        #
        # BIG CAVEAT: this breaks the statelessness we're trying to trend towards.
        # admittedly the original PathsManager was stateful, but that was long ago.
        # this should only be used if really needed.
        #
        # TODO: verify there are no good uses and remove
        #
        return self._last_add_metadata

    @last_add_metadata.setter
    def last_add_metadata(self, mdata: PathsMetadata) -> None:
        self._last_add_metadata = mdata

    """
    @property
    def nos(self) -> Nos:
        box = Box()
        if self._nos is None:
            self._nos = box.get("boto_s3_nos")
            if self._nos is None:
                self._nos = Nos(None)
                box.add("boto_s3_nos", self._nos)
        return self._nos
    """

    #
    # ================== publics =====================
    #
    @property
    def paths_root_manifest_path(self) -> str:
        """@private"""
        r = self.csvpaths.config.get(section="inputs", name="csvpaths")
        p = Nos(r).join("manifest.json")
        # p = os.path.join(r, "manifest.json")
        # nos = self.nos
        nos = Nos(r)
        if not nos.dir_exists():
            nos.makedirs()
        nos.path = p
        if not nos.exists():
            with DataFileWriter(path=p) as file:
                file.write("[]")
        return p

    @property
    def paths_root_manifest(self) -> str:
        """@private"""
        p = self.paths_root_manifest_path
        with DataFileReader(p) as reader:
            return json.load(reader.source)

    def get_manifest_for_name(self, name: str) -> dict:
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            if ref.datatype != ref.CSVPATHS:
                raise ValueError(f"Reference datatype is not valid: {ref.datatype}")
            name = ref.root_major
        home = self.named_paths_home(name)
        home = Nos(home).join("manifest.json")
        # home = os.path.join(home, "manifest.json")
        return self.registrar.get_manifest(home)

    @property
    def registrar(self) -> PathsRegistrar:
        """@private"""
        if self._registrar is None:
            self._registrar = PathsRegistrar(self.csvpaths)
        return self._registrar

    def named_paths_home(self, name: NamedPathsName) -> str:
        """@private"""
        home = Nos(self.named_paths_dir).join(name)
        # home = os.path.join(self.named_paths_dir, name)
        # nos = self.nos
        nos = Nos(home)
        b = nos.dir_exists()
        if not b:
            nos.makedirs()
        return home

    def get_named_paths_uuid(self, name: NamedPathsName) -> str:
        if name is None:
            raise ValueError("Paths name cannot be None")
        if name.find("#") > -1:
            name = name[0 : name.find("#")]
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            if ref.datatype != ReferenceParser.CSVPATHS:
                raise ValueError(
                    "Must be a reference of type {ReferenceParser.CSVPATHS}"
                )
            name = ref.root_major

        path = self.named_paths_home(name)
        path = Nos(path).join("manifest.json")
        # nos = self.nos
        nos = Nos(path)
        if nos.exists():
            with DataFileReader(path) as reader:
                m = json.load(reader.source)
                return m[len(m) - 1]["uuid"]
        raise ValueError(f"No manifest for path named {name}")

    @property
    def named_paths_dir(self) -> str:
        """@private"""
        return self.csvpaths.config.inputs_csvpaths_path

    def set_named_paths(self, np: dict[NamedPathsName, list[Csvpath]]) -> None:
        for name in np:
            if not isinstance(np[name], list):
                msg = f"{name} does not key a list of csvpaths"
                self.csvpaths.error_manager.handle_error(source=self, msg=msg)
                if self.csvpaths.ecoms.do_i_raise():
                    raise InputException(msg)
                return
        for k, v in np.items():
            self.add_named_paths(name=k, paths=v)
        self.csvpaths.logger.info("Set named-paths to %s groups", len(np))

    def add_named_paths_from_dir(
        self, *, directory: str, name: NamedPathsName = None, template=None
    ) -> list[str]:
        #
        # we return a list of references to the loaded paths. these are not
        # references to a particular version of the paths, as would be the case,
        # with files, because we don't store versions, only track them.
        #
        if directory is None:
            msg = "Named paths collection name needed"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise InputException(msg)
        if self.can_load(directory) is not True:
            return
        lst = []
        # nos = self.nos
        nos = Nos(directory)
        if not nos.isfile():
            try:
                dlist = nos.listdir()
                base = directory
                agg = []
                for p in dlist:
                    if p[0] == ".":
                        continue
                    if p.find(".") == -1:
                        continue
                    ext = p[p.rfind(".") + 1 :].strip().lower()
                    if ext not in self.csvpaths.config.get(
                        section="extensions", name="csvpath_files"
                    ):
                        continue
                    path = Nos(base).join(p)
                    # path = os.path.join(base, p)
                    if name is None:
                        #
                        # add files one by one under their own names
                        #
                        aname = self._name_from_name_part(p)
                        ref = self.add_named_paths_from_file(
                            name=aname, file_path=path, template=template
                        )
                        lst.append(ref)
                    else:
                        #
                        # if a name, aggregate all the files
                        #
                        _ = self._get_csvpaths_from_file(path)
                        #
                        # try to find a run-index: N metadata and use it
                        # to try to impose order? we could do this, but it would
                        # be messy and a work-around to avoid making people
                        # use the ordered ways of creating named-paths that
                        # already exist: JSON and all-in-ones
                        #
                        agg += _
                if len(agg) > 0:
                    ref = self.add_named_paths(
                        name=name, paths=agg, source_path=directory, template=template
                    )
                    lst.append(ref)
            except Exception as ex:
                msg = f"Error adding named-paths from directory: {ex}"
                self.csvpaths.error_manager.handle_error(source=self, msg=msg)
                if self.csvpaths.ecoms.do_i_raise():
                    raise
        else:
            msg = "Dirname must point to a directory"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise InputException(msg)
        return lst

    def add_named_paths_from_file(
        self,
        *,
        name: NamedPathsName,
        file_path: str,
        template=None,
        append: bool = False,
    ) -> str:
        if self.can_load(file_path) is not True:
            return None
        try:
            #
            # change for FP: added append as a pass-through
            #
            self.csvpaths.logger.debug("Reading csvpaths file at %s", file_path)
            _ = self._get_csvpaths_from_file(file_path)
            ref = self.add_named_paths(
                name=name,
                paths=_,
                source_path=file_path,
                template=template,
                append=append,
            )
            #
            # absolute ref to the named-paths group in its present form.
            #
            return ref
        except Exception as ex:
            msg = f"Error adding named-paths from file: {ex}"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise
            return None

    def add_named_paths_from_json(self, file_path: str) -> list[str]:
        if file_path is None:
            raise ValueError(
                "Named-paths group definition JSON file path cannot be None"
            )
        #
        # we return a list of references to the loaded paths. these are not
        # references to a particular version of the paths, as would be the case,
        # with files, because we don't store versions, only track them. with
        # JSON the working assumption has been that you usually create one JSON
        # per named-paths group; however, that won't always be the case.
        #
        lst = []
        try:
            if self.can_load(file_path) is not True:
                return
            self.csvpaths.logger.debug("Opening JSON file at %s", file_path)
            #
            # FlightPath - should not be tied to the local file system.
            #
            nos = Nos(file_path)
            if not nos.exists():
                raise ValueError(
                    f"{file_path} is not a JSON named-paths group definition file"
                )
            with DataFileReader(file_path) as f:
                j = json.load(f.source)
                self.csvpaths.logger.debug("Found JSON file with %s keys", len(j))
                for k in j:
                    #
                    # _config is an optional dict of pathname-to-configuration data.
                    # config data includes run_dir templates. it may come to include
                    # modes or other settings.
                    #
                    if k == "_config":
                        continue
                    self.store_json_paths_file(k, file_path)
                    v = j[k]
                    paths = []
                    for f in v:
                        _ = self._get_csvpaths_from_file(f)
                        paths += _
                    template = None
                    if "_config" in j:
                        c = j["_config"]
                        if k in c:
                            template = c[k].get("template")

                    ref = self.add_named_paths(
                        name=k, paths=paths, source_path=file_path, template=template
                    )
                    lst.append(ref)
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            self.csvpaths.error_manager.handle_error(source=self, msg=f"{ex}")
            if self.csvpaths.ecoms.do_i_raise():
                raise
        return lst

    def can_load(self, path: str) -> bool:
        #
        # in multi-user envs, e.g. flightpath server, we may not want a user to
        # be able to register files from anywhere on the local machine or an
        # unrestricted HTTP server.
        #
        config = self.csvpaths.config
        http = config.get(section="inputs", name="allow_http_files", default=False)
        http = str(http).strip().lower() in ["true", "yes"]
        local = config.get(section="inputs", name="allow_local_files", default=False)
        local = str(local).strip().lower() in ["true", "yes"]
        nos = Nos(path)
        if nos.is_http and http is not True:
            msg = f"Cannot add {path} because loading files over HTTP is not allowed"
            self.csvpaths.logger.error(msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise FileException(msg)
            return False
        if nos.is_local and local is not True:
            msg = f"Cannot add {path} because loading local files is not allowed"
            self.csvpaths.logger.error(msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise FileException(msg)
            return False
        return True

    def add_named_paths(
        self,
        *,
        name: NamedPathsName,
        paths: list[Csvpath] = None,
        from_file: str = None,
        from_dir: str = None,
        from_json: str = None,
        source_path: str = None,
        template: str = None,
        append: bool = False,
        #
        # exp. added for FP
        #
        assure_definition: bool = True,
    ) -> str:
        self.last_add_metadata = None
        if template is not None:
            #
            # this will raise an error. if that's a problem use temu.validate
            #
            temu.valid(template)
        if from_file is not None:
            #
            # change for FP. added append as a pass-through
            #
            ref = self.add_named_paths_from_file(
                name=name, file_path=from_file, template=template, append=append
            )
            return ref
        elif from_dir is not None:
            return self.add_named_paths_from_dir(
                name=name, directory=from_dir, template=template
            )
        elif from_json is not None:
            return self.add_named_paths_from_json(file_path=from_json)
        if not isinstance(paths, list):
            msg = """Paths must be a list of csvpaths.
                    If you want to load a file use add_named_paths_from_file or
                    set_named_paths_from_json."""
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise InputException(msg)
            return
        self.csvpaths.logger.debug("Adding csvpaths to named-paths group %s", name)
        try:
            for _ in paths:
                self.csvpaths.logger.debug("Adding %s to %s", _, name)
            s = self._str_from_list(paths)
            group_file_path = self._copy_in(name, s, append=append)
            #
            # the paths have to be reacquired because we might be appending.
            #
            # need paths to be the full set of csvpaths in the named-paths group
            # from this point down.
            #
            paths = self._get_csvpaths_from_file(group_file_path)
            #
            grp_paths = self.get_identified_paths_in(name, paths=paths)
            ids = [t[0] for t in grp_paths]
            for i, t in enumerate(ids):
                if t is None or t.strip() == "":
                    ids[i] = f"{i}"
            if template is not None:
                self.store_template_for_paths(name, template)
            #
            # exp.
            # added for FP
            #
            # make sure there is a json definition file?
            # if true, just ask for the file and it will be created if not found.
            #
            if assure_definition is True:
                self.get_json_paths_file(name)
            #
            # end exp
            #
            mdata = PathsMetadata(self.csvpaths.config)
            mdata.archive_name = self.csvpaths.config.archive_name
            mdata.named_paths_name = name
            # nos = self.nos
            nos = Nos(mdata.named_paths_root)
            sep = nos.sep
            mdata.named_paths_home = f"{mdata.named_paths_root}{sep}{name}"
            mdata.group_file_path = f"{mdata.named_paths_home}{sep}group.csvpaths"
            #
            # even when appending we need paths, ids, and len(ids) to be the complete set
            # so that the metadata represents the named-paths group, not just the append
            # action.
            #
            mdata.named_paths = paths
            mdata.named_paths_identities = ids
            mdata.named_paths_count = len(ids)
            #
            #
            #
            mdata.source_path = source_path
            mdata.template = template
            self.registrar.register_complete(mdata)
            #
            # with named-paths we don't keep separate versions of the group, so
            # we don't include dates in references. the versions can be "easily"
            # compiled from metadata, fwiw.
            #
            ref = f"${name}.csvpaths.0:from"
            self.last_add_metadata = mdata
            return ref
        except Exception as ex:
            msg = f"Error adding named-paths list to named-paths group: {ex}"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise
            return None

    #
    # adding ref handling for the form: $many.csvpaths.food
    #
    def get_named_paths(self, name: NamedPathsName) -> list[Csvpath]:
        self.csvpaths.logger.info("Getting named-paths for %s", name)
        ret = None
        npn = None
        identity = None
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            if ref.datatype != ReferenceParser.CSVPATHS:
                raise InputException(
                    f"Reference datatype must be {ReferenceParser.CSVPATHS}"
                )
            npn = ref.root_major
            identity = ref.name_one
            #
            # atm, we haven't changed as part of the new ref grammar. we don't use
            # the ref directly so we have to rebuild any tokens on name_one
            #
            if len(ref.name_one_tokens) > 0:
                t = ":".join(ref.name_one_tokens)
                identity = f"{identity}:{t}"
        else:
            npn, identity = self._paths_name_path(name)
        if identity is None and self.has_named_paths(npn):
            ret = self._get_named_paths(npn)
        elif identity is not None and identity.find(":") == -1:
            ret = [self._find_one(npn, identity)]
        #
        # we need to be able to grab paths up to and starting from like this:
        #   $many.csvpaths.food:to
        #   $many.csvpaths.food:from
        #
        elif identity is not None:
            i = identity.find(":")
            directive = identity[i:]
            identity = identity[0:i]
            if directive == ":to":
                ret = self._get_to(npn, identity)
            elif directive == ":from":
                ret = self._get_from(npn, identity)
            else:
                #
                #
                #
                directive = directive[1:]
                i = expu.to_int(directive)
                if isinstance(i, int):
                    path = self._group_file_path(npn)
                    lst = self._get_csvpaths_from_file(path)
                    if i >= len(lst):
                        raise ValueError("Cannot find a csvpath in {npn} at {i}")
                    csvpath = lst[i]
                    return [csvpath]
                #
                #
                #
                self.csvpaths.logger.error(
                    "Incorrect reference directive: name: %s, paths-name: %s, identity: %s",
                    name,
                    npn,
                    identity,
                )
                raise InputException(
                    f"Reference directive must be :to or :from or :<int>, not {directive}"
                )
        else:
            ...
        return ret

    def store_json_paths_file(self, name: NamedPathsName, jsonpath: str) -> None:
        """@private"""
        if name is None:
            raise ValueError("Name cannot be None")
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            name = ref.root_major
        nos = Nos(jsonpath)
        if nos.exists():
            with DataFileReader(jsonpath) as file:
                j = file.read()
                if not j or len(j.strip()) == 0:
                    raise ValueError(
                        f"Path to JSON file at {jsonpath} does not have valid JSON"
                    )
                self.store_json_for_paths(name, j)

    def store_json_for_paths(self, name: NamedPathsName, definition: str) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            name = ref.root_major
        home = self.named_paths_home(name)
        p = Nos(home).join("definition.json")
        with DataFileWriter(path=p) as writer:
            writer.write(definition)

    def get_json_paths_file(self, name: NamedPathsName) -> dict:
        if name is None:
            raise ValueError("Name cannot be None")
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            name = ref.root_major
        home = self.named_paths_home(name)
        path = Nos(home).join("definition.json")
        # path = os.path.join(home, "definition.json")
        nos = Nos(path)
        definition = None
        if nos.exists():
            with DataFileReader(path) as file:
                definition = json.load(file.source)
        else:
            definition = {}
            #
            # exp. improved for FP
            #
            self._get_named_paths(name)
            definition[name] = []
            #
            # end exp.
            #
            with DataFileWriter(path=path, mode="w") as writer:
                json.dump(definition, writer.sink, indent=2)
        return definition

    def get_template_for_paths(self, name: NamedPathsName) -> str:
        if name is None:
            raise ValueError("Name cannot be None")
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            name = ref.root_major
        definition = self.get_json_paths_file(name)
        if "_config" not in definition:
            return ""
        config = definition["_config"]
        if name not in config:
            return None
        template = config[name].get("template")
        if template is None:
            return None
        return template

    def store_template_for_paths(self, name: NamedPathsName, template: str) -> None:
        if template is None:
            raise ValueError("Template cannot be None")
        if name is None:
            raise ValueError("Name cannot be None")
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            name = ref.root_major
        definition = self.get_json_paths_file(name)
        config = definition.get("_config")
        if config is None:
            config = {}
            definition["_config"] = config
        if name not in config:
            config[name] = {"template": template}
        else:
            config[name]["template"] = template
        j = json.dumps(definition)
        self.store_json_for_paths(name, j)

    def get_config_for_paths(self, name: NamedPathsName) -> dict:
        if name.startswith("$"):
            name = ReferenceParser(name, csvpaths=self.csvpaths).root_major
        definition = self.get_json_paths_file(name)
        config = definition.get("_config")
        if config is None:
            config = {}
        config = config.get(name)
        if config is None:
            config = {}
        return config

    def store_config_for_paths(self, name: NamedPathsName, cfg: dict) -> None:
        if name.startswith("$"):
            name = ReferenceParser(name, csvpaths=self.csvpaths).root_major
        j = self.get_json_paths_file(name)
        j["_config"] = cfg
        d = json.dumps(j, indent=2)
        self.store_json_for_paths(name, d)

    #
    # store script to run after the named-path. we could make this a mode, but it
    # should be in the named-paths first.
    #
    def store_script_for_paths(
        self,
        *,
        name: NamedPathsName,
        script_name: str,
        when: str = None,
        script_type: str = None,
        text: str = None,
    ) -> None:
        if script_name is None:
            raise ValueError("script_name cannot be None")
        if when not in [None, "all", "errors", "valid", "invalid"]:
            raise ValueError(
                "When must be one of 'all', 'errors', 'valid', or 'invalid'; it cannot be None"
            )
        if script_type is None and when is None:
            when = "all"
        elif script_type is not None and when is not None:
            raise ValueError("Cannot provide both when and script_type")
        if script_type is None:
            script_type = f"on_complete_{when}_script"

        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            name = ref.root_major
        # check this creates if not found
        definition = self.get_json_paths_file(name)
        config = definition.get("_config")
        if config is None:
            config = {}
            definition["_config"] = config
        if name not in config:
            config[name] = {script_type: script_name}
        else:
            config[name][script_type] = script_name
        j = json.dumps(definition)
        self.store_json_for_paths(name, j)
        #
        # if we have the text of the script, store that too
        #
        script_file = None
        if text is not None:
            #
            # if the user configured a shell we'll use it to add a shebang.
            #
            if not text.startswith("#!"):
                s = self.csvpaths.config.get(section="scripts", name="shell")
                if s is not None:
                    text = f"#!{s}\n{text}"
            script_file = Nos(self.named_paths_home(name)).join(script_name)
            # script_file = os.path.join(self.named_paths_home(name), script_name)
            try:
                with DataFileWriter(path=script_file, mode="wb") as file:
                    print(f"textx: text: {text} {type(text)}")
                    # bs = text.encode("utf-8")
                    file.write(text)
            except Exception as e:
                import traceback

                print(traceback.format_exc())
                msg = f"Could not store script at {script_file}: {e}"
                self.csvpaths.logger.error(e)
                self.csvpaths.error_manager.handle_error(source=self, msg=msg)
                if self.csvpaths.ecoms.do_i_raise():
                    raise RuntimeError(msg)
                return

    def get_scripts_for_paths(self, name: NamedPathsName) -> list:
        config = self.get_config_for_paths(name)
        lst = []
        for t in self.SCRIPT_TYPES:
            s = config.get(t)
            if s is not None:
                lst.append((t, s))
        return lst

    #
    # given a named-paths name and one of the four types of scripts, returns the
    # full filesystem path to the script file. the four types of scripts are:
    #    - on_complete_all_script
    #    - on_complete_errors_script
    #    - on_complete_valid_script
    #    - on_complete_invalid_script
    #
    def get_script_path_for_paths(
        self, *, name: NamedPathsName, script_type: str
    ) -> str:
        if name is None:
            raise ValueError("Name cannot be None")
        if script_type is None:
            raise ValueError("Script type cannot be None")
        if script_type not in PathsManager.SCRIPT_TYPES:
            raise ValueError(f"Unknown script type {script_type}")

        definition = self.get_json_paths_file(name)
        config = definition.get("_config")
        if config is None:
            raise ValueError(f"Script {script_type} is not configured")
        cfg = config.get(name)
        if cfg is None:
            raise ValueError(f"Script {script_type} is not configured")
        script_name = cfg.get(script_type)
        return Nos(self.named_paths_home(name)).join(script_name)
        # return os.path.join(self.named_paths_home(name), script_name)

    #
    # gets the text of the script indicated by named-paths name and script type
    #
    def get_script_for_paths(self, *, name: NamedPathsName, script_type: str) -> str:
        path = self.get_script_path_for_paths(name=name, script_type=script_type)
        if path is None:
            raise ValueError(f"Script path for {script_type} is not found in {name}")
        nos = Nos(path)
        if nos.exists():
            with DataFileReader(path) as file:
                return file.read()
        else:
            raise ValueError(f"Script {path} not found")

    @property
    def named_paths_names(self) -> list[str]:
        """@private"""
        path = self.named_paths_dir
        names = []
        # nos = self.nos
        nos = Nos(path)
        lst = nos.listdir()
        for n in lst:
            nos.path = Nos(path).join(n)
            # nos.path = os.path.join(path, n)
            if not nos.isfile():
                names.append(n)
        return names

    def remove_named_paths(self, name: NamedPathsName, strict: bool = False) -> None:
        """@private"""
        if not self.has_named_paths(name) and strict is True:
            raise InputException(f"Named-paths name {name} not found")
        if not self.has_named_paths(name):
            return
        home = self.named_paths_home(name)
        # nos = self.nos
        nos = Nos(home)
        nos.remove()

    def remove_all_named_paths(self) -> None:
        """@private"""
        names = self.named_paths_names
        for name in names:
            self.remove_named_paths(name)

    def has_named_paths(self, name: NamedPathsName) -> bool:
        """@private"""
        path = Nos(self.named_paths_dir).join(name)
        # path = os.path.join(self.named_paths_dir, name)
        # nos = self.nos
        nos = Nos(path)
        return nos.dir_exists()

    def number_of_named_paths(self, name: NamedPathsName) -> int:
        """@private"""
        paths = self._get_named_paths(name)
        return 0 if not paths else len(paths)

    def total_named_paths(self) -> int:
        """@private"""
        return len(self.named_paths_names)  # pragma: no cover

    @property
    def named_paths_count(self) -> int:
        #
        # this signature matches the file_manager interface
        #
        return self.total_named_paths()

    #
    # ================== internals =====================
    #

    def _get_named_paths(self, name: NamedPathsName) -> list[Csvpath]:
        if not self.has_named_paths(name):
            return None
        s = ""
        path = self.named_paths_home(name)
        grp = Nos(path).join("group.csvpaths")
        # nos = self.nos
        nos = Nos(grp)
        if nos.exists():
            with DataFileReader(grp) as reader:
                s = reader.read()
        cs = s.split("---- CSVPATH ----")
        cs = [s for s in cs if s.strip() != ""]
        #
        # this update may not result in broadcasting an update event to listeners.
        # that all depends on if group.csvpaths was changed outside the manager.
        # if someone put a new group.csvpaths file by hand we want to capture its
        # fingerprint for future reference. this shouldn't happen, but it probably
        # will happen.
        #
        # seen 1x with FlightPath. not yet clear if FP is doing something new and
        # desireable or if it has a bug. in principle, still don't see a reason this
        # update should obtain, unless a user edits a file they shouldn't.
        #
        self.registrar.update_manifest_if(name=name, group_file_path=grp, paths=cs)
        return cs

    def _str_from_list(self, paths: list[Csvpath]) -> Csvpath:
        """@private"""
        f = ""
        for _ in paths:
            f = f"{f}\n\n---- CSVPATH ----\n\n{_}"
        return f

    def _copy_in(self, name: NamedPathsName, csvpathstr: Csvpath, append=False) -> str:
        #
        # if we have a set of paths we append these new paths
        #
        if self.has_named_paths(name) and append is True:
            existing = self.get_named_paths(name)
            estr = self._str_from_list(existing)
            if not estr.strip().endswith(
                "---- CSVPATH ----"
            ) and not csvpathstr.strip().startswith("---- CSVPATH ----"):
                csvpathstr = f"{estr}\n\n---- CSVPATH ----\n\n"
            csvpathstr = f"{estr}{csvpathstr}"
        #
        # continue with the write
        #
        temp = self._group_file_path(name)
        with DataFileWriter(path=temp, mode="w") as writer:
            #
            # note that this only actually appends if mode is "a" or "ab". here it
            # "w" so we rewrite the file. but we append to the existing above.
            #
            writer.append(csvpathstr)
        return temp

    def _group_file_path(self, name: NamedPathsName) -> str:
        temp = Nos(self.named_paths_home(name)).join("group.csvpaths")
        return temp

    def _get_csvpaths_from_file(self, file_path: str) -> list[Csvpath]:
        if self.can_load(file_path) is not True:
            return []
        with DataFileReader(file_path) as reader:
            cp = reader.read()
            _ = [
                apath.strip()
                for apath in cp.split(PathsManager.MARKER)
                if apath.strip() != ""
            ]
            self.csvpaths.logger.debug("Found %s csvpaths in file", len(_))
            return _

    def _paths_name_path(self, pathsname) -> tuple[NamedPathsName, Identity]:
        specificpath = None
        i = pathsname.find("#")
        if i > 0:
            specificpath = pathsname[i + 1 :]
            pathsname = pathsname[0:i]
        return (pathsname, specificpath)

    def _get_to(self, npn: NamedPathsName, identity: Identity) -> list[Csvpath]:
        ps = []
        paths = self.get_identified_paths_in(npn)
        for path in paths:
            ps.append(path[1])
            if path[0] == identity:
                break
        return ps

    def _get_from_names(self, npn: NamedPathsName, identity: Identity) -> list[Csvpath]:
        ps = []
        paths = self.get_identified_paths_in(npn)
        for path in paths:
            if path[0] != identity and len(ps) == 0:
                continue
            ps.append(path[0])
        return ps

    #
    # this version correctly picks up csvpaths that the Framework identifies by index
    # because they don't have user assigned identities. this was seen in FlightPath
    # but applies in general.
    #
    def _get_from(self, npn: NamedPathsName, identity: Identity) -> list[Csvpath]:
        index = expu.to_int(identity)
        ps = []
        paths = self.get_identified_paths_in(npn)
        for i, path in enumerate(paths):
            #
            # if we have the identity or the identity is the index or we are collecting
            # after our first collection because :from collects all csvpaths coming after
            # a starting csvpath
            #
            if (path[0] == identity or (path[0] is None and index == i)) or len(ps) > 0:
                ps.append(path[1])
        return ps

    def get_preceeding_instance_identity(self, name, index: int) -> str:
        if index <= 0:
            raise ValueError("0 is the first csvpath in named-paths group")
        paths = self.get_named_paths(name)
        paths = self.get_identified_paths_in(name, paths)
        return paths[index - 1][0]

    def get_identified_path_names_in(
        self, nps: NamedPathsName, paths: list[Csvpath] = None
    ) -> list[str]:
        paths = self.get_identified_paths_in(nps, paths)
        names = []
        for p in paths:
            names.append(p[0])
        return names

    def get_identified_paths_in(
        self, nps: NamedPathsName, paths: list[Csvpath] = None
    ) -> list[tuple[Identity, Csvpath]]:
        """@private"""
        #
        # used by PathsRegistrar
        #
        if paths is None:
            paths = self.get_named_paths(nps)
        idps = []
        for path in paths:
            #
            # we can get this from our self.csvpath, should we?
            #
            c = CsvPath()
            MetadataParser(c).extract_metadata(instance=c, csvpath=path)
            idps.append((c.identity, path))
        return idps

    def _find_one(self, npn: NamedPathsName, identity: Identity) -> Csvpath:
        #
        # this version of the method is a change for FlightPath. the change is correct for
        # all purposes, but showed up clearly in FP. the problem is that we don't test index
        # for unidentitied paths. luckily we do return all paths with None as the identity
        # for those w/o user specified id. for those we just need to test the index.
        #
        # this version assumes that if a csvpath is identitied we do not allow using the
        # index to point to it. this may not be the right assumption, but it is arguably a
        # good way to go. if the writer bothered to identify, the id is more specific than
        # the index and so less error-prone.
        #
        index = expu.to_int(identity)
        if npn is not None:
            paths = self.get_identified_paths_in(npn)
            for i, path in enumerate(paths):
                if path[0] == identity or index == i:
                    return path[1]
        raise InputException(
            f"Csvpath identified as '{identity}' must be in the group identitied as '{npn}'"
        )

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name
