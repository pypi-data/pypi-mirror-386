import ast
try:
    from ast import unparse as ast_unparse
except ImportError:
    import astor
    ast_unparse = astor.to_source

import builtins
import json
import keyword
import re
import uuid
from datetime import datetime
from typing import Dict

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import JSONType

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    # id = db.Column(db.Integer)
    username = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    # email = db.Column(db.String)
    hashPassword = db.Column(db.String(255))

    # password = db.Column()
    def __init__(self, username, password):
        # self.id = id
        self.username = username
        # self.email = email
        self.hashPassword = password

    def get_id(self):
        return self.username


class Script(db.Model):
    __tablename__ = 'script'
    # id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), primary_key=True, unique=True)
    deck = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    script_dict = db.Column(JSONType, nullable=True)
    time_created = db.Column(db.String(50), nullable=True)
    last_modified = db.Column(db.String(50), nullable=True)
    id_order = db.Column(JSONType, nullable=True)
    editing_type = db.Column(db.String(50), nullable=True)
    author = db.Column(db.String(50), nullable=False)
    # registered = db.Column(db.Boolean, nullable=True, default=False)

    def __init__(self, name=None, deck=None, status=None, script_dict: dict = None, id_order: dict = None,
                 time_created=None, last_modified=None, editing_type=None, author: str = None,
                 # registered:bool=False,
                 python_script: str = None
                 ):
        if script_dict is None:
            script_dict = {"prep": [], "script": [], "cleanup": []}
        elif type(script_dict) is not dict:
            script_dict = json.loads(script_dict)
        if id_order is None:
            id_order = {"prep": [], "script": [], "cleanup": []}
        elif type(id_order) is not dict:
            id_order = json.loads(id_order)
        if status is None:
            status = 'editing'
        if time_created is None:
            time_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if last_modified is None:
            last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if editing_type is None:
            editing_type = "script"

        self.name = name
        self.deck = deck
        self.status = status
        self.script_dict = script_dict
        self.time_created = time_created
        self.last_modified = last_modified
        self.id_order = id_order
        self.editing_type = editing_type
        self.author = author
        self.python_script = python_script
        # self.r = registered

    def as_dict(self):
        dict = self.__dict__
        dict.pop('_sa_instance_state', None)
        return dict

    def get(self):
        workflows = db.session.query(Script).all()
        # result = script_schema.dump(workflows)
        return workflows

    def find_by_uuid(self, uuid):
        for stype in self.script_dict:
            for action in self.script_dict[stype]:

                if action['uuid'] == int(uuid):
                    return action

    def _convert_type(self, args, arg_types):
        if arg_types in ["list", "tuple", "set"]:
            try:
                args = ast.literal_eval(args)
                return args
            except Exception:
                pass
        if type(arg_types) is not list:
            arg_types = [arg_types]
        for arg_type in arg_types:
            try:
                # print(arg_type)
                args = eval(f"{arg_type}('{args}')")
                return
            except Exception:

                pass
        raise TypeError(f"Input type error: cannot convert '{args}' to {arg_type}.")

    def update_by_uuid(self, uuid, args, output):
        action = self.find_by_uuid(uuid)
        if not action:
            return
        arg_types = action['arg_types']
        if type(action['args']) is dict:
            # pass
            self.eval_list(args, arg_types)
        else:
            pass
        action['args'] = args
        action['return'] = output

    @staticmethod
    def eval_list(args, arg_types):
        for arg in args:
            arg_type = arg_types[arg]
            if arg_type in ["list", "tuple", "set"]:

                if type(arg) is str and not args[arg].startswith("#"):
                    # arg_types = arg_types[arg]
                    # if arg_types in ["list", "tuple", "set"]:
                    convert_type = getattr(builtins, arg_type)  # Handle unknown types s
                    try:
                        output = ast.literal_eval(args[arg])
                        if type(output) not in [list, tuple, set]:
                            output = [output]
                        args[arg] = convert_type(output)
                        # return args
                    except ValueError:
                        _list = ''.join(args[arg]).split(',')
                        # convert_type = getattr(builtins, arg_types)  # Handle unknown types s
                        args[arg] = convert_type([s.strip() for s in _list])

    @property
    def stypes(self):
        return list(self.script_dict.keys())

    @property
    def currently_editing_script(self):
        return self.script_dict[self.editing_type]

    @currently_editing_script.setter
    def currently_editing_script(self, script):
        self.script_dict[self.editing_type] = script

    @property
    def currently_editing_order(self):
        return self.id_order[self.editing_type]

    @currently_editing_order.setter
    def currently_editing_order(self, script):
        self.id_order[self.editing_type] = script

    def update_time_stamp(self):
        self.last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_script(self, stype: str):
        return self.script_dict[stype]

    def isEmpty(self) -> bool:
        if not (self.script_dict['script'] or self.script_dict['prep'] or self.script_dict['cleanup']):
            return True
        return False

    def _sort(self, script_type):
        if len(self.id_order[script_type]) > 0:
            for action in self.script_dict[script_type]:
                for i in range(len(self.id_order[script_type])):
                    if action['id'] == int(self.id_order[script_type][i]):
                        # print(i+1)
                        action['id'] = i + 1
                        break
            self.id_order[script_type].sort()
            if not int(self.id_order[script_type][-1]) == len(self.script_dict[script_type]):
                new_order = list(range(1, len(self.script_dict[script_type]) + 1))
                self.id_order[script_type] = [str(i) for i in new_order]
            self.script_dict[script_type].sort(key=lambda x: x['id'])

    def sort_actions(self, script_type=None):
        if script_type:
            self._sort(script_type)
        else:
            for i in self.stypes:
                self._sort(i)

    def add_action(self, action: dict, insert_position=None):
        current_len = len(self.currently_editing_script)
        action_to_add = action.copy()
        action_to_add['id'] = current_len + 1
        action_to_add['uuid'] = uuid.uuid4().fields[-1]
        self.currently_editing_script.append(action_to_add)
        self._insert_action(insert_position, current_len)
        self.update_time_stamp()

    def add_variable(self, statement, variable, type, insert_position=None):
        variable = self.validate_function_name(variable)
        convert_type = getattr(builtins, type)
        statement = convert_type(statement)
        current_len = len(self.currently_editing_script)
        uid = uuid.uuid4().fields[-1]
        action = {"id": current_len + 1, "instrument": 'variable', "action": variable,
                        "args": {"statement": 'None' if statement == '' else statement}, "return": '', "uuid": uid,
                        "arg_types": {"statement": type}}
        self.currently_editing_script.append(action)
        self._insert_action(insert_position, current_len)
        self.update_time_stamp()

    def _insert_action(self, insert_position, current_len, action_len:int=1):

        if insert_position is None:
            self.currently_editing_order.extend([str(current_len + i + 1) for i in range(action_len)])
        else:
            index = int(insert_position) - 1
            self.currently_editing_order[index:index] = [str(current_len + i + 1) for i in range(action_len)]
            self.sort_actions()

    def get_added_variables(self):
        added_variables: Dict[str, str] = {action["action"]: action["arg_types"]["statement"] for action in
                                           self.currently_editing_script if action["instrument"] == "variable"}

        return added_variables

    def get_output_variables(self):
        output_variables: Dict[str, str] = {action["return"]: "function_output" for action in
                                            self.currently_editing_script if action["return"]}

        return output_variables

    def get_variables(self):
        output_variables: Dict[str, str] = self.get_output_variables()
        added_variables = self.get_added_variables()
        output_variables.update(added_variables)

        return output_variables

    def validate_variables(self, kwargs):
        """
        Validates the kwargs passed to the Script
        """
        output_variables: Dict[str, str] = self.get_variables()
        # print(output_variables)
        for key, value in kwargs.items():
            if isinstance(value, str):
                if value in output_variables:
                    var_type = output_variables[value]
                    kwargs[key] = {value: var_type}
                elif value.startswith("#"):
                    kwargs[key] = f"#{self.validate_function_name(value[1:])}"
                else:
                    # attempt to convert to numerical or bool value for args with no type hint
                    try:
                        converted = ast.literal_eval(value)
                        if isinstance(converted, (int, float, bool)):
                            kwargs[key] = converted
                    except (ValueError, SyntaxError):
                        pass
        return kwargs

    def add_logic_action(self, logic_type: str, statement, insert_position=None):
        current_len = len(self.currently_editing_script)
        uid = uuid.uuid4().fields[-1]
        logic_dict = {
            "if":
                [
                    {"id": current_len + 1, "instrument": 'if', "action": 'if',
                     "args": {"statement": 'True' if statement == '' else statement},
                     "return": '', "uuid": uid, "arg_types": {"statement": ''}},
                    {"id": current_len + 2, "instrument": 'if', "action": 'else', "args": {}, "return": '',
                     "uuid": uid},
                    {"id": current_len + 3, "instrument": 'if', "action": 'endif', "args": {}, "return": '',
                     "uuid": uid},
                ],
            "while":
                [
                    {"id": current_len + 1, "instrument": 'while', "action": 'while',
                     "args": {"statement": 'False' if statement == '' else statement}, "return": '', "uuid": uid,
                     "arg_types": {"statement": ''}},
                    {"id": current_len + 2, "instrument": 'while', "action": 'endwhile', "args": {}, "return": '',
                     "uuid": uid},
                ],

            "wait":
                [
                    {"id": current_len + 1, "instrument": 'wait', "action": "wait",
                     "args": {"statement": 1 if statement == '' else statement},
                     "return": '', "uuid": uid, "arg_types": {"statement": "float"}},
                ],
            "repeat":
                [
                    {"id": current_len + 1, "instrument": 'repeat', "action": "repeat",
                     "args": {"statement": 1 if statement == '' else statement}, "return": '', "uuid": uid,
                     "arg_types": {"statement": "int"}},
                    {"id": current_len + 2, "instrument": 'repeat', "action": 'endrepeat',
                     "args": {}, "return": '', "uuid": uid},
                ],
            "pause":
                [
                    {"id": current_len + 1, "instrument": 'pause', "action": "pause",
                     "args": {"statement": 1 if statement == '' else statement}, "return": '', "uuid": uid,
                     "arg_types": {"statement": "str"}}
                ],
        }
        action_list = logic_dict[logic_type]
        self.currently_editing_script.extend(action_list)
        self._insert_action(insert_position, current_len, len(action_list))
        self.update_time_stamp()

    def delete_action(self, id: int):
        """
        Delete the action by id (step number)
        """
        uid = next((action['uuid'] for action in self.currently_editing_script if action['id'] == int(id)), None)
        id_to_be_removed = [action['id'] for action in self.currently_editing_script if action['uuid'] == uid]
        order = self.currently_editing_order
        script = self.currently_editing_script
        self.currently_editing_order = [i for i in order if int(i) not in id_to_be_removed]
        self.currently_editing_script = [action for action in script if action['id'] not in id_to_be_removed]
        self.sort_actions()
        self.update_time_stamp()

    def duplicate_action(self, id: int):
        """
        duplicate action by id (step number), available only for non logic actions
        """
        action_to_duplicate = next((action for action in self.currently_editing_script if action['id'] == int(id)),
                                   None)
        insert_id = action_to_duplicate.get("id")
        self.add_action(action_to_duplicate)
        # print(self.currently_editing_script)
        if action_to_duplicate is not None:
            # Update IDs for all subsequent actions
            for action in self.currently_editing_script:
                if action['id'] > insert_id:
                    action['id'] += 1
            self.currently_editing_script[-1]['id'] = insert_id + 1
            # Sort actions if necessary and update the time stamp
            self.sort_actions()
            self.update_time_stamp()
        else:
            raise ValueError("Action not found: Unable to duplicate the action with ID", id)

    def config(self, stype):
        """
        take the global script_dict
        :return: list of variable that require input
        """
        configure = []
        config_type_dict = {}
        for action in self.script_dict[stype]:
            args = action['args']
            if args is not None:
                if type(args) is not dict:
                    if type(args) is str and args.startswith("#") and not args[1:] in configure:
                        configure.append(args[1:])
                        config_type_dict[args[1:]] = action['arg_types']

                else:
                    for arg in args:
                        if type(args[arg]) is str \
                                and args[arg].startswith("#") \
                                and not args[arg][1:] in configure:
                            configure.append(args[arg][1:])
                            if arg in action['arg_types']:
                                if action['arg_types'][arg] == '':
                                    config_type_dict[args[arg][1:]] = "any"
                                else:
                                    config_type_dict[args[arg][1:]] = action['arg_types'][arg]
                            else:
                                config_type_dict[args[arg][1:]] = "any"
        # todo
        return configure, config_type_dict

    def config_return(self):
        """
        take the global script_dict
        :return: list of variable that require input
        """

        return_list = set([action['return'] for action in self.script_dict['script'] if not action['return'] == ''])
        output_str = "return {"
        for i in return_list:
            output_str += "'" + i + "':" + i + ","
        output_str += "}"
        return output_str, return_list

    def finalize(self):
        """finalize script, disable editing"""
        self.status = "finalized"
        self.update_time_stamp()

    def save_as(self, name):
        """resave script, enable editing"""
        self.name = name
        self.status = "editing"
        self.update_time_stamp()

    def indent(self, unit=0):
        """helper: create _ unit of indent in code string"""
        string = "\n"
        for _ in range(unit):
            string += "\t"
        return string

    def convert_to_lines(self, exec_str_collection: dict):
        """
        Parse a dictionary of script functions and extract function body lines.

        :param exec_str_collection: Dictionary containing script types and corresponding function strings.
        :return: A dict containing script types as keys and lists of function body lines as values.
        """
        line_collection = {}

        for stype, func_str in exec_str_collection.items():
            if func_str:
                module = ast.parse(func_str)

                # Find the first function (regular or async)
                func_def = next(
                    node for node in module.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                )

                # Extract function body as source lines, skipping 'return' nodes
                line_collection[stype] = [
                    ast_unparse(node) for node in func_def.body if not isinstance(node, ast.Return)
                ]
        return line_collection

    def compile(self, script_path=None):
        """
        Compile the current script to a Python file.
        :return: String to write to a Python file.
        """
        self.needs_call_human = False
        self.blocks_included = False

        self.sort_actions()
        run_name = self.name if self.name else "untitled"
        run_name = self.validate_function_name(run_name)
        exec_str_collection = {}

        for i in self.stypes:
            if self.script_dict[i]:
                is_async = any(a.get("coroutine", False) for a in self.script_dict[i])
                func_str = self._generate_function_header(run_name, i, is_async) + self._generate_function_body(i)
                exec_str_collection[i] = func_str
        if script_path:
            self._write_to_file(script_path, run_name, exec_str_collection)

        return exec_str_collection



    @staticmethod
    def validate_function_name(name):
        """Replace invalid characters with underscores"""
        name = re.sub(r'\W|^(?=\d)', '_', name)
        # Check if it's a Python keyword and adjust if necessary
        if keyword.iskeyword(name):
            name += '_'
        return name

    def _generate_function_header(self, run_name, stype, is_async):
        """
        Generate the function header.
        """
        configure, config_type = self.config(stype)

        configure = [param + f":{param_type}" if not param_type == "any" else param for param, param_type in
                     config_type.items()]

        script_type = f"_{stype}" if stype != "script" else ""
        async_str = "async " if is_async else ""
        function_header = f"{async_str}def {run_name}{script_type}("

        if stype == "script":
            function_header += ", ".join(configure)

        function_header += "):"
        # function_header += self.indent(1) + f"global {run_name}_{stype}"
        return function_header

    def _generate_function_body(self, stype):
        """
        Generate the function body for each type in stypes.
        """
        body = ''
        indent_unit = 1

        for index, action in enumerate(self.script_dict[stype]):
            text, indent_unit = self._process_action(indent_unit, action, index, stype)
            body += text
        return_str, return_list = self.config_return()
        if return_list and stype == "script":
            body += self.indent(indent_unit) + return_str
        return body

    def _process_action(self, indent_unit, action, index, stype):
        """
        Process each action within the script dictionary.
        """
        instrument = action['instrument']
        statement = action['args'].get('statement')
        args = self._process_args(action['args'])

        save_data = action['return']
        action_name = action['action']
        next_action = self._get_next_action(stype, index)
        # print(args)
        if instrument == 'if':
            return self._process_if(indent_unit, action_name, statement, next_action)
        elif instrument == 'while':
            return self._process_while(indent_unit, action_name, statement, next_action)
        elif instrument == 'variable':
            return self.indent(indent_unit) + f"{action_name} = {statement}", indent_unit
        elif instrument == 'wait':
            return f"{self.indent(indent_unit)}time.sleep({statement})", indent_unit
        elif instrument == 'repeat':
            return self._process_repeat(indent_unit, action_name, statement, next_action)
        elif instrument == 'pause':
            self.needs_call_human = True
            return f"{self.indent(indent_unit)}pause('{statement}')", indent_unit
        #todo
        # elif instrument == 'registered_workflows':
        #     return inspect.getsource(my_function)
        else:
            is_async = action.get("coroutine", False)
            return self._process_instrument_action(indent_unit, instrument, action_name, args, save_data, is_async)

    def _process_args(self, args):
        """
        Process arguments, handling any specific formatting needs.
        """
        if isinstance(args, str) and args.startswith("#"):
            return args[1:]
        return args

    def _process_if(self, indent_unit, action, args, next_action):
        """
        Process 'if' and 'else' actions.
        """
        exec_string = ""
        if action == 'if':
            exec_string += self.indent(indent_unit) + f"if {args}:"
            indent_unit += 1
            if next_action and next_action['instrument'] == 'if' and next_action['action'] == 'else':
                exec_string += self.indent(indent_unit) + "pass"
            # else:

        elif action == 'else':
            indent_unit -= 1
            exec_string += self.indent(indent_unit) + "else:"
            indent_unit += 1
            if next_action and next_action['instrument'] == 'if' and next_action['action'] == 'endif':
                exec_string += self.indent(indent_unit) + "pass"
        else:
            indent_unit -= 1
        return exec_string, indent_unit

    def _process_while(self, indent_unit, action, args, next_action):
        """
        Process 'while' and 'endwhile' actions.
        """
        exec_string = ""
        if action == 'while':
            exec_string += self.indent(indent_unit) + f"while {args}:"
            indent_unit += 1
            if next_action and next_action['instrument'] == 'while':
                exec_string += self.indent(indent_unit) + "pass"
        elif action == 'endwhile':
            indent_unit -= 1
        return exec_string, indent_unit

    def _process_repeat(self, indent_unit, action, args, next_action):
        """
        Process 'while' and 'endwhile' actions.
        """
        exec_string = ""
        if action == 'repeat':
            exec_string += self.indent(indent_unit) + f"for _ in range({args}):"
            indent_unit += 1
            if next_action and next_action['instrument'] == 'repeat':
                exec_string += self.indent(indent_unit) + "pass"
        elif action == 'endrepeat':
            indent_unit -= 1
        return exec_string, indent_unit

    def _process_instrument_action(self, indent_unit, instrument, action, args, save_data, is_async=False):
        """
        Process actions related to instruments.
        """
        async_str = "await " if is_async else ""

        function_call = f"{instrument}.{action}"
        if instrument.startswith("blocks"):
            self.blocks_included = True
            function_call = action

        if isinstance(args, dict) and args != {}:
            args_str = self._process_dict_args(args)
            single_line = f"{async_str}{function_call}(**{args_str})"
        elif isinstance(args, str):
            single_line = f"{function_call} = {args}"
        else:
            single_line = f"{async_str}{function_call}()"

        if save_data:
            save_data += " = "

        return self.indent(indent_unit) + save_data + single_line, indent_unit

    def _process_dict_args(self, args):
        """
        Process dictionary arguments, handling special cases like variables.
        """
        args_str = args.__str__()
        for arg in args:
            if isinstance(args[arg], str) and args[arg].startswith("#"):
                args_str = args_str.replace(f"'#{args[arg][1:]}'", args[arg][1:])
            elif isinstance(args[arg], dict):
                # print(args[arg])
                if not args[arg]:
                    continue
                # Extract the variable name (first key in the dict)
                value = next(iter(args[arg]))
                var_type = args[arg].get(value)

                # Only process if it's a function_output variable reference
                if var_type == "function_output":
                    variables = self.get_variables()
                    if value not in variables:
                        raise ValueError(f"Variable ({value}) is not defined.")
                    # Replace the dict string representation with just the variable name
                    args_str = args_str.replace(f"{args[arg]}", value)

        # elif self._is_variable(arg):
            #     print("is variable")
            #     args_str = args_str.replace(f"'{args[arg]}'", args[arg])
        return args_str

    def _get_next_action(self, stype, index):
        """
        Get the next action in the sequence if it exists.
        """
        if index < (len(self.script_dict[stype]) - 1):
            return self.script_dict[stype][index + 1]
        return None

    def _is_variable(self, arg):
        """
        Check if the argument is of type 'variable'.
        """
        return arg in self.script_dict and self.script_dict[arg].get("arg_types") == "variable"

    def _write_to_file(self, script_path, run_name, exec_string, call_human=False):
        """
        Write the compiled script to a file.
        """
        with open(script_path + run_name + ".py", "w") as s:
            if self.deck:
                s.write(f"import {self.deck} as deck")
            else:
                s.write("deck = None")
            s.write("\nimport time")
            if self.blocks_included:
                s.write(f"\n{self._create_block_import()}")
            if self.needs_call_human:
                s.write("""\n\ndef pause(reason="Manual intervention required"):\n\tprint(f"\\nHUMAN INTERVENTION REQUIRED: {reason}")\n\tinput("Press Enter to continue...\\n")""")

            for i in exec_string.values():
                s.write(f"\n\n\n{i}")

    def _create_block_import(self):
        imports = {}
        from ivoryos.utils.decorators import BUILDING_BLOCKS
        for category, methods in BUILDING_BLOCKS.items():
            for method_name, meta in methods.items():
                func = meta["func"]
                module = meta["path"]
                name = func.__name__
                imports.setdefault(module, set()).add(name)
        lines = []
        for module, funcs in imports.items():
            lines.append(f"from {module} import {', '.join(sorted(funcs))}")
        return "\n".join(lines)

class WorkflowRun(db.Model):
    """Represents the entire experiment"""
    __tablename__ = 'workflow_runs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    platform = db.Column(db.String(128), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.now())
    end_time = db.Column(db.DateTime)
    data_path = db.Column(db.String(256))
    repeat_mode = db.Column(db.String(64), default="none")  # static_repeat, sweep, optimizer

    # A run contains multiple iterations
    phases = db.relationship(
        'WorkflowPhase',
        backref='workflow_runs', # Clearer back-reference name
        cascade='all, delete-orphan',
        lazy='dynamic' # Good for handling many iterations
    )
    def as_dict(self):
        dict = self.__dict__
        dict.pop('_sa_instance_state', None)
        return dict

class WorkflowPhase(db.Model):
    """Represents a single function call within a WorkflowRun."""
    __tablename__ = 'workflow_phases'

    id = db.Column(db.Integer, primary_key=True)
    # Foreign key to link this iteration to its parent run
    run_id = db.Column(db.Integer, db.ForeignKey('workflow_runs.id', ondelete='CASCADE'), nullable=False)

    # NEW: Store iteration-specific parameters here
    name = db.Column(db.String(64), nullable=False)  # 'prep', 'main', 'cleanup'
    repeat_index = db.Column(db.Integer, default=0)

    parameters = db.Column(JSONType)  # Use db.JSON for general support
    outputs = db.Column(JSONType)
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)

    # An iteration contains multiple steps
    steps = db.relationship(
        'WorkflowStep',
        backref='workflow_phases',  # Clearer back-reference name
        cascade='all, delete-orphan'
    )

    def as_dict(self):
        dict = self.__dict__.copy()
        dict.pop('_sa_instance_state', None)
        return dict

class WorkflowStep(db.Model):
    __tablename__ = 'workflow_steps'

    id = db.Column(db.Integer, primary_key=True)
    # workflow_id = db.Column(db.Integer, db.ForeignKey('workflow_runs.id', ondelete='CASCADE'), nullable=True)
    phase_id = db.Column(db.Integer, db.ForeignKey('workflow_phases.id', ondelete='CASCADE'), nullable=True)

    # phase = db.Column(db.String(64), nullable=False)  # 'prep', 'main', 'cleanup'
    # repeat_index = db.Column(db.Integer, default=0)   # Only applies to 'main' phase
    step_index = db.Column(db.Integer, default=0)
    method_name = db.Column(db.String(128), nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    run_error = db.Column(db.Boolean, default=False)
    output = db.Column(JSONType, default={})
    # Using as_dict method from ModelBase

    def as_dict(self):
        dict = self.__dict__.copy()
        dict.pop('_sa_instance_state', None)
        return dict


class SingleStep(db.Model):
    __tablename__ = 'single_steps'

    id = db.Column(db.Integer, primary_key=True)
    method_name = db.Column(db.String(128), nullable=False)
    kwargs = db.Column(JSONType, nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    run_error = db.Column(db.String(128))
    output = db.Column(JSONType, nullable=True)

    def as_dict(self):
        dict = self.__dict__.copy()
        dict.pop('_sa_instance_state', None)
        return dict

if __name__ == "__main__":
    a = Script()

    print("")
