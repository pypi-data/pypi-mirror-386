import networkx as nx
import numpy as np
import re
import pandas as pd
from itertools import product
from pprint import pprint
from scipy import stats
from scipy.interpolate import interp1d
from copy import deepcopy
import matplotlib.pyplot as plt
import logging
from pathlib import Path

logger_parser = logging.getLogger('asdm.parser')
logger_solver = logging.getLogger('asdm.solver')
logger_graph_function = logging.getLogger('asdm.graph_function')
logger_conveyor = logging.getLogger('asdm.conveyor')
logger_data_feeder = logging.getLogger('asdm.data_feeder')
logger_sdmodel = logging.getLogger('asdm.simrun')
logger_model_creation = logging.getLogger('asdm.model_creation')

class VariableLogFilter(logging.Filter):
    """Filter logs to show only specific variables."""
    
    def __init__(self, variable_names=None):
        super().__init__()
        self.variable_names = variable_names or []
        # Convert to set for faster lookup
        self.variable_set = set(self.variable_names)
    
    def filter(self, record):
        # If no variables specified, allow all logs
        if not self.variable_set:
            return True
        
        # Check if any of the target variables are mentioned in the log message
        message = record.getMessage()
        for var_name in self.variable_set:
            if var_name in message:
                return True
        
        return False

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: | %(name)s | %(message)s"
)

logger_parser.setLevel(logging.INFO)
logger_solver.setLevel(logging.INFO)
logger_graph_function.setLevel(logging.INFO)
logger_conveyor.setLevel(logging.INFO)
logger_data_feeder.setLevel(logging.INFO)
logger_sdmodel.setLevel(logging.INFO)
logger_model_creation.setLevel(logging.INFO)

class Node:
    def __init__(self, node_id, operator=None, value=None, operands=None, subscripts=None):
        self.node_id = node_id
        self.operator = operator
        self.value = value
        self.subscripts = subscripts if subscripts is not None else []
        self.operands = operands if operands is not None else []

        # print(f"\nCreated Node: id={self.node_id}, operator={self.operator}, value={self.value}, subscripts={self.subscripts}, operands={[operand.node_id for operand in self.operands]}\n")

    def __str__(self):
        if self.operands:
            return f'{self.operator}({", ".join(str(operand) for operand in self.operands)})' 
        else: 
            if self.subscripts:
                return f'{self.operator}({self.value}{self.subscripts})'
            else:
                return f'{self.operator}({self.value})'

class Parser:
    def __init__(self, dimension_elements={}):
        self.logger = logger_parser
        self.dimension_elements = dimension_elements

        self.numbers = {
            'NUMBER': r'(?<![a-zA-Z0-9)])[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'
        }
        self.special_symbols = {
            'COMMA': r',',
            'LPAREN': r'\(',
            'RPAREN': r'\)',
            'LSPAREN': r'\[',
            'RSPAREN': r'\]',
            'DOT': r'\.',
            'COLON': r':',
        }

        self.logic_operators ={
            'NGT': r'\<\=',
            'NLT': r'\>\=',
            'GT': r'\>',
            'LT': r'\<',
            'EQS': r'\=',
            'AND': r'AND',
            'OR': r'OR',
            'NOT': r'NOT',
            'CONIF': r'IF',
            'CONTHEN': r'THEN',
            'CONELSE': r'ELSE',
            }

        self.arithmetic_operators = {
            'PLUS': r'\+',
            'MINUS': r'\-',
            'TIMES': r'\*',
            'FLOORDIVIDE': r'\/\/',
            'DIVIDE': r'\/',
            'MOD': r'MOD(?=\s)', # there are spaces surronding MOD, but the front space is strip()-ed
            'EXP_OP': r'\^',
        }

        self.functions = { # use lookahead (?=\s*\() to ensure only match INIT( or INIT  ( not INITIAL
            'MIN': r'MIN(?=\s*\()',
            'MAX': r'MAX(?=\s*\()',
            'SAFEDIV': r'SAFEDIV(?=\s*\()',
            'RBINOM': r'RBINOM(?=\s*\()',
            'INIT': r'INIT(?=\s*\()',
            'DELAY': r'DELAY(?=\s*\()',
            'DELAY1': r'DELAY1(?=\s*\()',
            'DELAY3': r'DELAY3(?=\s*\()',
            'SMTH1': r'SMTH1(?=\s*\()',
            'SMTH3': r'SMTH3(?=\s*\()',
            'STEP': r'STEP(?=\s*\()',
            'HISTORY': r'HISTORY(?=\s*\()',
            'LOOKUP': r'LOOKUP(?=\s*\()',
            'SUM': r'SUM(?=\s*\()',
            'PULSE': r'PULSE(?=\s*\()',
            'INT': r'INT(?=\s*\()',
            'LOG10': r'LOG10(?=\s*\()',
            'EXP': r'EXP(?=\s*\()', # e^a is equivalent to EXP(a)
            'LOGISTICBOUND': r'LOGISTICBOUND(?=\s*\()',
            'EXPBOUND': r'EXPBOUND(?=\s*\()',
        }

        self.names = {
            'ABSOLUTENAME': r'"[\s\S]*?"', # match quoted strings
            'NAME': r'[a-zA-Z0-9_£$\?&]*', # add support for £ and $ in variable names
        }

        self.HEAD = "PARSER"

        self.node_id = 0
        self.tokens = []
        self.current_index = 0

    def tokenise(self, s):
        tokens = []
        # remove everything after "{"" (inclusive) which are comments
        s = s.split('{')[0]
        # strip " " (white spaces) around string
        s = s.strip()
        while len(s) > 0:
            self.logger.debug(f"Tokenising: {s} len: {len(s)}")
            for type_name, type_regex in (
                self.numbers | \
                self.special_symbols | \
                self.logic_operators | \
                self.arithmetic_operators | \
                self.functions | \
                self.names
                ).items():
                m = re.match(pattern=type_regex, string=s)
                if m:
                    token = m[0]
                    if token[0] == "\"" and token[-1] == "\"": # strip quotation marks from matched string
                        token = token[1:-1]
                    if type_name == 'ABSOLUTENAME':
                        type_name = 'NAME'

                    if token in self.dimension_elements.keys():
                        tokens.append(['DIMENSION', token])
                        s = s[m.span()[1]:].strip()
                    else:
                        if type_name in self.functions:
                            tokens.append(['FUNC', token])
                        else:
                            tokens.append([type_name, token])
                        s = s[m.span()[1]:].strip()
                    break
        
        return tokens
    
    def parse(self, expression, plot=False):
        # remove \n in the expression
        expression = expression.replace('\n', ' ')

        self.logger.debug("")
        self.logger.debug(f"Starting parse of expression: {expression}")
        self.tokens = self.tokenise(expression)
        self.logger.debug(f"Tokens: {self.tokens}")
        
        ast = self.parse_statement()
        if self.current_index != len(self.tokens):
            raise ValueError(f"Unexpected end of parsing of expression {expression} at index {self.current_index} of tokens {self.tokens}")
        self.logger.debug("Completed parse")
        self.logger.debug(f"AST: {ast}")
        
        # create ast graph
        ast_graph = nx.DiGraph()
        node_labels = {}

        def add_nodes_and_edges(current_node, parent=None):
            ast_graph.add_node(
                current_node.node_id, 
                operator=current_node.operator, 
                value=current_node.value,
                subscripts=current_node.subscripts,
                operands=[operand.node_id for operand in current_node.operands]
                )
            if parent is not None:
                ast_graph.add_edge(
                    parent.node_id, current_node.node_id
                    )
                

            label_node_id = str(current_node.node_id)
            label_node_op = 'operator:\n' + str(current_node.operator)
            if len(current_node.operands) > 0:
                label_node_operands = 'operands:\n' + str([operand.node_id for operand in current_node.operands])
            elif current_node.subscripts:
                label_node_operands = str(current_node.value)+str(current_node.subscripts)
            elif current_node.value:
                label_node_operands = str(current_node.value)
            else:
                label_node_operands = ''
            node_labels[current_node.node_id] = label_node_id+'\n'+ label_node_op+'\n'+ label_node_operands
            for operand in current_node.operands:
                add_nodes_and_edges(operand, current_node)

        add_nodes_and_edges(ast)

        ast_graph.add_node('root')
        ast_graph.add_edge('root', ast.node_id)
        node_labels['root'] = 'root'

        self.logger.debug(f"AST_graph {ast_graph.nodes.data(True)}")

        if plot:
            pos = nx.nx_agraph.graphviz_layout(ast_graph, prog="dot")
            plt.figure(figsize=(12, 8))
            nx.draw(ast_graph, pos, labels=node_labels, with_labels=True, node_size=500, node_color="lightblue", font_size=9, font_weight="bold", arrows=True)
            plt.title("AST Visualization")
            plt.show()
        
        # reset parser state
        self.node_id = 0
        self.tokens = []
        self.current_index = 0

        return ast_graph
    
    def parse_statement(self):
        self.logger.debug("")
        self.logger.debug(f"parse_statement    {self.tokens[self.current_index:]}")
        """Parse a statement. The statement could be an IF-THEN-ELSE statement or an expression."""
        if self.tokens[self.current_index][0] == 'CONIF':
            self.current_index += 1
            condition = self.parse_statement()
            if self.tokens[self.current_index][0] == 'CONTHEN':
                self.current_index += 1
                then_branch = self.parse_statement()
                if self.tokens[self.current_index][0] == 'CONELSE':
                    self.current_index += 1
                    else_branch = self.parse_statement()
                    self.node_id += 1
                    return Node(node_id=self.node_id, operator='CON', operands=[condition, then_branch, else_branch])
                else:
                    raise ValueError(f"Expected ELSE, got {self.tokens[self.current_index]}")
            else:
                raise ValueError(f"Expected THEN, got {self.tokens[self.current_index]}")
        return self.parse_expression()

    def parse_expression(self):
        """Parse an expression."""
        self.logger.debug(f"parse_expression   {self.tokens[self.current_index:]}")
        return self.parse_or_expression()

    def parse_or_expression(self):
        """Parse an or expression."""
        self.logger.debug(f"parse_or_expr      {self.tokens[self.current_index:]}")
        nodes = [self.parse_and_expression()]
        while self.current_index < len(self.tokens) and self.tokens[self.current_index][0] == 'OR':
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = nodes.pop()
            right = self.parse_and_expression()
            self.node_id += 1
            nodes.append(Node(node_id=self.node_id, operator=op[0], operands=[left, right]))
        return nodes[0]

    def parse_and_expression(self):
        """Parse an and expression."""
        self.logger.debug(f"parse_and_expr     {self.tokens[self.current_index:]}")
        nodes = [self.parse_not_expression()]
        while self.current_index < len(self.tokens) and self.tokens[self.current_index][0] == 'AND':
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = nodes.pop()
            right = self.parse_not_expression()
            self.node_id += 1
            nodes.append(Node(node_id=self.node_id, operator=op[0], operands=[left, right]))
        return nodes[0]
    
    def parse_not_expression(self):
        """Parse a NOT expression."""
        self.logger.debug(f"parse_not_expr     {self.tokens[self.current_index:]}")
        if self.tokens[self.current_index][0] == 'NOT':
            self.current_index += 1
            self.node_id += 1
            return Node(node_id=self.node_id, operator='NOT', operands=[self.parse_statement()])
        return self.parse_compare_expression()
    
    def parse_compare_expression(self):
        """Parse a comparison expression."""
        self.logger.debug(f"parse_compare_expr {self.tokens[self.current_index:]}")
        node = self.parse_arith_expression()
        if self.current_index < len(self.tokens) and self.tokens[self.current_index][0] in ['GT', 'LT', 'EQS', 'NGT', 'NLT']:
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = node
            right = self.parse_arith_expression()
            self.node_id += 1
            return Node(node_id=self.node_id, operator=op[0], operands=[left, right])
        return node

    def parse_arith_expression(self):
        """Parse an expression for '+' and '-' with lower precedence."""
        self.logger.debug(f"parse_arith_expr   {self.tokens[self.current_index:]}")
        nodes = [self.parse_mod()]
        while self.current_index < len(self.tokens) and self.tokens[self.current_index][0] in ['PLUS', 'MINUS']:
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = nodes.pop()
            right = self.parse_mod()
            self.node_id += 1
            nodes.append(Node(node_id=self.node_id, operator=op[0], operands=[left, right]))
        return nodes[0]
    
    def parse_mod(self):
        """Parse a mod operation."""
        self.logger.debug(f"parse_mod          {self.tokens[self.current_index:]}")
        nodes = [self.parse_term()]
        while self.current_index < len(self.tokens) and self.tokens[self.current_index][0] == 'MOD':
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = nodes.pop()
            right = self.parse_term()
            self.node_id += 1
            nodes.append(Node(node_id=self.node_id, operator=op[0], operands=[left, right]))
        return nodes[0]

    def parse_term(self):
        """Parse a term for '*' and '/' with higher precedence."""
        self.logger.debug(f"parse_term         {self.tokens[self.current_index:]} ")
        nodes = [self.parse_exponent_op()]
        while self.current_index < len(self.tokens) and self.tokens[self.current_index][0] in ['TIMES', 'DIVIDE', 'FLOORDIVIDE']:
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = nodes.pop()
            right = self.parse_exponent_op()
            self.node_id += 1
            nodes.append(Node(node_id=self.node_id, operator=op[0], operands=[left, right]))
        return nodes[0]
    
    def parse_exponent_op(self):
        """Parse an EXP_OP (^) operation."""
        self.logger.debug(f"parse_exponent     {self.tokens[self.current_index:]}")
        nodes = [self.parse_dot()]
        while self.current_index < len(self.tokens) and self.tokens[self.current_index][0] == 'EXP_OP':
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = nodes.pop()
            right = self.parse_dot()
            self.node_id += 1
            nodes.append(Node(node_id=self.node_id, operator=op[0], operands=[left, right]))
        return nodes[0]
    
    def parse_dot(self):
        """Parse a DOT (.) operation with left-to-right associativity."""
        self.logger.debug(f"parse_dot          {self.tokens[self.current_index:]}")
        nodes = [self.parse_factor()]
        while self.current_index < len(self.tokens) and self.tokens[self.current_index][0] == 'DOT':
            op = self.tokens[self.current_index]
            self.current_index += 1
            left = nodes.pop()
            right = self.parse_factor()
            self.node_id += 1
            nodes.append(Node(node_id=self.node_id, operator=op[0], operands=[left, right]))
        return nodes[0]

    def parse_factor(self):
        """Parse a factor which could be a number, a variable, a function call, or an expression in parentheses."""
        self.logger.debug(f"parse_factor       {self.tokens[self.current_index:]}")
        token = self.tokens[self.current_index]
        
        # Handle unary minus (negation)
        if token[0] == 'MINUS':
            self.current_index += 1
            operand = self.parse_factor()  # Recursively parse the operand
            self.node_id += 1
            return Node(node_id=self.node_id, operator='UNARY_MINUS', operands=[operand])
        # Handle unary plus
        elif token[0] == 'PLUS':
            self.current_index += 1
            operand = self.parse_factor()  # Recursively parse the operand
            self.node_id += 1
            return Node(node_id=self.node_id, operator='UNARY_PLUS', operands=[operand])
        elif token[0] == 'LPAREN':
            self.current_index += 1
            node = self.parse_statement()
            self.current_index += 1  # Skipping the closing ')'
            return node
        elif token[0] == 'FUNC':
            return self.parse_function_call()
        elif token[0] == 'DIMENSION':
            return self.parse_dimension()
        elif token[0] == 'NAME':
            return self.parse_variable()
        elif token[0] == 'NUMBER':
            self.current_index += 1
            self.node_id += 1
            return Node(node_id=self.node_id, operator='IS', value=token[1])
        raise ValueError(f"Unexpected token: {token}")

    def parse_function_call(self):
        """Parse a function call."""
        self.logger.debug(f"parse_function_call{self.tokens[self.current_index:]}")
        func_name = self.tokens[self.current_index]
        self.current_index += 2  # Skipping the function name and the opening '('
        args = []
        while self.tokens[self.current_index][0] != 'RPAREN':
            args.append(self.parse_expression())
            if self.tokens[self.current_index][0] == 'COMMA':
                self.current_index += 1  # Skipping the comma
        self.current_index += 1  # Skipping the closing ')'
        self.node_id += 1
        return Node(node_id=self.node_id, operator=func_name[1], operands=args)
    
    def parse_dimension(self):
        """Parse a dimension name."""
        self.logger.debug(f"parse_dimension     {self.tokens[self.current_index:]}")
        dimension_name = self.tokens[self.current_index]
        if dimension_name[0] == 'DIMENSION':
            self.current_index += 1
            self.node_id += 1
            return Node(node_id=self.node_id, operator='DIMENSION', value=dimension_name[1])
        raise ValueError(f"Unexpected token: {dimension_name}")

    def parse_variable(self):
        """Parse a variable. The variable may be subscripted."""
        self.logger.debug(f"parse_variable     {self.tokens[self.current_index:]}")
        var_name = self.tokens[self.current_index][1]
        self.current_index += 1
        if self.current_index < len(self.tokens) and self.tokens[self.current_index][0] == 'LSPAREN':
            subscripts = []
            subscripts_in_token = []
            subscript_in_token = []
            self.current_index += 1 # Skipping the opening '['
            # split subscript tokens by commas
            while self.tokens[self.current_index][0] != 'RSPAREN':
                # in runtime, referring to other element in the same dimension (e.g. another age group) can be done by
                # something like "Age-1", where Age is the dimension name.
                if self.tokens[self.current_index][0] != 'COMMA':
                    subscript_in_token.append(self.tokens[self.current_index]) # collect this token into the current subscript
                else:
                    subscripts_in_token.append(subscript_in_token)
                    subscript_in_token = []
                self.current_index += 1
            subscripts_in_token.append(subscript_in_token) # add the last subscript
            subscripts = subscripts_in_token
            self.current_index += 1 # Skipping the closing ']'
            self.node_id += 1
            return Node(node_id=self.node_id, operator='SPAREN', value=var_name, subscripts=subscripts)
        self.node_id += 1
        return Node(node_id=self.node_id, operator='EQUALS', value=var_name)

class Solver(object):
    def __init__(self, sim_specs=None, dimension_elements=None, var_dimensions=None, name_space=None, graph_functions=None, data_feeder_functions=None):
        self.logger = logger_solver

        self.sim_specs = sim_specs # current_time, initial_time, dt, simulation_time, time_units
        self.dimension_elements = dimension_elements
        self.var_dimensions = var_dimensions
        self.name_space = name_space
        self.graph_functions = graph_functions
        self.data_feeder_functions = data_feeder_functions

        ### Functions ###

        def integer(a):
            return int(a)

        def logic_and(a, b):
            return (a and b)
        
        def logic_or(a, b):
            return (a or b)
        
        def logic_not(a):
            return (not a)
        
        def greater_than(a, b):
            if a > b:
                return True
            elif a <= b:
                return False
            else:
                raise Exception()

        def less_than(a, b):
            if a < b:
                return True
            elif a >= b:
                return False
            else:
                raise Exception()

        def no_greater_than(a, b):
            if a <= b:
                return True
            elif a > b:
                return False
            else:
                raise Exception()

        def no_less_than(a, b):
            if a >= b:
                return True
            elif a < b:
                return False
            else:
                raise Exception()

        def equals(a, b):
            if a == b:
                return True
            elif a != b:
                return False
            else:
                raise Exception

        def plus(a, b):
            try:
                return a + b
            except TypeError as e:
                if type(a) is dict and type(b) is dict:
                    o = dict()
                    for k in a:
                        o[k] = a[k] + b[k]
                    return o
                else:
                    raise e

        def minus(a, b):
            try:
                return a - b
            except TypeError as e:
                if type(a) is dict and type(b) is dict:
                    o = dict()
                    for k in a:
                        o[k] = a[k] - b[k]
                    return o
                elif type(a) is dict and type(b) in [int, float]:
                    o = dict()
                    for k in a:
                        o[k] = a[k] - b
                    return o
                elif type(a) in [int, float] and type(b) is dict:
                    o = dict()
                    for k in b:
                        o[k] = a - b[k]
                    return o
                else:
                    raise e

        def unary_minus(a):
            """Unary minus operator (negation)"""
            try:
                return -a
            except TypeError as e:
                if type(a) is dict:
                    o = dict()
                    for k in a:
                        o[k] = -a[k]
                    return o
                else:
                    raise e

        def unary_plus(a):
            """Unary plus operator"""
            try:
                return +a
            except TypeError as e:
                if type(a) is dict:
                    o = dict()
                    for k in a:
                        o[k] = +a[k]
                    return o
                else:
                    raise e

        def times(a, b):
            try:
                return a * b
            except TypeError as e:
                if type(a) is dict and type(b) is dict:
                    o = dict()
                    for k in a:
                        o[k] = a[k] * b[k]
                    return o
                elif type(a) is dict and type(b) in [int, float, np.float64]:
                    o = dict()
                    for k in a:
                        o[k] = a[k] * b
                    return o
                elif type(a) in [int, float, np.float64] and type(b) is dict:
                    o = dict()
                    for k in b:
                        o[k] = a * b[k]
                    return o
                else:
                    raise e

        def divide(a, b):
            """ Safely divide a by b, handling scalars and dictionaries, with logging for division by zero. """
            
            def safe_div(x, y, key=None):
                """ Helper function to safely divide x by y and log warnings if y is zero. """
                if y == 0:
                    msg = f"Warning: Divide by zero encountered in divide({x}, {y}), returning 0"
                    if key is not None:
                        msg += f" for subscript '{key}'"
                    print(msg)
                    return 0
                return x / y

            # Scalar / Scalar
            if isinstance(a, (int, float, np.float64)) and isinstance(b, (int, float, np.float64)):
                return safe_div(a, b)

            # Dictionary / Dictionary
            if isinstance(a, dict) and isinstance(b, dict):
                return {k: safe_div(a[k], b.get(k, 1), k) for k in a}

            # Dictionary / Scalar
            if isinstance(a, dict) and isinstance(b, (int, float, np.float64)):
                return {k: safe_div(a[k], b, k) for k in a}

            # Scalar / Dictionary
            if isinstance(a, (int, float, np.float64)) and isinstance(b, dict):
                return {k: safe_div(a, b[k], k) for k in b}

            # Unsupported types
            self.logger.error(f"TypeError in divide(): Unsupported types {type(a)} and {type(b)}")
            raise TypeError(f"Unsupported types for division: {type(a)}, {type(b)}")
        
        def floor_divide(a, b):
            try:
                return a // b
            except TypeError as e:
                if type(a) is dict and type(b) is dict:
                    # self.logger.debug('    '*self.id_level+'[ '+var_name+' ] ', 'a//b', a, b)
                    o = dict()
                    for k in a:
                        o[k] = a[k] // b[k]
                    return o
                elif type(a) is dict and type(b) in [int, float, np.float64]:
                    o = dict()
                    for k in a:
                        o[k] = a[k] // b
                    return o
                elif type(a) in [int, float, np.float64] and type(b) is dict:
                    o = dict()
                    for k in b:
                        o[k] = a // b[k]
                    return o
                else:
                    raise e
        
        def safe_div(a, b, c=0):
            if b == 0:
                return c
            else:
                return a / b

        def mod(a, b):
            try:
                return a % b
            except TypeError as e:
                if type(a) is dict and type(b) is dict:
                    # self.logger.debug('    '*self.id_level+'[ '+var_name+' ] ', 'a % b', a, b)
                    o = dict()
                    for k in a:
                        o[k] = a[k] % b[k]
                    return o
                elif type(a) is dict and type(b) in [int, float, np.float64]:
                    o = dict()
                    for k in a:
                        o[k] = a[k] % b
                    return o
                elif type(a) in [int, float, np.float64] and type(b) is dict:
                    o = dict()
                    for k in b:
                        o[k] = a % b[k]
                    return o
                else:
                    raise e
                
        def exp(a, b):
            return a ** b
        
        def exp_e(a):
            return np.e ** a

        def con(a, b, c):
            if a:
                return b
            else:
                return c

        def step(stp, time):
            # self.logger.debug('step:', stp, time)
            if sim_specs['current_time'] >= time:
                # self.logger.debug('step out:', stp)
                return stp
            else:
                # self.logger.debug('step out:', 0)
                return 0
            
        def pulse(volume, first_pulse=None, interval=None):
            if first_pulse is None:
                    first_pulse = sim_specs['initial_time']
            if interval is None:
                if sim_specs['current_time'] >= first_pulse: # pulse for all dt after fist pulse
                    return volume / sim_specs['dt']
                else:
                    return 0
            elif interval == 0 or interval > sim_specs['simulation_time']: # only one pulse
                if sim_specs['current_time'] == first_pulse:
                    return volume / sim_specs['dt']
                else:
                    return 0
            else:
                if (sim_specs['current_time'] >= first_pulse) and (sim_specs['current_time'] - first_pulse) % interval == 0: # pulse every interval
                    return volume / sim_specs['dt']
                else:
                    return 0
            
        def rbinom(n, p):
            s = stats.binom.rvs(int(n), p, size=1)[0]
            return float(s) # TODO: something is wrong here - the dimension of s goes high like [[[[30]]]] if not float()ed.
        
        def log10(a):
            return np.log10(a)
        
        def colon_range(start_operand, end_operand):
            """Handle colon operator for range selection like A34:A94"""
            # This will return a range representation that can be used by the solver
            # For now, return a tuple representing the range
            return (start_operand, end_operand)
        
        def logisticbound(yfrom, yto, x, xmiddle, speed, xstart=None, xfinish=None):
            """
            LOGISTICBOUND function: transitions from yfrom to yto when x goes from xstart to xfinish
            following a logistic (s-shaped) curve with given speed.
            
            Parameters:
            - yfrom: starting y value
            - yto: ending y value  
            - x: current x value
            - xmiddle: x value at the middle of the transition (inflection point)
            - speed: controls the steepness of the curve (higher = steeper)
            - xstart: starting x value (optional, defaults to -infinity)
            - xfinish: ending x value (optional, defaults to +infinity)
            
            Returns the y value on the logistic curve at position x
            """
            import numpy as np
            
            # Handle optional parameters
            if xstart is not None and x <= xstart:
                return yfrom
            if xfinish is not None and x >= xfinish:
                return yto
            
            # Calculate the logistic function
            # Standard logistic: 1 / (1 + exp(-speed * (x - xmiddle)))
            # Scaled and shifted: yfrom + (yto - yfrom) * logistic
            try:
                logistic_value = 1.0 / (1.0 + np.exp(-speed * (x - xmiddle)))
                result = yfrom + (yto - yfrom) * logistic_value
                return result
            except (OverflowError, ZeroDivisionError):
                # Handle extreme values
                if x < xmiddle:
                    return yfrom
                else:
                    return yto
        
        def expbound(yfrom, yto, x, exponent, xstart, xfinish):
            """
            EXPBOUND function: transitions from yfrom to yto when x goes from xstart to xfinish
            following an exponential curve with the given exponent.
            
            Parameters:
            - yfrom: starting y value
            - yto: ending y value  
            - x: current x value
            - exponent: controls the shape of the exponential curve
            - xstart: starting x value
            - xfinish: ending x value
            
            Returns the y value on the exponential curve at position x
            
            The behavior depends on the exponent:
            - exponent = 0: linear transition
            - exponent > 0: slow near xstart, fast near xfinish  
            - exponent < 0: fast near xstart, slow near xfinish
            """
            import numpy as np
            
            # Handle boundary conditions
            if x <= xstart:
                return yfrom
            if x >= xfinish:
                return yto
            
            # Normalize x to [0, 1] range
            normalized_x = (x - xstart) / (xfinish - xstart)
            
            try:
                if exponent == 0:
                    # Linear interpolation when exponent is 0
                    exponential_value = normalized_x
                else:
                    # Exponential transformation
                    # Formula: (exp(exponent * normalized_x) - 1) / (exp(exponent) - 1)
                    if abs(exponent) < 1e-10:  # Very small exponent, treat as linear
                        exponential_value = normalized_x
                    else:
                        exponential_value = (np.exp(exponent * normalized_x) - 1) / (np.exp(exponent) - 1)
                
                # Scale and shift to get final result
                result = yfrom + (yto - yfrom) * exponential_value
                return result
                
            except (OverflowError, ZeroDivisionError):
                # Handle extreme values
                if exponent > 0:
                    # For positive exponent, curve starts slow then accelerates
                    if normalized_x < 0.5:
                        return yfrom + (yto - yfrom) * 0.1  # Small progress
                    else:
                        return yfrom + (yto - yfrom) * 0.9  # Most progress
                else:
                    # For negative exponent, curve starts fast then decelerates
                    if normalized_x < 0.5:
                        return yfrom + (yto - yfrom) * 0.9  # Most progress
                    else:
                        return yfrom + (yto - yfrom) * 0.99  # Nearly complete
        
        ### Function mapping ###

        self.built_in_functions = {
            'AND':      logic_and,
            'OR':       logic_or,
            'NOT':      logic_not,
            'GT':       greater_than,
            'LT':       less_than,
            'NGT':      no_greater_than,
            'NLT':      no_less_than,
            'EQS':      equals,
            'PLUS':     plus,
            'UNARY_PLUS': unary_plus,
            'MINUS':    minus,
            'UNARY_MINUS': unary_minus,
            'TIMES':    times,
            'DIVIDE':   divide,
            'FLOORDIVIDE': floor_divide,
            'MIN':      min,
            'MAX':      max,
            'SAFEDIV':  safe_div,
            'CON':      con,
            'STEP':     step,
            'MOD':      mod,
            'RBINOM':   rbinom,
            'PULSE':    pulse,
            'EXP_OP':   exp,
            'EXP': exp_e,
            'INT':      integer,
            'LOG10':    log10,
            'COLON':    colon_range,
            'LOGISTICBOUND': logisticbound,
            'EXPBOUND': expbound,
        }

        self.time_related_functions = [
            'INIT',
            'DELAY',
            'DELAY1',
            'DELAY3',
            'HISTORY',
            'SMTH1',
            'SMTH3',
        ]

        self.array_related_functions = [ # they take variable name as argument, not its value
            'SUM',
        ]

        self.lookup_functions = [
            'LOOKUP'
        ]

        self.custom_functions = {}
        self.time_expr_register = {}
        
        self.id_level = 0

        self.HEAD = "SOLVER"

    def calculate_node(self, var_name, parsed_equation, mode, node_id='root', subscript=None):        
        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v0.0 processing node {node_id}:")

        self.id_level += 1
        
        if type(parsed_equation) is dict:  
            raise Exception(f'Parsed equation should not be a dict. var: {var_name}')

        if node_id == 'root':
            node_id = list(parsed_equation.successors('root'))[0]
        node = parsed_equation.nodes[node_id]
        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] node: {node_id} {node}")
        node_operator = node['operator']
        node_value = node['value']
        node_subscripts_in_token = node['subscripts']
        node_operands = node['operands']
        if node_operator == 'IS':
            value = np.float64(node_value)
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v2 IS: {value}")
        elif node_operator == 'EQUALS':
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operator v3 node_operator {node_operator}")
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operator v3 node_value {node_value}")
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operator v3 node_subscripts_in_token {node_subscripts_in_token}")
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operands v3 node_operands {node_operands}")
            
            # Case 1: node_value is a variable name, e.g. "Population"
            if node_value in self.name_space.keys():
                node_var = node_value
                if subscript:
                    value = self.name_space[node_var]
                    if type(value) is dict:
                        value = value[subscript]
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.1.1 EQUALS: subscript present, variable subscripted {value}")
                    else:
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.1.2 EQUALS: subscript present, variable not subscripted {value}")
                else:
                    value = self.name_space[node_var]
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.2 EQUALS: subscript not present {value}")
                
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3 EQUALS: {value}")
            else:
                raise Exception(f'Name {node_value} is not defined in the name space. var: {var_name}')

        elif node_operator == 'DIMENSION':
            # Case 2: node_value is a dimension name, e.g. "Age"
            if node_value in self.var_dimensions[var_name]: # only consider the dimension of the variable we are calculating
                # In this case, evaluate something like "Age=1" to determine if the current element is the one we are looking for.
                # Our job here is to return the order of the element (we are currently calculating) in the dimension.
                if subscript is not None:
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.3.0 EQUALS: subscript present {subscript}")
                    dimension_order = list(self.var_dimensions[var_name]).index(node_value) # get the index of the dimension name in var_dimensions
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.3.1 EQUALS: dimension {node_value} within {self.var_dimensions[var_name]} order {dimension_order}")
                    try:
                        element_order = self.dimension_elements[node_value].index(subscript[dimension_order])
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.3.2.1 EQUALS: element {subscript[dimension_order]} within {self.var_dimensions[var_name][dimension_order]} order {element_order}, number {element_order + 1}")
                    except ValueError:
                        self.logger.error(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.3.2.2 EQUALS: element {subscript[dimension_order]} not found within dimension: elements {node_value}: {list(self.dimension_elements[node_value])}")
                        raise

                    value = element_order + 1 # +1 because the order starts from 0, but we want to return 1, 2, 3, etc.
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.3.3 EQUALS: value {value}")
                else:
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.3.4 EQUALS: subscript not present")
                    raise Exception(f'Subscript is not provided for dimension {node_value}. var: {var_name}')
            # Raise Exception('Dimension name should not be used as a variable name. var:', node_value)
            else:
                self.logger.error(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.3.5 EQUALS: dimension name {node_value} is not defined in the dimension elements.")
                raise Exception(f'Dimension name {node_value} is not defined in the dimension elements. var: {var_name}')

        elif node_operator == 'DOT': 
            # 20251019 temporary solution for dimension.element access
            # Dimension names are reserved (cannot be used as variable names), but element names are not. We therefore do not give element names a different token type
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.4.0 DOT: operands: {node_operands}")
            dot_dimension = parsed_equation.nodes[node_operands[0]]['value'] # directly access the 'DIMENSION' node
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.4.1 DOT: dimension name: {dot_dimension}")
            dot_element = parsed_equation.nodes[node_operands[1]]['value'] # directly access the 'EQUALS' node
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.4.2 DOT: element name: {dot_element}")
            element_order_number = self.dimension_elements[dot_dimension].index(dot_element) + 1
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v3.4.3 DOT: element order number: {element_order_number}")
            value = element_order_number
        elif node_operator == 'SPAREN': # TODO this part is very dynamic, therefore can be slow.
            var_name = node_value
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1 context subscript {subscript}")
            if node_subscripts_in_token is None: # only var_name; no subscript is specified
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.1")
                # this could be 
                # (1) this variable (var_name) is not subscripted therefore the only value of it should be used;
                # (2) this variable (var_name) is subscripted in the same way as the variable using it (a contextual info is needed and provided in the arg subscript)
                if subscript:
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.1.1")
                    value = self.name_space[var_name][subscript] 
                else:
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.1.2")
                    value = self.name_space[var_name]
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v4.1 Sparen without sub: {value}")
            else: # there are explicitly specified subscripts in oprands like a[b]
                # print('subscripts from node definition', node_subscripts_in_token)
                # print('subscripts from context', subscript)
                # After allowing "Dimention-1" in the subscript, we need to ad-hoc construct the right subscripts to use for retrieving variable value
                # TODO: may need to consider more cases here.
                node_subscripts = []
                for subscript_in_token in node_subscripts_in_token:
                    # Case 1: just a subscript in the context, e.g. a[Element_1]
                    if len(subscript_in_token) == 1 and subscript_in_token[0][0] in ['DIMENSION', 'NAME', 'NUMBER']:
                        node_subscripts.append(subscript_in_token[0][1]) # it's a dimension name, e.g. Age
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.2.1 subscript in token: {subscript_in_token[0][1]} ({subscript_in_token[0][0]})")
                    # Case 2: subscript has in-line referencing to another element in the same dimension, e.g. a[Age-1]
                    elif len(subscript_in_token) == 3 and subscript_in_token[0][0] == 'DIMENSION':
                        # step 1: find out the dimension name
                        dimension_name = subscript_in_token[0][1]
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.2.2.1 dimension name: {dimension_name}")
                        elements = self.dimension_elements[dimension_name]
                        # step 2: find out the offset direction
                        offset_operator = subscript_in_token[1][0]
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.2.2.2 offset operator: {offset_operator}")
                        # step 3: find out the offset amount
                        offset_amount = subscript_in_token[2][1]
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.2.2.3 offset amount: {offset_amount}")
                        
                        # We need to read from the context subscript the current element in the relevant dimension
                        # in case of wrong order in context subscripts, we check every one of them if they belong to elements
                        for context_element in subscript:
                            if context_element in elements:
                                ind_context_element = elements.index(context_element)
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.2.2.4 context element index: {ind_context_element}")
                                if offset_operator == 'MINUS':
                                    ind_new_element = ind_context_element - int(offset_amount)
                                elif offset_operator == 'PLUS':
                                    ind_new_element = ind_context_element + int(offset_amount)
                                else:
                                    raise Exception(f"Invalid offset operator {offset_operator} in subscript {subscript_in_token}.")
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.2.2.5 new element index: {ind_new_element}")
                                new_element = elements[ind_new_element]
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.2.2.6 new element: {new_element}")
                                node_subscripts.append(new_element)
                                break
                    else:
                        raise Exception(f"Invalid length of subscript tokens {subscript_in_token}: {len(subscript_in_token)}, should be 1 or 3.")

                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.3 subscript from node definition: {node_subscripts[:]} subscript from context: {subscript}")
                # prioritise subscript from node definition
                try:
                    subscript_from_definition = tuple(node_subscripts[:]) # use tuple to make it hashable
                    value = self.name_space[var_name][subscript_from_definition]
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.3.1 value{str(value)}")
                except KeyError as e: # subscript in operands looks like a[Dimension_1, Element_1], inference needed
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.3.2 subscript in operands contains dimension name(s)")
                    if subscript: # there's subscript in context
                        subscript_from_definition = node_subscripts[:] # definition is what user put in equation, should take higher priority
                        subscript_from_definition_with_replacement = list()
                        for i in range(len(subscript_from_definition)):
                            if subscript_from_definition[i] in self.var_dimensions[var_name]: # it's sth like Dimension_1 - needed to be replaced by the contextual element as it's not specified
                                dimension_from_definition = subscript_from_definition[i]
                                # now need to find out which element in the context subscript corresponds to this dimension
                                subscript_from_context_index = 0 # search should start from 0, as dimensions from definition and dimensions from context can ba in different orders, e.g., variable itself is [Dim1, Dim2] but referring to another variable subscribed as [Dim2, Dim1]
                                while subscript_from_context_index < len(subscript) and subscript[subscript_from_context_index] not in self.dimension_elements[dimension_from_definition]:
                                    subscript_from_context_index += 1
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.3.2.1 replace {dimension_from_definition} with {subscript[subscript_from_context_index]} from context subscript {subscript}")
                                subscript_from_definition_with_replacement.append(subscript[subscript_from_context_index]) # take the element from context subscript in the same position to replace Dimension_1
                                subscript_from_context_index += 1
                            else: # it's sth like Element_1 - specified by the user, should take priority
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.3.2.2 keep {subscript_from_definition[i]} as is, since it is not in dimension names of this model")
                                subscript_from_definition_with_replacement.append(subscript_from_definition[i]) # add to list directly
                        subscript_from_definition_with_replacement = tuple(subscript_from_definition_with_replacement)
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] a1.3.2.2 {subscript_from_definition_with_replacement}")
                        value = self.name_space[var_name][subscript_from_definition_with_replacement] # try if subscript is Element_1
                    else: # there's no subscript in context
                        raise e
                        
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v4.2 SPAREN with sub: {value}")
        
        elif node_operator in self.built_in_functions.keys(): # plus, minus, con, etc.
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operator v7 Built-in operator: {node_operator}, {node_operands}")
            func_name = node_operator
            function = self.built_in_functions[func_name]
            oprds = []
            for operand in node_operands:
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v7.1 operand {operand}")
                v = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=operand, subscript=subscript)
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v7.2 operand {operand} value {v} {subscript}")
                oprds.append(v)
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v7.3 operands {oprds}")
            value = function(*oprds)
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v7 Built-in operator {node_operator}: {value}")
        
        elif node_operator in self.custom_functions.keys(): # graph functions
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] custom func operator {node_operator}")
            func_name = node_operator
            function = self.custom_functions[func_name]
            oprds = []
            for operand in node_operands:
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operand {operand}")
                v = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=operand, subscript=subscript)
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] value {v}")
                oprds.append(v)
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operands {oprds}")
            value = function(*oprds)
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v8 GraphFunc: {value}")
        
        elif node_operator in self.data_feeder_functions.keys(): # data feeders
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] data feeder operator {node_operator}")
            func_name = node_operator
            function = self.data_feeder_functions[func_name]
            oprds = []
            for operand in node_operands:
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operand {operand}")
                v = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=operand, subscript=subscript)
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] value {v}")
                oprds.append(v)
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] operands {oprds}")
            value = function(*oprds)
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v9 DataFeeder: {value}")

        elif node_operator in self.time_related_functions: # init, delay, etc
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] time-related func. operator: {node_operator} operands {node_operands}")
            func_name = node_operator
            if func_name == 'INIT':
                if tuple([var_name, parsed_equation, node_id, node_operands[0]]) in self.time_expr_register.keys():
                    value = self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])]
                else:
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])] = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                    value = self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])]
            elif func_name == 'DELAY':
                if mode == 'init' and len(node_operands) == 3:
                    # this is 'init' mode with 3 operands, meaning an initial value is specified; in this case, just calculate the initial value, not the other 2 operands.
                    init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])] = init_value
                    value = init_value
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'value'])] = [value]
                else: # 'iter' mode or 'init' mode with 2 oprands
                    # delay time is (1) the constant or (2) initial value of the target variable whose value is used for delay time
                    if tuple([var_name, subscript, node_id, func_name, 'delay_time']) not in self.time_expr_register.keys():
                        delay_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])] = delay_time
                    else:
                        delay_time = self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])]

                    # initial value
                    if tuple([var_name, subscript, node_id, func_name, 'init_value']) not in self.time_expr_register.keys():
                        if len(node_operands) == 3:
                            init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                        elif len(node_operands) == 2:
                            init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                        else:
                            raise Exception('Invalid number of args for DELAY.')
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])] = init_value
                    else:
                        init_value = self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])]
                    
                    # calculate the current value of operand[0] and push it to the register
                    expr_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                    if tuple([var_name, subscript, node_id, func_name, 'value']) in self.time_expr_register.keys():
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'value'])].append(expr_value)
                    else:
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'value'])] = [expr_value]
                    
                    # determin which value to return
                    if (self.sim_specs['current_time'] - self.sim_specs['initial_time']) < delay_time: # (use current - initial_time) because simulation might not start from time 0 (e.g., year 2011)
                        value = init_value
                    else:
                        # take the past value from the stack
                        delay_steps = delay_time / self.sim_specs['dt']
                        value = self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'value'])][-int(delay_steps+1)]
                
            elif func_name == 'DELAY1':
                order = 1
                if mode == 'init' and len(node_operands) == 3:
                    # this is 'init' mode with 3 operands, meaning an initial value is specified; in this case, just calculate the initial value
                    init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])] = init_value
                    # initialize the stocks with init_value
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])] = list()
                    # delay_time needed for initialization
                    delay_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])] = delay_time
                    for i in range(order):
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])].append(delay_time/order*init_value)
                    value = init_value
                else: # 'iter' mode or 'init' mode with 2 operands
                    # delay_time is (1) the constant or (2) initial value of the target variable whose value is used for delay time
                    if tuple([var_name, subscript, node_id, func_name, 'delay_time']) not in self.time_expr_register.keys():
                        delay_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])] = delay_time
                    else:
                        delay_time = self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])]
                    
                    # initial value
                    if tuple([var_name, subscript, node_id, func_name, 'init_value']) not in self.time_expr_register.keys():
                        if len(node_operands) == 3:
                            init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                        elif len(node_operands) == 2:
                            init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                        else:
                            raise Exception('Invalid number of args for DELAY1.')
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])] = init_value
                    else:
                        init_value = self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])]
                    
                    # initialize stocks if not already done
                    if tuple([var_name, subscript, node_id, func_name, 'stocks']) not in self.time_expr_register.keys():
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])] = list()
                        for i in range(order):
                            self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])].append(delay_time/order*init_value)
                    
                    # calculate the current value of operand[0]
                    expr_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                    
                    # compute outflows from each stock
                    outflows = list()
                    for i in range(order):
                        outflows.append(self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][i]/(delay_time/order) * self.sim_specs['dt'])
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][i] -= outflows[i]
                    
                    # compute inflows to each stock
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][0] += expr_value * self.sim_specs['dt']
                    for i in range(1, order):
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][i] += outflows[i-1]
                    
                    value = outflows[-1] / self.sim_specs['dt']

            elif func_name == 'DELAY3':
                order = 3
                if mode == 'init' and len(node_operands) == 3:
                    # this is 'init' mode with 3 operands, meaning an initial value is specified; in this case, just calculate the initial value
                    init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])] = init_value
                    # initialize the stocks with init_value
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])] = list()
                    # delay_time needed for initialization
                    delay_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])] = delay_time
                    for i in range(order):
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])].append(delay_time/order*init_value)
                    value = init_value
                else: # 'iter' mode or 'init' mode with 2 operands
                    # delay_time is (1) the constant or (2) initial value of the target variable whose value is used for delay time
                    if tuple([var_name, subscript, node_id, func_name, 'delay_time']) not in self.time_expr_register.keys():
                        delay_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])] = delay_time
                    else:
                        delay_time = self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'delay_time'])]
                    
                    # initial value
                    if tuple([var_name, subscript, node_id, func_name, 'init_value']) not in self.time_expr_register.keys():
                        if len(node_operands) == 3:
                            init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                        elif len(node_operands) == 2:
                            init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                        else:
                            raise Exception('Invalid number of args for DELAY3.')
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])] = init_value
                    else:
                        init_value = self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'init_value'])]
                    
                    # initialize stocks if not already done
                    if tuple([var_name, subscript, node_id, func_name, 'stocks']) not in self.time_expr_register.keys():
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])] = list()
                        for i in range(order):
                            self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])].append(delay_time/order*init_value)
                    
                    # calculate the current value of operand[0]
                    expr_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                    
                    # compute outflows from each stock
                    outflows = list()
                    for i in range(order):
                        outflows.append(self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][i]/(delay_time/order) * self.sim_specs['dt'])
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][i] -= outflows[i]
                    
                    # compute inflows to each stock
                    self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][0] += expr_value * self.sim_specs['dt']
                    for i in range(1, order):
                        self.time_expr_register[tuple([var_name, subscript, node_id, func_name, 'stocks'])][i] += outflows[i-1]
                    
                    value = outflows[-1] / self.sim_specs['dt']

            elif func_name == 'HISTORY':
                # expr value
                expr_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                if tuple([var_name, parsed_equation, node_id, node_operands[0]]) in self.time_expr_register.keys():
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])].append(expr_value)
                else:
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])] = [expr_value]

                # historical time
                historical_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                if historical_time > self.sim_specs['current_time'] or historical_time < self.sim_specs['initial_time']:
                    value = 0
                else:
                    historical_steps = (historical_time - self.sim_specs['initial_time']) / self.sim_specs['dt']
                    value = self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][int(historical_steps)]

            elif func_name == 'SMTH1':
                # arg values
                order = 1
                expr_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                if type(expr_value) is dict:
                    if subscript is not None:
                        expr_value = expr_value[subscript]
                    else:
                        raise Exception('Invalid subscript.')
                smth_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                if len(node_operands) == 3:
                    init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                elif len(node_operands) == 2:
                    init_value = expr_value
                else:
                    raise Exception('Invalid number of args for SMTH1.')
                
                # register
                if tuple([var_name, parsed_equation, node_id, node_operands[0]]) not in self.time_expr_register.keys():
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])] = list()
                    for i in range(order):
                        self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])].append(smth_time/order*init_value)
                # outflows
                outflows = list()
                for i in range(order):
                    outflows.append(self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][i]/(smth_time/order) * self.sim_specs['dt'])
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][i] -= outflows[i]
                # inflows
                self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][0] += expr_value * self.sim_specs['dt']
                for i in range(1, order):
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][i] += outflows[i-1]

                value = outflows[-1] / self.sim_specs['dt']

            elif func_name == 'SMTH3':
                # arg values
                order = 3
                expr_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[0], subscript=subscript)
                if type(expr_value) is dict:
                    if subscript is not None:
                        expr_value = expr_value[subscript]
                    else:
                        raise Exception('Invalid subscript.')
                smth_time = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                if len(node_operands) == 3:
                    init_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[2], subscript=subscript)
                elif len(node_operands) == 2:
                    init_value = expr_value
                else:
                    raise Exception('Invalid number of args for SMTH3.')
                
                # register
                if tuple([var_name, parsed_equation, node_id, node_operands[0]]) not in self.time_expr_register.keys():
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])] = list()
                    for i in range(order):
                        self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])].append(smth_time/order*init_value)
                # outflows
                outflows = list()
                for i in range(order):
                    outflows.append(self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][i]/(smth_time/order) * self.sim_specs['dt'])
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][i] -= outflows[i]
                # inflows
                self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][0] += expr_value * self.sim_specs['dt']
                for i in range(1, order):
                    self.time_expr_register[tuple([var_name, parsed_equation, node_id, node_operands[0]])][i] += outflows[i-1]

                value = outflows[-1] / self.sim_specs['dt']

            else:
                raise Exception(f'Unknown time-related operator {node_operator}')
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v9 Time-related Func: {value}")
        
        elif node_operator in self.array_related_functions: # Array-RELATED
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10 Array-related func. operator: {node_operator} operands: {node_operands}")
            func_name = node_operator
            if func_name == 'SUM':
                arrayed_target_var_name = parsed_equation.nodes[node_operands[0]]['value']
                arrayed_target_var_subscripts = parsed_equation.nodes[node_operands[0]]['subscripts']
                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] arrayed target var: {arrayed_target_var_name} subscripts: {arrayed_target_var_subscripts}")
                if len(arrayed_target_var_subscripts) == 0: # SUM(Population)
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.1 arrayed target var: {arrayed_target_var_name} all elements in the variable")
                    sum_array = 0
                    for _, sub_val in self.name_space[arrayed_target_var_name].items():
                        sum_array += sub_val
                    value = sum_array
                elif len(arrayed_target_var_subscripts) >= 1: 
                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2 arrayed target var: {arrayed_target_var_name} subscripts: {arrayed_target_var_subscripts}")
                    n_dimensions = len(arrayed_target_var_subscripts)
                    # the idea here is to create an allowed list for each dimension - only those element_combinations with all elements appearing in the corresponding list should be summed
                    list_allowed_elements_per_dimension = []
                    for i in range(n_dimensions):
                        list_allowed_elements_per_dimension.append(list())
                        # which dimension are we talking about?
                        dimension_name = self.var_dimensions[arrayed_target_var_name][i]
                        # which elements does this dimension have?
                        dimension_elements = self.dimension_elements[dimension_name]
                        # what does the token say?
                        dimension_tokens = arrayed_target_var_subscripts[i]
                        # case-1
                        if len(dimension_tokens) == 1: # it's either a specific element like ['NAME', 'A9'] or a * like ['TIMES', '*'] or a dimension like ['DIMENSION', Age]
                            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.1 arrayed target var: {arrayed_target_var_name} dimension: {dimension_name} tokens: {dimension_tokens}")
                            if dimension_tokens[0][1] == '*':
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.1.1 arrayed target var: {arrayed_target_var_name} all elements in dimension: {dimension_name}")
                                # if it's a *, we take all elements
                                list_allowed_elements_per_dimension[i] = dimension_elements
                            elif dimension_tokens[0][0] == 'DIMENSION':
                                dimension_name = dimension_tokens[0][1]
                                # if it's a dimension, there are two cases:
                                # case-1.1: the current variable is not subscripted at all. take all elements in the dimension
                                if subscript is None:
                                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.1.2.1.1 arrayed target var: {arrayed_target_var_name} dimension: {dimension_name} is not subscripted at all, taking all elements in the dimension")
                                    list_allowed_elements_per_dimension[i] = dimension_elements
                                # case-1.2: the current variable (the one that is currently being caculated) is subscripted, but not subscripted with this dimension)
                                # In this case, we take all elements in that dimension
                                elif subscript is not None and dimension_name not in self.var_dimensions[var_name]:
                                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.1.2.2 arrayed target var: {arrayed_target_var_name} dimension: {dimension_name} is not subscripted with this dimension, taking all elements in the dimension")
                                    list_allowed_elements_per_dimension[i] = dimension_elements
                                # case-1.3: the current variable (the one that is currently being caculated) is subscripted with this dimension.
                                # In this case, the dimension should be replaced with the current element in the subscript.
                                elif subscript is not None and dimension_name in self.var_dimensions[var_name]:
                                    self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.1.2.1 arrayed target var: {arrayed_target_var_name} dimension: {dimension_name} is subscripted with this dimension, taking only the element in its subscript")
                                    # find out which element is the current element of dimension_name in the subscript. we have to go through the subscript instead of relying onn the order of the elements in the subscript, to avoid order issues
                                    for element in subscript:
                                        if element in dimension_elements:
                                            list_allowed_elements_per_dimension[i] = [element]
                                            break
                                        else:
                                            raise Exception(f"Element {element} is not in dimension {dimension_name}.")   
                                else:
                                    raise Exception(f"Invalid subscript in dimension {dimension_name}.")
                            else:
                                element_name = dimension_tokens[0][1]
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.1.3 arrayed target var: {arrayed_target_var_name} element: {element_name}")
                                # otherwise, we take the specific element
                                if element_name in dimension_elements:
                                    list_allowed_elements_per_dimension[i] = [element_name]
                                else:
                                    raise Exception(f"Element {element_name} is not in dimension {dimension_name}.")
                        # case-2
                        if len(dimension_tokens) == 3: # it's a range like ['NAME', 'A9'], ['COLON', ':'], ['NAME', 'A14']
                            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.2 arrayed target var: {arrayed_target_var_name} dimension: {dimension_name} tokens: {dimension_tokens}")
                            if dimension_tokens[1][1] == ':' and dimension_tokens[2][0] == 'NAME':
                                start = dimension_tokens[0][1]
                                end = dimension_tokens[2][1]
                                if start in dimension_elements and end in dimension_elements:
                                    list_allowed_elements_per_dimension[i] = dimension_elements[dimension_elements.index(start):dimension_elements.index(end)+1]
                                else:
                                    raise Exception(f"Range {start}:{end} is not valid in dimension {dimension_name}.")
                            else:
                                raise Exception(f"Invalid range syntax in dimension {dimension_name}.")
                    sum_array =0
                    for sub_elements, sub_val in self.name_space[arrayed_target_var_name].items():
                        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.3 adding up arrayed target var: {arrayed_target_var_name} checking: {sub_elements} with value: {sub_val}")
                        add_this = True
                        for i in range(n_dimensions):
                            if sub_elements[i] not in list_allowed_elements_per_dimension[i]:
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.3.1 {sub_elements[i]} not in allowed list {list_allowed_elements_per_dimension[i]} for dimension {self.var_dimensions[arrayed_target_var_name][i]}")
                                add_this = False
                                break
                            else:
                                self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.3.2 {sub_elements[i]} in allowed list {list_allowed_elements_per_dimension[i]} for dimension {self.var_dimensions[arrayed_target_var_name][i]}")
                        if add_this:
                            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.3.3 adding up {sub_elements} with value: {sub_val}")
                            sum_array += sub_val
                            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10.2.3.4 current sum_array: {sum_array}")
                    value = sum_array
            else:
                raise Exception(f'v10 Unknown Array-related function {node_operator}')

            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v10 Array-related Func: {value}")
        
        elif node_operator in self.lookup_functions: # LOOKUP
            self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] Lookup func. operator: {node_operator} operands: {node_operands}")
            func_name = node_operator
            if func_name == 'LOOKUP':
                look_up_func_node_id = node_operands[0]
                look_up_func_name = parsed_equation.nodes[look_up_func_node_id]['value']
                look_up_func = self.graph_functions[look_up_func_name]
                input_value = self.calculate_node(var_name=var_name, parsed_equation=parsed_equation, mode=mode, node_id=node_operands[1], subscript=subscript)
                value = look_up_func(input_value)
            else:
                raise Exception(f'Unknown Lookup function {node_operator}')
        
        else:
            raise Exception(f'Unknown operator {node_operator}')
        
        self.id_level -= 1

        self.logger.debug(f"{'    '*self.id_level}[ {var_name}:{subscript} ] v0.1 value for node {node_id}: {value}")

        return value


class GraphFunc(object):
    def __init__(self, out_of_bound_type, yscale, ypts, xscale=None, xpts=None):
        self.logger = logger_graph_function

        self.out_of_bound_type = out_of_bound_type
        self.yscale = yscale
        self.xscale = xscale
        self.xpts = xpts
        self.ypts = ypts
        self.eqn = None
        
        # Track whether xpts was explicitly provided (for XMILE serialization)
        self._xpts_explicit = xpts is not None
        
        self.initialize()
    
    def initialize(self):
        if self.xpts is None:
            self.xpts = np.linspace(self.xscale[0], self.xscale[1], num=len(self.ypts))
        self.interp_func = interp1d(self.xpts, self.ypts, kind='linear')
        self.interp_func_above = interp1d(self.xpts[-2:], self.ypts[-2:], kind='linear', fill_value='extrapolate')
        self.interp_func_below = interp1d(self.xpts[:2], self.ypts[:2], kind='linear', fill_value='extrapolate')

    def __call__(self, input):
        # input out of xscale treatment:
        if self.out_of_bound_type is None: # default to continuous
            input = max(input, self.xpts[0])
            input = min(input, self.xpts[-1])
            output = float(self.interp_func(input)) # the output (like array([1.])) needs to be converted to float to avoid dimension explosion
            return output
        elif self.out_of_bound_type == 'extrapolate':
            if input < self.xpts[0]:
                output = float(self.interp_func_below(input))
            elif input > self.xpts[-1]:
                output = float(self.interp_func_above(input))
            else:
                output = float(self.interp_func(input))
            return output
        elif self.out_of_bound_type == 'discrete':
            if input < self.xpts[0]:
                return self.ypts[0]
            elif input > self.xpts[-1]:
                return self.ypts[-1]
            else:
                for i, xpt in enumerate(self.xpts):
                    if input < xpt:
                        return self.ypts[i-1]
                return self.ypts[-1]
        else:
            raise Exception(f'Unknown out_of_bound_type {self.out_of_bound_type}')
    
    def overwrite_xpts(self, xpts):
        # if len(self.xpts) != len(xpts):
            # self.logger.debug("Warning: new set of x points have a different length to the old set.")
        self.xpts = xpts
        
    def overwrite_xscale(self, xscale):
        self.xscale = xscale
        self.xpts = None # to auto-infer self.xpts from self.xscale, self.xpts must set to None

    def overwrite_ypts(self, ypts):
        # if len(self.ypts) != len(ypts):
            # self.logger.debug("Warning: new set of y points have a different length to the old set.")
        self.ypts = ypts


class Conveyor(object):
    def __init__(self, length, eqn):
        self.logger = logger_conveyor

        self.length_time_units = length
        self.equation = eqn
        self.length_steps = None # to be decided at runtime
        self.total = 0 # to be decided when initializing stocks
        self.slats = list() # pipe [new, ..., old]
        self.is_initialized = False
        self.leaks = list()
        self.leak_fraction = 0

    def initialize(self, length, value, leak_fraction=None):
        self.total = value
        self.length_steps = length
        if leak_fraction is None or leak_fraction == 0:
            for _ in range(self.length_steps):
                self.slats.append(self.total/self.length_steps)
                self.leaks.append(0)
        else:
            self.leak_fraction = leak_fraction
            n_leak = 0
            for i in range(self.length_steps):
                n_leak += i+1
            # self.logger.debug('Conveyor N total leaks:', n_leak)
            self.output = self.total / (self.length_steps + (n_leak * self.leak_fraction) / ((1-self.leak_fraction)*self.length_steps))
            # self.logger.debug('Conveyor Output:', output)
            leak = self.output * (self.leak_fraction/((1-self.leak_fraction)*self.length_steps))
            # self.logger.debug('Conveyor Leak:', leak)
            # generate slats
            for i in range(self.length_steps):
                self.slats.append(self.output + (i+1)*leak)
                self.leaks.append(leak)
            self.slats.reverse()
        # self.logger.debug('Conveyor initialized:', self.conveyor, '\n')
        self.is_initialized = True

    def level(self):
        return self.total

    # order of execution:
    # 1 Leak from every slat
    #   to do this we need to know the leak for every slat
    # 2 Pop the last slat
    # 3 Input as the first slat

    def leak_linear(self):
        for i in range(self.length_steps):
            self.slats[i] = self.slats[i] - self.leaks[i]
        
        total_leaked = sum(self.leaks)
        self.total -= total_leaked
        return total_leaked
    
    def outflow(self):
        output = self.slats.pop()
        self.total -= output
        self.leaks.pop()
        return output

    def inflow(self, value):
        self.total += value
        self.slats = [value] + self.slats
        self.leaks = [value* self.leak_fraction/self.length_steps]+self.leaks


class Stock(object):
    def __init__(self):
        self.initialized = False


class DataFeeder(object):
    def __init__(self, data, from_time=0, data_dt=1, interpolate=False):
        """
        data: a list

        """
        self.logger = logger_data_feeder
        self.interpolate = interpolate
        self.data_dt = data_dt
        self.from_time =from_time
        self.time_data = dict()
        time = self.from_time
        for d in data:
            self.time_data[time] = d
            time += self.data_dt
        # self.logger.debug(self.time_data)
        self.last_success_time = None

    def __call__(self, current_time): # make a datafeeder callable
        try:
            d = self.time_data[current_time]
            self.last_success_time = current_time
        except KeyError:
            if current_time < self.from_time:
                raise Exception("Current time < external data starting time.")
            elif current_time > list(self.time_data.keys())[-1]:
                raise Exception("Current time > external data ending time.")
            else:
                if self.interpolate:
                    d_0 = self.time_data[self.last_success_time]
                    d_1 = self.time_data[self.last_success_time + self.data_dt]
                    interp_func_2pts = interp1d(
                        [self.last_success_time, self.last_success_time + self.data_dt],
                        [d_0, d_1]
                        )
                    d = interp_func_2pts(current_time)
                else:
                    d = self.time_data[self.last_success_time]
        return(np.float64(d))


class sdmodel(object):
    # equations
    def __init__(self, from_xmile=None, parser_debug_level='info', solver_debug_level='info', simulator_debug_level='info', model_creation_debug_level='info', variable_filter=None):
        # Debug
        self.HEAD = 'ENGINE'
        self.debug_level_trace_error = 0
        self.logger = logger_sdmodel
        self.logger_model_creation = logger_model_creation

        # model debug level
        if simulator_debug_level == 'debug':
            self.logger.setLevel(logging.DEBUG)
        elif simulator_debug_level == 'info':
            self.logger.setLevel(logging.INFO)
        elif simulator_debug_level == 'warning':
            self.logger.setLevel(logging.WARNING)
        elif simulator_debug_level == 'error':
            self.logger.setLevel(logging.ERROR)
        else:
            raise Exception(f'Unknown debug level {simulator_debug_level}')

        # model creation debug level
        if model_creation_debug_level == 'debug':
            self.logger_model_creation.setLevel(logging.DEBUG)
        elif model_creation_debug_level == 'info':
            self.logger_model_creation.setLevel(logging.INFO)
        elif model_creation_debug_level == 'warning':
            self.logger_model_creation.setLevel(logging.WARNING)
        elif model_creation_debug_level == 'error':
            self.logger_model_creation.setLevel(logging.ERROR)
        else:
            raise Exception(f'Unknown debug level {model_creation_debug_level}')

        # sim_specs
        self.sim_specs = {
            'initial_time': 0,
            'current_time': 0,
            'dt': 0.25,
            'simulation_time': 13,
            'time_units' :'Weeks',
        }

        # XMILE preservation (for smart save)
        self._xmile_soup = None  # Full BeautifulSoup object of original XMILE
        self._xmile_views = None  # Views/layout section (unparsed)
        self._xmile_header = None  # Header section (unparsed)
        self._modified_elements = set()  # Track modified variables
        self._xmile_name_mapping = {}  # Map friendly_name -> original_xmile_name
        self._variable_array_format = {}  # Track subscripted variable format: 'parallel' or 'element'
        self._original_equations = {}  # Store original equations before DataFeeder replacement
        
        # Variable documentation and tags
        self.variable_docs = {}  # Map var_name -> documentation text
        self.variable_tags = {}  # Map var_name -> list of tags
        self._modified_docs = set()  # Track variables with modified documentation
        self._modified_tags = set()  # Track variables with modified tags

        # dimensions
        self.var_dimensions = dict() # 'dim1':['ele1', 'ele2']
        self.dimension_elements = dict()
        self.element_names = list() # dimension names can not be used as variable name
        
        # stocks
        self.stocks = dict()
        self.stock_equations = dict()
        self.stock_equations_parsed = dict()
        self.stock_non_negative = dict()
        self.stock_shadow_values = dict() # temporary device to store in/out flows' effect on stocks.
        self.stock_non_negative_temp_value = dict()
        self.stock_non_negative_out_flows = dict()

        # discrete variables
        self.conveyors = dict()
        
        # flow
        self.flow_positivity = dict()
        self.flow_equations = dict()
        self.flow_equations_parsed = dict()

        # connections
        self.stock_flows = dict()
        self.flow_stocks = dict()
        self.leak_conveyors = dict()
        self.outflow_conveyors = dict()
        
        # aux
        self.aux_equations = dict()
        self.aux_equations_parsed = dict()

        # delayed auxiliaries # virtually stocks with an auxiliary appearance and a SMOOTH/DELAY type of definition
        self.delayed_auxiliary_equations = dict()
        self.delayed_auxiliary_equations_parsed = dict()

        # graph_functions
        self.graph_functions = dict()
        self.graph_functions_renamed = dict()

        # variable_values
        self.name_space = dict()
        self.time_slice = dict()
        self.full_result = dict()
        self.full_result_flattened = dict()

        # env variables
        self.env_variables = {
            'TIME': 0,
            'DT': 0.25
        }

        # dependency graphs
        self.dg_init = nx.DiGraph()
        self.dg_iter = nx.DiGraph()
        self.ordered_vars_init = list()
        self.ordered_vars_iter = list()

        # custom functions
        self.custom_functions = {}
        
        # data feeder functions (DataFeeder)
        self.data_feeder_functions = {}
        self.data_feeders_renamed = {}
        
        # state
        self.state = 'created'

        # If the model is based on an XMILE file
        if from_xmile is not None:
            self._load_xmile_model(from_xmile)

        self.name_space.update(self.env_variables)

        # parser
        self.parser = Parser(dimension_elements=self.dimension_elements)

        # parser debug level
        if parser_debug_level == 'debug':
            self.parser.logger.setLevel(logging.DEBUG)
        elif parser_debug_level == 'info':
            self.parser.logger.setLevel(logging.INFO)
        elif parser_debug_level == 'warning':
            self.parser.logger.setLevel(logging.WARNING)
        elif parser_debug_level == 'error':
            self.parser.logger.setLevel(logging.ERROR)
        else:
            raise Exception(f'Unknown debug level {parser_debug_level}')
        
        # solver
        self.solver = Solver(
            sim_specs=self.sim_specs,
            dimension_elements=self.dimension_elements,
            var_dimensions=self.var_dimensions,
            name_space=self.name_space,
            graph_functions=self.graph_functions,
            data_feeder_functions=self.data_feeder_functions,
        )
        
        # solver debug level
        if solver_debug_level == 'debug':
            self.solver.logger.setLevel(logging.DEBUG)
        elif solver_debug_level == 'info':
            self.solver.logger.setLevel(logging.INFO)
        elif solver_debug_level == 'warning':
            self.solver.logger.setLevel(logging.WARNING)
        elif solver_debug_level == 'error':
            self.solver.logger.setLevel(logging.ERROR)
        else:
            raise Exception(f'Unknown debug level {solver_debug_level}')
            
        # Apply variable filter if specified
        if variable_filter:
            self.variable_filter = VariableLogFilter(variable_filter)
            # Apply filter to relevant loggers
            self.solver.logger.addFilter(self.variable_filter)
            self.parser.logger.addFilter(self.variable_filter)
            self.logger_model_creation.addFilter(self.variable_filter)
            self.logger.info(f"Applied variable filter for: {variable_filter}")

    def _load_xmile_model(self, from_xmile):
        """Load and parse an XMILE model file."""
        from pathlib import Path
        xmile_path = Path(from_xmile)
        if not xmile_path.exists():
            raise Exception("Specified model file does not exist.")
            
        # Store the XMILE file path for relative path resolution and for save
        self.xmile_path = xmile_path
            
        with open(xmile_path, encoding='utf-8') as f:
            xmile_content = f.read()
            
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(xmile_content, 'xml')
        
        # Store full soup for smart preservation
        self._xmile_soup = soup
        
        # Extract and store views/layout (unparsed) for preservation
        views = soup.find('views')
        if views:
            self._xmile_views = views
            self.logger_model_creation.debug("Stored views/layout section for preservation")
        
        # Extract and store header (unparsed) for preservation
        header = soup.find('header')
        if header:
            self._xmile_header = header
            self.logger_model_creation.debug("Stored header section for preservation")
        
        # Parse different sections of the XMILE file
        self._parse_sim_specs(soup)
        self._parse_dimensions(soup)
        self._parse_variables(soup)
        self._parse_data(soup)
        
        self.state = 'loaded'

    def _parse_sim_specs(self, soup):
        """Parse simulation specifications from XMILE content."""
        sim_specs_root = soup.find('sim_specs')
        if sim_specs_root is None:
            return
            
        time_units = sim_specs_root.get('time_units')
        sim_start = float(sim_specs_root.find('start').text)
        sim_stop = float(sim_specs_root.find('stop').text)
        sim_duration = sim_stop - sim_start
        
        sim_dt_root = sim_specs_root.find('dt')
        sim_dt = float(sim_dt_root.text)
        if sim_dt_root.get('reciprocal') == 'true':
            sim_dt = 1/sim_dt
        
        self.sim_specs['initial_time'] = sim_start
        self.sim_specs['current_time'] = sim_start
        self.env_variables['TIME'] = sim_start
        self.sim_specs['dt'] = sim_dt
        self.env_variables['DT'] = sim_dt
        self.sim_specs['simulation_time'] = sim_duration
        self.sim_specs['time_units'] = time_units

    def _parse_dimensions(self, soup):
        """Parse dimensions/subscripts from XMILE content."""
        try:
            subscripts_root = soup.find('dimensions')
            if subscripts_root is None:
                return
                
            dimensions = subscripts_root.find_all('dim')
            dims = dict()
            
            for dimension in dimensions:
                name = dimension.get('name')
                try:
                    size = dimension.get('size')
                    dims[name] = [str(i) for i in range(1, int(size)+1)]
                except:
                    elems = dimension.find_all('elem')
                    elem_names = list()
                    for elem in elems:
                        elem_names.append(elem.get('name'))
                    dims[name] = elem_names
                    self.element_names.extend(elem_names)
            self.dimension_elements.update(dims)
        except AttributeError:
            pass

    def _parse_variables(self, soup):
        """Parse variables (stocks, flows, auxiliaries) from XMILE content."""
        variables_root = soup.find('variables')
        if variables_root is None:
            return
            
        stocks = variables_root.find_all('stock')
        flows = variables_root.find_all('flow')
        auxiliaries = variables_root.find_all('aux')
        
        # Create stocks
        for stock in stocks:
            self._create_stock(stock)
            
        # Create auxiliaries
        for auxiliary in auxiliaries:
            self._create_auxiliary(auxiliary)
            
        # Create flows
        for flow in flows:
            self._create_flow(flow)

    def _create_stock(self, stock):
        """Create a stock variable from XMILE stock element."""
        original_name = stock.get('name')
        name = self.name_handler(original_name)
        
        # Store name mapping for round-trip fidelity
        self._xmile_name_mapping[name] = original_name
        
        # Parse and store documentation
        doc_elem = stock.find('doc')
        if doc_elem and doc_elem.string:
            tags, text = self.parse_doc_content(doc_elem.string)
            if text:  # Only store if there's actual text
                self.variable_docs[name] = text
            if tags:  # Only store if there are tags
                self.variable_tags[name] = tags
        
        non_negative = stock.find('non_negative') is not None
        is_conveyor = stock.find('conveyor') is not None
        
        inflows = stock.find_all('inflow')
        outflows = stock.find_all('outflow')
        
        self.add_stock(
            name, 
            equation=self._create_subscripted_equation(stock), 
            non_negative=non_negative,
            is_conveyor=is_conveyor,
            in_flows=[f.text for f in inflows],
            out_flows=[f.text for f in outflows],
        )

    def _create_auxiliary(self, auxiliary):
        """Create an auxiliary variable from XMILE aux element."""
        original_name = auxiliary.get('name')
        name = self.name_handler(original_name)
        
        # Store name mapping for round-trip fidelity
        self._xmile_name_mapping[name] = original_name
        
        # Parse and store documentation
        doc_elem = auxiliary.find('doc')
        if doc_elem and doc_elem.string:
            tags, text = self.parse_doc_content(doc_elem.string)
            if text:  # Only store if there's actual text
                self.variable_docs[name] = text
            if tags:  # Only store if there are tags
                self.variable_tags[name] = tags
        
        # Store original equation text (before potential DataFeeder replacement)
        if auxiliary.find('eqn'):
            eqn_text = auxiliary.find('eqn').text
            if eqn_text:
                self._original_equations[name] = eqn_text.strip()
        
        equation = self._create_subscripted_equation(auxiliary)
        
        # Check if it's a delayed auxiliary
        delay_aux = auxiliary.find('isee:delay_aux')
        if delay_aux is not None:
            self.add_delayed_aux(name, equation=equation)
        else:
            self.add_aux(name, equation=equation)

    def _create_flow(self, flow):
        """Create a flow variable from XMILE flow element."""
        original_name = flow.get('name')
        name = self.name_handler(original_name)
        
        # Store name mapping for round-trip fidelity
        self._xmile_name_mapping[name] = original_name
        
        # Parse and store documentation
        doc_elem = flow.find('doc')
        if doc_elem and doc_elem.string:
            tags, text = self.parse_doc_content(doc_elem.string)
            if text:  # Only store if there's actual text
                self.variable_docs[name] = text
            if tags:  # Only store if there are tags
                self.variable_tags[name] = tags
        
        leak = flow.find('leak') is not None
        non_negative = flow.find('non_negative') is not None
        
        self.add_flow(
            name, 
            equation=self._create_subscripted_equation(flow), 
            leak=leak, 
            non_negative=non_negative
        )

    def _create_subscripted_equation(self, var):
        """Create subscripted equations for variables from XMILE variable element."""
        if var.find('dimensions'):
            return self._create_subscripted_equation_with_dimensions(var)
        else:
            return self._create_simple_equation(var)

    def _create_subscripted_equation_with_dimensions(self, var):
        """Create subscripted equation for variables with dimensions."""
        var_name = self.name_handler(var.get('name'))
        self.var_dimensions[var_name] = list()
        var_dimensions = var.find('dimensions').find_all('dim')
        
        var_dims = dict()
        for dimension in var_dimensions:
            dim_name = dimension.get('name')
            self.var_dimensions[var_name].append(dim_name)
            var_dims[dim_name] = self.dimension_elements[dim_name]
        
        var_subscripted_eqn = dict()
        var_elements = var.find_all('element')
        
        if len(var_elements) != 0:
            # Different equation for each element (element-by-element format)
            self._variable_array_format[var_name] = 'element'
            for var_element in var_elements:
                element_combination_text = var_element.get('subscript')
                elements = self.process_subscript(element_combination_text)
                equation = self._parse_variable_equation(var, var_element)
                var_subscripted_eqn[elements] = equation
        else:
            # All elements share the same equation (parallel format)
            self._variable_array_format[var_name] = 'parallel'
            equation = self._parse_variable_equation(var, None)
            element_combinations = product(*list(var_dims.values()))
            for ect in element_combinations:
                var_subscripted_eqn[ect] = equation
                
        return var_subscripted_eqn

    def _create_simple_equation(self, var):
        """Create equation for variables without dimensions."""
        var_name = self.name_handler(var.get('name'))
        self.var_dimensions[var_name] = None
        return self._parse_variable_equation(var, None)

    def _parse_variable_equation(self, var, var_element=None):
        """Parse the equation for a variable, handling different types (conveyor, graph function, etc.)."""
        # Determine which element to check for equation types
        element_to_check = var_element if var_element is not None else var
        
        if var.find('conveyor'):
            equation_text = element_to_check.find('eqn').text if element_to_check.find('eqn') else var.find('eqn').text
            equation_text = equation_text.strip() if equation_text else equation_text
            length = var.find('len').text.strip() if var.find('len').text else var.find('len').text
            equation = Conveyor(length, equation_text)
        elif element_to_check.find('gf'):
            equation = self._read_graph_function(element_to_check)
            eqn_text = var.find('eqn').text
            equation.eqn = eqn_text.strip() if eqn_text else eqn_text
        elif element_to_check.find('eqn'):
            eqn_text = element_to_check.find('eqn').text
            equation = eqn_text.strip() if eqn_text else eqn_text
        else:
            var_name = self.name_handler(var.get('name'))
            raise Exception(f'No meaningful definition found for variable {var_name}')
            
        return equation

    def _read_graph_function(self, var):
        """Read and create a GraphFunc object from XMILE graph function element."""
        gf = var.find('gf')
        out_of_bound_type = gf.get('type')
        
        if gf.find('xscale'):
            xscale = [
                float(gf.find('xscale').get('min')),
                float(gf.find('xscale').get('max'))
            ]
        else:
            xscale = None
        
        if gf.find('xpts'):
            xpts = [float(t) for t in gf.find('xpts').text.split(',')]
        else:
            xpts = None
        
        if xscale is None and xpts is None:
            raise Exception("GraphFunc: xscale and xpts cannot both be None.")

        yscale = [
            float(gf.find('yscale').get('min')),
            float(gf.find('yscale').get('max'))
        ]
        ypts = [float(t) for t in gf.find('ypts').text.split(',')]

        equation = GraphFunc(
            out_of_bound_type=out_of_bound_type, 
            yscale=yscale, 
            ypts=ypts, 
            xscale=xscale, 
            xpts=xpts
        )
        return equation

    def _parse_data(self, soup):
        """Parse data import/export specifications from XMILE content."""
        data_root = soup.find('data')
        if data_root is None:
            return
            
        # Initialize data storage if not already present
        if not hasattr(self, 'export_specs'):
            self.export_specs = []
        if not hasattr(self, 'import_specs'):
            self.import_specs = []
            
        logger_model_creation.debug("Parsing data import/export specifications")
            
        # Parse export specifications
        exports = data_root.find_all('export')
        for export in exports:
            export_spec = {
                'resource': export.get('resource'),
                'interval': export.get('interval'),
                'precomputed': export.get('precomputed') == 'true',
                'format': export.get('isee:format', 'numbers')
            }
            self.export_specs.append(export_spec)
            logger_model_creation.debug(f"Found export specification: {export_spec['resource']}")
            
        # Parse import specifications
        imports = data_root.find_all('import')
        for import_elem in imports:
            # Skip disabled imports
            if import_elem.get('enabled') == 'false':
                logger_model_creation.debug(f"Skipping disabled import: {import_elem.get('resource')}")
                continue
                
            import_spec = {
                'resource': import_elem.get('resource'),
                'overwrite': import_elem.get('isee:overwrite') == 'true',
                'timevarying': import_elem.get('isee:timevarying') == 'true',
                'orientation': import_elem.get('orientation', 'vertical')
            }
            
            self.import_specs.append(import_spec)
            logger_model_creation.debug(f"Processing import: {import_spec['resource']} (overwrite={import_spec['overwrite']}, timevarying={import_spec['timevarying']})")
            
            # Process the import based on its type
            self._process_import(import_spec)

    def _process_import(self, import_spec):
        """Process a single import specification."""
        try:
            # Resolve resource path - handle relative paths starting with 'r../'
            resource_path = import_spec['resource']
            if resource_path.startswith('r../'):
                # Convert relative path to actual path relative to XMILE file
                xmile_dir = Path(self.xmile_path).parent if hasattr(self, 'xmile_path') else Path('.')
                resource_path = xmile_dir / resource_path[4:]
                resource_path = str(resource_path)
            
            if not Path(resource_path).exists():
                logger_model_creation.error(f"Import file not found: {resource_path}")
                return
                
            logger_model_creation.debug(f"Reading CSV file: {resource_path}")
                
            # Read CSV data and normalize to unified format: columns = variables
            try:
                df = self._read_and_normalize_csv(resource_path, import_spec)
            except Exception as e:
                logger_model_creation.error(f"Error reading CSV file {resource_path}: {e}")
                return
                
            if import_spec['overwrite'] and not import_spec['timevarying']:
                # Case 1: Set parameters (overwrite=true, timevarying=false)
                self._process_parameter_import(df, resource_path)
            elif not import_spec['overwrite'] and import_spec['timevarying']:
                # Case 2: Load time varying values (overwrite=false, timevarying=true)
                self._process_timevarying_import(df, resource_path)
            elif not import_spec['overwrite'] and not import_spec['timevarying']:
                # Case 3: Set parameters without overwrite flag (treat as parameter import)
                logger_model_creation.debug(f"Treating non-overwrite, non-timevarying import as parameter import: {resource_path}")
                self._process_parameter_import(df, resource_path)
            else:
                logger_model_creation.error(f"Unsupported import configuration: overwrite={import_spec['overwrite']}, timevarying={import_spec['timevarying']}")
                
        except Exception as e:
            logger_model_creation.error(f"Error processing import {import_spec['resource']}: {e}")

    def _read_and_normalize_csv(self, resource_path, import_spec):
        """
        Read CSV file and normalize to unified format: columns = variables, rows = observations.
        
        This unifies all CSV formats to have:
        - Columns represent variables 
        - Rows represent observations (time points for time-varying, single values for parameters)
        - First column contains time values for time-varying data (or index for parameters)
        """
        orientation = import_spec.get('orientation', 'vertical')
        is_timevarying = import_spec['timevarying']
        
        if orientation == 'horizontal':
            if is_timevarying:
                # Horizontal time-varying: rows=variables, columns=time
                # After transpose: columns=variables, rows=time (desired format)
                df = pd.read_csv(resource_path).dropna().transpose()

                # Reset index to avoid assuming any column as index
                df = df.reset_index(drop=False)
                
                # Set first row as column headers to remove the index row and make data start at row 0
                df.columns = df.iloc[0]  # Use first row as column names
                df = df.drop(df.index[0])  # Drop the first row
                df = df.reset_index(drop=True)  # Reset index so data starts at 0
                df.columns.name = None  # Remove column name

                logger_model_creation.debug(f"Processed resource path: {resource_path}")
                logger_model_creation.debug(f"Normalized horizontal time-varying CSV: {df.shape} (rows=time, cols=variables)")
                logger_model_creation.debug(f"Normalized horizontal time-varying CSV: \n{df.head()}")
            else:
                # Horizontal parameters: rows=variables with values
                # Transform to: columns=variables, single row=values
                temp_df = pd.read_csv(resource_path, header=None, names=['variable', 'value'])
                # drop empty rows
                temp_df = temp_df.dropna()
                # Pivot to get variables as columns
                df = temp_df.set_index('variable').T
                logger_model_creation.debug(f"Processed resource path: {resource_path}")
                logger_model_creation.debug(f"Normalized horizontal parameter CSV: {df.shape} (single row, cols=variables)")
                logger_model_creation.debug(f"Normalized horizontal parameter CSV: \n{df.head()}")
        else:
            # Vertical orientation (default)
            if is_timevarying:
                # Already in desired format: columns=variables, rows=time
                df = pd.read_csv(resource_path)
                logger_model_creation.debug(f"Processed resource path: {resource_path}")
                logger_model_creation.debug(f"Normalized vertical time-varying CSV: {df.shape} (rows=time, cols=variables)")
                logger_model_creation.debug(f"Normalized vertical time-varying CSV: \n{df.head()}")
            else:
                # Vertical parameters: assume 2-column format (variable, value)
                # Transform to: columns=variables, single row=values  
                temp_df = pd.read_csv(resource_path)
                if len(temp_df.columns) == 2:
                    # Standard 2-column format
                    var_col, val_col = temp_df.columns[0], temp_df.columns[1]
                    df = temp_df.set_index(var_col)[val_col].to_frame().T
                    df.index = [0]  # Ensure single row index
                    logger_model_creation.debug(f"Processed resource path: {resource_path}")
                    logger_model_creation.debug(f"Normalized vertical parameter CSV: {df.shape} (single row, cols=variables)")
                    logger_model_creation.debug(f"Normalized vertical parameter CSV: \n{df.head()}")
                else:
                    # Assume already in correct format
                    df = temp_df
                    logger_model_creation.debug(f"Processed resource path: {resource_path}")
                    logger_model_creation.debug(f"Normalized vertical parameter CSV: {df.shape} (single row, cols=variables)")
                    logger_model_creation.debug(f"Normalized vertical parameter CSV: \n{df.head()}")
        
        return df

    def _process_parameter_import(self, df, resource_path):
        """Process parameter imports (set parameters, replace equations once)."""
        try:
            logger_model_creation.debug(f"Processing parameter import from {resource_path}")
            
            # With unified format: columns = variables, single row = values
            # Process each column as a variable
            for var_name in df.columns:
                # Skip invalid column names
                if pd.isna(var_name) or str(var_name).strip() == '' or str(var_name).lower() in ['nan', 'unnamed']:
                    continue
                
                # Get the value from the first (and typically only) row
                if len(df) > 0:
                    var_value = df[var_name].iloc[0]
                    # Skip if the value itself is NaN
                    if pd.isna(var_value):
                        continue
                else:
                    continue
                    
                var_name_str = str(var_name).strip()
                self._apply_parameter_value(var_name_str, var_value, resource_path)
                    
        except Exception as e:
            logger_model_creation.error(f"Error processing parameter import from {resource_path}: {e}")

    def _apply_parameter_value(self, var_name, var_value, resource_path):
        """Apply a parameter value to a variable with proper arrayed variable handling."""
        if self._is_time_column(var_name):
            return
        try:
            # Parse the value to handle comma separators and other formatting
            parsed_value = self._parse_number(var_value)
            if pd.isna(parsed_value):
                logger_model_creation.error(f"Could not parse parameter value '{var_value}' for {var_name}")
                return
            # Handle subscripted variables (e.g., "variable[subscript]")
            if '[' in var_name and ']' in var_name:
                base_name = var_name.split('[')[0].strip()
                subscript_part = var_name.split('[')[1].split(']')[0].strip()
                processed_name = self.name_handler(base_name)
                
                # Parse subscript (may contain multiple dimensions separated by commas)
                subscript_elements = [elem.strip() for elem in subscript_part.split(',')]
                subscript_tuple = tuple(subscript_elements)
                
                # Check if the variable exists in the model
                variable_found = False
                target_dict = None
                
                for var_dict, var_type in [(self.stock_equations, 'stock'), 
                                         (self.aux_equations, 'auxiliary'), 
                                         (self.flow_equations, 'flow')]:
                    if processed_name in var_dict:
                        target_dict = var_dict
                        variable_found = True
                        logger_model_creation.debug(f"Found {var_type} variable {processed_name} for parameter import")
                        break
                
                if not variable_found:
                    logger_model_creation.error(f"Variable {processed_name} not found in model for parameter import from {resource_path}")
                    return
                
                # Check if this is an arrayed variable
                if isinstance(target_dict[processed_name], dict):
                    # Arrayed variable - check if the subscript exists
                    if subscript_tuple in target_dict[processed_name]:
                        # Use replace_element_equation for proper processing
                        new_equation = {subscript_tuple: str(parsed_value)}
                        self.replace_element_equation(processed_name, new_equation)
                        logger_model_creation.debug(f"Set parameter {processed_name}[{subscript_part}] = {parsed_value}")
                    else:
                        available_keys = list(target_dict[processed_name].keys())
                        logger_model_creation.error(f"Subscript {subscript_tuple} not found for variable {processed_name}. Available: {available_keys}")
                else:
                    logger_model_creation.error(f"Variable {processed_name} is not arrayed but subscript provided: {subscript_part}")
                    
            else:
                # Non-subscripted variable
                processed_name = self.name_handler(var_name)
                
                # Check if the variable exists in the model
                variable_found = False
                
                for var_dict, var_type in [(self.stock_equations, 'stock'), 
                                         (self.aux_equations, 'auxiliary'), 
                                         (self.flow_equations, 'flow')]:
                    if processed_name in var_dict:
                        # Use replace_element_equation for proper processing
                        self.replace_element_equation(processed_name, str(parsed_value))
                        variable_found = True
                        logger_model_creation.debug(f"Set parameter {processed_name} = {parsed_value}")
                        break
                
                if not variable_found:
                    logger_model_creation.error(f"Variable {processed_name} not found in model for parameter import from {resource_path}")
                
        except Exception as e:
            logger_model_creation.error(f"Error applying parameter {var_name} = {var_value}: {e}")

    def _process_timevarying_import(self, df, resource_path):
        """Process time-varying imports (replace equations with DataFeeder objects)."""
        try:
            logger_model_creation.debug(f"Processing time-varying import from {resource_path}")
            
            # Extract time values from DataFrame
            time_values = self._extract_time_values(df, resource_path)
            if time_values is None:
                return
                
            # Get simulation period from sim_specs for missing time handling
            sim_start = self.sim_specs.get('initial_time')
            sim_end = sim_start + self.sim_specs.get('simulation_time')
            sim_dt = self.sim_specs.get('dt')
            
            logger_model_creation.debug(f"Simulation period: {sim_start} to {sim_end} with dt={sim_dt}")
            logger_model_creation.debug(f"Data time range: {min(time_values)} to {max(time_values)}")
                
            # With unified format: all columns are variables (except time column for vertical CSVs)
            # Process each variable column, excluding time columns
            for col in df.columns:
                # Skip time columns for vertical CSVs (horizontal CSVs already have time in index)
                if self._is_time_column(col):
                    continue
                    
                # Skip invalid column names
                if pd.isna(col) or str(col).lower().strip() in ['nan', 'unnamed', '']:
                    continue
                # Extract data for this variable (parse numbers to handle comma separators)
                raw_data = df[col].dropna().values
                data_values = [self._parse_number(val) for val in raw_data]
                # Filter out NaN values that couldn't be parsed
                data_values = [val for val in data_values if not pd.isna(val)]
                
                if len(data_values) == 0:
                    logger_model_creation.error(f"No data found for variable {col} in {resource_path}")
                    continue
                    
                # Handle missing time by processing data to cover simulation period
                processed_data, processed_time_values = self._handle_missing_time(
                    data_values, time_values, sim_start, sim_end, sim_dt, col, resource_path
                )
                
                if len(processed_data) == 0:
                    logger_model_creation.error(f"No valid data after processing for variable {col}")
                    continue
                
                # Determine time step (dt) and starting time from processed data
                if len(processed_time_values) > 1:
                    data_dt = float(processed_time_values[1]) - float(processed_time_values[0])
                    from_time = float(processed_time_values[0])
                else:
                    data_dt = sim_dt
                    from_time = float(processed_time_values[0]) if len(processed_time_values) > 0 else sim_start
                
                # Apply time-varying data to arrayed variables properly
                self._apply_timevarying_data(col, processed_data, from_time, data_dt, resource_path)
                    
        except Exception as e:
            logger_model_creation.error(f"Error processing time-varying import from {resource_path}: {e}")

    def _extract_time_values(self, df, resource_path):
        """Extract time values from DataFrame with unified format."""
        # for every column name, check if it is a time column
        for col in df.columns:
            if self._is_time_column(col):
                time_values = [self._parse_number(val) for val in df[col].values]
                logger_model_creation.debug(f"Using column {col} as time values: {time_values}")
                return time_values
        
        logger_model_creation.error(f"No time values found in {resource_path}")

    def _is_time_column(self, col_name):
        """Check if a column name represents time based on sim_specs time_units."""
        sim_time_units = self.sim_specs.get('time_units', 'time')
        
        # Create list of valid time column names (singular and plural)
        time_col_candidates = []
        if sim_time_units:
            # Add the exact time units
            time_col_candidates.append(sim_time_units.lower())
            # Add singular form (remove 's' if it ends with 's')
            if sim_time_units.lower().endswith('s'):
                time_col_candidates.append(sim_time_units.lower()[:-1])
            # Add plural form (add 's' if it doesn't end with 's')
            else:
                time_col_candidates.append(sim_time_units.lower() + 's')
        
        return col_name.lower() in time_col_candidates

    def _parse_number(self, value):
        """Parse a number that might have comma separators (e.g., '1,234' or '1,234.56')."""
        if pd.isna(value):
            return float('nan')
        
        # Convert to string and handle common formatting
        str_val = str(value).strip()
        
        # Remove quotes if present
        if str_val.startswith('"') and str_val.endswith('"'):
            str_val = str_val[1:-1]
        
        # Remove thousands separators (commas)
        str_val = str_val.replace(',', '')
        
        try:
            return float(str_val)
        except (ValueError, TypeError) as e:
            logger_model_creation.error(f"Could not parse number '{value}': {e}")
            return float('nan')

    def _handle_missing_time(self, data_values, time_values, sim_start, sim_end, sim_dt, variable_name, resource_path):
        """Handle missing time data by interpolation/extrapolation according to simulation period."""
        logger_model_creation.debug(f"Handling missing time for {variable_name}")
        
        # Create time-data pairs and sort by time
        time_data_pairs = list(zip(time_values, data_values))
        time_data_pairs.sort(key=lambda x: x[0])

        sorted_times = [pair[0] for pair in time_data_pairs]
        sorted_data = [pair[1] for pair in time_data_pairs]
        
        # Generate simulation time steps
        sim_times = []
        current_time = sim_start
        while current_time <= sim_end:
            sim_times.append(current_time)
            current_time += sim_dt
            
        # Interpolate/extrapolate data for simulation times
        from scipy.interpolate import interp1d
        
        if len(sorted_times) == 1:
            # Only one data point - use constant extrapolation
            processed_data = [sorted_data[0]] * len(sim_times)
            logger_model_creation.debug(f"Single data point for {variable_name}, using constant value: {sorted_data[0]}")
        else:
            # Multiple data points - use interpolation with constant extrapolation (like Stella)
            # Create interpolation function once for efficiency
            interp_func = interp1d(sorted_times, sorted_data, kind='linear')
            
            processed_data = []
            for t in sim_times:
                if t < sorted_times[0]:
                    # Before first data point - use first value (constant extrapolation)
                    value = sorted_data[0]
                elif t > sorted_times[-1]:
                    # After last data point - use last value (constant extrapolation)
                    value = sorted_data[-1]
                else:
                    # Within data range - use linear interpolation
                    value = float(interp_func(t))
                processed_data.append(value)
            logger_model_creation.debug(f"Interpolated/extrapolated {len(processed_data)} data points for {variable_name} (constant extrapolation beyond bounds)")
        
        return processed_data, sim_times

    def _apply_timevarying_data(self, col_name, data_values, from_time, data_dt, resource_path):
        """Apply time-varying data to arrayed variables with proper key matching."""
        # Handle subscripted variables
        if '[' in col_name and ']' in col_name:
            base_name = col_name.split('[')[0].strip()
            subscript_part = col_name.split('[')[1].split(']')[0].strip()
            processed_name = self.name_handler(base_name)
            
            # Parse subscript (may contain multiple dimensions separated by commas)
            subscript_elements = [elem.strip() for elem in subscript_part.split(',')]
            subscript_tuple = tuple(subscript_elements)
            
            # Check if the variable exists in the model
            variable_found = False
            target_dict = None
            
            for var_dict, var_type in [(self.stock_equations, 'stock'), 
                                     (self.aux_equations, 'auxiliary'), 
                                     (self.flow_equations, 'flow')]:
                if processed_name in var_dict:
                    target_dict = var_dict
                    variable_found = True
                    logger_model_creation.debug(f"Found {var_type} variable {processed_name} for time-varying import")
                    break
            
            if not variable_found:
                logger_model_creation.error(f"Variable {processed_name} not found in model for time-varying import from {resource_path}")
                return
            
            # Check if this is an arrayed variable and if the subscript exists
            if isinstance(target_dict[processed_name], dict):
                if subscript_tuple in target_dict[processed_name]:
                    # Create DataFeeder for this specific subscript
                    data_feeder = DataFeeder(
                        data=data_values,
                        from_time=from_time,
                        data_dt=data_dt,
                        interpolate=True
                    )
                    # Use replace_element_equation for proper processing (don't track as modification)
                    new_equation = {subscript_tuple: data_feeder}
                    self.replace_element_equation(processed_name, new_equation, track_modification=False)
                    logger_model_creation.debug(f"Set time-varying data for {processed_name}[{subscript_part}] with {len(data_values)} data points")
                else:
                    available_keys = list(target_dict[processed_name].keys())
                    logger_model_creation.error(f"Subscript {subscript_tuple} not found for variable {processed_name}. Available: {available_keys}")
            else:
                logger_model_creation.error(f"Variable {processed_name} is not arrayed but subscript provided: {subscript_part}")
                
        else:
            # Non-subscripted variable
            processed_name = self.name_handler(col_name)
            
            # Check if the variable exists in the model
            variable_found = False
            
            for var_dict, var_type in [(self.stock_equations, 'stock'), 
                                     (self.aux_equations, 'auxiliary'), 
                                     (self.flow_equations, 'flow')]:
                if processed_name in var_dict:
                    # Create DataFeeder for the entire variable
                    data_feeder = DataFeeder(
                        data=data_values,
                        from_time=from_time,
                        data_dt=data_dt,
                        interpolate=True
                    )
                    # Use replace_element_equation for proper processing (don't track as modification)
                    self.replace_element_equation(processed_name, data_feeder, track_modification=False)
                    variable_found = True
                    logger_model_creation.debug(f"Set time-varying data for {processed_name} with {len(data_values)} data points")
                    break
            
            if not variable_found:
                logger_model_creation.error(f"Variable {processed_name} not found in model for time-varying import from {resource_path}")

    # utilities
    def name_handler(self, name):
        return name.replace(' ', '_').replace('\\n', '_')
    
    @staticmethod
    def parse_doc_content(doc_text):
        """
        Parse doc content to extract tags and text.
        
        Tags format: ${tag1,tag2,...}\nText content
        
        Args:
            doc_text: Raw doc content from XMILE
            
        Returns:
            tuple: (tags_list, text_content)
                   tags_list: List of tag strings (empty if no tags)
                   text_content: Documentation text (empty string if none)
        """
        if not doc_text:
            return ([], '')
        
        # Check if starts with ${...}
        if doc_text.startswith('${') and '}' in doc_text:
            end_idx = doc_text.index('}')
            tags_str = doc_text[2:end_idx]  # Extract content between ${ and }
            tags = [tag.strip() for tag in tags_str.split(',')]
            
            # Text is after the } and optional newline
            remaining = doc_text[end_idx+1:]
            text = remaining.lstrip('\n')  # Remove leading newline after tags
            
            return (tags, text)
        else:
            # No tags, entire content is text
            return ([], doc_text)
    
    @staticmethod
    def format_doc_content(tags, text):
        """
        Format doc content from tags and text.
        
        Args:
            tags: List of tag strings (can be empty)
            text: Documentation text
            
        Returns:
            Formatted doc content string
        """
        if not tags:
            return text
        
        tags_str = ','.join(tags)
        return f"${{{tags_str}}}\n{text}"
    
    @staticmethod
    def process_subscript(subscript):
        # subscript = subscript.replace(',', '__cmm__').replace(' ', '')
        subscript = tuple(subscript.replace(' ', '').split(','))
        return subscript

    # model building
    def add_stock(self, name, equation, non_negative=True, is_conveyor=False, in_flows=[], out_flows=[]):
        if type(equation) in [int, float, np.int_, np.float64]:
            equation = str(equation)
        self.stock_equations[name] = equation
        self.stock_non_negative[name] = non_negative
        connections = dict()
        if len(in_flows) != 0:
            connections['in'] = in_flows
        if len(out_flows) != 0:
            connections['out'] = out_flows
        self.stock_flows[name] = connections

        for in_flow in in_flows:
            if in_flow not in self.flow_stocks:
                self.flow_stocks[in_flow] = dict()
            self.flow_stocks[in_flow]['to'] = name
        for out_flow in out_flows:
            if out_flow not in self.flow_stocks:
                self.flow_stocks[out_flow] = dict()
            self.flow_stocks[out_flow]['from'] = name
        
        self.stocks[name] = Stock()

        self.state = 'loaded'
    
    def add_flow(self, name, equation, leak=None, non_negative=False):
        if type(equation) in [int, float, np.int_, np.float64]:
            equation = str(equation)
        self.flow_positivity[name] = non_negative
        if leak:
            self.leak_conveyors[name] = None # to be filled when parsing the conveyor
        self.flow_equations[name] = equation

        self.state = 'loaded'
    
    def add_aux(self, name, equation):
        if type(equation) in [int, float, np.int_, np.float64]:
            equation = str(equation)
        self.aux_equations[name] = equation

        self.state = 'loaded'

    def add_delayed_aux(self, name, equation):
        if type(equation) in [int, float, np.int_, np.float64]:
            equation = str(equation)
        self.delayed_auxiliary_equations[name] = equation

    def format_new_equation(self, new_equation):
        if type(new_equation) is str:
            pass
        elif type(new_equation) in [int, float, np.int_, np.float64]:
            new_equation = str(new_equation)
        elif type(new_equation) is DataFeeder:
            pass
        elif type(new_equation) is dict:
            pass
        else:
            raise Exception(f'Unsupported new equation {new_equation} type {type(new_equation)}')
        return new_equation

    def replace_element_equation(self, name, new_equation, track_modification=True):
        new_equation = self.format_new_equation(new_equation)
        
        # Track modification for smart save (unless it's a DataFeeder which will be recreated)
        if track_modification and not isinstance(new_equation, DataFeeder):
            # Also check if it's a dict containing DataFeeders
            if isinstance(new_equation, dict):
                # Only track if not all values are DataFeeders
                has_non_datafeeder = any(not isinstance(v, DataFeeder) for v in new_equation.values())
                if has_non_datafeeder:
                    self._modified_elements.add(name)
            else:
                self._modified_elements.add(name)
        
        if name in self.stock_equations:
            if type(new_equation) is dict:
                if type(self.stock_equations[name]) is not dict: # if the old equation is not subscripted
                    self.stock_equations[name] = new_equation # replace the whole equation
                    for k_new, v_new in self.stock_equations[name].items():
                        self.stock_equations[name][k_new] = self.format_new_equation(v_new)
                else:
                    for k_new, v_new in new_equation.items():
                        if k_new in self.stock_equations[name]:
                            self.stock_equations[name][k_new] = self.format_new_equation(v_new)
            else:
                self.stock_equations[name] = new_equation
        elif name in self.flow_equations:
            if type(new_equation) is dict:
                if type(self.flow_equations[name]) is not dict: # if the old equation is not subscripted
                    self.flow_equations[name] = new_equation # replace the whole equation
                    for k_new, v_new in self.flow_equations[name].items():
                        self.flow_equations[name][k_new] = self.format_new_equation(v_new)
                else:
                    for k_new, v_new in new_equation.items():
                        if k_new in self.flow_equations[name]:
                            self.flow_equations[name][k_new] = self.format_new_equation(v_new)
            else:
                self.flow_equations[name] = new_equation
        elif name in self.aux_equations:
            if type(new_equation) is dict:
                if type(self.aux_equations[name]) is not dict: # if the old equation is not subscripted
                    self.aux_equations[name] = new_equation # replace the whole equation
                    for k_new, v_new in self.aux_equations[name].items():
                        self.aux_equations[name][k_new] = self.format_new_equation(v_new)
                else:
                    for k_new, v_new in new_equation.items():
                        if k_new in self.aux_equations[name]:
                            self.aux_equations[name][k_new] = self.format_new_equation(v_new)
            else:
                self.aux_equations[name] = new_equation
        else:
            raise Exception(f'Unable to find {name} in the current model')

        if self.state == 'loaded':
            pass
        elif self.state == 'simulated':
            self.state = 'changed'
    
    def get_variable_doc(self, var_name):
        """
        Get the documentation text for a variable.
        
        Args:
            var_name: Variable name (Python format with underscores)
            
        Returns:
            Documentation text string, or None if no documentation exists
        """
        return self.variable_docs.get(var_name)
    
    def set_variable_doc(self, var_name, doc_text):
        """
        Set the documentation text for a variable.
        
        Args:
            var_name: Variable name (Python format with underscores)
            doc_text: Documentation text (plain text or HTML)
        """
        # Check if variable exists
        if (var_name not in self.stock_equations and 
            var_name not in self.flow_equations and 
            var_name not in self.aux_equations and
            var_name not in self.delayed_auxiliary_equations):
            raise ValueError(f"Variable '{var_name}' not found in model")
        
        self.variable_docs[var_name] = doc_text
        self._modified_docs.add(var_name)
        
        if self.state == 'loaded':
            pass
        elif self.state == 'simulated':
            self.state = 'changed'
    
    def get_variable_tags(self, var_name):
        """
        Get the tags for a variable.
        
        Args:
            var_name: Variable name (Python format with underscores)
            
        Returns:
            List of tag strings, or empty list if no tags exist
        """
        return self.variable_tags.get(var_name, [])
    
    def set_variable_tags(self, var_name, tags):
        """
        Set the tags for a variable.
        
        Args:
            var_name: Variable name (Python format with underscores)
            tags: List of tag strings (e.g., ['data', 'need references'])
        """
        # Check if variable exists
        if (var_name not in self.stock_equations and 
            var_name not in self.flow_equations and 
            var_name not in self.aux_equations and
            var_name not in self.delayed_auxiliary_equations):
            raise ValueError(f"Variable '{var_name}' not found in model")
        
        self.variable_tags[var_name] = tags if tags else []
        self._modified_tags.add(var_name)
        
        if self.state == 'loaded':
            pass
        elif self.state == 'simulated':
            self.state = 'changed'

    def overwrite_graph_function_points(self, name, new_xpts=None, new_xscale=None, new_ypts=None):
        if new_xpts is None and new_xscale is None and new_ypts is None:
            raise Exception("Inputs cannot all be None")

        if name in self.stock_equations:
            graph_func_equation = self.stock_equations[name]
        elif name in self.flow_equations:
            graph_func_equation = self.flow_equations[name]
        elif name in self.aux_equations:
            graph_func_equation = self.aux_equations[name]
        else:
            raise Exception(f'Unable to find {name} in the current model')
        
        if new_xpts is not None:
            # self.logger.debug('Old xpts:', graph_func_equation.xpts)
            graph_func_equation.overwrite_xpts(new_xpts)
            # self.logger.debug('New xpts:', graph_func_equation.xpts)
        
        if new_xscale is not None:
            # self.logger.debug('Old xscale:', graph_func_equation.xscale)
            graph_func_equation.overwrite_xscale(new_xscale)
            # self.logger.debug('New xscale:', graph_func_equation.xscale)
        
        if new_ypts is not None:
            # self.logger.debug('Old ypts:', graph_func_equation.ypts)
            graph_func_equation.overwrite_ypts(new_ypts)
            # self.logger.debug('New ypts:', graph_func_equation.ypts)
        
        graph_func_equation.initialize()

    def parse_equation(self, var, equation):
        if type(equation) is GraphFunc:
            gfunc_name = f'GFUNC{len(self.graph_functions_renamed)}'
            self.graph_functions_renamed[gfunc_name] = equation # just for length ... for now
            self.graph_functions[var] = equation
            self.parser.functions.update({gfunc_name:gfunc_name+r"(?=\()"}) # make name var also a function name and add it to the parser
            self.solver.custom_functions.update({gfunc_name:equation})
            equation = f'{gfunc_name}({equation.eqn})'  # make equation into form like var(eqn), 
                                            # where eqn is the euqaiton whose outcome is the input to GraphFunc var()
                                            # this is also how Vensim handles GraphFunc
            parsed_equation = self.parser.parse(equation)
            return parsed_equation

        elif type(equation) is DataFeeder:
            # Handle DataFeeder similar to GraphFunc but in separate function dictionary
            data_name = f'DATA{len(self.data_feeders_renamed)}'
            self.data_feeders_renamed[data_name] = equation
            # Register in parser as a function
            self.parser.functions.update({data_name: data_name + r"(?=\()"})
            # Register in solver as a data feeder function
            self.data_feeder_functions.update({data_name: equation})
            # Create equation that calls the DataFeeder function with TIME as argument
            equation = f'{data_name}(TIME)'
            parsed_equation = self.parser.parse(equation)
            return parsed_equation
        
        elif type(equation) is Conveyor: # TODO we should also consider arrayed conveyors
            self.conveyors[var] = {
                'conveyor': equation, # the Conveyor object
                'inflow': self.stock_flows[var]['in'],
                'outflow': self.stock_flows[var]['out'],
                'outputflow': [], # this list should have a fixed length of 1
                'leakflow': {},
            }
            for flow in self.stock_flows[var]['out']:
                if flow in self.leak_conveyors:
                    self.conveyors[var]['leakflow'][flow] = 0
                    self.leak_conveyors[flow] = var
                else:
                    self.conveyors[var]['outputflow'].append(flow)
                    self.outflow_conveyors[flow] = var
            equation_length = equation.length_time_units # this is the equation for its length
            parsed_equation_len = self.parser.parse(equation_length)

            equation_init_value = equation.equation # this is the equation for its initial value
            parsed_equation_val = self.parser.parse(equation_init_value)

            return [ # using list to store [len_eqn, val_eqn]. Don't use {'len':xxx, 'val':xxx} to avoid confusion with subscripted equation.
                parsed_equation_len, 
                parsed_equation_val
                ]

        elif type(equation) in [str, int, float, np.int_, np.float64]:
            parsed_equation = self.parser.parse(equation)
            return parsed_equation

        else:
            raise Exception(f'Unsupported equation {equation} type {type(equation)}')
    
    def batch_parse(self, equations, parsed_equations):
        # Debug logic: collect all equations that cannot be parsed and log them, then end the parsing process.
        unparsed_equations = list()
        counter_all_equations = 0
        counter_unparsed_variables = 0
        counter_all_variables = 0

        for var, equation in equations.items():
            # self.logger.debug("Parsing: {}".format(var))
            # self.logger.debug("    Eqn: {}".format(equation))
            
            if type(equation) is dict:
                un_parsed = False
                parsed_equations[var] = dict()
                for k, ks in equation.items():
                    try:
                        parsed_equations[var][k] = self.parse_equation(var=var, equation=ks)
                        counter_all_equations += 1
                    except Exception as e:
                        self.logger.error(f"Error parsing equation for variable {var}: {e}")
                        unparsed_equations.append(((var, k), ks, e))
                        counter_all_equations += 1
                        un_parsed = True
                        exit() # debug line of code: exit on error to examine the log. commented out by default
                if un_parsed:
                    counter_unparsed_variables += 1
            else:
                try:
                    parsed_equations[var] = self.parse_equation(var=var, equation=equation)
                    counter_all_equations += 1
                except Exception as e:
                    self.logger.error(f"Error parsing equation for variable {var}: {e}")
                    unparsed_equations.append((var, equation, e))
                    counter_all_equations += 1
                    counter_unparsed_variables += 1
                    exit() # debug line of code: exit on error to examine the log. commented out by default
            counter_all_variables += 1
        
        if len(unparsed_equations) > 0:
            self.logger.error(f"The following {len(unparsed_equations)} equations (out of {counter_all_equations}) could not be parsed:")
            self.logger.error("")
            for i in range(len(unparsed_equations)):
                var, eqn, error = unparsed_equations[i]
                self.logger.error(f"{i+1} Variable: {var}")
                self.logger.error(f"{i+1} Equation: {eqn}")
                self.logger.error(f"{i+1} Error: {error}")
                self.logger.error("")
            raise Exception(f"Parsing failed for {len(unparsed_equations)} equations out of {counter_all_equations} ({counter_unparsed_variables} variables out of {counter_all_variables}). See logs for details.")

    def parse(self):
        # string equation -> calculation tree

        self.batch_parse(self.stock_equations, self.stock_equations_parsed)
        self.batch_parse(self.flow_equations, self.flow_equations_parsed)
        self.batch_parse(self.aux_equations, self.aux_equations_parsed)
        self.batch_parse(self.delayed_auxiliary_equations, self.delayed_auxiliary_equations_parsed)
        self.state = 'parsed'

    def is_dependent(self, var1, var2):
        # determine if var2 depends directly on var1, i.e., var1 --> var2 or var1 appears in var2's equation
        
        def is_dependent_sub(var1, parsed_equation_var2, dependent=False):
            leafs = [x for x in parsed_equation_var2.nodes() if parsed_equation_var2.out_degree(x)==0]
            for leaf in leafs:
                dependent = False
                operator = parsed_equation_var2.nodes[leaf]['operator']
                if operator == 'EQUALS':
                    value = parsed_equation_var2.nodes[leaf]['value']
                    if value == var1:
                        dependent = True
                elif operator == 'SPAREN': # TODO: This branch needs further test
                    operands = parsed_equation_var2.nodes[leaf]['operands']
                    if operands[0][0] == 'FUNC': # this refers to a subscripted variable like 'a[ele1]'
                        # need to find that 'SPAREN' node
                        var_dependent_node_id = operands[0][2]
                        var_dependent = parsed_equation_var2.nodes[var_dependent_node_id]['operands'][0][1]
                        if var_dependent == var1:
                            dependent = True
                            break
                else:
                    pass
            return dependent

        parsed_equation_var2 = (self.stock_equations_parsed | self.flow_equations_parsed | self.aux_equations_parsed | self.delayed_auxiliary_equations_parsed)[var2]
        if type(parsed_equation_var2) is dict:
            for _, sub_eqn in parsed_equation_var2.items():
                dependent = is_dependent_sub(var1, sub_eqn)
                if dependent:
                    return True
            return False
        else:
            return is_dependent_sub(var1, parsed_equation_var2)

    def calculate_variable(self, var, dg, mode, subscript=None, leak_frac=False, conveyor_init=False, conveyor_len=False):
        if leak_frac or conveyor_init or conveyor_len:
            self.logger.debug(f"Calculating: {var:<15} on subscript {subscript}; flags leak_frac={leak_frac}, conveyor_init={conveyor_init}, conveyor_len={conveyor_len}")
        else:
            self.logger.debug(f"Calculating: {var:<15} on subscript {subscript}")
        # debug
        if var in self.env_variables.keys():
            return
        
        if subscript is not None:
            parsed_equation = (self.stock_equations_parsed | self.flow_equations_parsed | self.aux_equations_parsed | self.delayed_auxiliary_equations_parsed)[var][subscript]
        else:
            parsed_equation = (self.stock_equations_parsed | self.flow_equations_parsed | self.aux_equations_parsed | self.delayed_auxiliary_equations_parsed)[var]

        # DataFeeder - external data
        if type(parsed_equation) is DataFeeder:
            if var not in self.name_space:
                self.name_space[var] = parsed_equation(self.sim_specs['current_time'])

        # A: var is a Conveyor
        if var in self.conveyors:
            # self.logger.debug('Calculating Conveyor {}'.format(var))
            if not (conveyor_init or conveyor_len):
                if not self.conveyors[var]['conveyor'].is_initialized:
                    self.logger.debug(f"    Initializing conveyor {var}")
                    # when initializing, equation of the conveyor needs to be evaluated, using flag conveyor_len=True 
                    self.calculate_variable(var=var, dg=dg, mode=mode, subscript=subscript, conveyor_len=True)
                    conveyor_length = self.conveyors[var]['len']
                    length_steps = int(conveyor_length/self.sim_specs['dt'])
                    
                    # when initializing, equation of the conveyor needs to be evaluated, using flag conveyor_init=True 
                    self.calculate_variable(var=var, dg=dg, mode=mode, subscript=subscript, conveyor_init=True)
                    conveyor_init_value = self.conveyors[var]['val']
                    
                    leak_flows = self.conveyors[var]['leakflow']
                    if len(leak_flows) == 0:
                        leak_fraction = 0
                    else:
                        for leak_flow in leak_flows.keys():
                            self.calculate_variable(var=leak_flow, dg=dg, mode=mode, subscript=subscript, leak_frac=True)
                            leak_fraction = self.conveyors[var]['leakflow'][leak_flow] # TODO multiple leakflows
                    self.conveyors[var]['conveyor'].initialize(length_steps, conveyor_init_value, leak_fraction)
                    
                    # put initialized conveyor value to name_space
                    value = self.conveyors[var]['conveyor'].level()
                    self.name_space[var] = value

                    self.logger.debug(f"    Initialized conveyor {var}")
                
                if var not in self.stock_shadow_values:
                    # self.logger.debug("Updating {} and its outflows".format(var))
                    # self.logger.debug("    Name space1:", self.name_space)
                    # leak
                    for leak_flow, leak_fraction in self.conveyors[var]['leakflow'].items():
                        if leak_flow not in self.name_space: 
                            # self.logger.debug('    Calculating leakflow {} for {}'.format(leak_flow, var))
                            leaked_value = self.conveyors[var]['conveyor'].leak_linear()
                            self.name_space[leak_flow] = leaked_value / self.sim_specs['dt'] # TODO: we should also consider when leak flows are subscripted
                    # out
                    for outputflow in self.conveyors[var]['outputflow']:
                        if outputflow not in self.name_space:
                            # self.logger.debug('    Calculating outflow {} for {}'.format(outputflow, var))
                            outflow_value = self.conveyors[var]['conveyor'].outflow()
                            self.name_space[outputflow] = outflow_value / self.sim_specs['dt']
                    # self.logger.debug("    Name space2:", self.name_space)
                    self.stock_shadow_values[var] = self.conveyors[var]['conveyor'].level()

            elif conveyor_len:
                # self.logger.debug('Calculating LEN for {}'.format(var))
                # it is the intitial value of the conveyoer
                parsed_equation = self.stock_equations_parsed[var][0]
                self.conveyors[var]['len'] = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode)

            elif conveyor_init:
                # self.logger.debug('Calculating INIT VAL for {}'.format(var))
                # it is the intitial value of the conveyoer
                parsed_equation = self.stock_equations_parsed[var][1]
                self.conveyors[var]['val'] = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode)

        # B: var is a normal stock
        elif var not in self.conveyors and var in self.stocks:
            if not self.stocks[var].initialized:
                self.logger.debug(f"    Stock {var} not initialized")
                if type(parsed_equation) is dict:
                    for sub, sub_parsed_equation in parsed_equation.items():
                        sub_value = self.solver.calculate_node(var_name=var, parsed_equation=sub_parsed_equation, mode=mode, subscript=sub)
                        if var not in self.name_space:
                            self.name_space[var] = dict()
                        self.name_space[var][sub] = sub_value
                elif var in self.var_dimensions and self.var_dimensions[var] is not None: # The variable is subscripted but all elements uses the same equation
                    for sub in self.dimension_elements[self.var_dimensions[var]]:
                        sub_value = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode, subscript=sub)
                        if var not in self.name_space:
                            self.name_space[var] = dict()
                        self.name_space[var][sub] = sub_value
                else: # The variable is not subscripted
                    value = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode, subscript=subscript)
                    self.name_space[var] = value
                
                self.stocks[var].initialized = True
                self.stock_shadow_values[var] = deepcopy(self.name_space[var])
                if self.stock_non_negative[var] is True:
                    self.stock_non_negative_temp_value[var] = deepcopy(self.name_space[var])

                self.logger.debug(f"    Stock {var} initialized = {self.name_space[var]}")
            
            else:
                if self.stock_non_negative[var] is True:
                    self.logger.debug(f"    Stock {var} already initialized = {self.name_space[var]}, temp value: {self.stock_non_negative_temp_value[var]}")
                else:
                    self.logger.debug(f"    Stock {var} already initialized = {self.name_space[var]}")
        
        # C: var is a flow
        elif var in self.flow_equations:
            # var is a leakflow. In this case the conveyor needs to be initialized
            if var in self.leak_conveyors:
                if not leak_frac:
                    # if mode is not 'leak_frac', something other than the conveyor is requiring the leak_flow; 
                    # then it is the real value of the leak flow that is requested.
                    # then conveyor needs to be calculated. Otherwise it is the conveyor that requires it 
                    if var not in self.name_space: # the leak_flow is not calculated, which means the conveyor has not been initialized
                        self.calculate_variable(var=self.leak_conveyors[var], dg=dg, mode=mode, subscript=subscript)
                else:
                    # it is the value of the leak_fraction (a percentage) that is requested.    
                    # leak_fraction is calculated using leakflow's equation. 
                    parsed_equation = self.flow_equations_parsed[var]
                    self.conveyors[self.leak_conveyors[var]]['leakflow'][var] = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode)

            elif var in self.outflow_conveyors:
                # requiring an outflow's value triggers the calculation of its connected conveyor
                if var not in self.name_space: # the outflow is not calculated, which means the conveyor has not been initialized
                    self.calculate_variable(var=self.outflow_conveyors[var], dg=dg, mode=mode, subscript=subscript)

            elif var in self.flow_equations: # var is a normal flow
                if var not in self.name_space:
                    if type(parsed_equation) is dict:
                        for sub, sub_parsed_equation in parsed_equation.items():
                            sub_value = self.solver.calculate_node(var_name=var, parsed_equation=sub_parsed_equation, mode=mode, subscript=sub)
                            if var not in self.name_space:
                                self.name_space[var] = dict()
                            self.name_space[var][sub] = sub_value
                    elif var in self.var_dimensions and self.var_dimensions[var] is not None: # The variable is subscripted but all elements uses the same equation
                        for sub in self.dimension_elements[self.var_dimensions[var]]:
                            sub_value = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode, subscript=sub)
                            if var not in self.name_space:
                                self.name_space[var] = dict()
                            self.name_space[var][sub] = sub_value
                    else:
                        value = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode, subscript=subscript)
                        self.name_space[var] = value

                    # control flow positivity by itself
                    if self.flow_positivity[var] is True:
                        if type(self.name_space[var]) is dict:
                            for sub, sub_value in self.name_space[var].items():
                                if sub_value < 0:
                                    self.name_space[var][sub] = np.float64(0)
                                    self.logger.debug(f"    Non-negative flow {var}[{sub}] cannot be negative, set to 0")
                        else:
                            if self.name_space[var] < 0:
                                self.name_space[var] = np.float64(0)
                                self.logger.debug(f'    '+"Non-negative flow {var} cannot be negative, set to 0")

                    # do not use 'value' from here on, use 'self.name_space[var]' instead
                    # check flow attributes for its constraints from non-negative stocks
                    flow_attributes = dg.nodes[var]
                    self.logger.debug(f'    '+'Checking attributes: {flow_attributes}')
                    
                    if 'considered_for_non_negative_stock' in flow_attributes:
                        if flow_attributes['considered_for_non_negative_stock'] is True:
                            flow_to_stock = self.flow_stocks[var]['to']
                            self.logger.debug(f'    ----considering inflow {var} into non-negative stocks {flow_to_stock} whose temp value is {self.stock_non_negative_temp_value[flow_to_stock]}')
                            # this is an in_flow to a non-negative stock and this in_flow should be considered before constraining out_flows using that stock

                            # situation 1:
                            # To prevent a negative inflow from making its "flow-to" stock negative, we need to constrain the inflow
                            # This only happens if the inflow is a biflow
                            if self.flow_positivity[var] is False:
                                if type(self.name_space[var]) is dict:
                                    for sub, sub_value in self.name_space[var].items():
                                        if self.stock_non_negative_temp_value[flow_to_stock][sub] + sub_value * self.sim_specs['dt'] < 0:
                                            self.name_space[var][sub] = self.stock_non_negative_temp_value[flow_to_stock][sub] / self.sim_specs['dt'] *-1 # this outcome is different from Stella, but it is more reasonable. See AwkwardStockFlow.stmx, stock10
                                            self.stock_non_negative_temp_value[flow_to_stock][sub] = np.float64(0)
                                        else:
                                            self.stock_non_negative_temp_value[flow_to_stock][sub] += sub_value * self.sim_specs['dt']
                                elif var in self.var_dimensions and self.var_dimensions[var] is not None: # The variable is subscripted but all elements uses the same equation
                                    for sub in self.stock_non_negative_temp_value[flow_to_stock]:
                                        if self.stock_non_negative_temp_value[flow_to_stock][sub] + self.name_space[var] * self.sim_specs['dt'] < 0:
                                            self.name_space[var] = self.stock_non_negative_temp_value[flow_to_stock][sub] / self.sim_specs['dt'] *-1
                                            self.stock_non_negative_temp_value[flow_to_stock][sub] = np.float64(0)
                                        else:
                                            self.stock_non_negative_temp_value[flow_to_stock][sub] += self.name_space[var] * self.sim_specs['dt']
                                else:
                                    if self.stock_non_negative_temp_value[flow_to_stock] + self.name_space[var] * self.sim_specs['dt'] < 0:
                                        self.name_space[var] = self.stock_non_negative_temp_value[flow_to_stock] / self.sim_specs['dt'] *-1 # this outcome is different from Stella, but it is more reasonable. See AwkwardStockFlow.stmx, stock10
                                        self.stock_non_negative_temp_value[flow_to_stock] = np.float64(0)
                                    else:
                                        self.stock_non_negative_temp_value[flow_to_stock] += self.name_space[var] * self.sim_specs['dt']
                            # situation 2:
                            # Even if the flow is a unidirectional (non-negative) flow, it still can add to the "flow-to" stock's temp value, and this will affect how that stock constrains its out_flows
                            else:
                                self.logger.debug(f'    ----Flow {var} is a unidirectional (non-negative flow), adding its value {self.name_space[var]} to the "flow-to" stock {flow_to_stock} whose temp value is {self.stock_non_negative_temp_value[flow_to_stock]}')
                                if type(self.name_space[var]) is dict:
                                    for sub, sub_value in self.name_space[var].items():
                                        self.stock_non_negative_temp_value[flow_to_stock][sub] += sub_value * self.sim_specs['dt']
                                elif var in self.var_dimensions and self.var_dimensions[var] is not None: # The variable is subscripted but all elements uses the same equation
                                    for sub in self.stock_non_negative_temp_value[flow_to_stock]:
                                        self.stock_non_negative_temp_value[flow_to_stock][sub] += sub_value * self.sim_specs['dt']
                                else:
                                    self.stock_non_negative_temp_value[flow_to_stock] += self.name_space[var] * self.sim_specs['dt']
                            

                    if 'out_from_non_negative_stock' in flow_attributes:
                        out_from_non_negative_stock = flow_attributes['out_from_non_negative_stock']
                        self.logger.debug('    '+f'----considering outflow {var} out from for non-negative stock {out_from_non_negative_stock} whose name_space value is {self.name_space[var]}')
                        
                        # constrain this out_flow
                        self.logger.debug('    '+f'----stock {out_from_non_negative_stock} temp value is {self.stock_non_negative_temp_value[out_from_non_negative_stock]}')
                        if type(self.name_space[var]) is dict:
                            for sub, sub_value in self.name_space[var].items():
                                if self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] - sub_value * self.sim_specs['dt'] < 0:
                                    self.name_space[var][sub] = self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] / self.sim_specs['dt']
                                    self.logger.debug(f'    ----constraining flow {var} for non-negative stocks {out_from_non_negative_stock} to {self.name_space[var]}')
                                    self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] = np.float64(0)
                                else:
                                    self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] -= sub_value * self.sim_specs['dt']
                        elif var in self.var_dimensions and self.var_dimensions[var] is not None: # The variable is subscripted but all elements uses the same equation
                            for sub in self.stock_non_negative_temp_value[out_from_non_negative_stock]:
                                if self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] - self.name_space[var] * self.sim_specs['dt'] < 0:
                                    self.name_space[var] = self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] / self.sim_specs['dt']
                                    self.logger.debug(f'    ----constraining flow {var} for non-negative stocks {out_from_non_negative_stock} to {self.name_space[var]}')
                                    self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] = np.float64(0)
                                else:
                                    self.stock_non_negative_temp_value[out_from_non_negative_stock][sub] -= self.name_space[var] * self.sim_specs['dt']
                        else:                        
                            if self.stock_non_negative_temp_value[out_from_non_negative_stock] - self.name_space[var] * self.sim_specs['dt'] < 0:
                                self.name_space[var] = self.stock_non_negative_temp_value[out_from_non_negative_stock] / self.sim_specs['dt']
                                self.logger.debug(f'    ----constraining flow {var} for non-negative stocks {out_from_non_negative_stock} to {self.name_space[var]}')
                                self.stock_non_negative_temp_value[out_from_non_negative_stock] = np.float64(0)
                            else:
                                self.stock_non_negative_temp_value[out_from_non_negative_stock] -= self.name_space[var] * self.sim_specs['dt']

                    self.logger.debug(f'    ----Flow {var} = {self.name_space[var]}')
                else:
                    self.logger.debug(f'    ----Flow {var} is already in name space.')
                    # raise Warning('Flow {} is already in name space.'.format(var)) # this should not happen, just in case of any bugs as we switched from dynamic calculation to static calculation
        
        # D: var is an auxiliary
        elif var in self.aux_equations:
            if var not in self.name_space:
                if type(parsed_equation) is dict:
                    for sub, sub_parsed_equation in parsed_equation.items():
                        value = self.solver.calculate_node(var_name=var, parsed_equation=sub_parsed_equation, mode=mode, subscript=sub)
                        if var not in self.name_space:
                            self.name_space[var] = dict()
                        self.name_space[var][sub] = value
                elif var in self.var_dimensions and self.var_dimensions[var] is not None: # The variable is subscripted but all elements uses the same equation
                    for sub in self.dimension_elements[self.var_dimensions[var]]:
                        value = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode, subscript=sub)
                        if var not in self.name_space:
                            self.name_space[var] = dict()
                        self.name_space[var][sub] = value
                else:
                    value = self.solver.calculate_node(var_name=var, parsed_equation=parsed_equation, mode=mode, subscript=subscript)
                    self.name_space[var] = value
                self.logger.debug(f'Aux {var} = {value}')
                        
            else:
                pass
        
        else:
            raise Exception(f"Undefined var: {var}")

    def update_stocks(self):
        for stock, in_out_flows in self.stock_flows.items():
            if stock not in self.conveyors: # coneyors are updated separately
                if stock in self.stock_shadow_values:
                    self.logger.debug(f'updating stock {stock} shadow_value is {self.stock_shadow_values[stock]}')
                else:
                    self.logger.debug(f'updating stock {stock} shadow_value not exist, name_space value is {self.name_space[stock]}')
                
                if len(in_out_flows) != 0:
                    for direction, flows in in_out_flows.items():
                        if direction == 'in':
                            for flow in flows:
                                self.logger.debug(f'--inflow {flow} = {self.name_space[flow]}')
                                if stock not in self.stock_shadow_values:
                                    self.stock_shadow_values[stock] = deepcopy(self.name_space[stock])
                                if type(self.stock_shadow_values[stock]) is dict:
                                    if type(self.name_space[flow]) is dict:
                                        for sub, sub_value in self.name_space[flow].items():
                                            self.stock_shadow_values[stock][sub] += sub_value * self.sim_specs['dt']
                                    else:
                                        for sub in self.stock_shadow_values[stock].keys():
                                            self.stock_shadow_values[stock][sub] += self.name_space[flow] * self.sim_specs['dt']
                                else:
                                    self.stock_shadow_values[stock] += self.name_space[flow] * self.sim_specs['dt']
                                self.logger.debug(f'----stock_shadow_value {stock} bcomes {self.stock_shadow_values[stock]}')
                        elif direction == 'out':
                            for flow in flows:
                                self.logger.debug(f'--outflow {flow} = {self.name_space[flow]}')
                                if stock not in self.stock_shadow_values:
                                    self.stock_shadow_values[stock] = deepcopy(self.name_space[stock])
                                if type(self.stock_shadow_values[stock]) is dict:
                                    if type(self.name_space[flow]) is dict:
                                        for sub, sub_value in self.name_space[flow].items():
                                            self.stock_shadow_values[stock][sub] -= sub_value * self.sim_specs['dt']
                                    else:
                                        for sub in self.stock_shadow_values[stock].keys():
                                            self.stock_shadow_values[stock][sub] -= self.name_space[flow] * self.sim_specs['dt']
                                else:
                                    self.stock_shadow_values[stock] -= self.name_space[flow] * self.sim_specs['dt']
                                self.logger.debug(f'    ----stock_shadow_value {stock} becomes {self.stock_shadow_values[stock]}')
                else: # there are obsolete stocks that are not connected to any flows
                    self.logger.debug(f'stock {stock} is not connected to any flows')
                    self.stock_shadow_values[stock] = deepcopy(self.name_space[stock])
                    self.logger.debug(f'stock_shadow_value {stock} remains {self.stock_shadow_values[stock]}')
            else:
                pass # conveyors are updated separately
    
    def update_conveyors(self):
        for conveyor_name, conveyor in self.conveyors.items(): # Stock is a Conveyor
            self.logger.debug(f'updating conveyor {conveyor_name}')
            total_flow_effect = 0
            connected_flows = self.stock_flows[conveyor_name]
            for direction, flows in connected_flows.items():
                if direction == 'in':
                    for flow in flows:
                        total_flow_effect += self.name_space[flow]

            # in
            conveyor['conveyor'].inflow(total_flow_effect * self.sim_specs['dt'])
            self.stock_shadow_values[conveyor_name] = conveyor['conveyor'].level()

    def simulate(self, time=None, dt=None):
        self.logger.debug(f'Simulation started with specs: {self.sim_specs}')
        self.logger.debug(f'Equations: {self.stock_equations | self.flow_equations | self.aux_equations | self.delayed_auxiliary_equations}')
        
        if time is None:
            time = self.sim_specs['simulation_time']
        if dt is None:
            dt = self.sim_specs['dt']
        iterations = int(time/dt)

        if self.state in ['simulated', 'changed']:
            if self.state == 'changed':
                self.logger.debug('Equation changed after last simulation, re-parsing.')
                self.parse() # set state to 'parsed'
                self.generate_ordered_vars()

            self.logger.debug("")
            self.logger.debug("*** Resuming ***")
            self.logger.debug("")
            # self.name_space.clear()
            # # use last time slice as the initial values for the next simulation, do not do initialization again
            # # self.sim_specs['current_time'] -= self.sim_specs['dt'] # go back to the last time step
            # for stock in (self.stocks | self.conveyors):
            #     last_value = self.time_slice[self.sim_specs['current_time'] - self.sim_specs['dt']][stock]
            #     self.name_space[stock] = last_value
            
            # self.name_space['TIME'] = self.sim_specs['current_time']
            # self.name_space['DT'] = self.sim_specs['dt']

            self.logger.debug(f'Continuing simulation from time {self.sim_specs["current_time"]} for {iterations} iteration')
        
        elif self.state == 'loaded':
            # parse equations and order execution (compile)
            self.parse() # set state to 'parsed'
            self.generate_ordered_vars()
            # Initialization Phase
            self.logger.debug("")
            self.logger.debug("*** Initialization ***")
            self.logger.debug("")
            self.logger.debug(f"self.ordered_vars_init {self.ordered_vars_init}")

            # Initialize self.stock_non_negative_temp_value
            for stock, is_non_negative in self.stock_non_negative.items():
                if is_non_negative:
                    self.stock_non_negative_temp_value[stock] = None

            for var in self.ordered_vars_init:
                self.calculate_variable(var=var, dg=self.dg_init, mode='init')
        
            # Since it's just loaded, we need 2 iterations (if we were to simulate 1 DT)
            # The 1st iteration is to calculate the flows (and auxiliaries) based on the initialilized stocks (1st row of outcome) and update the stocks (2nd row of outcome)
            # The 2nd iteration is to calculate the flows (and auxiliaries) based on the updated stocks (2nd row of outcome) and update the stocks.
            # The updated stocks (in name_space) should be part of the 3rd row of outcome, but they are not saved (bus still in name_space) as we only simulate 1 DT.
            iterations += 1 

        # Iteration Phase
        self.logger.debug("")
        self.logger.debug("*** Iteration ***")
        self.logger.debug("")
        self.logger.debug(f"self.ordered_vars_iter {self.ordered_vars_iter}")
        self.logger.debug(f"Current name_space: {self.name_space}")

        # self.current_iteration = 0

        for s in range(iterations):
            self.logger.debug("")
            self.logger.debug(f'---- iteration {s} start, current time {self.sim_specs["current_time"]} ----')
            
            # Iter step 1: calculate flows and auxiliaries they depend on
            self.logger.debug('calculating flows and auxiliaries they depend on')
            for var in self.ordered_vars_iter:
                self.calculate_variable(var=var, dg=self.dg_iter, mode='iter')

            # Iter step 2: update stocks using flows and conveyors
            self.logger.debug('updating stocks using flows and conveyors')
            self.update_stocks() # update stock shadow values using flows
            self.update_conveyors() # update stock shadow values as well as conveyors 

            # Snapshot current name space
            self.logger.debug('snapshotting current name space as a new time slice')
            current_snapshot = deepcopy(self.name_space)
            current_snapshot[self.sim_specs['time_units']] = current_snapshot['TIME']
            current_snapshot.pop('TIME')
            
            self.time_slice[self.sim_specs['current_time']] = current_snapshot

            self.logger.debug(f'---- iteration {s} finished ----') 
            self.logger.debug(f'name_space: {self.name_space}')
            self.logger.debug(f'shadow_val: {self.stock_shadow_values}')
            self.logger.debug(f'time_expr_register: {self.solver.time_expr_register}')

            
            # Iter step 3: update simulation time
            self.logger.debug(f'updating simulation time (current_time) from {self.sim_specs["current_time"]} to {self.sim_specs["current_time"] + dt}')
            self.sim_specs['current_time'] += dt
            # self.current_iteration += 1

            # prepare name_space for next step
            self.logger.debug('---- preparing name_space for next step ----')
            self.logger.debug('clearing name space')
            self.name_space.clear()
            self.logger.debug(f'name space: {self.name_space}')

            self.logger.debug('populate name_space using shadow values')
            # Here this shadow value is used directly as the stock value for the next time step
            # This is OK if the model equations are not changed 'dynamically' during the simulation
            # However if flow equations are changed, either in themselves or in their dependencies,
            # then the shadow value will be incorrect.
            for stock, stock_value in self.stock_shadow_values.items():
                self.name_space[stock] = deepcopy(stock_value)

            # then we need to add delayed auxiliaries as they are implicit stocks

            self.logger.debug(f'name space: {self.name_space}')
            
            self.logger.debug('clear shadow value')
            self.stock_shadow_values.clear()
            self.logger.debug(f'shadow value: {self.stock_shadow_values}')

            self.logger.debug('populate non-negative temp value with their name_space values')
            for k, v in self.stock_non_negative_temp_value.items():
                self.stock_non_negative_temp_value[k] = deepcopy(self.name_space[k])
            self.logger.debug(f'non-negative temp value: {self.stock_non_negative_temp_value}')
            
            self.name_space['TIME'] = self.sim_specs['current_time']
            self.name_space['DT'] = self.sim_specs['dt']

            self.logger.debug('---- end of preparation ----')

        self.state = 'simulated'

    def var_name_to_csv_entry(self, var, sub=None):
        if sub is None:
            series_key = var.replace('_', ' ')
        else:
            series_key = f"{var}[{', '.join(sub)}]".replace('_', ' ')
        
        if series_key[0].isdigit() or series_key[-1] == ')': # 1 day -> "1 day", a(b)-> "a(b)"
            series_key = '\"'+ series_key + '\"'
        return series_key
        
    def clear_last_run(self):
        self.sim_specs['current_time'] = self.sim_specs['initial_time']
        self.name_space = dict()
        self.name_space.update(self.env_variables)
        self.stock_shadow_values = dict()
        self.time_slice = dict()
        for stock_name, stock in self.stocks.items():
            stock.initialized = False

        self.stock_equations_parsed = dict()
        self.flow_equations_parsed = dict()
        self.aux_equations_parsed = dict()
        self.delayed_auxiliary_equations_parsed = dict()

        self.graph_functions = dict()
        self.graph_functions_renamed = dict()

        self.full_result = dict()
        self.full_result_flattened = dict()

        self.solver = Solver(
            sim_specs=self.sim_specs,
            dimension_elements=self.dimension_elements,
            var_dimension=self.var_dimension,
            name_space=self.name_space,
            graph_functions=self.graph_functions,
            )

        self.custom_functions = dict()

        self.state = 'loaded'

    def summary(self):
        print('\nSummary:\n')
        # print('------------- Definitions -------------')
        # pprint(self.stock_equations | self.flow_equations | self.aux_equations)
        # print('')
        print('-------------  Sim specs  -------------')
        pprint(self.sim_specs)
        print('')
        print('-------------  Runtime    -------------')
        pprint(self.name_space)
        print('-------------  State      -------------')
        print(self.state)
        print('')
    
    def get_element_simulation_result(self, name, subscript=None):
        if not subscript:
            if type((self.stock_equations | self.flow_equations | self.aux_equations | self.delayed_auxiliary_equations)[name]) is dict:
                result = dict()
                for sub in (self.stock_equations | self.flow_equations | self.aux_equations | self.delayed_auxiliary_equations)[name].keys():
                    result[sub] = list()
                for time, slice in self.time_slice.items():
                    for sub, value in slice[name].items():
                        result[sub].append(value)
                return result
            else:
                result = list()
                for time, slice in self.time_slice.items():
                    result.append(slice[name])
                return result
        else:
            result= list()
            for time, slice in self.time_slice.items():
                try:
                    result.append(slice[name][subscript])
                except KeyError as e:
                    print(f'Subscript {subscript} not found for variable {name}; available subscripts: {list(slice[name].keys())}')
                    raise e
            return result
            
    def export_simulation_result(self, flatten=False, format='dict', to_csv=False):
        self.full_result = dict()
        self.full_result_df = None
        
        # generate full_result
        for time, slice in self.time_slice.items():
            for var, value in slice.items():
                if var == 'DT':
                    continue
                if type(value) is dict:
                    for sub, subvalue in value.items():
                        try:
                            self.full_result[var][sub].append(subvalue)
                        except:
                            try:
                                self.full_result[var][sub] = [subvalue]
                            except:
                                self.full_result[var] = dict()
                                self.full_result[var][sub] = [subvalue]
                else:
                    try:
                        self.full_result[var].append(value)
                    except:
                        self.full_result[var] = [value]
        # flatten the full_result
        self.full_result_flattened = dict()
        for var, result in self.full_result.items():
            if type(result) is dict:
                for sub, subresult in result.items():
                    self.full_result_flattened[f'{var}[{", ".join(sub)}]'] = subresult
            else:
                self.full_result_flattened[var] = result
        if format == 'dict':
            if flatten:
                return self.full_result_flattened
            else:
                return self.full_result
        elif format == 'df':
            import pandas as pd
            self.full_result_df = pd.DataFrame.from_dict(self.full_result_flattened)
            self.full_result_df.reindex(sorted(self.full_result_df.columns), axis=1)
            if to_csv:
                if type(to_csv) is not str:
                    self.full_result_df.to_csv('asdm.csv', index=False)
                else:
                    self.full_result_df.to_csv(to_csv, index=False)
            return self.full_result_df
    
    def display_results(self, variables=None):
        if type(variables) is list and len(variables) == 0:
            variables = list((self.stock_equations | self.flow_equations | self.aux_equations | self.delayed_auxiliary_equations).keys())
        if type(variables) is str:
            variables = [variables]
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        if len(self.full_result) == 0:
            self.full_result = self.export_simulation_result()
        for var in variables:
            result = self.full_result[var]
            if type(result) is list:
                ax.plot(result, label=f'{var}')
            else:
                for sub, subresult in self.full_result[var].items():
                    ax.plot(subresult, label=f'{var}[{", ".join(sub)}]')
        ax.legend()
        plt.show()

    def create_variable_dependency_graph(self, var, mode, graph=None, visited=None):
        if self.state == 'loaded':
            self.parse()
        
        self.logger.debug(f"Creating dependency graph for variable '{var}' in mode '{mode}'")
        if graph is None:
            graph = nx.DiGraph()
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion by checking if we've already visited this variable
        if var in visited:
            return graph
        
        visited.add(var)


        all_equations = (self.stock_equations_parsed | self.flow_equations_parsed | self.aux_equations_parsed | self.delayed_auxiliary_equations_parsed)
        if var in self.env_variables: # like 'TIME'
            visited.remove(var)
            return graph

        def get_dependent_variables(parsed_equation):
            self.logger.debug("."*80)
            self.logger.debug(f"Getting dependent variables of variable '{var}'")
            dependent_variables = set()
            self.id_level = 0
            
            def trace_node(parsed_equation, node_id):
                self.id_level += 1
                self.logger.debug(f"{'    '*self.id_level}-->Tracing node {node_id} with current dependent variables: {dependent_variables}, node detail: {parsed_equation.nodes[node_id]}")
                node = parsed_equation.nodes[node_id]
                operands_to_trace = set()
                if len(node) == 0:
                    successor_nodes = list(parsed_equation.successors(node_id))
                    successor_id = successor_nodes[0]
                    self.logger.debug(f"{'    '*self.id_level}This is root node, moving to its successsor node {successor_id}.")
                    trace_node(parsed_equation, successor_id)
                else:
                    node_operator = node['operator']
                    node_operands = node['operands']
                    self.logger.debug(f"{'    '*self.id_level}Examining node {node_id} with operator {node_operator}")
                    if node_operator in ['IS']:
                        self.logger.debug(f"{'    '*self.id_level}Node {node_id} has operator {node_operator}, a number; no dependent, no further tracing needed.")
                        return
                    elif node_operator in ['DELAY', 'DELAY1', 'DELAY3', 'SMTH1', 'SMTH3']:
                        # these functions have 2 or 3 operands; if 2 then no initial value, only 1st is used for initialization; if 3 then with initial value, only 3rd is used for initialization; 1st is indirectly (through cumulation) used for iteration; 2nd is directly (delay time) used for iteration
                        self.logger.debug(f"{'    '*self.id_level}Node {node_id} is a delay/smooth function {node_operator}, handling operands based on mode '{mode}'")
                        if mode == 'init':
                            self.logger.debug(f"{'    '*self.id_level}Initialization mode: only considering the operand used for initialization")
                            if len(node['operands']) == 3:
                                self.logger.debug(f"{'    '*self.id_level}Node {node_id} has 3 operands, adding only the 3rd operand for initialization")
                                operands_to_trace.add(node['operands'][2])
                            elif len(node['operands']) == 2:
                                self.logger.debug(f"{'    '*self.id_level}Node {node_id} has 2 operands, adding the target variable and delay time for initialization")
                                operands_to_trace.add(node['operands'][0])
                                operands_to_trace.add(node['operands'][1])
                        elif mode == 'iter':
                            self.logger.debug(f"{'    '*self.id_level}Iteration mode: considering target variable and delay time for iteration")
                            operands_to_trace.add(node['operands'][0])
                            operands_to_trace.add(node['operands'][1])
                        else:
                            raise Exception(f"Invalid mode: {mode}")
                    elif node_operator in ['EQUALS', 'SPAREN']:
                        self.logger.debug(f"{'    '*self.id_level}Node {node_id} has operator {node_operator}")
                        dependent_variable_name = parsed_equation.nodes[node_id]['value']
                        self.logger.debug(f"{'    '*self.id_level}-- Node {node_id} is a variable {dependent_variable_name}, adding to dependent variables; no further tracing needed.")
                        dependent_variables.add(dependent_variable_name)
                    else:
                        for node_operand in node_operands:
                            operands_to_trace.add(node_operand)

                    # the remaining nodes (post-processing) could have dependencies on other variables, trace them recursively
                    if len(operands_to_trace) == 0:
                        pass
                    else:
                        for node_operand in operands_to_trace:
                            trace_node(parsed_equation, node_operand)
                self.id_level -= 1

            if type(parsed_equation) is not dict:
                trace_node(parsed_equation, node_id='root')
            else:
                for _, sub_eqn in parsed_equation.items():
                    trace_node(sub_eqn, node_id='root')
            
            self.logger.debug(f"{'    '*self.id_level}Variable {var} is dependent on {dependent_variables}")
            self.logger.debug("="*80)
            
            return dependent_variables
        
        parsed_equation = all_equations[var]
        
        if type(parsed_equation) is list: # this variable might be a conveyor
            if var in self.conveyors:
                dep_graph_len = get_dependent_variables(parsed_equation[0])
                dep_graph_val = get_dependent_variables(parsed_equation[1])
                # combine the two lists without duplicates
                dependent_variables = list(set(dep_graph_len | dep_graph_val))
            else:
                visited.remove(var)
                raise Exception(f"Non-conveyor variable with parsed equation as list: {var}")
        else: # this is a normal variable
            if mode == 'init':
                dependent_variables = get_dependent_variables(parsed_equation)
            elif mode == 'iter':
                if var in self.stock_equations:
                    dependent_variables = list() # stock variables' equations are only for initialization, they are not dependent on any other variables during iteration step 1
                    self.logger.debug(f'ITER Graph: Stock variable {var} is considered for iteration, but its equation is only used for initialization, thus no dependence on other variables during iteration')
                else:
                    dependent_variables = get_dependent_variables(parsed_equation)
                    self.logger.debug(f'ITER Graph: Variable {var} is considered for iteration, it depends on: {dependent_variables}')
            else:
                raise Exception(f"Invalid mode: {mode}")

        if len(dependent_variables) == 0:
            graph.add_node(var)
            visited.remove(var)
            return graph
        else:
            for dependent_var in dependent_variables:
                # Only recurse if we haven't already visited this dependent variable
                if dependent_var not in visited:
                    graph.add_edge(dependent_var, var)
                    self.create_variable_dependency_graph(dependent_var, mode=mode, graph=graph, visited=visited)
                else:
                    # Circular dependency detected
                    self.logger.error(f"Warning: Circular dependency detected between {dependent_var} and {var}")
                    self.logger.error(f"Warning: Full dependency path - direction A: {nx.shortest_path(graph, dependent_var, var)}")
                    self.logger.error(f"Warning: Full dependency path - direction B: {nx.shortest_path(graph, var, dependent_var)}\n")

            visited.remove(var)
            return graph

    def generate_full_dependent_graph(self, show=False):
        ########################
        # Initialization graph #
        ########################

        self.logger.debug(f'{"*"*80}')
        self.logger.debug(f'Initialization phase')
        self.logger.debug(f'{"*"*80}')

        dg_init = nx.DiGraph()
        if len(self.stock_equations_parsed) > 0:
            for stock in self.stock_equations_parsed:
                dg_stock = self.create_variable_dependency_graph(stock, mode='init')
                dg_init = nx.compose(dg_init, dg_stock)
        else:
            self.logger.debug(f"INIT Graph: No stocks, skipping")

        if len(self.delayed_auxiliary_equations_parsed) > 0:
            for delayed_aux in self.delayed_auxiliary_equations_parsed:
                dg_delayed_aux = self.create_variable_dependency_graph(delayed_aux, mode='init')
                dg_init = nx.compose(dg_init, dg_delayed_aux)
        else:
            self.logger.debug(f"INIT Graph: No delayed auxiliaries, skipping")

        self.logger.debug(f'INIT Graph: Nodes (before sanitization): {dg_init.nodes(data=True)}')
        self.logger.debug(f'INIT Graph: Edges (before sanitization): {dg_init.edges(data=True)}')
        
        # check each non-negative stock for its dependency on inflows and outflows and add to dg_init
        for stock, in_out_flows in self.stock_flows.items():
            if self.stock_non_negative[stock] is True:
                self.logger.debug(f'INIT Graph: Considering non-negative stock {stock}')
                if 'out' in in_out_flows:
                    out_flows = in_out_flows['out']

                    for out_flow in out_flows:
                        if out_flow in dg_init:
                            self.logger.debug(f'INIT Graph: Outflow {out_flow} is in the graph, considering it')
                            # if stock explicitly depends on outflow for initiliazation, we cannot let outflow be constrained by stock in the initialization phase
                            if nx.has_path(dg_init, out_flow, stock):
                                self.logger.debug(f'INIT Graph: Stock {stock} explicitly depends on outflow {out_flow}, skipping')
                            else: # out_flow does not depend on stock, add it to the graph
                                self.logger.debug(f'INIT Graph: Outflow {out_flow} does not depend on stock {stock}, adding to the graph, so that it is constrained by stock in the initialization phase')
                                nx.set_node_attributes(dg_init, {out_flow: {'out_from_non_negative_stock': stock}}) # this attribute triggers the constrains in runtime
                        else:
                            self.logger.debug(f'INIT Graph: Outflow {out_flow} is not in the graph, skipping it')

                    if 'in' in in_out_flows:
                        in_flows = in_out_flows['in']
                        # for each inflow, we need to check if it depends on (i.e., is affected by) any outflow; if yes, we exclude it from outflow constraining.
                        # Exception: when the inflow is a delayed outflow with an independent initial value; in this case, we do not consider its dependency on the outflow but consider it TRUE as a sanity inflow during initialization.
                        
                        in_flow_sanities = {} # sanity: True if the inflow is not explicitly dependent on any outflow

                        for in_flow in in_flows:
                            if in_flow in dg_init:
                                self.logger.debug(f'INIT Graph: Inflow {in_flow} is in the graph, examining it...')
                                # we assume all inflows are sanity at the beginning
                                in_flow_sanities[in_flow] = True
                                for out_flow in out_flows:
                                    if out_flow in dg_init:
                                        self.logger.debug(f'INIT Graph:     for Inflow {in_flow}, Outflow {out_flow} is in the graph, meaning it is needed during initialization')
                                        if nx.has_path(dg_init, out_flow, in_flow):
                                            self.logger.debug(f'INIT Graph:     Inflow {in_flow} explicitly depends on outflow {out_flow}, not a sanity inflow')
                                            in_flow_sanities[in_flow] = False # if inflow depends on any outflow, it is not a sanity inflow
                                            # dg_init
                                            if in_flow in dg_init:
                                                self.logger.debug(f'INIT Graph:     Inflow {in_flow} is excluded from outflow constraining')
                                                nx.set_node_attributes(dg_init, {in_flow: {'considered_for_non_negative_stock': False}}) # this attribute excludes the inflow from 'how much can flow out'
                                        else:
                                            self.logger.debug(f'INIT Graph:     Inflow {in_flow} does not depend on outflow {out_flow} during initialization')
                                    else:
                                        self.logger.debug(f'INIT Graph:     for Inflow {in_flow}, Outflow {out_flow} is not in the graph, meaning it is not needed during initialization, skipping it')

                                    if not in_flow_sanities[in_flow]:
                                        break
                                if in_flow_sanities[in_flow]:
                                    # dg_init
                                    if in_flow in dg_init:
                                        self.logger.debug(f'INIT Graph: Inflow {in_flow} is included in outflow constraining')
                                        nx.set_node_attributes(dg_init, {in_flow: {'considered_for_non_negative_stock': True}}) # this attribute includes the inflow in 'how much can flow out'
                            else:
                                pass

                        # for inflows without sanity, we need to make them dependent on all outflows, so that they are only calculated after constraining the outflows
                        for in_flow, sanity in in_flow_sanities.items():
                            if not sanity:
                                for out_flow in out_flows:
                                    # dg_init
                                    if (out_flow, in_flow) not in dg_init.edges: # avoid overwriting
                                        dg_init.add_edge(out_flow, in_flow)
                                        self.logger.debug(f'INIT Graph: Inflow {in_flow} implicitly depends on outflow {out_flow}')

                            else: # for inflow with sanity, we need to make all outflows dependent on it, so that they are calculated before constraining the outflows
                                for out_flow in out_flows:
                                    # dg_init
                                    if (in_flow, out_flow) not in dg_init.edges: # avoid overwriting
                                        dg_init.add_edge(in_flow, out_flow)
                                        self.logger.debug(f'INIT Graph: Outflow {out_flow} implicitly depends on inflow {in_flow}')
                    
                    else: # no inflow, just determine the prioritisation of outflows
                        pass
                
                    # set output priorities
                    # outflow prioritisation
                    # rule 1: first added first
                    # rule 2: dependents ranked higher
                    if len(out_flows) > 1:
                        for i in range(len(out_flows)-1, 0, -1):
                            for j in range(i):
                                if self.is_dependent(out_flows[j+1], out_flows[j]):
                                    temp = out_flows[j+1]
                                    out_flows[j+1] = out_flows[j]
                                    out_flows[j] = temp
                    
                    priority_level = 1
                    for out_flow in out_flows:
                        if out_flow in dg_init:
                            nx.set_node_attributes(dg_init, {out_flow: {'priority': priority_level}})

                    self.stock_non_negative_out_flows[stock] = out_flows
                
                else: # no outflows
                    self.logger.debug(f"INIT Graph: Stock {stock} has no outflows, only considering inflows")
                    if 'in' in in_out_flows: # no outflows, just inflows
                        self.logger.debug(f"INIT Graph: Stock {stock} has inflows, considering them")
                        in_flows = in_out_flows['in']
                        for in_flow in in_flows:
                            if in_flow in dg_init:
                                nx.set_node_attributes(dg_init, {in_flow: {'considered_for_non_negative_stock': True}}) # this attribute includes the inflow in 'how much can flow out'
                                self.logger.debug(f"INIT Graph: Inflow {in_flow} is considered for non-negative stock {stock}")
                    else:
                        self.logger.debug(f"INIT Graph: Stock {stock} has no inflows, skipping")
                
                # temporary fix, further validation needed
                if 'in' in in_out_flows:
                    in_flows = in_out_flows['in']
                    # Exception: when the stock depends on the inflow for initialization; in this case, we consider it FALSE as a sanity inflow during initialization.
                    for in_flow in in_flows:
                        if in_flow in dg_init:
                            if nx.has_path(dg_init, in_flow, stock):
                                nx.set_node_attributes(dg_init, {in_flow: {'considered_for_non_negative_stock': False}}) # this attribute excludes the inflow from 'how much can flow out'
                        else:
                            pass
            else:
                self.logger.debug(f"INIT Graph: Stock {stock} is not a non-negative stock, skipping")

        # Conveyor: add dependency of leakflow on the conveyor
        for conveyor_name, conveyor in self.conveyors.items():
            leakflows=conveyor['leakflow']
            for leakflow in leakflows:
                # the 'value' (not leak_fraction) of leakflow depends on the conveyor
                dg_init.add_edge(conveyor_name, leakflow) 

                # the conveyor depends on the leak_fraction 
                dg_leakflow = self.create_variable_dependency_graph(leakflow, mode='init')
                dg_leak_fraction = deepcopy(dg_leakflow)
                # replace leakflow with conveyor in the graph
                dg_leak_fraction.remove_node(leakflow)
                dg_leak_fraction.add_node(conveyor_name)
                for pred in dg_leakflow.predecessors(leakflow):
                    dg_leak_fraction.add_edge(pred, conveyor_name)
                
                dg_init = nx.compose(dg_init, dg_leak_fraction)

        ordered_vars_init = list(nx.topological_sort(dg_init))

        self.logger.debug(f'INIT Graph: Dependent graph for initialization:')
        self.logger.debug(f'INIT Graph: Nodes (after sanitization): {dg_init.nodes(data=True)}')
        self.logger.debug(f'INIT Graph: Edges (after sanitization): {dg_init.edges(data=True)}')
        self.logger.debug(f"INIT Graph: Ordered vars for initialization: {ordered_vars_init}")

        ###################
        # Iteration graph #
        ###################

        self.logger.debug(f'{"*"*80}')
        self.logger.debug(f'Iteration phase')
        self.logger.debug(f'{"*"*80}')

        dg_iter = nx.DiGraph()
        for flow in self.flow_equations_parsed:
            dg_flow = self.create_variable_dependency_graph(flow, mode='iter')
            dg_iter = nx.compose(dg_iter, dg_flow)

        # add obsolete auxiliaries to the dg_iter
        for var in self.aux_equations:
            if var not in dg_iter.nodes:
                dg_obsolete = self.create_variable_dependency_graph(var, mode='iter')
                dg_iter = nx.compose(dg_iter, dg_obsolete)
        
        self.logger.debug(f'ITER Graph: Nodes (before sanitization): {dg_iter.nodes(data=True)}')
        self.logger.debug(f'ITER Graph: Edges (before sanitization): {dg_iter.edges(data=True)}')

        # check each non-negative stock for dependencies of inflow and outflow and add to dg_iter
        for stock, in_out_flows in self.stock_flows.items():
            if self.stock_non_negative[stock] is True:
                self.logger.debug(f'ITER Graph: for non negative stock {stock}')
                if 'out' in in_out_flows:
                    out_flows = in_out_flows['out']

                    for out_flow in out_flows:
                        self.logger.debug(f'ITER Graph: for outflow {out_flow}')
                        nx.set_node_attributes(dg_iter, {out_flow: {'out_from_non_negative_stock': stock}}) # this attribute triggers the constrains in runtime

                    if 'in' in in_out_flows:
                        in_flows = in_out_flows['in']
                        # for each inflow, we need to check if it is dependent on (affected by) any outflow; if yes, we exclude it from outflow constraining.
                        in_flow_sanities = {}

                        for in_flow in in_flows:
                            self.logger.debug(f'ITER Graph: for inflow {in_flow}')
                            in_flow_sanities[in_flow] = True
                            for out_flow in out_flows:
                                if nx.has_path(dg_iter, out_flow, in_flow):
                                    in_flow_sanities[in_flow] = False
                                    nx.set_node_attributes(dg_iter, {in_flow: {'considered_for_non_negative_stock': False}}) # this attribute excludes the inflow from 'how much can flow out'
                                if not in_flow_sanities[in_flow]:
                                    break
                            if in_flow_sanities[in_flow]:
                                nx.set_node_attributes(dg_iter, {in_flow: {'considered_for_non_negative_stock': True}}) # this attribute includes the inflow in 'how much can flow out'
                        
                        # for inflows without sanity, we need to make them dependent on all outflows, so that they are only calculated after constraining the outflows
                        for in_flow, sanity in in_flow_sanities.items():
                            if not sanity:
                                for out_flow in out_flows:
                                    if (out_flow, in_flow) not in dg_iter.edges: # avoid overwriting
                                        dg_iter.add_edge(out_flow, in_flow)
                                        self.logger.debug(f'ITER Graph: inflow {in_flow} implicitly depends on outflow {out_flow}')

                            else: # for inflow with sanity, we need to make all outflows dependent on it, so that they are calculated before constraining the outflows
                                for out_flow in out_flows:
                                    if (in_flow, out_flow) not in dg_iter.edges: # avoid overwriting
                                        dg_iter.add_edge(in_flow, out_flow)
                                        self.logger.debug(f'ITER Graph: outflow {out_flow} implicitly depends on inflow {in_flow}')

                    
                    else: # no inflow, just determine the prioritisation of outflows
                        pass
                
                    # set output priorities
                    # outflow prioritisation
                    # rule 1: first added first
                    # rule 2: dependents ranked higher
                    if len(out_flows) > 1:
                        for i in range(len(out_flows)-1, 0, -1):
                            for j in range(i):
                                if self.is_dependent(out_flows[j+1], out_flows[j]):
                                    temp = out_flows[j+1]
                                    out_flows[j+1] = out_flows[j]
                                    out_flows[j] = temp
                    
                    priority_level = 1
                    for out_flow in out_flows:
                        priority_level += 1

                    self.stock_non_negative_out_flows[stock] = out_flows
                
                else: # no outflows
                    if 'in' in in_out_flows: # no outflows, just inflows
                        self.logger.debug(f'ITER Graph: no outflow')
                        in_flows = in_out_flows['in']
                        for in_flow in in_flows:
                            nx.set_node_attributes(dg_iter, {in_flow: {'considered_for_non_negative_stock': True}}) # this attribute includes the inflow in 'how much can flow out'
                            self.logger.debug(f'ITER Graph: consider inflow {in_flow}')

        ordered_vars_iter = list(nx.topological_sort(dg_iter))


        self.logger.debug(f'ITER Graph: Dependent graph for iteration:')
        self.logger.debug(f'ITER Graph: Nodes (after sanitization): {dg_iter.nodes(data=True)}')
        self.logger.debug(f'ITER Graph: Edges (after sanitization): {dg_iter.edges(data=True)}')
        self.logger.debug(f"ITER Graph: Ordered vars for iteration: {ordered_vars_iter}")

        if not show:
            return (dg_init, ordered_vars_init, dg_iter, ordered_vars_iter)
        else:
            if show == 'init':
                dg = dg_init
            elif show == 'iter':
                dg = dg_iter
            else:
                raise Exception(f'Invalid show parameter {show}. Use "init" or "iter"')

            import matplotlib.pyplot as plt
            from networkx.drawing.nx_agraph import graphviz_layout
            pos = graphviz_layout(dg, prog='dot')
            # pos = nx.spring_layout(dg)
            nx.draw(
                dg,
                pos,
                with_labels=True,
                node_size=300,
                node_color="skyblue",
                node_shape="s",
                alpha=1,
                linewidths=5
                )
            plt.show()
            return (dg_init, ordered_vars_init, dg_iter, ordered_vars_iter)
    
    def generate_ordered_vars(self):
        self.dg_init, self.ordered_vars_init, self.dg_iter, self.ordered_vars_iter = self.generate_full_dependent_graph()
    
    def generate_cld(self, vars=None, show=False, loop=True):
        # Make sure the model equations are parsed
        if self.state == 'loaded':
            self.parse()

        if vars is None:
            vars = list(self.flow_equations.keys())
        elif type(vars) is str:
            vars = [vars]
        
        dg = nx.DiGraph()

        for var in vars:
            dg_var = self.create_variable_dependency_graph(var, mode='iter')
            dg = nx.compose(dg, dg_var)

        # create flow-to-stock edges if loop=True
        if loop:
            for flow in self.flow_stocks.keys():
                if flow in vars:
                    for stock in self.flow_stocks[flow].values():
                        dg.add_edge(flow, stock)
        
        if not show:
            return dg
        else:
            import matplotlib.pyplot as plt
            from networkx.drawing.nx_agraph import graphviz_layout
            pos = graphviz_layout(dg, prog='dot')
            # pos = nx.spring_layout(dg)
            nx.draw(
                dg, 
                pos, 
                with_labels=True, 
                node_size=300, 
                node_color="skyblue", 
                node_shape="s", 
                alpha=1, 
                linewidths=5
                )
            plt.show()
    
    def save_xmile(self, filepath=None, _force_update_all=False):
        """
        Save the model to XMILE format.
        
        This method updates an existing XMILE file with modifications made to the model.
        It preserves the original structure, including views/layout, and only updates
        modified variables. The model must have been loaded from an XMILE file.
        
        Args:
            filepath: Path to save the file. If None, saves to original file with '_asdm' suffix.
            _force_update_all: Internal testing parameter. If True, forces all variables to be
                              updated (not just modified ones). This tests all equation serialization
                              logic. Not intended for production use.
        
        Returns:
            Path to the saved file
            
        Raises:
            RuntimeError: If model was not loaded from an XMILE file
        """
        from pathlib import Path
        
        # Check if model was loaded from XMILE
        if self._xmile_soup is None:
            raise RuntimeError(
                "Cannot save to XMILE: model was not loaded from an XMILE file. "
                "save_xmile() can only be used to update existing XMILE files, "
                "preserving their views and layout information."
            )
        
        # Testing mode: mark all variables as modified to test serialization
        if _force_update_all:
            self.logger_model_creation.debug("Testing mode: forcing update of all variables")
            self._modified_elements = set(
                list(self.stock_equations.keys()) +
                list(self.flow_equations.keys()) +
                list(self.aux_equations.keys()) +
                list(self.delayed_auxiliary_equations.keys())
            )
        
        # Determine output filepath
        if filepath is None:
            if not hasattr(self, 'xmile_path') or self.xmile_path is None:
                # This shouldn't happen if _xmile_soup exists - indicates inconsistent state
                raise RuntimeError(
                    "Inconsistent model state: _xmile_soup exists but xmile_path is not set. "
                    "Please provide an explicit filepath for save_xmile()."
                )
            # Original file exists, add _asdm suffix before extension
            original_path = Path(self.xmile_path)
            filepath = original_path.parent / f"{original_path.stem}_asdm{original_path.suffix}"
        else:
            filepath = Path(filepath)
        
        self.logger_model_creation.info(f"Saving model to {filepath}")
        
        # Update existing XMILE structure
        self.logger_model_creation.debug("Updating existing XMILE structure")
        output_soup = self._update_xmile_structure()
        
        # Write to file
        xml_string = str(output_soup)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_string)
        
        self.logger_model_creation.info(f"Model saved successfully to {filepath}")
        return filepath
    
    def _update_xmile_structure(self):
        """Update existing XMILE structure with current model state."""
        from copy import deepcopy
        
        # Work with a copy to avoid modifying the original
        output_soup = deepcopy(self._xmile_soup)
        
        # Update sim_specs
        self._update_sim_specs_in_soup(output_soup)
        
        # Update variables (only modified ones for efficiency)
        self._update_variables_in_soup(output_soup)
        
        # Views/layout are already preserved in the soup
        
        return output_soup
    
    def _update_sim_specs_in_soup(self, soup):
        """Update simulation specifications in soup."""
        sim_specs = soup.find('sim_specs')
        if sim_specs is None:
            # Create sim_specs if it doesn't exist
            xmile = soup.find('xmile')
            sim_specs = soup.new_tag('sim_specs')
            xmile.insert(0, sim_specs)
        
        # Update or create time_units attribute
        sim_specs['time_units'] = self.sim_specs.get('time_units', 'Time')
        
        # Update start time
        start = sim_specs.find('start')
        if start is None:
            start = soup.new_tag('start')
            sim_specs.append(start)
        start.string = str(self.sim_specs['initial_time'])
        
        # Update stop time
        stop = sim_specs.find('stop')
        if stop is None:
            stop = soup.new_tag('stop')
            sim_specs.append(stop)
        stop_time = self.sim_specs['initial_time'] + self.sim_specs['simulation_time']
        stop.string = str(stop_time)
        
        # Update dt (preserve reciprocal format if it was in original)
        dt_elem = sim_specs.find('dt')
        if dt_elem is None:
            dt_elem = soup.new_tag('dt')
            sim_specs.append(dt_elem)
        
        # Check if original had reciprocal format
        if dt_elem.get('reciprocal') == 'true':
            # Preserve reciprocal format
            dt_elem.string = str(int(1.0 / self.sim_specs['dt']) if self.sim_specs['dt'] != 0 else 1)
        else:
            dt_elem.string = str(self.sim_specs['dt'])
        
        self.logger_model_creation.debug("Updated sim_specs in XMILE")
    
    def _update_variables_in_soup(self, soup):
        """Update variables in soup (for updating existing XMILE)."""
        variables_section = soup.find('variables')
        if variables_section is None:
            self.logger_model_creation.warning("No variables section found in original XMILE")
            return
        
        # Update only modified variables
        for var_name in self._modified_elements:
            self.logger_model_creation.debug(f"Updating modified variable: {var_name}")
            
            # Get the original XMILE name from mapping
            original_name = self._xmile_name_mapping.get(var_name, var_name.replace('_', ' '))
            
            # Find the variable in soup
            var_elem = None
            for tag_name in ['stock', 'flow', 'aux']:
                var_elem = variables_section.find(tag_name, attrs={'name': original_name})
                if var_elem:
                    break
            
            if var_elem is None:
                self.logger_model_creation.warning(f"Modified variable {var_name} (original: '{original_name}') not found in original XMILE, skipping")
                continue
            
            # Update the equation
            self._update_variable_equation_in_elem(soup, var_elem, var_name)
        
        # Update modified docs
        for var_name in self._modified_docs:
            self.logger_model_creation.debug(f"Updating documentation for: {var_name}")
            
            # Get the original XMILE name from mapping
            original_name = self._xmile_name_mapping.get(var_name, var_name.replace('_', ' '))
            
            # Find the variable in soup
            var_elem = None
            for tag_name in ['stock', 'flow', 'aux']:
                var_elem = variables_section.find(tag_name, attrs={'name': original_name})
                if var_elem:
                    break
            
            if var_elem is None:
                self.logger_model_creation.warning(f"Variable {var_name} not found for doc update, skipping")
                continue
            
            # Update the doc
            self._update_variable_doc_in_elem(soup, var_elem, var_name)
        
        # Update modified tags (tags need to be combined with docs)
        for var_name in self._modified_tags:
            if var_name not in self._modified_docs:  # Only if not already updated via docs
                self.logger_model_creation.debug(f"Updating tags for: {var_name}")
                
                # Get the original XMILE name from mapping
                original_name = self._xmile_name_mapping.get(var_name, var_name.replace('_', ' '))
                
                # Find the variable in soup
                var_elem = None
                for tag_name in ['stock', 'flow', 'aux']:
                    var_elem = variables_section.find(tag_name, attrs={'name': original_name})
                    if var_elem:
                        break
                
                if var_elem is None:
                    self.logger_model_creation.warning(f"Variable {var_name} not found for tag update, skipping")
                    continue
                
                # Update the doc with tags
                self._update_variable_doc_in_elem(soup, var_elem, var_name)
        
        self.logger_model_creation.debug(f"Updated {len(self._modified_elements)} equations, {len(self._modified_docs)} docs, {len(self._modified_tags)} tags")
    
    def _add_equation_to_elem(self, soup, var_elem, var_name, equation):
        """Add equation to a variable element.
        
        Note: This function does NOT add <dimensions> tags - those should already
        exist in the original XMILE structure and are preserved during updates.
        
        Equation elements are inserted before structural tags (inflow, outflow,
        non_negative, units) to preserve XMILE element ordering.
        """
        # Find insertion point - before structural/UI tags
        # Note: UI tags (format, scale, summing) should be checked first so equations go before them
        # summing is 'isee:summing' in Stella-specific namespace
        insert_before = None
        for tag_name in ['format', 'scale', 'summing', 'inflow', 'outflow', 'non_negative', 'units']:
            elem = var_elem.find(tag_name)
            if elem:
                insert_before = elem
                break
        
        def insert_element(new_elem):
            """Helper to insert element at correct position."""
            if insert_before:
                insert_before.insert_before(new_elem)
            else:
                var_elem.append(new_elem)
        
        if isinstance(equation, dict):
            # Subscripted variable - check format (parallel vs element-by-element)
            # (dimensions should already exist in var_elem from original XMILE)
            array_format = self._variable_array_format.get(var_name, 'element')
            
            if array_format == 'parallel':
                # Parallel format: single <eqn> applies to all elements
                # All values in the dict should be the same, so just take the first
                first_eqn = next(iter(equation.values()))
                
                # If it's a DataFeeder, use the original equation (before DataFeeder replaced it)
                if isinstance(first_eqn, DataFeeder):
                    if var_name in self._original_equations:
                        self.logger_model_creation.debug(f"Using original equation for {var_name} (currently DataFeeder)")
                        eqn_elem = soup.new_tag('eqn')
                        eqn_elem.string = self._original_equations[var_name]
                        insert_element(eqn_elem)
                    else:
                        self.logger_model_creation.debug(f"Skipping DataFeeder for {var_name} - no original equation stored")
                else:
                    eqn_elem = soup.new_tag('eqn')
                    eqn_elem.string = str(first_eqn)
                    insert_element(eqn_elem)
            else:
                # Element-by-element format: separate <element> for each subscript
                shared_graph_func_eqn = None  # For subscripted graph functions
                
                for subscript, sub_eqn in equation.items():
                    # Skip DataFeeder objects in subscripted variables
                    if isinstance(sub_eqn, DataFeeder):
                        self.logger_model_creation.debug(f"Skipping DataFeeder for {var_name}[{subscript}] - will be recreated from data import")
                        continue
                        
                    element_elem = soup.new_tag('element')
                    if isinstance(subscript, tuple):
                        element_elem['subscript'] = ', '.join(subscript)
                    else:
                        element_elem['subscript'] = str(subscript)
                    
                    # Check if this is a graph function
                    if isinstance(sub_eqn, GraphFunc):
                        # For subscripted graph functions, add <gf> inside <element>
                        self._add_graph_function_content_to_elem(soup, element_elem, sub_eqn)
                        
                        # Store the shared eqn (all graph functions share the same .eqn attribute)
                        if shared_graph_func_eqn is None and sub_eqn.eqn is not None:
                            shared_graph_func_eqn = str(sub_eqn.eqn)
                    else:
                        # Regular equation
                        eqn_elem = soup.new_tag('eqn')
                        eqn_elem.string = str(sub_eqn)
                        element_elem.append(eqn_elem)
                    
                    insert_element(element_elem)
                
                # Add shared eqn at parent level for subscripted graph functions
                # This handles both GraphFuncs and variables where GraphFuncs were replaced by DataFeeders
                if shared_graph_func_eqn is not None:
                    eqn_elem = soup.new_tag('eqn')
                    eqn_elem.string = shared_graph_func_eqn
                    insert_element(eqn_elem)
                elif var_name in self._original_equations and all(isinstance(v, DataFeeder) for v in equation.values()):
                    # All elements are DataFeeders, but there was an original parent-level eqn
                    # This can happen when graph functions are overridden by data imports
                    eqn_elem = soup.new_tag('eqn')
                    eqn_elem.string = self._original_equations[var_name]
                    insert_element(eqn_elem)
        elif isinstance(equation, DataFeeder):
            # DataFeeder objects should not be saved as equations
            # They will be recreated from data import specifications
            self.logger_model_creation.debug(f"Skipping DataFeeder equation for {var_name} - will be recreated from data import")
            # Don't add any equation element
            pass
        elif isinstance(equation, GraphFunc):
            # Graph function
            self._add_graph_function_to_elem(soup, var_elem, equation, insert_element)
        elif isinstance(equation, Conveyor):
            # Conveyor - XMILE format:
            # 1. <eqn> - initial value
            # 2. <inflow> and <outflow> (structural elements, already in var_elem)
            # 3. <conveyor> containing <len>
            # 4. <units> (if present)
            
            # Add initial value equation first
            eqn_elem = soup.new_tag('eqn')
            eqn_elem.string = str(equation.equation)
            insert_element(eqn_elem)
            
            # Add conveyor element with len inside it, AFTER inflows/outflows
            # Insert before units (if present), otherwise append at end
            conveyor_elem = soup.new_tag('conveyor')
            len_elem = soup.new_tag('len')
            len_elem.string = str(equation.length_time_units)
            conveyor_elem.append(len_elem)
            
            # Find units tag to insert before it, or append at end
            units_elem = var_elem.find('units')
            if units_elem:
                units_elem.insert_before(conveyor_elem)
            else:
                var_elem.append(conveyor_elem)
        else:
            # Simple equation (string or number)
            eqn_elem = soup.new_tag('eqn')
            eqn_elem.string = str(equation)
            insert_element(eqn_elem)
    
    def _add_graph_function_content_to_elem(self, soup, parent_elem, graph_func):
        """Add graph function <gf> element to a parent element (for subscripted graph functions).
        
        This method adds ONLY the <gf> element without an <eqn>, used for subscripted
        graph functions where each element has its own <gf>.
        """
        gf_elem = soup.new_tag('gf')
        
        # Add type attribute if present
        if graph_func.out_of_bound_type is not None:
            gf_elem['type'] = graph_func.out_of_bound_type
        
        # XMILE element order for graph functions:
        # 1. xscale (if continuous) or nothing
        # 2. yscale
        # 3. xpts (if discrete)
        # 4. ypts
        
        # Add xscale (for continuous functions)
        if graph_func.xscale is not None:
            xscale_elem = soup.new_tag('xscale', attrs={
                'min': str(graph_func.xscale[0]),
                'max': str(graph_func.xscale[1])
            })
            gf_elem.append(xscale_elem)
        
        # Add yscale
        yscale_elem = soup.new_tag('yscale', attrs={
            'min': str(graph_func.yscale[0]),
            'max': str(graph_func.yscale[1])
        })
        gf_elem.append(yscale_elem)
        
        # Add xpts (only if explicitly provided, not generated from xscale)
        if hasattr(graph_func, '_xpts_explicit') and graph_func._xpts_explicit:
            xpts_elem = soup.new_tag('xpts')
            xpts_elem.string = ','.join(str(x) for x in graph_func.xpts)
            gf_elem.append(xpts_elem)
        
        # Add ypts
        ypts_elem = soup.new_tag('ypts')
        ypts_elem.string = ','.join(str(y) for y in graph_func.ypts)
        gf_elem.append(ypts_elem)
        
        parent_elem.append(gf_elem)
    
    def _add_graph_function_to_elem(self, soup, var_elem, graph_func, insert_element):
        """Add graph function to a variable element.
        
        XMILE format for graph functions:
        1. <eqn> - the expression that uses the graph function
        2. <gf> - the graph function definition
        """
        # Add the eqn that uses the graph function FIRST
        if graph_func.eqn is not None:
            eqn_elem = soup.new_tag('eqn')
            eqn_elem.string = str(graph_func.eqn)
            insert_element(eqn_elem)
        
        # Then add the gf element
        gf_elem = soup.new_tag('gf')
        
        # Add type
        if graph_func.out_of_bound_type is not None:
            gf_elem['type'] = graph_func.out_of_bound_type
        
        # XMILE element order for graph functions:
        # 1. xscale (if continuous) or nothing
        # 2. yscale
        # 3. xpts (if discrete)
        # 4. ypts
        
        # Add xscale (for continuous functions)
        if graph_func.xscale is not None:
            xscale_elem = soup.new_tag('xscale', attrs={
                'min': str(graph_func.xscale[0]),
                'max': str(graph_func.xscale[1])
            })
            gf_elem.append(xscale_elem)
        
        # Add yscale
        yscale_elem = soup.new_tag('yscale', attrs={
            'min': str(graph_func.yscale[0]),
            'max': str(graph_func.yscale[1])
        })
        gf_elem.append(yscale_elem)
        
        # Add xpts (only if explicitly provided, not generated from xscale)
        if hasattr(graph_func, '_xpts_explicit') and graph_func._xpts_explicit:
            xpts_elem = soup.new_tag('xpts')
            xpts_elem.string = ','.join(str(x) for x in graph_func.xpts)
            gf_elem.append(xpts_elem)
        
        # Add ypts
        ypts_elem = soup.new_tag('ypts')
        ypts_elem.string = ','.join(str(y) for y in graph_func.ypts)
        gf_elem.append(ypts_elem)
        
        # Insert gf element at correct position:
        # <gf> should come after <scale> (if present) but before other structural tags
        gf_insert_before = None
        for tag_name in ['inflow', 'outflow', 'non_negative', 'units']:
            elem = var_elem.find(tag_name)
            if elem:
                gf_insert_before = elem
                break
        
        if gf_insert_before:
            gf_insert_before.insert_before(gf_elem)
        else:
            var_elem.append(gf_elem)
    
    def _update_variable_equation_in_elem(self, soup, var_elem, var_name):
        """Update equation in an existing variable element."""
        # Get current equation from model
        equation = None
        if var_name in self.stock_equations:
            equation = self.stock_equations[var_name]
        elif var_name in self.flow_equations:
            equation = self.flow_equations[var_name]
        elif var_name in self.aux_equations:
            equation = self.aux_equations[var_name]
        
        if equation is None:
            return
        
        # Don't update if it's a DataFeeder (will be recreated from data import)
        if isinstance(equation, DataFeeder):
            self.logger_model_creation.debug(f"Skipping update for {var_name} (DataFeeder)")
            return
        
        # Special handling for subscripted variables with ALL DataFeeders
        # These were likely graph functions overridden by data imports - restore original structure
        if isinstance(equation, dict) and all(isinstance(v, DataFeeder) for v in equation.values()):
            self.logger_model_creation.debug(f"Restoring original element structure for DataFeeder-only variable: {var_name}")
            
            # Remove current equation elements
            for tag_name in ['eqn', 'element', 'gf', 'conveyor', 'len']:
                for elem in var_elem.find_all(tag_name):
                    elem.decompose()
            
            # Find original variable in _xmile_soup to restore element structure
            original_name = self._xmile_name_mapping.get(var_name, var_name)
            orig_var = None
            for var_type in ['stock', 'flow', 'aux']:
                orig_var = self._xmile_soup.find(var_type, attrs={'name': original_name})
                if orig_var:
                    break
            
            if orig_var:
                # Copy original equation elements from source XMILE
                for elem in orig_var.find_all(['element', 'eqn', 'gf'], recursive=False):
                    # Clone the element and add to current var_elem
                    from copy import deepcopy
                    cloned = deepcopy(elem)
                    
                    # Insert at correct position
                    insert_before = None
                    for tag_name in ['format', 'scale', 'inflow', 'outflow', 'non_negative', 'units']:
                        before_elem = var_elem.find(tag_name)
                        if before_elem:
                            insert_before = before_elem
                            break
                    
                    if insert_before:
                        insert_before.insert_before(cloned)
                    else:
                        var_elem.append(cloned)
            return
        
        # Remove all equation-related elements (but preserve dimensions, doc, units, format, summing, etc.)
        # This ensures a clean slate for the new equation
        # Note: We preserve 'summing' (isee:summing) which is a Stella UI flag
        for tag_name in ['eqn', 'element', 'gf', 'conveyor', 'len']:
            for elem in var_elem.find_all(tag_name):
                elem.decompose()
        
        # Add new equation
        self._add_equation_to_elem(soup, var_elem, var_name, equation)
    
    def _update_variable_doc_in_elem(self, soup, var_elem, var_name):
        """Update documentation in an existing variable element."""
        # Get current doc and tags from model
        doc_text = self.variable_docs.get(var_name, '')
        tags = self.variable_tags.get(var_name, [])
        
        # Remove old doc element if exists
        old_doc = var_elem.find('doc')
        if old_doc:
            old_doc.decompose()
        
        # Create new doc element if there's content
        if doc_text or tags:
            doc_elem = soup.new_tag('doc')
            # Format with tags if they exist
            full_doc_content = self.format_doc_content(tags, doc_text)
            doc_elem.string = full_doc_content
            var_elem.append(doc_elem)