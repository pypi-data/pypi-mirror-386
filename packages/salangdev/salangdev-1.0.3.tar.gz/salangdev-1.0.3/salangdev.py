#!/usr/bin/env python3
"""
SaLangDev interpreter (fixed)
- Handles comments starting with // or #
- Accepts single- and double-quoted strings
- Supports: set declarations, assignments, outcome (print), + - * /, parentheses
- Tolerant to blank lines and whitespace
- CLI entry: salangdev <file>
"""

import re
import sys

# ---------- TOKENIZER ----------
TOKEN_SPEC = [
    ('NUMBER',    r'\d+(?:\.\d+)?'),
    # single or double quoted strings
    ('STRING',    r'(?:"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\')'),
    ('SET',       r'\bset\b'),
    ('DIGIT',     r'\bdigit\b'),
    ('ONE_LETTER',r'\bone_letter\b'),
    ('LETTERS',   r'\bletters\b'),
    ('OUTCOME',   r'\boutcome\b'),
    ('ID',        r'[A-Za-z_][A-Za-z0-9_]*'),
    ('ASSIGN',    r'='),
    ('PLUS',      r'\+'),
    ('MINUS',     r'-'),
    ('MUL',       r'\*'),
    ('DIV',       r'/'),
    ('LPAREN',    r'\('),
    ('RPAREN',    r'\)'),
    ('NEWLINE',   r'\n'),
    ('SKIP',      r'[ \t\r]+'),
    # allow both // and # comments
    ('COMMENT',   r'(//.*|#.*)'),
]

TOKEN_REGEX = re.compile('|'.join(f'(?P<{n}>{p})' for n, p in TOKEN_SPEC), re.MULTILINE)

def tokenize(code):
    tokens = []
    for m in TOKEN_REGEX.finditer(code):
        kind = m.lastgroup
        value = m.group()
        if kind == 'SKIP' or kind == 'COMMENT' or value == '':
            continue
        if kind == 'NUMBER':
            value = int(value) if value.isdigit() else float(value)
        elif kind == 'STRING':
            # strip quotes correctly and unescape
            if value[0] == '"' and value[-1] == '"':
                raw = value[1:-1]
            elif value[0] == "'" and value[-1] == "'":
                raw = value[1:-1]
            else:
                raw = value
            value = bytes(raw, "utf-8").decode("unicode_escape")
        tokens.append((kind, value))
    tokens.append(('EOF', None))
    return tokens

# ---------- PARSER ----------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos][0]

    def eat(self, expected=None):
        tok = self.tokens[self.pos]
        if expected and tok[0] != expected:
            raise SyntaxError(f'Expected {expected}, got {tok}')
        self.pos += 1
        return tok

    def parse(self):
        stmts = []
        while self.peek() != 'EOF':
            if self.peek() == 'NEWLINE':
                self.eat('NEWLINE')
                continue
            stmts.append(self.parse_statement())
        return ('PROGRAM', stmts)

    def parse_statement(self):
        tok = self.peek()
        if tok == 'SET':
            return self.parse_set()
        elif tok == 'OUTCOME':
            self.eat('OUTCOME')
            expr = self.parse_expression()
            return ('OUTCOME', expr)
        elif tok == 'ID':
            # assignment: id = expr
            name = self.eat('ID')[1]
            if self.peek() == 'ASSIGN':
                self.eat('ASSIGN')
                expr = self.parse_expression()
                return ('ASSIGN', name, expr)
            else:
                raise SyntaxError('Expected "=" after identifier')
        else:
            raise SyntaxError(f'Unknown statement starting with {tok}')

    def parse_set(self):
        # set name [type] = expr
        self.eat('SET')
        if self.peek() != 'ID':
            raise SyntaxError('Expected identifier after set')
        name = self.eat('ID')[1]
        var_type = None
        if self.peek() in ('DIGIT', 'ONE_LETTER', 'LETTERS'):
            var_type = self.eat()[0]
        if self.peek() == 'ASSIGN':
            self.eat('ASSIGN')
            expr = self.parse_expression()
            return ('SET', name, var_type, expr)
        else:
            raise SyntaxError('Expected "=" in set declaration')

    # Expression parsing with precedence
    def parse_expression(self):
        return self.parse_term()

    def parse_term(self):
        node = self.parse_factor()
        while self.peek() in ('PLUS', 'MINUS'):
            op = self.eat()[0]
            right = self.parse_factor()
            node = (op, node, right)
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.peek() in ('MUL', 'DIV'):
            op = self.eat()[0]
            right = self.parse_unary()
            node = (op, node, right)
        return node

    def parse_unary(self):
        if self.peek() == 'MINUS':
            self.eat('MINUS')
            node = self.parse_unary()
            return ('NEG', node)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()
        if tok == 'NUMBER':
            return ('NUMBER', self.eat('NUMBER')[1])
        elif tok == 'STRING':
            return ('STRING', self.eat('STRING')[1])
        elif tok == 'ID':
            return ('VAR', self.eat('ID')[1])
        elif tok == 'LPAREN':
            self.eat('LPAREN')
            node = self.parse_expression()
            self.eat('RPAREN')
            return node
        else:
            raise SyntaxError(f'Unexpected token in expression: {tok}')

# ---------- INTERPRETER ----------
class Interpreter:
    def __init__(self):
        self.env = {}

    def cast_value(self, value, vtype):
        if vtype is None:
            return value
        if vtype == 'DIGIT':
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str) and value.isdigit():
                return int(value)
            raise TypeError(f'Cannot cast {value!r} to digit')
        if vtype == 'ONE_LETTER':
            if isinstance(value, str) and len(value) == 1:
                return value
            raise TypeError(f'Value {value!r} is not a single letter')
        if vtype == 'LETTERS':
            return str(value)
        return value

    def eval(self, node):
        t = node[0]
        if t == 'PROGRAM':
            for stmt in node[1]:
                self.eval(stmt)
            return None
        elif t == 'SET':
            name = node[1]; vtype = node[2]; expr = node[3]
            val = self.eval(expr)
            if vtype:
                val = self.cast_value(val, vtype)
            self.env[name] = val
            return val
        elif t == 'ASSIGN':
            name = node[1]; expr = node[2]
            val = self.eval(expr)
            self.env[name] = val
            return val
        elif t == 'OUTCOME':
            val = self.eval(node[1])
            print(val)
            return None
        elif t == 'NUMBER' or t == 'STRING':
            return node[1]
        elif t == 'VAR':
            name = node[1]
            if name in self.env:
                return self.env[name]
            raise NameError(f'Undefined variable: {name}')
        elif t == 'NEG':
            return -self.eval(node[1])
        elif t == 'PLUS':
            left = self.eval(node[1]); right = self.eval(node[2])
            # if either is string, concat as strings
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        elif t == 'MINUS':
            return self.eval(node[1]) - self.eval(node[2])
        elif t == 'MUL':
            return self.eval(node[1]) * self.eval(node[2])
        elif t == 'DIV':
            return self.eval(node[1]) / self.eval(node[2])
        else:
            raise RuntimeError(f'Unknown AST node: {t}')

# ---------- RUN/TOP-LEVEL ----------
def run(code, show_tokens=False):
    tokens = tokenize(code)
    if show_tokens:
        print('TOKENS:', tokens)
    p = Parser(tokens)
    ast = p.parse()
    intr = Interpreter()
    intr.eval(ast)

def run_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    run(code)

def repl():
    intr = Interpreter()
    print('SaLangDev REPL — type "exit" to quit.')
    buffer = ''
    while True:
        try:
            line = input('>>> ').rstrip()
        except (EOFError, KeyboardInterrupt):
            print('\\nBye'); break
        if line.strip() == 'exit':
            break
        if not line and buffer:
            try:
                run(buffer)
            except Exception as e:
                print('Error:', e)
            buffer = ''
            continue
        buffer += line + '\\n'
        # heuristics: evaluate when user ends a statement
        if line.strip().startswith('outcome') or line.strip().startswith('set') or '=' in line:
            try:
                run(buffer)
            except Exception as e:
                print('Error:', e)
            buffer = ''

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print('Usage: salangdev <file.salangdev>  OR  salangdev -i  for REPL')
        return
    if argv[0] in ('-i', '--repl'):
        repl(); return
    filepath = argv[0]
    run_file(filepath)

if __name__ == '__main__':
    main()
