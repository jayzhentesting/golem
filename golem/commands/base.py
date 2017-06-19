import os
from golem.core import test_runner, utils
from golem.gui import (gui_start, test_case,
                       suite as suite_module)


class BaseCommand:
    cmd = None

    def __init__(self, parser):
        sub_parser = parser.add_parser(self.cmd)
        self.add_arguments(sub_parser)

    def add_arguments(self, parser):
        pass

    def run(self, *args):
        raise NotImplementedError('Command not implemented')


class CommandException(Exception):
    pass


class RunCommand(BaseCommand):
    cmd = 'run'

    def add_arguments(self, parser):
        parser.add_argument('project', default='',
                            nargs='?', help="project name")
        parser.add_argument('test_or_suite', nargs='?',
                            default='', metavar='test case or suite',
                            help="test case or test suite to run")
        parser.add_argument('-t', '--threads', action='store',
                            nargs='?', default=0, type=int,
                            metavar='amount of threads for parallel execution',
                            help="amount of threads for parallel execution")
        parser.add_argument('-d', '--drivers', action='store',
                            nargs='*', choices=['firefox', 'chrome'],
                            type=str, metavar='Web Drivers',
                            help="Web Drivers")
        parser.add_argument('--timestamp', action='store', nargs='?', type=str,
                                metavar='Timestamp', help="Timestamp")

    def run(self, test_execution, args):
        test_execution.thread_amount = args.threads
        print('args.threads', args.threads)
        test_execution.drivers = args.drivers
        test_execution.timestamp = args.timestamp

        root_path = test_execution.root_path

        if not args.project:
            msg = ['Usage:', parser.usage, '\n\n', 'Project List:']
            for proj in utils.get_projects(root_path):
                msg.append('> {}'.format(proj))
            raise CommandException('\n'.join(msg))
        elif not args.project in utils.get_projects(root_path):
            raise CommandException(
                'Error: the project {0} does not exist'.format(
                    test_execution.project)
            )
        else:
            test_execution.project = args.project
            test_execution.settings = utils.get_project_settings(
                args.project,
                test_execution.settings)
            # check if test_or_suite value is present
            if not args.test_or_suite:
                msg = ['Usage: {}'.format(parser.usage),
                       'Test Cases:']
                test_cases = utils.get_test_cases(root_path,
                                                  test_execution.project)
                # TODO FIX TO SHOW THIS ON Exception
                utils.display_tree_structure_command_line(test_cases)
                msg.append('Test Suites:')
                test_suites = utils.get_suites(root_path, test_execution.project)
                for suite in test_suites:
                    msg.append('> ' + suite)
                raise CommandException(msg)
            # check if test_or_suite value matches an existing test suite
            elif utils.test_suite_exists(root_path, test_execution.project,
                                         args.test_or_suite):
                test_execution.suite = args.test_or_suite
                # execute test suite
                test_runner.run_suite(root_path,
                                      test_execution.project,
                                      test_execution.suite)

            # check if test_or_suite value matches a first level directory
            # in the test cases directory. this allows to execute all the
            # test cases in a directory as a test suite
            elif utils.is_first_level_directory(root_path,
                                                test_execution.project,
                                                args.test_or_suite):
                test_execution.suite = args.test_or_suite
                # execute test suite
                test_runner.run_suite(root_path,
                                      test_execution.project,
                                      test_execution.suite,
                                      is_directory=True)
            # check if test_or_suite value matches an existing test case
            elif utils.test_case_exists(root_path, test_execution.project,
                                        args.test_or_suite):
                test_execution.test = args.test_or_suite
                # execute test case
                test_runner.run_single_test_case(root_path,
                                                 test_execution.project,
                                                 test_execution.test)
            else:
                # test_or_suite does not match any existing suite or test
                raise CommandException(
                    'Error: the value {0} does not match an existing '
                    'suite or test'.format(args.test_or_suite))


class GuiCommand(BaseCommand):
    cmd = 'gui'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--port', action='store',
                            nargs='?', default=5000, type=int,
                            metavar='port number',
                            help="port number to use for Golem GUI")
        parser.add_argument('-d', '--debug', action='store_true',
                            default=False,
                            help="Start the gui application in debug mode")

    def run(self, test_execution, args):
        port_number = args.port
        debug = args.debug
        gui_start.run_gui(port_number, debug)


class CreateProjectCommand(BaseCommand):
    cmd = 'createproject'

    def add_arguments(self, parser):
        parser.add_argument('project', help="project name")

    def run(self, test_execution, args):
        root_path = test_execution.root_path

        if args.project in utils.get_projects(root_path):
            msg = 'Error: a project with the name \'{}\' already exists'.format(
                args.project
            )
            raise CommandException(msg)
        elif args.project == 'demo':
            utils.create_demo_project(root_path)
        else:
            utils.create_new_project(root_path, args.project)


class CreateTestCommand(BaseCommand):
    cmd = 'createtest'

    def add_arguments(self, parser):
        parser.add_argument('project', help="project name")
        parser.add_argument('test', metavar='test case name',
                            help="test case name")

    def run(self, test_execution, args):
        root_path = test_execution.root_path

        if args.project not in utils.get_projects(root_path):
            raise CommandException(
                'Error: a project with that name does not exist'
            )
        split_path = args.test.split('.')
        test_name = split_path.pop()
        errors = test_case.new_test_case(root_path, args.project,
                                         split_path, test_name)
        if errors:
            raise CommandException('\n'.join(errors))


class CreateSuiteCommand(BaseCommand):
    cmd = 'createsuite'

    def add_arguments(self, parser):
        parser.add_argument('project', help="project name")
        parser.add_argument('suite', metavar='suite name', help="suite name")

    def run(self, test_execution, args):
        if args.project not in utils.get_projects(
                test_execution.root_path):
            raise CommandException(
                'Error: a project with that name does not exist')
        errors = suite_module.new_suite(root_path, args.project, args.suite)
        if errors:
            raise CommandException('\n'.join(errors))


class CreateUserCommand(BaseCommand):
    cmd = 'createuser'

    def add_arguments(self, parser):
        parser.add_argument('username', help="username")
        parser.add_argument('password', help="suite name")
        parser.add_argument('-a', '--admin', action='store_true', default=False,
                            help="is admin")
        parser.add_argument('-p', '--projects', nargs='+', default=[],
                            help="projects the user has access")
        parser.add_argument('-r', '--reports', nargs='+', default=[],
                            help="reports the user has access")

    def run(self, test_execution, args):
        errors = utils.create_user(root_path, args.username,
                                   args.password, args.admin,
                                   args.projects, args.reports)
        if errors:
            raise CommandException('\n'.join(errors))
        else:
            print('User {} was created successfully'.format(args.username))


class CreateDirAdminCommand(BaseCommand):
    cmd = 'createdirectory'

    def add_arguments(self, parser):
        parser.add_argument('name', metavar='name',
                            help='directory name')

    def run(self, args):
        # Generate a new 'golem' directory
        dir_name = args.name

        if os.path.exists(dir_name):
            raise CommandException(
                'Error: the directory {} already exists'.format(dir_name)
            )

        destination = os.path.join(os.getcwd(), dir_name)
        utils.create_test_dir(destination)
