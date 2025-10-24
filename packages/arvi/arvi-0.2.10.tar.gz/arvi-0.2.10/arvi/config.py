from pathlib import Path
import configparser
from pprint import pprint


def get_config_path():
    return Path.home() / '.config' / 'arvi.ini'

def get_config():
    config = configparser.ConfigParser()
    config.add_section('config')
    if (path := get_config_path()).exists():
        config.read(path)
    return config

def save_config(config):
    config.write(get_config_path().open('w'))


def instancer(cls):
    return cls()

@instancer
class config:
    # configuration values
    __conf = {
        # whether to return self from (some) RV methods
        'return_self': False,
        # whether to adjust instrument means before gls by default
        'adjust_means_gls': True,
        # whether to check internet connection before querying DACE
        'check_internet': False,
        # make all DACE requests without using a .dacerc file
        'request_as_public': False,
        # enable from arvi import star_name
        'fancy_import': True,
        # use the 'dark_background' matplotlib theme
        'dark_plots': False,
        # debug
        'debug': False,
    }
    __setters = list(__conf.keys())

    __user_config = get_config()

    def __getattr__(self, name):
        if name in ('__custom_documentations__', ):
            # return {'return_self': 'help!'}
            return {}

        try:
            if self.__user_config.has_option('config', name):
                value = self.__user_config.get('config', name)
                value = True if value == 'True' else value
                value = False if value == 'False' else value
                self.__conf[name] = value

            return self.__conf[name]
        except KeyError:
            raise KeyError(f"unknown config option '{name}'")

    def __setattr__(self, name, value):
        if name in config.__setters:
            self.__conf[name] = value
        else:
            if 'config' not in self.__user_config:
                self.__user_config.add_section('config')
            self.__user_config.set('config', name, str(value))
            save_config(self.__user_config)
            # raise NameError(f"unknown configuration name '{name}'")

    def show(self):
        if 'config' in self.__user_config:
            pprint(self.__conf | dict(self.__user_config['config']))
        else:
            pprint(self.__conf)
