'''opencos.commands.sim - Base class command handler for: eda sim ...

Intended to be overriden by Tool based classes (such as CommandSimVivado, etc)

Note that CommandSim is also a base class for opencos.commands.elab.CommandElab.'''

# Note - similar code waiver, tricky to eliminate it with inheritance when
# calling reusable methods.
# pylint: disable=R0801

# TODO(drew): clean up CommandSim.check_logs_for_errors and CommandSim.run_commands_check_logs
# pylint: disable=too-many-arguments,too-many-positional-arguments

import os

from opencos import util, export_helper
from opencos.eda_base import CommandDesign, Tool
from opencos.utils import status_constants

from opencos.utils.str_helpers import sanitize_defines_for_sh, strip_outer_quotes

def parameters_dict_get_command_list(params: dict, arg_prefix: str = '-G') -> list:
    '''Given dict of parameters, returns a command list'''

    ret_list = []
    if ' ' in arg_prefix:
        arg_list_prefix = arg_prefix.split()
        arg_str_prefix = ''
    else:
        arg_list_prefix = []
        arg_str_prefix = arg_prefix

    for k,v in params.items():
        if not isinstance(v, (int, str)):
            util.warning(f'parameter {k} has value: {v}, parameters must be int/string types')

        ret_list.extend(arg_list_prefix)
        if isinstance(v, int):
            ret_list.append(f'{arg_str_prefix}{k}={v}')
        else: # string
            v = strip_outer_quotes(v.strip('\n'))
            v = '"' + v + '"'
            ret_list.append(f'{arg_str_prefix}{k}={sanitize_defines_for_sh(v)}')
    return ret_list


class CommandSim(CommandDesign):
    '''Base class command handler for: eda sim ...'''

    CHECK_REQUIRES = [Tool] # Used by check_command_handler_cls()
    error_on_no_files_or_targets = True
    error_on_missing_top = True
    tool_config = {} # Children with Tool parent classes will set on Tool constructor.

    command_name = 'sim'

    def __init__(self, config: dict):
        CommandDesign.__init__(self, config=config)
        self.args.update({
            "pre-sim-tcl": [],
            'compile-args': [],
            'elab-args': [],
            'sim-args': [],
            'sim-plusargs': [], # lists are handled by 'set_arg(k,v)' so they append.
            'sim-library': [],
            'compile-waivers': [],
            'sim-waivers': [],
            'coverage': False,
            'waves': False,
            'waves-start': 0,
            'pass-pattern': "",
            'optimize': False,
            'log-bad-strings': ['ERROR: ', 'FATAL: ', 'Error: ', 'Fatal: '],
            'log-must-strings': [],
            # verilate-args: list of args you can only pass to Verilator,
            # not used by other simulators, so these can go in DEPS files for custom things
            # like -CFLAGS -O0, etc.
            'verilate-args': [],
        })
        self.args_help.update({
            'compile-args': 'args added to sim/elab "compile" step',
            'coverage': 'attempt to run coverage steps on the compile/elab/simulation',
            'elab-args':    'args added to sim/elab "elaboration" step, if required by tool',
            'log-bad-strings': 'strings that if present in the log will fail the simulation',
            'log-must-strings': ('strings that are required by the log to not-fail the simulation.'
                                 ' Some tools use these at only certain phases'
                                 ' (compile/elab/sim).'),
            'pass-pattern': ('Additional string required to pass a simulation, appends to'
                             ' log-must-strings'),
            'sim-args':      'args added to final "simulation" step',
            'sim-plusargs':  ('"simulation" step run-time args passed to tool, these can also'
                              ' be set using --sim-plusargs=name[=value], or simply +name[=value]'),
            'stop-before-compile': ('Create work-dir sh scripts for compile/elab/simulate, but do'
                                    ' not run them.'),
            'stop-after-compile': 'Create work-dir sh scripts, but only run the compile step.',
            'stop-after-elaborate': ('Create work-dir sh scripts, but run compile+elab, skip'
                                     ' simulation step.'),
            'top': 'Name of topmost Verilog/SystemVerilog module, or VHDL entity',
            'verilate-args': ('args added to "compile" step in Verilator simulation'
                              ' (for --tool=verilator)'),
            'waves': 'Include waveforms, if possible for tool',
            'waves-start': 'Starting time of waveform capture, if possible for tool',
            'work-dir': 'Optional override for working directory, defaults to ./eda.work/<top>.sim',
            'test-mode': ('stops the command early without executing, if --gui is present will'
                          ' instead test without spawning gui')

        })


        self.args['verilate-args'] = []

    def process_parameters_get_list(self, arg_prefix: str = '-G') -> list:
        '''Returns list (suitable command list for shell or for tool) from self.parameters'''
        return parameters_dict_get_command_list(params=self.parameters, arg_prefix=arg_prefix)

    def process_plusarg(self, plusarg: str, pwd: str = os.getcwd()) -> None:
        '''Override for CommandDesign.process_plusarg(..)'''
        maybe_plusarg = CommandDesign.process_plusarg(self, plusarg, pwd)
        # Support for self.args['unprocessed-plusargs'] --> self.args['sim-plusargs']:
        if maybe_plusarg and \
           maybe_plusarg in self.args['unprocessed-plusargs'] and \
           maybe_plusarg not in self.args['sim-plusargs']:
            self.args['sim-plusargs'].append(maybe_plusarg)
            self.args['unprocessed-plusargs'].remove(maybe_plusarg)
            util.debug(f'For parent "sim" command (CommandSim), moved plusarg: {maybe_plusarg}',
                       'to sim-plusargs (from unprocessed-plusargs)')

    def process_tokens(self, tokens: list, process_all: bool = True,
                       pwd: str = os.getcwd()) -> list:
        self.defines['SIMULATION'] = None
        unparsed = CommandDesign.process_tokens(
            self, tokens=tokens, process_all=process_all, pwd=pwd
        )

        if self.stop_process_tokens_before_do_it():
            return unparsed

        # add defines for this job type
        if self.args['lint'] or self.args['stop-after-elaborate']:
            self.args['lint'] = True
            self.args['stop-after-elaborate'] = True
        if self.args['top']:
            # create our work dir
            self.create_work_dir()
            self.run_dep_commands()
            self.do_it()
            self.run_post_tool_dep_commands()
        return unparsed


    def set_tool_config_from_config(self) -> None:
        '''Sets self.tool_config (from original --config-yml=YAML|Default) and overrides
        self.defines, and self.args log-must-strings and log-bad-strings.'''
        tool = self.args.get('tool', '') # get from Command's self.args['tool']
        if tool:
            self.tool_config = self.config.get('tools', {}).get(tool, {})
            self.override_log_strings_from_tool_config()
            self.defines.update(self.tool_config.get('defines', {}))
            util.debug(f'set_tool_config_from_config: {tool=}')

    def update_tool_config(self):
        self.override_log_strings_from_tool_config()


    def override_log_strings_from_tool_config(self) -> None:
        '''Returns None, overrides memvers of self.args based on our tool_config

        (tool_config from eda.py --config-yml=YAML-CONFIG-FILE)
        '''
        if not getattr(self, 'tool_config', None):
            return

        # Collect (overwrite CommandSim) the bad and must strings, if present,
        # from our config.tools.verilator:
        for tool_config_key in ['log-bad-strings', 'log-must-strings']:
            if len(self.tool_config.get(tool_config_key, [])) > 0:
                self.args[tool_config_key] = self.tool_config.get(tool_config_key, [])


    # Methods that derived classes may override:

    def run_commands_check_logs( # pylint: disable=dangerous-default-value
            self, commands: list , check_logs: bool = True, log_filename=None,
            bad_strings: list = [],
            must_strings: list = [],
            use_bad_strings: bool = True, use_must_strings: bool = True
    ) -> None:
        '''Returns None, runs all commands (each element is a list) and checks logs

        for bad-strings and must-strings (args or class member vars)
        '''

        for obj in commands:

            assert isinstance(obj, list), \
                (f'{self.target=} command {obj=} is not a list or util.ShellCommandList,'
                 ' not going to run it.')

            clist = list(obj).copy()
            tee_fpath = getattr(obj, 'tee_fpath', None)

            util.debug(f'run_commands_check_logs: {clist=}, {tee_fpath=}')

            log_fname = None
            if tee_fpath:
                log_fname = tee_fpath
            if log_filename:
                log_fname = log_filename

            _, stdout, _ = self.exec(
                work_dir=self.args['work-dir'], command_list=clist, tee_fpath=tee_fpath
            )

            if check_logs and log_fname:
                # Note this call will check on stdout if not GUI, not opening the log_fname,
                # but if this is GUI we normally lose stdout and have to open the log.
                gui_mode = self.args.get('gui', False)
                file_contents_str = '' if gui_mode else stdout
                self.check_logs_for_errors(
                    filename=os.path.join(self.args['work-dir'], log_fname),
                    file_contents_str=file_contents_str,
                    bad_strings=bad_strings, must_strings=must_strings,
                    use_bad_strings=use_bad_strings, use_must_strings=use_must_strings
                )
            if log_fname:
                self.artifacts_add(
                    name=os.path.join(self.args['work-dir'], log_fname),
                    typ='text', description='Simulator stdout/stderr log file'
                )

    def do_export(self) -> None:
        '''CommandSim helper for handling args --export*

        We allow commands such as: eda sim --export <target>
        '''

        out_dir = os.path.join(self.args['work-dir'], 'export')

        target = self.target
        if not target:
            target = 'test'

        export_obj = export_helper.ExportHelper(
            cmd_design_obj=self,
            eda_command=self.command_name,
            out_dir=out_dir,
            # Note this may not be the correct target for debug infomation,
            # so we'll only have the first one.
            target=target
        )

        # Set things in the exported: DEPS.yml
        tool = self.args.get('tool', None)
        # Certain args are allow-listed here
        deps_file_args = []
        for a in self.get_command_line_args():
            if any(a.startswith(x) for x in [
                    '--compile-args',
                    '--elab-args',
                    '--sim-',
                    '--coverage',
                    '--waves',
                    '--pass-pattern',
                    '--optimize',
                    '--stop-',
                    '--lint-',
                    '--verilate',
                    '--verilator']):
                deps_file_args.append(a)

        export_obj.run(
            deps_file_args=deps_file_args,
            export_json_eda_config={
                'tool': tool,
            }
        )

        if self.args['export-run']:

            # remove the '--export' named args, we don't want those.
            args_no_export = self.get_command_line_args(remove_args_startswith=['export'])

            command_list = ['eda', self.command_name] + args_no_export + [target]

            util.info(f'export-run: from {export_obj.out_dir=}: {command_list=}')
            self.exec(
                work_dir=export_obj.out_dir,
                command_list=command_list,
            )


    def do_it(self) -> None:
        self.prepare_compile()
        self.write_eda_config_and_args()

        if self.is_export_enabled():
            # If we're exporting the target, we do NOT run the test here
            # (do_export() may run the test in a separate process and
            # from the out_dir if --export-run was set)
            self.do_export()
            return

        self.compile()
        self.elaborate()
        self.simulate()

    # Methods that derived classes may override:

    def prepare_compile(self):
        '''Derived classes may override if they want to create .sh scripts in the work-dir.

        Common use-case is to call:
            self.set_tool_defines()
            cmds0 = self.get_compile_command_lists()
            cmds1 = self.get_elaborate_command_lists()
            cmds2 = self.get_simulate_command_lists()
            cmds3 = self.get_post_simulate_command_lists()
        '''
        return

    def check_logs_for_errors( # pylint: disable=dangerous-default-value,too-many-locals,too-many-branches
            self, filename: str = '', file_contents_str: str = '',
            bad_strings: list = [], must_strings: list = [],
            use_bad_strings: bool = True, use_must_strings: bool = True
    ) -> None:
        '''Returns None, checks logs using args bad_strings, must_strings,

        and internals self.args["log-[bad|must]-strings"] (lists).

        file_contents_str will take precedence over opening filename, but filename is still
        used in messaging.
        '''

        _bad_strings = bad_strings
        _must_strings = must_strings
        # append, if not they would 'replace' the args values:
        if use_bad_strings:
            _bad_strings = bad_strings + self.args.get('log-bad-strings', [])
        if use_must_strings:
            _must_strings = must_strings + self.args.get('log-must-strings', [])

        if self.args['pass-pattern'] != "":
            _must_strings.append(self.args['pass-pattern'])

        if len(_bad_strings) == 0 and len(_must_strings) == 0:
            return

        hit_must_string_dict = dict.fromkeys(_must_strings)

        lines = []

        log_fpath = ''
        if os.path.exists(filename):
            log_fpath = filename

        if file_contents_str:
            lines = file_contents_str.split('\n')
            log_fname = log_fpath + '(STDOUT)'
            util.debug(f'Checking log for errors: {log_fpath=} but checking from STDOUT string...')
        elif filename:
            log_fname = log_fpath
            util.debug(f'Checking log for errors: {log_fpath=} opening file...')
            if not os.path.exists(log_fname):
                self.error(f'sim.check_logs_for_errors: log {log_fpath} does not exist, cannot',
                           'check it for errors or passing strings')
                return
            with open(log_fpath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
        else:
            self.error(f'sim.check_logs_for_errors: {log_fpath=} does not exist, and no',
                       'file_contents_str exists to check')

        if lines:
            for lineno, line in enumerate(lines):
                if any(must_str in line for must_str in _must_strings):
                    for k, _ in hit_must_string_dict.items():
                        if k in line:
                            hit_must_string_dict[k] = True
                if any(bad_str in line for bad_str in _bad_strings):
                    self.error(
                        f"log {log_fname}:{lineno} contains one of {_bad_strings=}",
                        error_code=status_constants.EDA_SIM_LOG_HAS_BAD_STRING
                    )

        if any(x is None for x in hit_must_string_dict.values()):
            self.error(
                f"Didn't get all passing patterns in log {log_fname}: {_must_strings=}",
                f" {hit_must_string_dict=}",
                error_code=status_constants.EDA_SIM_LOG_MISSING_MUST_STRING
            )

    def write_sh_scripts_to_work_dir(
            self, compile_lists: list, elaborate_lists: list, simulate_lists: list,
            compile_line_breaks: bool = True,
            elaborate_line_breaks: bool = False,
            simulate_line_breaks: bool = False,
            simulate_sh_fname: str = 'simulate.sh'
    ) -> None:
        '''Writes compile.sh, elaborate.sh, simulate.sh (if present), all.sh to work-dir

        Will include the pre_compile_dep_shell_commands.sh if those are present.
        compile_line_breaks defaults to True (one word per line w/ line breaks added)
        '''

        all_lists = [] # list - of - (command-list)
        if self.has_pre_compile_dep_shell_commands:
            all_lists = [
                ['./pre_compile_dep_shell_commands.sh']
            ]

        if compile_lists:
            util.write_shell_command_file(dirpath=self.args['work-dir'], filename='compile.sh',
                                          command_lists=compile_lists,
                                          line_breaks=compile_line_breaks)
            all_lists.append(['./compile.sh'])

        if elaborate_lists:
            util.write_shell_command_file(dirpath=self.args['work-dir'], filename='elaborate.sh',
                                          command_lists=elaborate_lists,
                                          line_breaks=elaborate_line_breaks)
            all_lists.append(['./elaborate.sh'])

        if simulate_lists:
            util.write_shell_command_file(dirpath=self.args['work-dir'], filename=simulate_sh_fname,
                                          command_lists=simulate_lists,
                                          line_breaks=simulate_line_breaks)
            all_lists.append(['./' + simulate_sh_fname])

        if self.has_post_tool_dep_shell_commands:
            all_lists = [
                ['./post_tool_dep_shell_commands.sh']
            ]

        util.write_shell_command_file(dirpath=self.args['work-dir'], filename='all.sh',
                                      command_lists=all_lists)

        self.write_eda_config_and_args()



    # Methods that derived classes must override:

    def compile(self) -> None:
        '''compile() runs as part of the CommandSim.do_it() flow'''
        raise NotImplementedError

    def elaborate(self) -> None:
        '''elaborate() runs as part of the CommandSim.do_it() flow, after compile()'''
        raise NotImplementedError

    def simulate(self) -> None:
        '''simulate() runs as part of the CommandSim.do_it() flow, after elaborate()'''
        raise NotImplementedError

    def get_compile_command_lists(self, **kwargs) -> list:
        ''' Returns a list of lists (list of command lists).'''
        raise NotImplementedError

    def get_elaborate_command_lists(self, **kwargs) -> list:
        ''' Returns a list of lists (list of command lists).'''
        raise NotImplementedError

    def get_simulate_command_lists(self, **kwargs) -> list:
        ''' Returns a list of lists (list of command lists).'''
        raise NotImplementedError

    def get_post_simulate_command_lists(self, **kwargs) -> list:
        ''' Returns a list of lists (list of command lists).'''
        raise NotImplementedError

    def add_waves_pkg_file(self) -> None:
        '''If --waves is present, and one of --waves-fst or --waves-vcd or --dump-vcd, and

        the user is missing any $dumpfile(), then adds a pre-written
        SystemVerilog package to their source code. Note that individual tools have
        to call this prior to their compile step, CommandSim does not run this method for
        you.
        '''
        if not self.args['waves']:
            return
        if not any(self.args.get(x, False) for x in ('waves-fst', 'waves-vcd', 'dump-vcd')):
            return
        found_dumpfile = False
        for fname in self.files_v + self.files_sv:
            if found_dumpfile:
                break
            with open(fname, encoding='utf-8') as f:
                for line in f.readlines():
                    if '$dumpfile' in line:
                        found_dumpfile = True
                        break

        if not found_dumpfile:
            thispath = os.path.dirname(__file__)
            file_to_add = os.path.join(thispath, '..', '_waves_pkg.sv')
            util.info(f'--waves arg present, no $dumpfile found, adding SV file: {file_to_add}')
            self.add_file(file_to_add)

        # register .vcd or .fst artifacts:
        util.artifacts.add_extension(
            search_paths=self.args['work-dir'], file_extension='fst',
            typ='waveform', description='Simulation Waveform FST (Fast Signal Trace) file'
        )
        util.artifacts.add_extension(
            search_paths=self.args['work-dir'], file_extension='vcd',
            typ='waveform', description='Simulation Waveform VCD (Value Change Dump) file'
        )
