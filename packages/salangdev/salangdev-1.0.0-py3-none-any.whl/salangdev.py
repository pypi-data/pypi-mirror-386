#!/usr/bin/env python3
"""SalLang interpreter v1.0
Keywords (mapped):
  digit       -> integer type
  one_letter  -> char (single-character string)
  letters     -> string
  outcome     -> print/output
Usage:
  - Declaration: set x [type] = expression
      Examples:
         set a digit = 5
         set name letters = "Salman"
         set c one_letter = "A"
  - Assignment without set (also allowed):
         a = 10
  - Print/output:
         outcome a + 5
  - Comments start with //
  - Save files with .salangdev extension and run:
         salangdev myprog.salangdev
"""

import re
import sys

# ---- Lexer ----
TOKEN_SPEC = [
    ('NUMBER',   r'\d+(?:\.\d+)?'),
    ('STRING',   r'"([^"\\]|\\.)*"'),
    ('SET',      r'set\b'),
    ('DIGIT',    r'digit\b'),
    ('ONE_LETTER', r'one_letter\b'),
    ('LETTERS',  r'letters\b'),
    ('OUTCOME',  r'outcome\b'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
    ('ASSIGN',   r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('MUL',      r'\*'),
    ('DIV',      r'/'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t]+'),
    ('COMMENT',  r'//.*'),
    ('UNKNOWN',  r'.'),
]

TOKEN_REGEX = re.compile('|'.join(f'(?P<{n}>{p})' for n,p in TOKEN_SPEC))
KEYWORDS = {'set','digit','one_letter','letters','outcome'}

def tokenize(code):
    pos = 0
    tokens = []
    while pos < len(code):
        m = TOKEN_REGEX.match(code, pos)
        if not m:
            raise SyntaxError(f'Unexpected character: {code[pos]!r} at {pos}')
        kind = m.lastgroup
        value = m.group()
        pos = m.end()
        if kind == 'NUMBER':
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
            tokens.append(('NUMBER', value))
        elif kind == 'STRING':
            tokens.append(('STRING', bytes(value[1:-1], "utf-8").decode("unicode_escape")))
        elif kind in ('SET','DIGIT','ONE_LETTER','LETTERS','OUTCOME'):
            tokens.append((kind, value))
        elif kind == 'ID':
            tokens.append(('ID', value))
        elif kind == 'NEWLINE' or kind == 'SKIP' or kind == 'COMMENT':
            if kind == 'NEWLINE':
                tokens.append(('NEWLINE', '\n'))
            continue
        elif kind == 'UNKNOWN':
            raise SyntaxError(f'Unknown token: {value}')
        else:
            tokens.append((kind, value))
    tokens.append(('EOF', None))
    return tokens

# ---- Parser & Interpreter ----
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    def peek(self):
        return self.tokens[self.pos][0]
    def peek_val(self):
        return self.tokens[self.pos][1]
    def eat(self, expected=None):
        tok = self.tokens[self.pos]
        if expected and tok[0] != expected:
            raise SyntaxError(f'Expected {expected}, got {tok} at pos {self.pos}')
        self.pos += 1
        return tok
    def parse(self):
        stmts = []
        while self.peek() != 'EOF':
            if self.peek() == 'NEWLINE':
                self.eat('NEWLINE'); continue
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
        # optional type
        var_type = None
        if self.peek() in ('DIGIT','ONE_LETTER','LETTERS'):
            typ = self.eat(self.peek())[0]
            var_type = typ  # 'DIGIT' etc.
        if self.peek() == 'ASSIGN':
            self.eat('ASSIGN')
            expr = self.parse_expression()
            return ('SET', name, var_type, expr)
        else:
            raise SyntaxError('Expected "=" in set declaration')
    # Expression parsing (basic precedence)
    def parse_expression(self):
        return self.parse_term()
    def parse_term(self):
        node = self.parse_factor()
        while self.peek() in ('PLUS','MINUS'):
            op = self.eat()[0]
            right = self.parse_factor()
            node = (op, node, right)
        return node
    def parse_factor(self):
        node = self.parse_unary()
        while self.peek() in ('MUL','DIV'):
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
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, str):
                return value
            return str(value)
        return value
    def eval(self, node):
        t = node[0]
        if t == 'PROGRAM':
            return self.eval_program(node)
        elif t == 'SET':
            name = node[1]; vtype = node[2]; expr = node[3]
            val = self.eval(expr)
            # cast based on declared type
            if vtype:
                val = self.cast_value(val, vtype)
            self.env[name] = val
            return val
        elif t == 'ASSIGN':
            name = node[1]; expr = node[2]
            if name not in self.env:
                # implicit declaration without type
                self.env[name] = self.eval(expr)
            else:
                self.env[name] = self.eval(expr)
            return self.env[name]
        elif t == 'OUTCOME':
            val = self.eval(node[1])
            print(val)
            return None
        elif t == 'NUMBER':
            return node[1]
        elif t == 'STRING':
            return node[1]
        elif t == 'VAR':
            name = node[1]
            if name in self.env:
                return self.env[name]
            else:
                raise NameError(f'Undefined variable: {name}')
        elif t in ('PLUS','MINUS','MUL','DIV'):
            left = self.eval(node[1]); right = self.eval(node[2])
            if t == 'PLUS': return left + right
            if t == 'MINUS': return left - right
            if t == 'MUL': return left * right
            if t == 'DIV': return left / right
        elif t == 'NEG':
            return -self.eval(node[1])
        else:
            raise RuntimeError(f'Unknown AST node: {t}')
    def eval_program(self, prog):
        for stmt in prog[1]:
            self.eval(stmt)
# ---- Utilities ----
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

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print('Usage: salangdev <file.salangdev>')
        print('Or run repl by passing -i')
        return
    if argv[0] in ('-i','--repl'):
        repl()
        return
    run_file(argv[0])

def repl():
    intr = Interpreter()
    print('SalLang REPL — type "exit" to quit.')
    buffer = ''
    while True:
        try:
            line = input('>>> ').rstrip()
        except (EOFError, KeyboardInterrupt):
            print('\nBye'); break
        if line.strip() == 'exit':
            break
        if not line and buffer:
            try:
                run(buffer)
            except Exception as e:
                print('Error:', e)
            buffer = ''
            continue
        buffer += line + '\n'
        if line.strip().startswith('outcome') or line.strip().startswith('set') or '=' in line:
            try:
                run(buffer)
            except Exception as e:
                print('Error:', e)
            buffer = ''

if __name__ == '__main__':
    main()
