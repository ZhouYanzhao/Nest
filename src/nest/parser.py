import os
import re
from typing import Any, Dict, Union, Optional
from datetime import datetime
from copy import deepcopy

import nest.utils as U
from nest.modules import module_manager
from nest.settings import settings
from nest.logger import logger


def parse_config(
    config: Union[list, dict],
    env_vars: Dict[str, str] = dict(),
    global_vars: Dict[str, str] = dict()) -> Union[list, dict]:
    """Parse experiment config.

    Parameters:
        config:
            The configuration of Nest modules, which specifies initial parameters, topologies, etc. 
        env_vars:
            The environment variables
        global_vars:
            The global variables

    Returns:
        The resolved config
    """

    def is_variable(name: str) -> bool:
        return isinstance(name, str) and name.startswith(settings['VARIABLE_PREFIX'])

    def resolve_variable(name: str) -> Any:
        if name[1:] in global_vars.keys():
            return global_vars[name[1:]]
        elif name[1:] in env_vars.keys():
            return env_vars[name[1:]]
        else:
            raise TypeError('Could not resolve variable "%s".' % name)

    if isinstance(config, list):
        for idx, val in enumerate(config):
            if is_variable(val):
                config[idx] = resolve_variable(val)
            elif isinstance(val, dict):
                config[idx] = parse_config(val, env_vars=env_vars, global_vars=global_vars)
    elif isinstance(config, dict):
        for key, val in config.items():
            if is_variable(val):
                config[key] = resolve_variable(val)
            elif isinstance(val, list):
                for sub_idx, sub_val in enumerate(val):
                    if is_variable(sub_val):
                        val[sub_idx] = resolve_variable(sub_val)
                    elif isinstance(sub_val, dict):
                        val[sub_idx] = parse_config(sub_val, env_vars=env_vars, global_vars=global_vars)
            elif isinstance(val, dict):
                config[key] = parse_config(
                    val, env_vars=env_vars, global_vars=global_vars)
                if key == '_var':
                    U.merge_dict(global_vars, config[key], union=True)

        nest_module_name = config.pop('_name', None)
        if nest_module_name:
            nest_module = module_manager[nest_module_name]
            if settings['PARSER_STRICT']:
                return nest_module(**config)
            else:
                return nest_module(**config, delay_resolve=True)

    return config


def run_tasks(
    config_file: str, 
    param_file: Optional[str] = None, 
    verbose: bool = False) -> None:
    """Run experiment tasks by resolving config.

    Parameters:
        config_file:
            The path to the config file
        param_file:
            The path to the parameter file
        verbose:
            Show verbose information
    """

    # helper function
    def check_all_resolved(resolved_config: Any) -> None:
        if isinstance(resolved_config, list):
            for v in resolved_config:
                check_all_resolved(v)
        elif isinstance(resolved_config, dict):
            for v in resolved_config.values():
                check_all_resolved(v)
        elif type(resolved_config).__name__ == 'NestModule':
            raise RuntimeError('Unresolved Nest module found in the result.\n%s' % (
                U.indent_text(str(resolved_config), 4)))

    # start resolving config
    try:
        start_time = datetime.now()
        # load config file
        config, raw = U.load_yaml(config_file)
        # load environment variables
        env_vars = {k: v for k, v in os.environ.items()}
        # record raw config
        env_vars['CONFIG'] = re.sub(r'\{(.*?)\}', r'{{\1}}', raw).replace('\\', '\\\\')
        env_vars['PARAMS'] = ''

        if param_file is not None:
            # initial global variables
            global_vars = dict()
            # iterate over params
            param_list, _ = U.load_yaml(param_file)
            if not isinstance(param_list, list):
                param_list = [param_list]
            for idx, param in enumerate(param_list):
                param_start_time = datetime.now()
                if isinstance(param, dict):
                    U.merge_dict(global_vars, param, union=True)        
                else:
                    raise TypeError('Parameter file should define a list of Dict[str, Any]. Got "%s" in it.' % param)
                # record parameters
                env_vars['PARAMS'] = U.yaml_format(global_vars)
                if verbose:
                    logger.info('(%d/%d) Resolving with parameters: \n' % (idx + 1, len(param_list)) + env_vars['PARAMS'])
                # parse config with updated vars
                resolved_config = parse_config(deepcopy(config), env_vars=env_vars, global_vars=global_vars)
                check_all_resolved(resolved_config)  
                if verbose:
                    end_time = datetime.now()
                    logger.info('Finished (%s).' % (U.format_elapse(seconds=(end_time - param_start_time).total_seconds())))
        else:
            resolved_config = parse_config(config, env_vars=env_vars)
            check_all_resolved(resolved_config)
        
        end_time = datetime.now()
        logger.info('All finished. (%s)' % U.format_elapse(seconds=(end_time - start_time).total_seconds()))

    except KeyboardInterrupt:
        logger.info('Processing is canceled by user.')
