import os
import yaml
from typing import Union, Dict, Any


SETTINGS_DIR = os.path.join(str(os.path.expanduser('~')), '.nest')
TEMPLATE_FILE = os.path.join(SETTINGS_DIR, 'template.yml')
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.yml')

DEFAULT_SETTINGS = """\
# Nest - A flexible tool for building and sharing deep learning modules
# Settings Template (User custom settings should be placed in "settings.yml")

# Enable logging to file
LOGGING_TO_FILE: true

# Logging path (default: <user_home>/.nest/nest.log)
LOGGING_PATH: null

# User defined search paths {namespace: path} for Nest module auto-discover (default: {})
SEARCH_PATHS: null

# Seperator between namespace and Nest module name
NAMESPACE_SEP: '.'

# Put namespace behind module name if set to true
NAMESPACE_ORDER_REVERSE: false

# Module manager update interval (seconds)
UPDATE_INTERVAL: 1.5

# Varaible prefix in Nest config syntax
VARIABLE_PREFIX: '@'

# Enable strict mode for config parser
# User must specify 'delay_resolve' for Nest modules 
# in the config file if set to true.
PARSER_STRICT: false

# Namespace config file name
NAMESPACE_CONFIG_FILENAME: 'nest.yml'

# Automatically install requirements when install Nest modules
AUTO_INSTALL_REQUIREMENTS: false

# Threshold of missing dependency matching
INSTALL_TIP_THRESHOLD: 0.15

# Internel debug flags
# Raises errors instead of warnings
RAISES_ERROR: false
"""


class SettingManager(object):

    @staticmethod
    def save_settings(path: str, settings: Union[str, Dict[str, Any]]) -> None:
        """Save Nest settings.
        
        Parameters:
            path:
                Path to the setting file
            settings:
                The settings dict or string
        """

        with open(path, 'w') as f:
            if isinstance(settings, str):
                f.write(settings)
            elif isinstance(settings, dict):
                yaml.dump(settings, f, default_flow_style=False)
            else:
                raise TypeError('The settings should have a type of "str" or "dict".')

    @staticmethod
    def load_settings() -> Dict[str, Any]:
        """Load Nest settings.

        Returns:
            The settings dict
        """
        
        # create if not exists
        if not os.path.exists(SETTINGS_DIR):
            os.mkdir(SETTINGS_DIR)
        if not os.path.exists(TEMPLATE_FILE):
            SettingManager.save_settings(TEMPLATE_FILE, DEFAULT_SETTINGS)
        if not os.path.exists(SETTINGS_FILE):
            SettingManager.save_settings(SETTINGS_FILE, '# User custom settings')

        # load settings
        settings = yaml.load(DEFAULT_SETTINGS)
        with open(SETTINGS_FILE, 'r') as f:
            user_settings = yaml.load(f) or dict()
            settings.update(user_settings)

        # handle defaults
        if settings['LOGGING_PATH'] is None:
            settings['LOGGING_PATH'] = os.path.join(SETTINGS_DIR, 'nest.log')
        if settings['SEARCH_PATHS'] is None:
            settings['SEARCH_PATHS'] = dict()

        return settings, user_settings

    def __init__(self):
        self.load()
    
    def __getitem__(self, key: str):
        return self.settings[key]

    def __setitem__(self, key: str, val: str):
        self.user_settings[key] = val

    def __contains__(self, key):
        return key in self.settings.keys()

    def load(self):
        self.settings, self.user_settings = SettingManager.load_settings()
    
    def save(self):
        SettingManager.save_settings(SETTINGS_FILE, self.user_settings)

# load global settings
try:
    settings = SettingManager()
except Exception as exc_info:
    raise RuntimeError('Unable to load global settings of Nest. %s' % exc_info)
