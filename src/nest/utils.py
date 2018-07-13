import os
import sys
import string
import inspect
import collections
import warnings
from typing import List, Set, Dict, Tuple, Callable, Any, Union, Iterable, Iterator

import yaml
from dateutil.relativedelta import relativedelta

from nest.logger import exception
from nest.settings import settings


# helper functions
def yaml_format(obj: object) -> str:
    """Format dict using YAML.
    
    Parameters:
        obj:
            The input dict object

    Returns:
        formated string
    """

    return yaml.dump(obj, default_flow_style=False)


def format_elapse(**elapse) -> str:
    """Format an elapse to human readable string.

    Parameters:
        elapse:
            The elapse dict, e.g., dict(seconds=10)
    
    Returns:
        Human readable string
    """

    attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
    elapse = relativedelta(**elapse)
    return ', '.join(['%d %s' % (getattr(elapse, attr), getattr(elapse, attr) > 1 and attr or attr[:-1]) for attr in attrs if getattr(elapse, attr)])


def load_yaml(path: str) -> Tuple[dict, str]:
    """Load yaml file.

    Parameters:
        path:
            The path to the file

    Returns:
        The dict
        Raw string
    """

    with open(path, 'r') as f:
        raw = ''.join(f.readlines())
        return yaml.load(raw), raw


def indent_text(text: str, indent: int) -> str:
    """Indent multi-line text.

    Parameters:
        text:
            The input text
        indent:
            Number of spaces
    """

    return '\n'.join([' ' * indent + v for v in text.split('\n')])


def encode_id(namespace: str, key: str) -> str:
    """Encode unique id from namespace and key.

    Parameters:
        namespace:
            The given namespace
        key:
            The given key

    Returns:
        a unique id
    """

    if settings['NAMESPACE_ORDER_REVERSE']:
        return key + settings['NAMESPACE_SEP'] + namespace
    else:
        return namespace + settings['NAMESPACE_SEP'] + key


def decode_id(unique_id: str) -> Tuple[str, str]:
    """Decode unique id to namespace and key.

    Parameters:
        unique_id:
            The given unique id

    Returns:
        namespace and key
    """

    if settings['NAMESPACE_ORDER_REVERSE']:
        return unique_id.split(settings['NAMESPACE_SEP'])[::-1]
    else:
        return unique_id.split(settings['NAMESPACE_SEP'])


@exception
def alert_msg(msg: str) -> None:
    """Show alert message.

    Parameters:
        msg:
            The message
    """

    if settings['RAISES_ERROR']:
        raise RuntimeError(msg)
    else:
        warnings.warn(msg)


def merge_dict(
    src: dict, 
    diff: dict, 
    union: bool = False, 
    _path: List[str] = None) -> dict:
    """Recursively merges two dicts.

    Parameters:
        src: 
            The source dict (will be modified)
        diff: 
            Differences to be merged
        union: 
            Whether to keep all keys
        _path: 
            The internal falg that should not be used by the user
    
    Returns:
        The merged dict
    """

    if _path is None:
        _path = []
    for key in diff:
        if key in src:
            if isinstance(src[key], dict) and isinstance(diff[key], dict):
                merge_dict(src[key], diff[key], _path+[str(key)])
            else:
                src[key] = diff[key]
        elif union:
            src[key] = diff[key]
    return src


@exception
def is_annotation_matched(var: object, annotation: object) -> bool:
    """Return True if annotation is matched with the given variable.
    {Any, List, Set, Tuple, Dict, Union, Callable, Iterable, Iterator} from "typing" are supported. 
    
    Parameters:
        var: 
            The variable
        annotation:
            The annotation
    
    Returns:
        True if matched, otherwise False.
    """

    var_type = type(var)
    anno_str = str(annotation).split('[')[0]

    if var is None and annotation is None:
        return True
    elif type(annotation) == type:
        return issubclass(var_type, annotation)
    elif anno_str.startswith('typing.'):
        anno_type = anno_str[7:]
        if anno_type == 'Any':
            return True
        elif anno_type == 'List':
            sub_annotation = annotation.__args__
            if var_type == list:
                if sub_annotation is None:
                    return True
                else:
                    return all(map(lambda x: is_annotation_matched(x, sub_annotation[0]), var))
            else:
                return False
        elif anno_type == 'Set':
            sub_annotation = annotation.__args__
            if var_type == set:
                if sub_annotation is None:
                    return True
                else:
                    return all(map(lambda x: is_annotation_matched(x, sub_annotation[0]), var))
            else:
                return False
        elif anno_type == 'Iterable':
            # currently we can't check the type of items
            return issubclass(var_type, collections.abc.Iterable)
        elif anno_type == 'Iterator':
            # currently we can't check the type of items
            return issubclass(var_type, collections.abc.Iterator)
        elif anno_type == 'Tuple':
            sub_annotation = annotation.__args__
            if var_type == tuple:
                if sub_annotation is None:
                    return True
                if len(sub_annotation) != len(var):
                    return False
                else:
                    return all(map(lambda x, y: is_annotation_matched(x, y), var, sub_annotation))
            else:
                return False
        elif anno_type == 'Dict':
            sub_annotation = annotation.__args__
            if var_type == dict:
                if sub_annotation is None:
                    return True
                else:
                    key_anno, val_anno = sub_annotation
                    return all(map(
                        lambda x: is_annotation_matched(x[0], key_anno) and \
                            is_annotation_matched(x[1], val_anno), var.items()))
            else:
                return False
        elif anno_type == 'Union':
            sub_annotation = annotation.__args__
            if sub_annotation is None:
                return False
            else:
                return any(map(lambda y: is_annotation_matched(var, y), sub_annotation))
        elif anno_type == 'Callable':
            sub_annotation = annotation.__args__
            if callable(var):
                if sub_annotation is None:
                    return True
                else:
                    if type(var).__name__ == 'NestModule':
                        # Nest module
                        # filter out resolved / optional params
                        sig = var.sig
                        func_annos = [v.annotation for k, v in sig.parameters.items() \
                            if not k in var.params.keys() and v.default is inspect.Parameter.empty]
                    else:
                        # regular callable object
                        sig = inspect.signature(var)
                        func_annos = [v.annotation for v in sig.parameters.values()]
                    if len(func_annos) == len(sub_annotation) - 1:
                        return all(map(lambda x, y: x == y, func_annos, sub_annotation)) and \
                            (sub_annotation[-1] == Any or \
                            sub_annotation[-1] == object or \
                            sig.return_annotation == sub_annotation[-1] or
                            (sig.return_annotation is None and sub_annotation[-1] == type(None)))
                    else:
                        return False
            else:
                return False

    raise NotImplementedError('The annotation type %s is not supported' % inspect.formatannotation(annotation))
