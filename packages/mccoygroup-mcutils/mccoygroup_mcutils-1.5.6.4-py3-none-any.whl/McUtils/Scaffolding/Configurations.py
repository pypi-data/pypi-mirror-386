"""
Provides functionality for managing configurations stored in files
without having to write bespoke serialization/deserialization/application
code every time a new job type comes up
"""

import os, inspect
from .Serializers import *
from ..Devutils import OptionsSet

__all__ = [ "Config", "ParameterManager"]

class Config:
    """
    A configuration object which basically just supports
    a dictionary interface, but which also can automatically
    filter itself so that it only provides the keywords supported
    by a `from_config` method.
    """
    def __init__(self, config, serializer=None, extra_params=None):
        """Loads the config from a file
        :param config:
        :type config: str
        :param serializer:
        :type serializer: None | BaseSerializer
        """
        self.config = self.find_config(config)
        self._serializer = serializer
        self._conf = None
        self._loaded = False
        if extra_params is None:
            extra_params = {}
        self.extra = extra_params

    config_file_name = "config"
    config_file_extensions = [".json", ".yml", ".yaml", ".py"]
    @classmethod
    def find_config(self, config, name=None, extensions=None):
        """
        Finds configuration file (if config isn't a file)

        :param config:
        :type config:
        :return:
        :rtype:
        """
        if os.path.isdir(config):
            if name is None:
                name = self.config_file_name
            if extensions is None:
                extensions = self.config_file_extensions
            for ext in extensions:
                test = os.path.join(config, name + ext)
                if os.path.isfile(test):
                    return test
        elif os.path.isfile(config):
            return config

    _serializer_map = {
        ".py": ModuleSerializer,
        ".json": JSONSerializer,
        ".yaml": YAMLSerializer,
        ".yml": YAMLSerializer
    }
    @classmethod
    def get_serializer(self, file):
        _, ext = os.path.splitext(file)
        if ext not in self._serializer_map:
            raise ValueError("no known serializer for file extension {}".format(ext))
        mode = self._serializer_map[ext]
        return mode()

    @classmethod
    def new(cls, loc, init=None):
        config = os.path.join(loc,
                              cls.config_file_name + cls.config_file_extensions[0]
                              )
        serializer = cls.get_serializer(config)
        if init is None:
            init = {}
        with open(config, 'w') as stream:
            serializer.serialize(stream, init)
        return cls(config)

    def serialize(self, file, ops):
        if self._serializer is None:
            ser = self.get_serializer(file)
        else:
            ser = self._serializer
        with open(file, 'w') as stream:
            return ser.serialize(stream, ops)
    def deserialize(self, file):
        if self._serializer is None:
            ser = self.get_serializer(file)
        else:
            ser = self._serializer
        with open(file, 'r') as stream:
            return ser.deserialize(stream)

    def save(self):
        return self.serialize(self.config, self.opt_dict)
    def load(self):
        return self.deserialize(self.config)

    @property
    def name(self):
        try:
            res = self.get_key("name")
        except KeyError:
            res = os.path.basename(self.config)
        return res
    @property
    def opt_dict(self):
        self.load_opts()
        return dict(self._conf, **self.extra)

    def filter(self, keys, strict=True):
        """
        Returns a filtered option dictionary according to keys.
        Strict mode will raise an error if there is a key in the config that isn't
        in keys.

        :param keys:
        :type keys: Iterable[str] | function
        :param strict:
        :type strict: bool
        :return:
        :rtype:
        """
        try:
            keys = list(keys)
        except TypeError:
            # method we need to inspect to ask about kwargs
            import inspect
            args = inspect.signature(keys).parameters.values()
            keys = [arg.name for arg in args if arg.kind == arg.POSITIONAL_OR_KEYWORD]
        opts = self.opt_dict
        opt_keys = set(opts.keys())
        filt = {}
        for k in keys:
            if k in opts:
                filt[k] = opts[k]
                opt_keys.remove(k)
        if strict:
            if len(opt_keys) > 0:
                raise ValueError("{}: excess keys in config {}".format(
                    type(self).__name__,
                    opt_keys
                ))
        return filt

    def apply(self, func, strict=True):
        """
        Applies func to stored parameters

        :param func:
        :type func:
        :return:
        :rtype:
        """
        kw = self.filter(func, strict=strict)
        return func(**kw)

    def update(self, **kw):
        opts = self.opt_dict
        opts.update(**kw)
        self.save()

    def load_opts(self):
        if not self._loaded:
            cfg = self.config
            if cfg is None:
                raise ValueError("can't load config from None")
            self._conf = self.load()
            self._conf['config_location'] = os.path.dirname(cfg)

    def get_conf_attr(self, item):
        if not self._loaded:
            self.load_opts()
        if self._conf_type is dict:
            return self._conf_obj[item]
        else:
            return getattr(self._conf_obj, item)

    def __getattr__(self, item):
        return self.get_conf_attr(item)

class ParameterManager(OptionsSet):

    def serialize(self, file, mode = None):
        return ModuleSerializer().serialize(file, self.ops, mode = mode)

    @classmethod
    def deserialize(cls, file, mode=None, attribute=None):
        return ModuleSerializer().deserialize(file, mode=mode, attribute=attribute)