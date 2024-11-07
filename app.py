import json
import re

from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    result_dic = {}
    try:
        source = request.data.decode()

        tokens = tokenize(source)
        tokens2 = tokenize(source)

        tokens_dic = {}

        for i in range(len(tokens2) - 1):
            tokens_dic['token-' + str(i + 1)] = tokens2[i]

        cf_tokens = constant_folding(tokens)

        cf_code = reconstruct(cf_tokens).split('\n')

        dce_tokens = dead_code_elimination(tokens)

        dce_code = reconstruct(dce_tokens).split('\n')

        combined_tokens = constant_folding(dce_tokens)

        combined_code = reconstruct(combined_tokens).split('\n')

        result_dic['Original Code'] = source.split('\n')
        result_dic['Constant Folding Optimized'] = cf_code
        result_dic['Dead Code Elimination Optimized'] = dce_code
        result_dic['Combined Techniques'] = combined_code
        result_dic['Tokens'] = tokens_dic

        return json.dumps(result_dic)

    except Exception as e:
        # Return an error message in case of exceptions
        print(f'Error: {e}')
    # return json.dumps({'error': 'An error occurred processing your file'}), 500
    return json.dumps(result_dic)





class ParsingException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message



def tokenize(source):

    token_regexes = [
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r'\{', 'LBRACE'),
    (r'\,', 'COMMA'),
    (r'\}', 'RBRACE'),
    (r'\;', 'SEMICOLON'),
    (r'\.', 'DOT'),
    (r'\[', 'LBRACKET'),
    (r'\]', 'RBRACKET'),
    (r'\+', 'PLUS'),
    (r'\-', 'MINUS'),
    (r'\*', 'ASTERISK'),
    (r'\/', 'SLASH'),
    (r'%', 'MOD'),
    (r'==', 'EE'),
    (r'=', 'EQUAL'),
    (r'!=', 'NOTEQUAL'),
    (r'<', 'LT'),
    (r'>', 'GT'),
    (r'<=', 'LTE'),
    (r'>=', 'GTE'),
    (r'&&', 'AND'),
    (r'\|\|', 'OR'),
    (r'!', 'NOT'),
    (r'if', 'IF'),
    (r'else', 'ELSE'),
    (r'while', 'WHILE'),
    (r'return', 'RETURN'),
    (r'printf', 'PRINT'),
    (r'int', 'INT'),
    (r'float', 'float'),
    (r'boolean', 'BOOLEAN'),
    (r'true', 'TRUE'),
    (r'false', 'FALSE'),
    (r'\d+', 'INTEGER'),
    (r'^\d+\.\d+$', 'FLOAT'),
    (r'main', 'MAIN'),
    (r'[a-zA-Z_]\w*', 'IDENTIFIER'),
    (r'\s+', 'WHITESPACE'),
    (r'\n', 'NEWLINE'),
    (r'"(.*?)"', 'STRING_LITERAL')
    ]

    tokens = []
    t = []
    line = 1

    while source:
        # Match the longest possible token
        for regex, token_type in token_regexes:
            match = re.match(regex, source)
            if match:
                # Extract the token and advance the source
                token = match.group(0)
                source = source[len(token):]

                # add the found token to the list of tokens
                tokens.append([
                     token_type, token
                ])

                # Break out of the loop if a token was found
                break

        # If no token was found, raise an error
        else:
            raise ValueError('Invalid character at line {}: {}'.format(line, source[0]))

    for c in tokens:
      if c[0] == "WHITESPACE":
        tokens.remove(c)

    return tokens

def constant_folding(tokens):
    new_tokens = []
    i = 0

    while i < len(tokens):
        if tokens[i][0] in ['INTEGER', 'FLOAT']:  # Check for both integer and float constants
            # Check if the next token is an operator and the following token is a constant
            if (tokens[i+1][0] in ['PLUS', 'MINUS', 'ASTERISK', 'SLASH']) and (tokens[i+2][0] in ['INTEGER', 'FLOAT']):
                result = ''
                # Evaluate the expression and replace it with the result
                operator = tokens[i+1][0]
                if tokens[i][0] == 'INTEGER':
                    left_operand = int(tokens[i][1])
                else:
                    left_operand = float(tokens[i][1])
                if tokens[i+2][0] == 'INTEGER':
                    right_operand = int(tokens[i+2][1])
                else:
                    right_operand = float(tokens[i+2][1])

                if operator == 'PLUS':
                    result = left_operand + right_operand
                elif operator == 'MINUS':
                    result = left_operand - right_operand
                elif operator == 'ASTERISK':
                    result = left_operand * right_operand
                elif operator == 'SLASH':
                    result = left_operand / right_operand

                if isinstance(result, int):  # Check if the result is an integer
                    new_tokens.append(['INTEGER', str(result)])
                else:
                    new_tokens.append(['FLOAT', str(result)])
                i += 3
            else:
                new_tokens.append(tokens[i])
                i += 1
        else:
            new_tokens.append(tokens[i])
            i += 1

    return new_tokens



def reconstruct(tokens):
    result = ""
    line = ""
    line_number = 1
    i = 0
    tokens = clean_up(tokens)

    while i < len(tokens):
        token = tokens[i]
        line += " "
        if token[0] == "STRING_LITERAL":
            line += '"' + token[1][1:-1] + '"'
        elif token[0] == "IDENTIFIER":
            if i + 1 < len(tokens) and tokens[i+1][0] == "EQUAL":
                line += token[1] + " " + tokens[i+1][1]
                i += 1
            else:
                line += token[1]
        elif token[0] in  ['SEMICOLON','LBRACE', 'RBRACE']:
            line += token[1] + '\n'
        else:
            line += token[1]
        i += 1
    result += line
    # print(result)
    return result


def parse_program(tokens):
    program_structure = []
    if tokens[0][0] == 'INT' and tokens[1][0] == 'MAIN' and tokens[2][0] == 'LPAREN' and tokens[3][0] == 'RPAREN' and tokens[4][0] == 'LBRACE':
      main_func = []
      main_func += tokens[0]
      main_func += tokens[1]
      main_func += tokens[2]
      main_func += tokens[3]

      program_structure += [['MAIN FUNCTION', main_func]]
      program_structure += tokens[4]

      index = 5
      while index < len(tokens)-1:
        # print('Outer While loop', index)
        try:
          statements, index = parse_statements(tokens, index)
          program_structure += ['STATEMENTS', statements]
        except ParsingException as e:
          raise e
          # break
    program_structure += tokens[index]

    print('Program Structure')
    return program_structure

def parse_return(tokens, index):
  ret_stmt = []
  if tokens[index][0] == 'RETURN':
        ret_stmt += tokens[index]
        ret_stmt += tokens[index+1]
        ret_stmt += tokens[index+2]
  else:
    raise ParsingException('Unable to parse return')

  return ret_stmt, index + 3


def parse_statements(tokens, index):
  statements = []
  while True:

    try:

      if_stmt, index = parse_if_statement(tokens, index)
      statements += ["IF STATEMENT" , if_stmt];
      else_stmt, index = parse_else_statement(tokens, index)
    except ParsingException:

      try:
        print_stmt, index = parse_print_statement(tokens, index)
        statements += ["PRINT STATEMENT", print_stmt ]
      except ParsingException:

        try:
          math_exp, index = parse_math_expression(tokens, index)
          statements += ["MATH", math_exp]
        except ParsingException:
            try:
              var_assign, index = parse_var_assign(tokens, index)
              statements += ["VAR ASSIGNMENT", var_assign]
            except ParsingException as e:
              try:

                ret_stmt, index = parse_return(tokens, index)
                statements+= ['RETURN LINE', ret_stmt]
              except ParsingException as e:
                break

  return statements, index


def parse_if_statement(tokens, index):
  if_stmt = []

  if tokens[index][0] == 'IF' and tokens[index+1][0] == 'LPAREN':
    if_stmt.append(tokens[index])
    if_stmt.append(tokens[index+1])
    comp_exp, index = parse_comp_expression(tokens, index+2)
    if comp_exp != []:
      for token in comp_exp:
        if_stmt.append(token)
    else:
      raise ParsingException('Invalid if statement')
    if tokens[index][0] == 'RPAREN' and tokens[index+1][0] == 'LBRACE':
      if_stmt.append(tokens[index])
      if_stmt.append(tokens[index+1])

      try:
        nested_stmts, index = parse_statements(tokens, index+2)
        for t in nested_stmts:
          if_stmt.append(t)
          # print(tokens[index], index)
          # print(tokens[index+1], index+1)
      except ParsingException:
        print()

      #add the nested statement to the if statement structure list


    if tokens[index][0] == 'RBRACE':
      if_stmt.append(tokens[index])
    else:
      raise ParsingException('atement')
    try:
      else_stmt, index = parse_else_statement(tokens, index+1)
    except ParsingException:
      pass
  else:
    raise ParsingException('Invalid if statement')

  return if_stmt, index


def parse_else_statement(tokens, index):
  else_stmt = []
  if tokens[index][0] == 'ELSE' and tokens[index+1][0] == 'LBRACE':
    else_stmt.append(tokens[index])
    else_stmt.append(tokens[index+1])

    nested_stmts, index = parse_statements(tokens, index+2)
    for t in nested_stmts:
        else_stmt.append(t)
  # print(tokens[index])
  if tokens[index][0] == 'RBRACE':
    else_stmt.append(tokens[index])
  else:
    raise ParsingException('Invalid else statement')
  return else_stmt, index+1


def parse_var_assign(tokens, index):
  var_assign = []
  if tokens[index][0] == "INT" and tokens[index+1][0] == "IDENTIFIER":

    var_assign.append(tokens[index])
    var_assign.append(tokens[index+1])
    X=2
    # print('works')
    while tokens[index+X][0] != 'SEMICOLON':
      var_assign.append(tokens[index+X])
      X+=1
    else:
      # print('works here')
      var_assign.append(tokens[index+X])
    index +=X + 1
  elif tokens[index][0] == "IDENTIFIER" and tokens[index+1][0] == "EQUAL":
    var_assign.append(tokens[index])
    var_assign.append(tokens[index+1])
    X=2
    # print('works')
    while tokens[index+X][0] != 'SEMICOLON':
      var_assign.append(tokens[index+X])
      X+=1
    else:
      # print('works here')
      var_assign.append(tokens[index+X])
    index +=X +1

  else:
    raise ParsingException('Invalid Assignment')
  return var_assign, index


def parse_print_statement(tokens, index):
  print_statement = []
  if tokens[index][0] == 'PRINT':
    if tokens[index+1][0] == "LPAREN" and tokens[index+2][0] == "STRING_LITERAL" and tokens[index+3][0] == "RPAREN" and tokens[index+4][0] == "SEMICOLON":
      print_statement.append(tokens[index])
      print_statement.append(tokens[index+1])
      print_statement.append(tokens[index+2])
      print_statement.append(tokens[index+3])
      print_statement.append(tokens[index+4])
      index+=5
    else:
      raise ParsingException("Invalid print statement")
  else:
    raise ParsingException("Invalid print statement")
  return print_statement, index


def parse_math_expression(tokens, index):
  math_exp = []
  if tokens[index][0] in ['INTEGER', 'FLOAT'] and tokens[index+1][0] in ['PLUS', 'MINUS', 'ASTERICK', 'SLASH']:
    math_exp.append(tokens[index])
    math_exp.append(tokens[index+1])
    math_exp.append(tokens[index+2])
    X=3
    while tokens[index+X][0] != 'SEMICOLON':
      if tokens[index + X][0] in ['INTEGER', 'FLOAT'] and tokens[index+X+1][0] in ['PLUS', 'MINUS', 'ASTERICK', 'SLASH','MOD']:
        math_exp.append(tokens[index+X])
        math_exp.append(tokens[index+X+1])
        X+=2
      else:
        math_exp.append(tokens[index+X])
    index += X + 1
  else:
    raise ParsingException('Invalid math expression')
  return math_exp, index


def parse_comp_expression(tokens, index):
  comp_exp = []

  if tokens[index][0] == "IDENTIFIER" or tokens[index][0] in ['INTEGER','FLOAT']:
    if tokens[index+1][0] in ['GT','LT','EQUAL', 'GTE', 'LTE']:
      comp_exp.append(tokens[index])
      comp_exp.append(tokens[index+1])
      comp_exp.append(tokens[index+2])
      index+=3
    else:
      raise ParsingException("Error in comparison expression")
  else:
    # print("exception")
    raise ParsingException("Error in comparison expression")
  return comp_exp, index


def dead_code_elimination(tokens):
    unused_identifiers = []
    for i in range(len(tokens)-1):
      used = False
      if tokens[i][0] == 'IDENTIFIER':
        for c in range(len(tokens)-1):
          if c==i:
            continue
          else:
            if tokens[c][0]== 'IDENTIFIER':
              if tokens[c][1] == tokens[i][1]:
                used = True

        if used == False :
          # unused_identifiers.append(tokens[i][1])
          # print(unused_identifiers)
          for m in range(i, len(tokens)-1):
            # print('M', m)
            # print('Token at index m', tokens[m])
            if tokens[m][0] == 'SEMICOLON':
              end_index = m
              break

          # for t in range(i-1, end_index):
          #   print('t', t)
          #   print(tokens[t])
          #   print(tokens[i], i)
          # del tokens[i-1:end_index+1]
          for p in range(i-1, end_index+1):
            tokens[p][0] = 'DELETED'


    for i in range(len(tokens)-1):
      result = False
      if tokens[i][0] == 'IF':
        if tokens[i+2][0] == 'INTEGER' and tokens[i+4][0] == 'INTEGER':
          if tokens[i+3][0]=='GT':
            result = int(tokens[i+2][1]) > int(tokens[i+4][1])
          elif tokens[i+3][0]=='GTE':
            result = int(tokens[i+2][1]) >= int(tokens[i+4][1])
          elif tokens[i+3][0]=='LT':
            result = int(tokens[i+2][1]) < int(tokens[i+4][1])
          elif tokens[i+3][0]=='LTE':
            result = int(tokens[i+2][1]) <= int(tokens[i+4][1])
          elif tokens[i+3][0]=='EE':
            result = int(tokens[i+2][1]) == int(tokens[i+4][1])
          elif tokens[i+3][0]=='NOTEQUAL':
            result = int(tokens[i+2][1]) <= int(tokens[i+4][1])
        # print(result)
        if result == True:
          for c in range(i, len(tokens)-1):

            if tokens[c][0] == 'ELSE':
              start_index = c
              for n in range(c,len(tokens)-1):
                # print(tokens[n])
                # print(tokens)
                if tokens[n][0] == 'RBRACE':
                  end_index = n
                  break
          # print(c,n)
          for x in range(start_index, end_index+1):
            tokens[x][0] = 'DELETED'
    return tokens


def clean_up(tokens):
    new_tokens = []
    for token in tokens:
        if token[0] != 'DELETED':
            new_tokens.append(token)

    return new_tokens


if __name__ == '__main__':
    app.run()
