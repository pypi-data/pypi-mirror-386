"""
This file manage to translate AST into our Nodes Graph,
By defining AstNodes, and statements to parse AST.

Copyright 2020 CDFMLR. All rights reserved.
Use of this source code is governed by a MIT
license that can be found in the LICENSE file.
"""

import _ast
import typing
import warnings
from typing import Tuple

from pyreactflow.node import *

# import astunparse
#
# `astunparse` is a third-party package, that provides a function `unparse` to translate AST into Python source code.
# This function is included in Python 3.9 std lib as `ast.unparse`.
# And there are bugs to continue to use `astunparse` in Python 3.9+.
# So here: we use `astunparse` in Python 3.8- and `ast.unparse` in Python 3.9+.
#
# See also:
#  - https://github.com/cdfmlr/pyflowchart/issues/28
#  - https://github.com/simonpercivall/astunparse/issues/56#issuecomment-1438353347
#  - https://docs.python.org/3/library/ast.html#ast.unparse
import sys

if sys.version_info < (3, 9):
    import astunparse
else:
    import ast as astunparse


# TODO: beautify tail connection direction
# TODO: Nested Function

class AstNode(Node):
    """AstNode is nodes from AST
    """

    def __init__(self, ast_object: _ast.AST, **kwargs):
        Node.__init__(self)
        self.ast_object = ast_object

    def ast_to_source(self) -> str:
        """
        self.ast_object (_ast.AST) back to Python source code
        """
        return astunparse.unparse(self.ast_object).strip()
    
    def extract_variables(self) -> list:
        """
        Extract variable names being assigned in this AST node
        """
        variables = []
        
        if isinstance(self.ast_object, _ast.Assign):
            # Handle regular assignments: var = value
            for target in self.ast_object.targets:
                variables.extend(self._extract_names_from_target(target))
        
        elif isinstance(self.ast_object, _ast.For):
            # Handle for loop variable: for var in iterable
            if isinstance(self.ast_object.target, _ast.Name):
                variables.append(self.ast_object.target.id)
            elif isinstance(self.ast_object.target, _ast.Tuple):
                # Handle tuple unpacking: for a, b in items
                for elt in self.ast_object.target.elts:
                    if isinstance(elt, _ast.Name):
                        variables.append(elt.id)
        
        elif isinstance(self.ast_object, _ast.AnnAssign) and self.ast_object.target:
            # Handle annotated assignments: var: int = value
            if isinstance(self.ast_object.target, _ast.Name):
                variables.append(self.ast_object.target.id)
        
        return variables
    
    def _extract_names_from_target(self, target):
        """Helper to extract variable names from assignment targets"""
        names = []
        if isinstance(target, _ast.Name):
            names.append(target.id)
        elif isinstance(target, _ast.Tuple):
            # Handle tuple unpacking: a, b = values
            for elt in target.elts:
                if isinstance(elt, _ast.Name):
                    names.append(elt.id)
        elif isinstance(target, _ast.List):
            # Handle list unpacking: [a, b] = values
            for elt in target.elts:
                if isinstance(elt, _ast.Name):
                    names.append(elt.id)
        return names
    
    def extract_function_calls(self) -> list:
        """
        Extract function and method calls from this AST node
        Returns a list of dicts with 'name' and 'args' keys
        """
        calls = []
        
        # Check the main AST object
        calls.extend(self._extract_calls_from_node(self.ast_object))
        
        return calls
    
    def _extract_calls_from_node(self, node, visited=None):
        """Recursively extract function calls from an AST node"""
        if visited is None:
            visited = set()
        
        # Avoid processing the same node multiple times
        node_id = id(node)
        if node_id in visited:
            return []
        visited.add(node_id)
        
        calls = []
        
        if isinstance(node, _ast.Call):
            # Extract function/method call info
            call_info = self._extract_call_info(node)
            if call_info:
                calls.append(call_info)
                
            # For method chaining, also check the object being called
            if isinstance(node.func, _ast.Attribute):
                calls.extend(self._extract_calls_from_node(node.func.value, visited))
            
            # Check arguments for nested calls
            for arg in node.args:
                calls.extend(self._extract_calls_from_node(arg, visited))
        
        elif isinstance(node, _ast.Assign):
            # Only check the value being assigned, not all children (to avoid duplicate processing)
            calls.extend(self._extract_calls_from_node(node.value, visited))
        
        elif isinstance(node, _ast.Expr):
            # Only check the value, not all children
            calls.extend(self._extract_calls_from_node(node.value, visited))
        
        elif isinstance(node, _ast.For):
            # Only check the iterable, don't recursively check all children as they're processed separately
            calls.extend(self._extract_calls_from_node(node.iter, visited))
        
        elif isinstance(node, _ast.If):
            # Only check the test condition, don't recursively check all children as they're processed separately
            calls.extend(self._extract_calls_from_node(node.test, visited))
        
        elif isinstance(node, _ast.Return):
            # Only check the return value
            if node.value:
                calls.extend(self._extract_calls_from_node(node.value, visited))
        
        elif isinstance(node, _ast.Attribute):
            # For attribute access (like obj.method), check the value
            calls.extend(self._extract_calls_from_node(node.value, visited))
        
        else:
            # For other nodes, check children only if we haven't handled them specifically
            import ast as ast_module
            for child in ast_module.iter_child_nodes(node):
                calls.extend(self._extract_calls_from_node(child, visited))
        
        return calls
    
    def _extract_call_info(self, call_node):
        """Extract structured information from a function call node"""
        if not isinstance(call_node, _ast.Call):
            return None
        
        # Get the function/method name
        if isinstance(call_node.func, _ast.Name):
            func_name = call_node.func.id
        elif isinstance(call_node.func, _ast.Attribute):
            func_name = call_node.func.attr
        else:
            return None
        
        # Extract argument information
        args = []
        for arg in call_node.args:
            arg_info = self._extract_arg_info(arg)
            if arg_info:
                args.append(arg_info)
        
        # Extract keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg:  # keyword.arg can be None for **kwargs
                arg_info = self._extract_arg_info(keyword.value)
                if arg_info:
                    arg_info['name'] = keyword.arg  # Override name with keyword name
                    args.append(arg_info)
        
        return {
            'name': func_name,
            'args': args
        }
    
    def _extract_arg_info(self, arg_node):
        """Extract information about a function argument"""
        if isinstance(arg_node, _ast.Name):
            return {
                'name': arg_node.id,
                'type': 'variable',
                'value': arg_node.id
            }
        elif isinstance(arg_node, _ast.Constant):
            # Handle constants (strings, numbers, etc.)
            value = arg_node.value
            if isinstance(value, bool):  # Check bool first since bool is subclass of int
                arg_type = 'boolean'
            elif isinstance(value, str):
                arg_type = 'string'
            elif isinstance(value, (int, float)):
                arg_type = 'number'
            else:
                arg_type = 'constant'
            return {
                'name': repr(value),
                'type': arg_type,
                'value': repr(value)
            }
        elif isinstance(arg_node, _ast.List):
            try:
                list_value = astunparse.unparse(arg_node).strip()
            except:
                list_value = 'list'
            return {
                'name': 'list',
                'type': 'list',
                'value': list_value
            }
        elif isinstance(arg_node, _ast.Dict):
            try:
                dict_value = astunparse.unparse(arg_node).strip()
            except:
                dict_value = 'dict'
            return {
                'name': 'dict',
                'type': 'dict',
                'value': dict_value
            }
        elif isinstance(arg_node, _ast.Call):
            # Nested function call
            try:
                call_value = astunparse.unparse(arg_node).strip()
            except:
                call_value = 'function_call'
            return {
                'name': 'function_call',
                'type': 'call',
                'value': call_value
            }
        elif isinstance(arg_node, _ast.Attribute):
            # Attribute access like obj.attr
            try:
                attr_name = astunparse.unparse(arg_node).strip()
                return {
                    'name': attr_name,
                    'type': 'attribute',
                    'value': attr_name
                }
            except:
                return {
                    'name': 'attribute',
                    'type': 'attribute',
                    'value': 'attribute'
                }
        else:
            # For other types, try to get a string representation
            try:
                name = astunparse.unparse(arg_node).strip()
                return {
                    'name': name,
                    'type': 'expression',
                    'value': name
                }
            except:
                return {
                    'name': 'unknown',
                    'type': 'unknown',
                    'value': 'unknown'
                }


class AstConditionNode(AstNode, ConditionNode):
    """
    AstConditionNode is a ConditionNode for _ast.For | _ast.While | _ast.If ({for|while|if}-sentence in code)
    """

    def __init__(self, ast_cond: _ast.stmt, **kwargs):
        """
        Args:
            ast_cond: instance of _ast.For or _ast.While or _ast.If
            **kwargs: None
        """
        AstNode.__init__(self, ast_cond, **kwargs)
        ConditionNode.__init__(self, cond=self.cond_expr())

    def cond_expr(self) -> str:
        """
        cond_expr returns the condition expression of if|while|for sentence.
        """
        # Extract only the condition part, not the entire statement
        if isinstance(self.ast_object, _ast.If):
            # For if statements, extract only the test condition
            condition_ast = self.ast_object.test
        elif isinstance(self.ast_object, _ast.For):
            # For for loops, extract the target and iter parts
            target = astunparse.unparse(self.ast_object.target).strip()
            iter_expr = astunparse.unparse(self.ast_object.iter).strip()
            return f"for {target} in {iter_expr}"
        elif isinstance(self.ast_object, _ast.While):
            # For while loops, include the 'while' keyword with the condition
            test_condition = astunparse.unparse(self.ast_object.test).strip()
            return f"while {test_condition}"
        else:
            # Fallback to the original method
            source = astunparse.unparse(self.ast_object)
            loop_statement = source.strip()
            single_line = ' '.join(loop_statement.splitlines()).strip()
            if single_line.endswith(':'):
                single_line = single_line[:-1]
            return single_line

        # For if and while statements, extract just the condition
        condition_source = astunparse.unparse(condition_ast).strip()
        # Ensure single line by replacing newlines and extra whitespace
        single_line = ' '.join(condition_source.splitlines()).strip()
        return single_line

    def fc_connection(self) -> str:
        """
        to avoid meaningless `cond999->`

        Returns: a blank str ""
        """
        return ""


###################
#   FunctionDef   #
###################

class FunctionDefStart(AstNode, StartNode):
    """
    FunctionDefStart is a StartNode from _ast.FunctionDef,
    standing for the start of a function.
    """

    def __init__(self, ast_function_def: _ast.FunctionDef, **kwargs):
        AstNode.__init__(self, ast_function_def, **kwargs)
        StartNode.__init__(self, ast_function_def.name)


class FunctionDefEnd(AstNode, EndNode):
    """
    FunctionDefEnd is a EndNode from _ast.FunctionDef,
     standing for the end of a function.
    """

    def __init__(self, ast_function_def: _ast.FunctionDef, **kwargs):
        AstNode.__init__(self, ast_function_def, **kwargs)
        EndNode.__init__(self, ast_function_def.name)


class FunctionDefArgsInput(AstNode, InputOutputNode):
    """
    FunctionDefArgsInput is a InputOutputNode from _ast.FunctionDef,
    standing for the args (input) of a function.
    """

    def __init__(self, ast_function_def: _ast.FunctionDef, **kwargs):
        AstNode.__init__(self, ast_function_def, **kwargs)
        params = self.extract_params()
        InputOutputNode.__init__(self, InputOutputNode.INPUT, self.func_args_str(), params=params)

    def func_args_str(self):
        # TODO(important): handle defaults, vararg, kwonlyargs, kw_defaults, kwarg
        assert isinstance(self.ast_object, _ast.FunctionDef) or \
               hasattr(self.ast_object, "args")
        args = []
        for arg in self.ast_object.args.args:
            args.append(str(arg.arg))

        return ', '.join(args)

    def extract_params(self):
        """Extract structured parameter data for React Flow node."""
        assert isinstance(self.ast_object, _ast.FunctionDef) or \
               hasattr(self.ast_object, "args")

        params = []
        args_list = self.ast_object.args.args
        defaults_list = self.ast_object.args.defaults

        # Calculate the offset: defaults apply to the last N arguments
        num_args = len(args_list)
        num_defaults = len(defaults_list)
        defaults_offset = num_args - num_defaults

        for i, arg in enumerate(args_list):
            param = {
                'name': str(arg.arg),
                'type': self._get_arg_type(arg)
            }

            # Add default value if present
            if i >= defaults_offset:
                default_index = i - defaults_offset
                default_value = self._get_default_value(defaults_list[default_index])
                if default_value is not None:
                    param['default'] = default_value

            params.append(param)

        return params
    
    def _get_arg_type(self, arg):
        """Extract type annotation from function argument if available."""
        if hasattr(arg, 'annotation') and arg.annotation:
            try:
                return astunparse.unparse(arg.annotation).strip()
            except:
                return 'any'
        return 'any'

    def _get_default_value(self, default_node):
        """Extract default value from AST node."""
        if default_node is None:
            return None

        try:
            # Use astunparse to convert the default value AST node to string
            return astunparse.unparse(default_node).strip()
        except:
            # Fallback to basic types if astunparse fails
            try:
                if isinstance(default_node, _ast.Constant):
                    return default_node.value
                elif isinstance(default_node, _ast.Num):  # For older Python versions
                    return default_node.n
                elif isinstance(default_node, _ast.Str):  # For older Python versions
                    return default_node.s
                elif isinstance(default_node, _ast.NameConstant):  # For older Python versions
                    return default_node.value
            except:
                pass

        return None


class FunctionDef(NodesGroup, AstNode):
    """
    FunctionDef is a AstNode for _ast.FunctionDef (def-sentence in python)

    This class is a NodesGroup with FunctionDefStart & FunctionDefArgsInput & function-body & FunctionDefEnd.
    """

    def __init__(self, ast_func: _ast.FunctionDef, **kwargs):  # _ast.For | _ast.While
        """
        FunctionDef.__init__ makes a NodesGroup object with following Nodes chain:
            FunctionDef -> FunctionDefStart -> FunctionDefArgsInput -> [function-body] -> FunctionDefEnd

        Args:
            **kwargs: None
        """
        AstNode.__init__(self, ast_func, **kwargs)

        # get nodes
        self.func_start = FunctionDefStart(ast_func, **kwargs)
        self.func_args_input = FunctionDefArgsInput(ast_func, **kwargs)
        self.body_head, self.body_tails = self.parse_func_body(**kwargs)
        self.func_end = FunctionDefEnd(ast_func, **kwargs)

        # connect
        self.func_start.connect(self.func_args_input)
        self.func_args_input.connect(self.body_head)
        for t in self.body_tails:
            if isinstance(t, Node):
                t.connect(self.func_end)

        NodesGroup.__init__(self, self.func_start, [self.func_end])

    def parse_func_body(self, **kwargs) -> Tuple[Node, List[Node]]:
        """
        parse function body.

        Returns:
            (Node, List[Node])
            - body_head
            - body_tails
        """
        assert isinstance(self.ast_object, _ast.FunctionDef) or \
               hasattr(self.ast_object, "body")
        p = parse(self.ast_object.body, **kwargs)
        return p.head, p.tails


###################
#   For, while    #
###################

class LoopCondition(AstConditionNode):
    """a AstConditionNode special for Loop"""

    def connect(self, sub_node, direction='') -> None:
        if direction:
            self.set_connect_direction(direction)
        self.connect_no(sub_node)

    def get_yes_label(self) -> str:
        return 'loop'

    def get_no_label(self) -> str:
        return 'exit'

    def to_react_flow_node(self, position=None):
        # Override to use 'loop' type instead of 'condition' for React Flow
        if position is None:
            position = {'x': 0, 'y': 0}
        
        # Check if this is a one-line body loop and create combined label
        label = ' '.join(self.node_text.splitlines()).strip() if self.node_text else ''

        # Only merge if we truly want to merge (not using parent-child relationships)
        should_merge_label = (self.is_one_line_body() and 
                             not getattr(self, '_prefer_parent_child', False))
        
        if should_merge_label:
            try:
                # Get the loop body node
                loop_body = self.connection_yes.next_node
                if isinstance(loop_body, CondYN) and isinstance(loop_body.sub, Node):
                    body_text = loop_body.sub.node_text.strip()
                    # Create combined label with arrow
                    label = f"{label} → {body_text}"
            except (AttributeError, TypeError):
                # Fall back to regular label if we can't access the body
                pass

        # Base data structure
        data = {'label': label}
        
        # Extract variables and function calls
        variables = self.extract_variables()
        if variables:
            data['vars'] = variables
        
        function_calls = self.extract_function_calls()
        if function_calls:
            data['tasks'] = function_calls

        return {
            'id': self.node_name,
            'type': 'loop',  # Use 'loop' type for loop conditions
            'data': data,
            'position': position,
        }

    def is_one_line_body(self) -> bool:
        """
        Is condition with one line body:
            for|while expr:
                one_line_body
        Returns:
            True or False
        """
        one_line_body = False
        try:
            if not self.connection_yes or not isinstance(self.connection_yes, Connection):
                return False
            loop_body = self.connection_yes.next_node
            one_line_body = isinstance(loop_body, CondYN) and \
                            isinstance(loop_body.sub, Node) and \
                            not isinstance(loop_body.sub, NodesGroup) and \
                            not isinstance(loop_body.sub, ConditionNode) and \
                            len(loop_body.sub.connections) == 1 and \
                            loop_body.sub.connections[0].next_node == self
        except Exception as e:
            print(e)
        return one_line_body


class Loop(NodesGroup, AstNode):
    """
    Loop is a AstNode for _ast.For | _ast.While ({for|while}-sentence in python source code)

    This class is a NodesGroup that connects to LoopCondition & loop-body.
    """

    def __init__(self, ast_loop: _ast.stmt, **kwargs):  # _ast.For | _ast.While
        """
        Construct Loop object will make following Node chain:
            Loop -> LoopCondition -> (yes) -> LoopCondition
                                  -> (no)  -> <next_node>

        Args:
            **kwargs:

                simplify={True | False}: simplify the one_line_body case?
                                           (Default: True)
                                           See `self.simplify`
        """
        AstNode.__init__(self, ast_loop, **kwargs)

        self.cond_node = LoopCondition(ast_loop)

        NodesGroup.__init__(self, self.cond_node)

        self.parse_loop_body(**kwargs)

        self._virtual_no_tail()

        if kwargs.get("simplify", True):
            self.simplify()

    def parse_loop_body(self, **kwargs) -> None:
        """
        Parse and Connect loop-body (a node graph) to self.cond_node (LoopCondition), extend `self.tails` with tails got.
        """
        assert isinstance(self.ast_object, _ast.For) or \
               isinstance(self.ast_object, _ast.While) or \
               hasattr(self.ast_object, "body")

        progress = parse(self.ast_object.body, **kwargs)

        if progress.head is not None:
            process = parse(self.ast_object.body, **kwargs)
            # head
            self.cond_node.connect_yes(process.head)
            # tails connect back to cond
            for tail in process.tails:
                if isinstance(tail, Node):
                    tail.set_connect_direction("left")
                    tail.connect(self.cond_node)
        else:
            noop = SubroutineNode("no-op")
            noop.set_connect_direction("left")
            noop.connect(self.cond_node)
            self.cond_node.connect_yes(noop)

    def _virtual_no_tail(self) -> None:
        # virtual_no = NopNode(parent=self.cond_node)
        # virtual_no = CondYN(self, CondYN.NO)
        virtual_no = None
        self.cond_node.connect_no(virtual_no)

        self.append_tails(self.cond_node.connection_no.next_node)
        pass

    # def connect(self, sub_node) -> None:
    #     self.cond_node.connect_no(sub_node)

    def simplify(self) -> None:
        """
        simplify following case:
            for|while expr:
                one_line_body
        before:
            ... -> Loop (self, NodesGroup) -> LoopCondition('for|while expr') -> CommonOperation('one_line_body') -> ...
        after:
            ... -> Loop (self, NodesGroup) -> CommonOperation('one_line_body while expr') -> ...
        Returns:
            None
        """
        try:
            if self.cond_node.is_one_line_body():  # simplify
                cond = self.cond_node
                assert isinstance(self.cond_node.connection_yes.next_node, CondYN)
                body = self.cond_node.connection_yes.next_node.sub

                simplified = OperationNode(f'{body.node_text} while {cond.node_text.lstrip("for").lstrip("while")}')

                simplified.node_name = self.head.node_name
                self.head = simplified
                self.tails = [simplified]

        except AttributeError as e:
            print(e)


##########
#   If   #
##########

class IfCondition(AstConditionNode):
    """a AstConditionNode special for If"""

    def is_one_line_body(self) -> bool:
        """
        Is IfCondition with one-line body?
            if expr:
                one_line_body

        Returns:
            True or False
        """
        one_line_body = False
        try:
            conn_yes = self.connection_yes
            one_line_body = isinstance(conn_yes, Connection) and \
                            isinstance(conn_yes.next_node, CondYN) and \
                            isinstance(conn_yes.next_node.sub, Node) and \
                            not isinstance(conn_yes.next_node.sub, NodesGroup) and \
                            not isinstance(conn_yes.next_node.sub, ConditionNode) and \
                            not conn_yes.next_node.sub.connections
        except Exception as e:
            print(e)
        return one_line_body

    def is_no_else(self) -> bool:
        """
        Is IfCondition without else-body?
            if expr:
                if-body
            # no elif, no else

        Returns:
            True or False
        """
        no_else = False
        try:
            conn2no = self.connection_no
            no_else = isinstance(conn2no, Connection) and \
                      isinstance(conn2no.next_node, CondYN) and \
                      not conn2no.next_node.sub
        except Exception as e:
            print(e)
        return no_else

    def is_ternary_candidate(self) -> bool:
        """
        Is IfCondition suitable for ternary expression (condition ? yes : no)?
        Both yes and no branches should have single statements.
        
        Returns:
            True or False
        """
        try:
            # Check if both yes and no branches exist and have single statements
            conn_yes = self.connection_yes
            conn_no = self.connection_no
            
            yes_single = (isinstance(conn_yes, Connection) and 
                         isinstance(conn_yes.next_node, CondYN) and
                         isinstance(conn_yes.next_node.sub, Node) and
                         not isinstance(conn_yes.next_node.sub, NodesGroup) and
                         not isinstance(conn_yes.next_node.sub, ConditionNode))
            
            no_single = (isinstance(conn_no, Connection) and 
                        isinstance(conn_no.next_node, CondYN) and
                        isinstance(conn_no.next_node.sub, Node) and
                        not isinstance(conn_no.next_node.sub, NodesGroup) and
                        not isinstance(conn_no.next_node.sub, ConditionNode))
            
            return yes_single and no_single
        except Exception as e:
            print(e)
        return False
    
    def is_complex_ternary_candidate(self):
        """Check if this is a condition that should be represented as a complex ternary expression.
        
        This handles cases where branches contain complex structures (NodesGroup) that would
        normally create depth > 1 violations. Only use complex ternary when the condition
        is nested and would otherwise violate depth limits.
        
        Returns:
            True if this should be a complex ternary, False otherwise
        """
        try:
            # Check if both yes and no branches exist
            conn_yes = self.connection_yes
            conn_no = self.connection_no
            
            if not (isinstance(conn_yes, Connection) and isinstance(conn_no, Connection)):
                return False
                
            # Check if branches have CondYN wrappers
            yes_branch = conn_yes.next_node
            no_branch = conn_no.next_node
            
            if not (isinstance(yes_branch, CondYN) and isinstance(no_branch, CondYN)):
                return False
            
            # Basic requirement: both branches must have content
            if not (yes_branch.sub is not None and no_branch.sub is not None):
                return False
            
            # Key logic: Only use complex ternary if this condition would cause depth violations
            # This happens when the condition is nested inside another condition/loop
            
            # Check if at least one branch contains complex content (NodesGroup with multiple statements)
            yes_is_complex = (hasattr(yes_branch.sub, 'head') and hasattr(yes_branch.sub, 'tails'))
            no_is_complex = (hasattr(no_branch.sub, 'head') and hasattr(no_branch.sub, 'tails'))
            
            # If neither branch is complex, prefer simple ternary or regular condition
            if not (yes_is_complex or no_is_complex):
                return False
            
            # Check if this condition is nested (which would cause depth violations)
            # This is a simplified check - in practice, the export logic will determine
            # if depth violations would occur, but we can make a reasonable guess here
            
            # For now, use complex ternary when we have complex branches
            # The export logic will filter appropriately based on actual depth constraints
            return True
            
        except Exception:
            return False
    
    def _extract_branch_content(self, branch_node):
        """Extract the content from a branch node for complex ternary formatting.
        
        Args:
            branch_node: The CondYN branch node to extract content from
            
        Returns:
            String representation of the branch content
        """
        try:
            if not isinstance(branch_node, CondYN) or not branch_node.sub:
                return ""
            
            sub_node = branch_node.sub
            
            # Handle NodesGroup (complex branches with multiple statements)
            if isinstance(sub_node, NodesGroup):
                # Try AST-based extraction first for better formatting
                # We need to determine which branch this is (YES or NO)
                is_yes_branch = (hasattr(self, 'connection_yes') and 
                               self.connection_yes and 
                               self.connection_yes.next_node == branch_node)
                
                ast_content = self._extract_from_ast_branch(is_yes_branch)
                if ast_content:
                    return ast_content
                # Fallback to node-based extraction
                return self._extract_nodesgroup_content(sub_node)
            
            # Handle single Node
            elif isinstance(sub_node, Node):
                # For single nodes, also try AST-based extraction for NO branch
                is_no_branch = (hasattr(self, 'connection_no') and 
                               self.connection_no and 
                               self.connection_no.next_node == branch_node)
                
                if is_no_branch:
                    ast_content = self._extract_from_ast_branch(False)
                    if ast_content:
                        return ast_content
                
                return sub_node.node_text.strip() if sub_node.node_text else ""
            
            return ""
            
        except Exception:
            return ""
    
    def _extract_from_ast_branch(self, is_yes_branch=True):
        """Extract branch content directly from the original AST for better formatting.
        
        Args:
            is_yes_branch: True for YES branch, False for NO branch
            
        Returns:
            String representation of the branch content or None if not available
        """
        try:
            # Check if we have access to the original AST
            if not (hasattr(self, 'ast_object') and self.ast_object):
                return None
            
            # Get the appropriate branch from the AST
            if is_yes_branch:
                if not hasattr(self.ast_object, 'body'):
                    return None
                ast_statements = self.ast_object.body
            else:
                if not hasattr(self.ast_object, 'orelse'):
                    return None
                ast_statements = self.ast_object.orelse
            
            content_parts = []
            
            for stmt in ast_statements:
                if isinstance(stmt, _ast.For):
                    # Format the for loop properly with original structure
                    target = astunparse.unparse(stmt.target).strip()
                    iter_expr = astunparse.unparse(stmt.iter).strip()
                    loop_header = f"for {target} in {iter_expr}:"
                    
                    # Get loop body with proper indentation
                    loop_body = []
                    for body_stmt in stmt.body:
                        body_text = astunparse.unparse(body_stmt).strip()
                        loop_body.append(f"    {body_text}")
                    
                    if loop_body:
                        loop_content = f"{loop_header}\n" + "\n".join(loop_body)
                    else:
                        loop_content = loop_header
                    
                    content_parts.append(loop_content)
                else:
                    # Regular statement
                    stmt_text = astunparse.unparse(stmt).strip()
                    content_parts.append(stmt_text)
            
            return "\n".join(content_parts) if content_parts else None
            
        except Exception:
            return None
    
    def _extract_nodesgroup_content(self, nodes_group):
        """Extract formatted content from a NodesGroup for complex ternary.
        
        Args:
            nodes_group: NodesGroup containing multiple statements
            
        Returns:
            Properly formatted string representation
        """
        try:
            content_parts = []
            visited = set()
            
            # Traverse through the NodesGroup to collect all content
            current_node = nodes_group.head
            while current_node and id(current_node) not in visited:
                visited.add(id(current_node))
                
                # Handle Loop nodes specially to get the original for loop format
                if hasattr(current_node, 'cond_node') and hasattr(current_node.cond_node, 'ast_object'):
                    # This is a Loop node - extract the original loop format
                    loop_content = self._format_loop_content(current_node.cond_node)
                    if loop_content:
                        content_parts.append(loop_content)
                elif hasattr(current_node, 'node_text') and current_node.node_text:
                    # Check if this is a loop condition that needs special formatting
                    if isinstance(current_node, LoopCondition):
                        loop_content = self._format_loop_content(current_node)
                        if loop_content:
                            content_parts.append(loop_content)
                    else:
                        content_parts.append(current_node.node_text.strip())
                
                # Move to next node by following connections
                next_node = None
                if hasattr(current_node, 'connections') and current_node.connections:
                    for conn in current_node.connections:
                        if (hasattr(conn, 'next_node') and conn.next_node and 
                            id(conn.next_node) not in visited):
                            next_node = conn.next_node
                            break
                
                # For Loop nodes, also check tails as they contain following statements
                if not next_node and hasattr(current_node, 'tails') and current_node.tails:
                    for tail in current_node.tails:
                        if tail and id(tail) not in visited:
                            next_node = tail
                            break
                
                current_node = next_node
            
            # Join with newlines for proper formatting
            return '\n'.join(content_parts)
            
        except Exception:
            return ""
    
    def _format_loop_content(self, loop_node):
        """Format loop content for complex ternary display.
        
        Args:
            loop_node: LoopCondition node to format
            
        Returns:
            Properly formatted loop content
        """
        try:
            # Get the original AST loop text if available
            if hasattr(loop_node, 'ast_object') and loop_node.ast_object:
                # Extract the loop header
                ast_obj = loop_node.ast_object
                if hasattr(ast_obj, 'target') and hasattr(ast_obj, 'iter'):
                    target = astunparse.unparse(ast_obj.target).strip()
                    iter_expr = astunparse.unparse(ast_obj.iter).strip()
                    loop_header = f"for {target} in {iter_expr}:"
                    
                    # Get body content from the original AST
                    body_content = []
                    if hasattr(ast_obj, 'body') and ast_obj.body:
                        for stmt in ast_obj.body:
                            stmt_text = astunparse.unparse(stmt).strip()
                            body_content.append(f"    {stmt_text}")
                    
                    if body_content:
                        return f"{loop_header}\n" + "\n".join(body_content)
                    else:
                        return loop_header
            
            # Fallback to node_text
            return loop_node.node_text.strip() if hasattr(loop_node, 'node_text') and loop_node.node_text else ""
            
        except Exception:
            return ""

    def to_react_flow_node(self, position=None):
        # Check for complex ternary (with NodesGroup branches) first
        # Only use it if this node has been marked for complex ternary by export logic
        if (self.is_complex_ternary_candidate() and 
            getattr(self, '_use_complex_ternary', False)):
            try:
                # Get the condition text
                condition_text = ' '.join(self.node_text.splitlines()).strip() if self.node_text else ''
                
                # Extract content from both branches
                yes_text = self._extract_branch_content(self.connection_yes.next_node)
                no_text = self._extract_branch_content(self.connection_no.next_node)
                
                # Create complex ternary expression
                label = f'{condition_text} ? {yes_text} : {no_text}'
                
                if position is None:
                    position = {'x': 0, 'y': 0}
                
                # Base data structure
                data = {'label': label}
                
                # Extract variables and function calls
                variables = self.extract_variables()
                if variables:
                    data['vars'] = variables
                
                function_calls = self.extract_function_calls()
                if function_calls:
                    data['tasks'] = function_calls
                
                return {
                    'id': self.node_name,
                    'type': 'condition',
                    'data': data,
                    'position': position,
                }
            except (AttributeError, TypeError):
                # Fall back to regular condition node
                pass
        
        # Check if this should be a simple ternary expression (only if explicitly requested)
        # For now, disable simple ternary to use parent-child structure instead
        use_simple_ternary = getattr(self, '_use_simple_ternary', False)
        if use_simple_ternary and self.is_ternary_candidate():
            try:
                # Get the condition text
                condition_text = ' '.join(self.node_text.splitlines()).strip() if self.node_text else ''
                
                # Get yes and no branch texts
                yes_text = self.connection_yes.next_node.sub.node_text.strip()
                no_text = self.connection_no.next_node.sub.node_text.strip()
                
                # Create ternary expression with consistent quote style
                label = f'{condition_text} ? {yes_text} : {no_text}'
                
                if position is None:
                    position = {'x': 0, 'y': 0}
                
                # Base data structure
                data = {'label': label}
                
                # Extract variables and function calls
                variables = self.extract_variables()
                if variables:
                    data['vars'] = variables
                
                function_calls = self.extract_function_calls()
                if function_calls:
                    data['tasks'] = function_calls
                
                return {
                    'id': self.node_name,
                    'type': 'condition',
                    'data': data,
                    'position': position,
                }
            except (AttributeError, TypeError):
                # Fall back to regular condition node
                pass
                
        # Default behavior - use regular condition node with children
        return super().to_react_flow_node(position)


class If(NodesGroup, AstNode):
    """
    If is a AstNode for _ast.If (the `if` sentences in python source code)

    This class is a NodesGroup that connects to IfCondition & if-body & else-body.
    """

    def __init__(self, ast_if: _ast.If, **kwargs):
        """
        Construct If object will make following Node chain:
            If -> IfCondition -> (yes) -> yes-path
                              -> (no)  -> no-path

        Args:
            **kwargs:

                simplify={True | False}: simplify the one_line_body case?
                                           (Default: True)
                                           See `self.simplify`
        """
        AstNode.__init__(self, ast_if, **kwargs)

        self.cond_node = IfCondition(ast_if)

        NodesGroup.__init__(self, self.cond_node)

        self.parse_if_body(**kwargs)
        self.parse_else_body(**kwargs)

        if kwargs.get("simplify", True):
            self.simplify()
        if kwargs.get("conds_align", False) and self.cond_node.is_no_else():
            self.cond_node.connection_yes.set_param("right")

    def parse_if_body(self, **kwargs) -> None:
        """
        Parse and Connect if-body (a node graph) to self.cond_node (IfCondition).
        """
        assert isinstance(self.ast_object, _ast.If) or \
               hasattr(self.ast_object, "body")

        progress = parse(self.ast_object.body, **kwargs)

        if progress.head is not None:
            self.cond_node.connect_yes(progress.head)
            # for t in progress.tails:
            #     if isinstance(t, Node):
            #         t.set_connect_direction("right")
            self.extend_tails(progress.tails)
        else:  # connect virtual connection_yes
            # virtual_yes = NopNode(parent=self.cond_node)
            # virtual_yes = CondYN(self, CondYN.YES)
            virtual_yes = None
            self.cond_node.connect_yes(virtual_yes)

            self.append_tails(self.cond_node.connection_yes.next_node)

    def parse_else_body(self, **kwargs) -> None:
        """
        Parse and Connect else-body (a node graph) to self.cond_node (IfCondition).
        """
        assert isinstance(self.ast_object, _ast.If) or \
               hasattr(self.ast_object, "orelse")

        progress = parse(self.ast_object.orelse, **kwargs)

        if progress.head is not None:
            self.cond_node.connect_no(progress.head)
            self.extend_tails(progress.tails)
        else:  # connect virtual connection_no
            # virtual_no = NopNode(parent=self.cond_node)
            # virtual_no = CondYN(self, CondYN.NO)
            virtual_no = None
            self.cond_node.connect_no(virtual_no)

            self.append_tails(self.cond_node.connection_no.next_node)

    def simplify(self) -> None:
        """simplify the one-line body case:
            if expr:
                one_line_body
            # no else

        before:
            ... -> If (self, NodesGroup) -> IfCondition('if expr') -> CommonOperation('one_line_body') -> ...
        after:
            ... -> If (self, NodesGroup) -> CommonOperation('one_line_body if expr') -> ...
        Returns:
            None
        """
        try:
            if self.cond_node.is_no_else() and self.cond_node.is_one_line_body():  # simplify
                cond = self.cond_node
                if not cond.connection_yes:
                    return

                assert isinstance(self.cond_node.connection_yes.next_node, CondYN)
                body = self.cond_node.connection_yes.next_node.sub

                simplified = OperationNode(f'{body.node_text} if {cond.node_text.lstrip("if")}')

                simplified.node_name = self.head.node_name
                self.head = simplified
                self.tails = [simplified]

        except AttributeError as e:
            print(e)

    def align(self):
        """ConditionNode alignment support #14
            if cond1:
                op1
            if cond2:
                op2
            if cond3:
                op3
            op_end

        Simplify: add param `align-next=no` to cond1~3, which improves the generated flowchart.

        See:
            - https://github.com/cdfmlr/pyflowchart/issues/14
            - https://github.com/adrai/flowchart.js/issues/221#issuecomment-846919013
            - https://github.com/adrai/flowchart.js/issues/115
        """
        self.cond_node.no_align_next()


####################
#   Common, Call   #
####################

class CommonOperation(AstNode, OperationNode):
    """
    CommonOperation is an OperationNode for any _ast.AST (any sentence in python source code)
    """

    def __init__(self, ast_object: _ast.AST, **kwargs):
        AstNode.__init__(self, ast_object, **kwargs)
        OperationNode.__init__(self, operation=self.ast_to_source())


class CallSubroutine(AstNode, SubroutineNode):
    """
    CallSubroutine is an SubroutineNode for _ast.Call (function call sentence in source)
    """

    def __init__(self, ast_call: _ast.Call, **kwargs):
        AstNode.__init__(self, ast_call, **kwargs)
        SubroutineNode.__init__(self, self.ast_to_source())


##############################
#   Break, Continue, Yield   #
##############################


class BreakContinueSubroutine(AstNode, SubroutineNode):
    """
    BreakContinueSubroutine is an SubroutineNode for _ast.Break or _ast.Continue (break/continue sentence in source)
    """

    # TODO: Including information about the LoopCondition that is to be break/continue.

    def __init__(self, ast_break_continue: _ast.stmt, **kwargs):  # Break & Continue is subclass of stmt
        AstNode.__init__(self, ast_break_continue, **kwargs)
        SubroutineNode.__init__(self, self.ast_to_source())

    def connect(self, sub_node, direction='') -> None:
        # a BreakContinueSubroutine should connect to nothing
        pass


class YieldOutput(AstNode, InputOutputNode):
    """
     YieldOutput is a InputOutputNode (Output) for _ast.Yield (yield sentence in python source code)
    """

    def __init__(self, ast_return: _ast.Return, **kwargs):
        AstNode.__init__(self, ast_return, **kwargs)
        InputOutputNode.__init__(self, InputOutputNode.OUTPUT, self.ast_to_source())


##############
#   Return   #
##############

class ReturnOutput(AstNode, InputOutputNode):
    """
     ReturnOutput is a InputOutputNode (Output) for _ast.Return (return sentence in python source code)
    """

    def __init__(self, ast_return: _ast.Return, **kwargs):
        AstNode.__init__(self, ast_return, **kwargs)
        InputOutputNode.__init__(self, InputOutputNode.OUTPUT, self.ast_to_source().lstrip("return"))


class ReturnEnd(AstNode, EndNode):
    """
    ReturnEnd is a EndNode for _ast.Return (return sentence in python source code)
    """

    def __init__(self, ast_return: _ast.Return, **kwargs):
        AstNode.__init__(self, ast_return, **kwargs)
        EndNode.__init__(self, "function return")  # TODO: the returning function name


class Return(NodesGroup, AstNode):
    """
    ReturnEnd is a AstNode for _ast.Return (return sentence in python source code)

    This class is an invisible virtual Node (i.e. NodesGroup) that connects to ReturnOutput & ReturnEnd.
    """

    def __init__(self, ast_return: _ast.Return, **kwargs):
        """
        Construct Return object will make following Node chain:
            Return -> ReturnOutput -> ReturnEnd
        Giving return sentence without return-values, the ReturnOutput will be omitted: (Return -> ReturnEnd)

        Args:
            **kwargs: None
        """
        AstNode.__init__(self, ast_return, **kwargs)

        self.output_node = None
        self.end_node = None

        self.head = None

        self.end_node = ReturnEnd(ast_return, **kwargs)
        self.head = self.end_node
        if ast_return.value:
            self.output_node = ReturnOutput(ast_return, **kwargs)
            self.output_node.connect(self.end_node)
            self.head = self.output_node

        self.connections.append(Connection(self.head))

        NodesGroup.__init__(self, self.head, [self.end_node])

    # def fc_definition(self) -> str:
    #     """
    #     Return object is invisible
    #     """
    #     return NodesGroup.fc_definition(self)
    #
    # def fc_connection(self) -> str:
    #     """
    #     Return object is invisible
    #     """
    #     return NodesGroup.fc_connection(self)
    #
    def connect(self, sub_node, direction='') -> None:
        """
        Return should not be connected with anything
        """
        pass


#############
#   Match   #
#############

# _ast_Match_t is a type alias to _ast.Match in Python 3.10+.
# for old Python versions, it can be anything (_ast.AST).
#
# This is a workaround for the problem that
# an _ast.NON_EXIST as a type hint will prevent the whole program from running:
#     AttributeError: module '_ast' has no attribute 'Match'
_ast_Match_t = _ast.AST
if sys.version_info >= (3, 10):
    _ast_Match_t = _ast.Match

# similar to _ast_Match_t
_ast_match_case_t = _ast.AST
if sys.version_info >= (3, 10):
    _ast_match_case_t = _ast.match_case


class MatchCaseCondition(ConditionNode):
    """
    MatchCaseConditionNode is ConditionNode special for the condition of a case in match-case:

        match {subject}:
            case {pattern} if {guard}:
                ...
    """

    def __init__(self, ast_match_case: _ast_match_case_t, subject: _ast.AST, **kwargs):
        """
        Args:
            ast_match_case: instance of _ast.match_case
            **kwargs: None
        """
        ConditionNode.__init__(self, cond=self.cond_expr(ast_match_case, subject))

    @staticmethod
    def cond_expr(ast_match_case: _ast_match_case_t, subject: _ast.AST) -> str:
        """
        cond_expr returns the condition expression of match-case sentence.

            "if {subject} match case {pattern} [if {guard}]"
        """
        subject = astunparse.unparse(subject).strip()
        pattern = astunparse.unparse(ast_match_case.pattern).strip()
        guard = astunparse.unparse(ast_match_case.guard).strip() if ast_match_case.guard else None

        s = f"if {subject} match case {pattern}"
        if guard:
            s += f" if {guard}"

        return s


class MatchCase(NodesGroup, AstNode):
    """
    MatchCase is a NodesGroup that connects to MatchCaseConditionNode & case-body.
    It is from a case in match-case:
        match {subject}:
            case {pattern} if {guard}:
                {body}
    We parse it to an NodesGroup, that looks like an If without Else:
        If (self, NodesGroup)
            -> IfCondition('if {subject} match case {pattern} [if {guard}]') ->
                -> yes -> [body]
                -> no -> aTransparentNode
    """

    def __init__(self, ast_match_case: _ast_match_case_t, subject: _ast.AST, **kwargs):
        AstNode.__init__(self, ast_match_case, **kwargs)

        self.cond_node = MatchCaseCondition(ast_match_case, subject)

        NodesGroup.__init__(self, self.cond_node)

        self.parse_body(**kwargs)

    def parse_body(self, **kwargs) -> None:
        assert isinstance(self.ast_object, _ast.match_case) or \
               hasattr(self.ast_object, "body")

        progress = parse(self.ast_object.body)

        if progress.head is not None:
            self.cond_node.connect_yes(progress.head)
            self.extend_tails(progress.tails)

        # always connect a transparent node as the no-path
        virtual_tail = TransparentNode(self.cond_node, connect_params=["no"])
        self.cond_node.connect_no(virtual_tail)
        self.append_tails(virtual_tail)

    def inlineable(self):
        """
        Is this MatchCase inlineable?
        If so, we can inline it into the MatchCondition.
        """
        conn_yes = self.cond_node.connection_yes
        try:
            one_line_body = isinstance(conn_yes, Connection) and \
                            isinstance(conn_yes.next_node, CondYN) and \
                            isinstance(conn_yes.next_node.sub, Node) and \
                            not isinstance(conn_yes.next_node.sub, NodesGroup) and \
                            not isinstance(conn_yes.next_node.sub, ConditionNode) and \
                            not conn_yes.next_node.sub.connections
        except Exception:
            # print(e)
            one_line_body = False
        return one_line_body

    def simplify(self) -> None:
        warnings.warn("MatchCase.simplify() is buggy, use it with caution.")

        if not self.inlineable():
            return

        try:
            conn_yes = self.cond_node.connection_yes

            assert isinstance(conn_yes, Connection)
            assert isinstance(conn_yes.next_node, CondYN)
            assert isinstance(conn_yes.next_node.sub, Node)

            body = conn_yes.next_node.sub

            simplified = OperationNode(f'{body.node_text} {self.cond_node.node_text}')

            simplified.node_name = self.head.node_name + "inline"
            self.head = simplified
            self.tails = [simplified]

        except AttributeError as e:
            warnings.warn(f"MatchCase.simplify() failed: {e}")
        except AssertionError as e:
            warnings.warn(f"MatchCase.simplify() failed: {e}")


class Match(NodesGroup, AstNode):
    """
    Match is a AstNode for _ast.Match (the `match-case` sentences in python source code)

    This class is a NodesGroup that connects to MatchCondition & its cases.
    """

    def __init__(self, ast_match: _ast_Match_t, **kwargs):
        """
        Construct Match object will make following Node chain:
            Match -> MatchCondition -> (case1) -> case1-path
                                    -> (case2) -> case2-path
                                    ...

        A match-case sentence contains:

            match {subject}:
                case {pattern} if {guard}:
                    {body}
                case ...:
                    ...

        Args:
            **kwargs:

                simplify={True | False}: simplify the one_line_body case?
                                           (Default: True)
                                           See `self.simplify`
        """
        AstNode.__init__(self, ast_match, **kwargs)

        # A Cond for match_case should be represented as "if {subject} match case {pattern}"
        self.subject = ast_match.subject

        # self.head = TransparentNode(self)
        # fuck the multi inheritance,,, my brain is buffer overflowing
        # god bless the jetbrains helped me figure out this overstep
        # well, never mind. I believe that NodesGroup.__init__()
        # is the right way to set it up as well as self.head properly.

        # Each case is a condition node.
        # Since we have not parsed any case body, (nor I want to peek one),
        # here we use a transparent node as the head of the NodesGroup.
        transparent_head = TransparentNode(self)
        NodesGroup.__init__(self, transparent_head)
        assert self.head is transparent_head

        self.cases: List[MatchCase] = []
        self.parse_cases(**kwargs)

        # remove the transparent_head
        try:
            debug(f"Match.__init__() replace head: self.head before: {type(self.head)}: {self.head.__dict__}")
            self.head = self.head.connections[0].next_node
            debug(f"Match.__init__() replace head self.head after: {type(self.head)}: {self.head.__dict__}")
        except IndexError or AttributeError:
            self.head = CommonOperation(ast_match)
            self.tails = [self.head]

        # simplify works not well, so I disable it by default.
        # (it's still possible to call simplify manually, though)
        # if kwargs.get("simplify", True):
        #     self.simplify()

    def parse_cases(self, **kwargs) -> None:
        """
        Parse and Connect cases of the match
        """
        assert isinstance(self.ast_object, _ast.Match) or \
               hasattr(self.ast_object, "cases")

        last_case = self.head  # at first, it's a transparent node
        for match_case in self.ast_object.cases:
            match_case_node = MatchCase(match_case, self.subject, **kwargs)
            last_case.connect(match_case_node)
            last_case = match_case_node
            self.cases.append(match_case_node)

        # connect the last case to the end of the match
        try:
            self.tails.extend(last_case.tails)
        except AttributeError:
            self.tails.append(last_case)

        # if kwargs.get("simplify", True):
        #     self.simplify()

    def simplify(self) -> None:
        """
        simplify the inlineable (one-line body) cases:
            match {subject}:
                case {pattern} if {guard}:
                    one_line_body
        """
        warnings.warn("Match.simplify() is buggy, use it with caution.")

        try:
            for case_node in self.cases:
                if case_node.inlineable():
                    case_node.simplify()
        except AttributeError as e:
            warnings.warn(f"Match.simplify() failed: {e}")


# With Python < 3.10, We have no _ast.Match and _ast.match_case,
# unable to parse match-case sentence. Just trait it as a common sentence.
# That is, unparse the whole match-case sentence, put the result into a OperationNode.
#
# DUCK, with Python 3.7, it is not possible for ast to parse match-case sentence:
#     File "/Users/z/Projects/pyflowchart/pyflowchart/flowchart.py", line 94, in from_code
#       code_ast = ast.parse(code)
#     File "/Users/z/.pyenv/versions/3.7.17/lib/python3.7/ast.py", line 35, in parse
#       return compile(source, filename, mode, PyCF_ONLY_AST)
#     File "<unknown>", line 3
#       match b:
#         ^
#     SyntaxError: invalid syntax
# So, this is in vain.
if sys.version_info < (3, 10):
    Match = CommonOperation

# Sentence: common | func | cond | loop | ctrl
# - func: def
# - cond: if
# - loop: for, while
# - ctrl: break, continue, return, yield, call
# - common: others
# Special sentence: cond | loop | ctrl
# TODO: Try, With

__func_stmts = {
    _ast.FunctionDef: FunctionDef
}

__cond_stmts = {
    _ast.If: If,
    # _ast_Match_t: Match,  # need to check Python version, handle it later manually.
}

__loop_stmts = {
    _ast.For: Loop,
    _ast.While: Loop,
}

__ctrl_stmts = {
    _ast.Break: BreakContinueSubroutine,
    _ast.Continue: BreakContinueSubroutine,
    _ast.Return: Return,
    _ast.Yield: YieldOutput,
    _ast.Call: CallSubroutine,
}

# merge dict: PEP448
__special_stmts = {**__func_stmts, **__cond_stmts, **__loop_stmts, **__ctrl_stmts}


class ParseProcessGraph(NodesGroup):
    """
    ParseGraph is a NodesGroup for parse process result.
    """
    pass


def parse(ast_list: List[_ast.AST], **kwargs) -> ParseProcessGraph:
    """
    parse an ast_list (from _ast.Module/FunctionDef/For/If/etc.body)

    Args:
        ast_list: a list of _ast.AST object

    Keyword Args:
        * simplify: for If & Loop: simplify the one line body cases
        * conds_align: for If: allow the align-next option set for the condition nodes.
            See https://github.com/cdfmlr/pyflowchart/issues/14

    Returns:
        ParseGraph
    """
    head_node = None
    tail_node = None

    process = ParseProcessGraph(head_node, tail_node)

    for ast_object in ast_list:
        # ast_node_class: some special AstNode subclass or CommonOperation by default.
        ast_node_class = __special_stmts.get(type(ast_object), CommonOperation)

        # special case:  Match for Python 3.10+
        if sys.version_info >= (3, 10) and type(ast_object) == _ast_Match_t:
            ast_node_class = Match

        # special case: special stmt as a expr value. e.g. function call
        if type(ast_object) == _ast.Expr:
            if hasattr(ast_object, "value"):
                # Skip docstrings (string literals at the beginning of functions/modules)
                if isinstance(ast_object.value, _ast.Constant) and isinstance(ast_object.value.value, str):
                    continue  # Skip docstring expressions
                elif sys.version_info < (3, 8) and isinstance(ast_object.value, _ast.Str):
                    continue  # Skip docstring expressions for older Python versions
                ast_node_class = __special_stmts.get(type(ast_object.value), CommonOperation)
            else:  # ast_object has no value attribute
                ast_node_class = CommonOperation

        assert issubclass(ast_node_class, AstNode)

        node = ast_node_class(ast_object, **kwargs)

        if head_node is None:  # is the first node
            head_node = node
            tail_node = node
        else:
            tail_node.connect(node)

            # ConditionNode alignment support (Issue#14)
            # XXX: It's ugly to handle it here. But I have no idea, for this moment, to make it ELEGANT.
            if isinstance(tail_node, If) and isinstance(node, If) and \
                    kwargs.get("conds_align", False):
                tail_node.align()

            tail_node = node

    process.set_head(head_node)
    process.append_tails(tail_node)

    return process
