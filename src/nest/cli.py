import os
import sys
import traceback
import logging
import argparse
from glob import glob
from shutil import rmtree
from typing import Any, Dict

from nest import utils as U
from nest.logger import logger
from nest.modules import module_manager
from nest.parser import run_tasks
from nest.settings import settings, SETTINGS_DIR, SETTINGS_FILE


ROOT_HELP = """Nest - A flexible tool for building and sharing deep learning modules
usage: nest <command> [<args>]

The currently available commands are
{}

"""

class Parser(argparse.ArgumentParser):
    """Custom parser for multi-level argparse.
    """

    def format_help(self) -> str:
        """Allow to use custom help.
        """

        if self.add_help:
            return super(Parser, self).format_help()
        else:
            return self.usage

    def error(self, message) -> None:
        """Show help when parse failed.
        """

        if self.add_help:
            logger.error('error: {}\n'.format(message))
        self.print_help()
        sys.exit(2)

    def add_argument(self, *args, **kwargs) -> None:
        """Hide metavar by default.
        """

        keys = kwargs.keys()
        if ('metavar' not in keys) and ('action' not in keys):
            kwargs['metavar'] = ''
        super(Parser, self).add_argument(*args, **kwargs)


class CLI(object):
    """Command line interface.
    """

    def __init__(self) -> None:
        # find available commands
        commands = [att for att in dir(self) if att.startswith('cmd_')][::-1]
        commands_help = '\n'.join(
            [getattr(self, cmd).__doc__.strip() for cmd in commands])
        # root parser
        parser = Parser(usage=ROOT_HELP.format(commands_help), add_help=False)
        parser.add_argument('command', choices=[cmd[4:] for cmd in commands])
        args = parser.parse_args(sys.argv[1:2])
        # dispatch
        getattr(self, 'cmd_' + args.command)('nest ' + args.command, sys.argv[2:])

    def hook_exceptions(self, logger: logging.RootLogger) -> None:
        """Format excetion traceback.
        
        Parameters:
            logger:
                The logger for logging exceptions.
        """

        def _hook(exc_type, value, exc_tb) -> None:
            nest_dir = os.path.dirname(os.path.abspath(__file__))
            traceback_str = ''
            idx = 0
            for file_name, line_number, func_name, text in traceback.extract_tb(exc_tb)[1:]:
                # skip Nest-related tracebacks to make it more readable
                if os.path.dirname(os.path.abspath(file_name)) == nest_dir:
                    continue
                idx += 1
                traceback_str += '\n  [%d] File "%s", line %d, in function "%s"\n    %s' % \
                    (idx, file_name, line_number, func_name, text)
            if traceback_str != '':
                traceback_str = 'Traceback: ' + traceback_str
            logger.critical('Exception occurred during resolving:\nType: %s\nMessage: %s\n%s' % \
                (exc_type.__name__, value, traceback_str))

        sys.excepthook = _hook

    def cmd_task(self, prog: str, arguments: str) -> None:
        """task           Task runner.
        """

        parser = Parser(prog=prog)
        subparsers = parser.add_subparsers(metavar="<command>", dest='command')

        # excute tasks
        parser_run = subparsers.add_parser('run', help='Execute tasks.')
        parser_run.add_argument('config', metavar='CONFIG', nargs='?', default='config.yml', 
            help='Path to the config file (default: config.yml).')
        parser_run.add_argument('-p', '--param', default=None,
            help='Path to the parameter file that can be used for hyper-params tuning.')
        parser_run.add_argument('-v', '--verbose', action='store_true', help='Show verbose information.')
        args = parser.parse_args(arguments)

        # exception formatter
        self.hook_exceptions(logger)

        if args.command == 'run':
            run_tasks(args.config, args.param, args.verbose)
        else:
            parser.print_help()

    def cmd_module(self, prog: str, arguments: str) -> None:
        """module         Nest module manager.
        """

        parser = Parser(prog=prog)
        subparsers = parser.add_subparsers(metavar="<command>", dest='command')

        # show modules
        parser_list = subparsers.add_parser('list', help='Show module information.')
        parser_list.add_argument('-f', '--filter', help='Keyword for filtering module list.')
        parser_list.add_argument('-v', '--verbose', action='store_true', help='Show verbose information.')
        # install modules
        parser_install = subparsers.add_parser('install', help='Install modules.')
        parser_install.add_argument('src', metavar='SRC', help='URL or path of the modules.')
        parser_install.add_argument('namespace', metavar='NAMESPACE', nargs='?', 
            help='The namespace for local path installation, use directory name if not specified.')
        parser_install.add_argument('-y', '--yes', action='store_true', help='Skip confirmation.')
        # remove modules
        parser_remove = subparsers.add_parser('remove', help='Remove modules.')
        parser_remove.add_argument('src', metavar='SRC', help='Namespace or path.')
        parser_remove.add_argument('-d', '--delete', action='store_true', help='Delete the namespace folder.')
        parser_remove.add_argument('-y', '--yes', action='store_true', help='Skip confirmation.')
        # pack modules
        parser_pack = subparsers.add_parser('pack', help='Pack modules.')
        parser_pack.add_argument('path', metavar='PATH', nargs='+', help='Path to namespaces.')
        parser_pack.add_argument('-s', '--save', default='./nest_modules.zip', help='Save path (default: ./nest_modules.zip).')
        parser_pack.add_argument('-y', '--yes', action='store_true', help='Skip confirmation.')
        # check modules
        parser_check = subparsers.add_parser('check', help='Check modules.')
        parser_check.add_argument('src', metavar='SRC', nargs='*',
            help='Path to the namespaces or python files (check all available modules if not specified).')
        args = parser.parse_args(arguments)
        
        if args.command == 'list':
            # list available Nest modules
            if args.verbose:
                module_info = ['%s (%s) by "%s":\n%s' % \
                (k, v.meta.get('version', 'version'), v.meta.get('author', 'author'), U.indent_text(str(v), 4)) for k, v in module_manager]
            else:
                module_info = ['%s (%s)' % (k, v.meta.get('version', 'version')) for k, v in module_manager]
            
            # filtering
            if args.filter:
                module_info = list(filter(lambda v: args.filter in v, module_info))
            module_info = ['[%d] ' % idx + v for idx, v in enumerate(sorted(module_info))]

            num_module = len(module_info)
            if num_module > 1:
                logger.info('%d Nest modules found.\n' % num_module + '\n'.join(module_info))
            elif num_module == 1:
                module_doc = U.indent_text(type(module_manager[module_info[0].split()[1]]).__doc__, 4)
                logger.info('1 Nest module found.\n' + module_info[0] + '\n\nDocumentation:\n' + module_doc)
            else:
                logger.info(
                    'No available Nest modules found. You can install build-in PyTorch modules by executing '
                    '"nest module install github@ZhouYanzhao/Nest:pytorch".')

        elif args.command == 'install':
            if os.path.isdir(args.src):
                # install Nest modules from path
                confirm = 'y' if args.yes else input('Install "%s" -> Search paths. Continue? (Y/n)' % (args.src,)).lower()
                if confirm == '' or confirm == 'y':
                    module_manager._install_namespaces_from_path(args.src, args.namespace)
            else:
                # install Nest modules from url
                confirm = 'y' if args.yes else input('Install "%s" --> "%s". Continue? (Y/n)' % (args.src, './')).lower()
                if confirm == '' or confirm == 'y':
                    module_manager._install_namespaces_from_url(args.src, args.namespace)

        elif args.command == 'remove':
            # remove Nest modules from paths
            confirm = 'y' if args.yes else input('Remove "%s" from paths. Continue? (Y/n)' % (args.src,)).lower()
            if confirm == '' or confirm == 'y':
                path = module_manager._remove_namespaces_from_path(args.src)
                if args.delete and path is not None and os.path.isdir(path):
                    del_confirm = 'y' if args.yes else input('Delete the namespace directory "%s". Continue? (Y/n)' % (path,)).lower()
                    if del_confirm == '' or del_confirm == 'y':
                        # error handler
                        def onerror(func, path, exc_info):
                            import stat
                            if not os.access(path, os.W_OK):
                                os.chmod(path, stat.S_IWUSR)
                                func(path)
                            else:
                                logger.warning('Failed to delete the namespace directory "%s".' % path)
                        rmtree(path, onerror=onerror)

        elif args.command == 'pack':
            # pack Nest modules to a zip file
            confirm = 'y' if args.yes else input('Pack "%s" --> "%s". Continue? (Y/n)' % (','.join(args.path), args.save)).lower()
            if confirm == '' or confirm == 'y':
                save_list = module_manager._pack_namespaces(args.path, args.save)
                logger.info('Packed list: \n%s', U.indent_text(U.yaml_format(save_list), 4))

        elif args.command == 'check':
            if len(args.src) == 0:
                logger.info('Checking all available modules')
                # check all
                module_manager._update_modules()
            else:
                for idx, path in enumerate(args.src):
                    logger.info('[%d/%d] Checking "%s"' % (idx + 1, len(args.src), path))
                    if os.path.isfile(path):
                        module_manager._import_nest_modules_from_file(path, 'nest_check', dict(), dict())
                    elif os.path.isdir(path):
                        module_manager._import_nest_modules_from_dir(path, 'nest_check', dict(), dict())
                    else:
                        logger.warning('Skipped as it does not exist.')
            logger.info('Done.')

        else:
            parser.print_help()

    def cmd_setting(self, prog: str, arguments: str) -> None:
        """setting        Settings configuration.
        """

        parser = Parser(prog=prog)
        subparsers = parser.add_subparsers(metavar="<command>", dest='command')
        
        # display settings
        parser_show = subparsers.add_parser('show', help='Show settings.')
        parser_show.add_argument('-d', '--directory', action='store_true', help='Locate setting file in directory.')
        parser_show.add_argument('-e', '--editor', action='store_true', help='Show settings in external editor.')
        # define settings
        parser_set = subparsers.add_parser('set', help='Modify settings.')
        parser_set.add_argument('key', metavar='KEY', help='The key.')
        parser_set.add_argument('val', metavar='VAL', help='The value (python expression).')
        args = parser.parse_args(arguments)

        # exception formatter
        self.hook_exceptions(logger)

        if args.command == 'show':
            import webbrowser
            if args.directory:
                webbrowser.open(SETTINGS_DIR)
            elif args.editor:
                webbrowser.open(SETTINGS_FILE)
            else:
                logger.info(U.yaml_format(settings.settings))
        elif args.command == 'set':
            if args.key in settings:
                settings[args.key] = eval(args.val)
                settings.save()
            else:
                raise KeyError('Invalid setting key "%s". Use "nest setting show" to check the supported settings.' % args.key)
        else:
            parser.print_help()
