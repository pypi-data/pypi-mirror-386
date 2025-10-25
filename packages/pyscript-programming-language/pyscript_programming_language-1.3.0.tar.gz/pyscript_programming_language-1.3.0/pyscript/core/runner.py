from .analyzer import PysAnalyzer
from .buffer import PysFileBuffer
from .constants import DEFAULT, SILENT, RETRES, COMMENT
from .context import PysContext
from .exceptions import PysException
from .handlers import handle_execute
from .interpreter import interpreter
from .lexer import PysLexer
from .parser import PysParser
from .position import PysPosition
from .results import PysExecuteResult
from .symtab import PysSymbolTable, build_symbol_table
from .utils import is_object_of, get_locals, print_display
from .version import version

from . import cache

import sys

def pys_runner(
    file,
    mode,
    symbol_table,
    flags=None,
    context_parent=None,
    context_parent_entry_position=None
):

    context = PysContext(
        file=file,
        name='<program>',
        flags=flags,
        symbol_table=symbol_table,
        parent=context_parent,
        parent_entry_position=context_parent_entry_position
    )

    result = PysExecuteResult(mode, context)

    try:

        try:

            lexer = PysLexer(
                file=file,
                flags=context.flags & ~COMMENT,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            tokens, error = lexer.make_tokens()
            if error:
                return result.failure(error)

            parser = PysParser(
                file=file,
                tokens=tokens,
                flags=context.flags,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            ast = parser.parse(None if mode == 'exec' else parser.expr)
            if ast.error:
                return result.failure(ast.error)

            analyzer = PysAnalyzer(
                file=file,
                flags=parser.flags,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            error = analyzer.visit(ast.node)
            if error:
                return result.failure(error)

        except RecursionError:
            return result.failure(
                PysException(
                    RecursionError("maximum recursion depth exceeded during complication"),
                    context,
                    PysPosition(file, -1, -1)
                )
            )

        context.flags = parser.flags

        runtime_result = interpreter.visit(ast.node, context)

        if runtime_result.error:
            return result.failure(runtime_result.error)

        return result.success(runtime_result.value)

    except KeyboardInterrupt as e:
        return result.failure(PysException(e, context, PysPosition(file, -1, -1)))

def pys_exec(source, globals=None, flags=DEFAULT):
    """
    Execute a PyScript code from source given.

    Parameters
    ----------
    source: A valid PyScript source code.

    globals: A namespace dictionary or symbol table that can be accessed. \
             If it is None, it uses the current global namespace at the Python level.

    flags: A special flags.
    """

    file = PysFileBuffer(source)

    if globals is None:
        globals = build_symbol_table(file, get_locals(2))
    elif isinstance(globals, dict):
        globals = build_symbol_table(file, globals)
    elif not isinstance(globals, PysSymbolTable):
        raise TypeError("pys_exec(): globals must be dict or pyscript.core.symtab.PysSymbolTable")

    if not isinstance(flags, int):
        raise TypeError("pys_exec(): flags must be integer")

    result = pys_runner(
        file=file,
        mode='exec',
        symbol_table=globals,
        flags=flags
    )

    if flags & RETRES:
        return result

    elif result.error and not (flags & SILENT):
        raise result.error.exception

def pys_eval(source, globals=None, flags=DEFAULT):
    """
    Evaluate a PyScript code from source given.

    Parameters
    ----------
    source: A valid PyScript (Expression) source code.

    globals: A namespace dictionary or symbol table that can be accessed. \
            If it is None, it uses the current global namespace at the Python level.

    flags: A special flags.
    """

    file = PysFileBuffer(source)

    if globals is None:
        globals = build_symbol_table(file, get_locals(2))
    elif isinstance(globals, dict):
        globals = build_symbol_table(file, globals)
    elif not isinstance(globals, PysSymbolTable):
        raise TypeError("pys_eval(): globals must be dict or pyscript.core.symtab.PysSymbolTable")

    if not isinstance(flags, int):
        raise TypeError("pys_eval(): flags must be integer")

    result = pys_runner(
        file=file,
        mode='eval',
        symbol_table=globals,
        flags=flags
    )

    if flags & RETRES:
        return result

    elif result.error and not (flags & SILENT):
        raise result.error.exception

    return result.value

def pys_shell(symbol_table=None, flags=DEFAULT):
    """
    Start an interactive PyScript shell.
    """

    print('PyScript {}'.format(version))
    print('Python {}'.format(sys.version))
    print('Type "license" for more information.')

    if symbol_table is None:
        symbol_table = build_symbol_table(PysFileBuffer('', '<pyscript-shell>'))
        symbol_table.set('__name__', '__main__')

    cache.hook.display = print_display

    line = 0
    parenthesis_level = 0
    in_string = False
    in_decorator = False
    is_triple_string = False
    next_line = False
    string_prefix = ''
    full_text = ''

    def reset_next_line():
        nonlocal parenthesis_level, in_string, in_decorator, string_prefix, is_triple_string, next_line, full_text
        parenthesis_level = 0
        in_string = False
        in_decorator = False
        string_prefix = ''
        is_triple_string = False
        next_line = False
        full_text = ''

    def is_next_line():
        return parenthesis_level > 0 or in_decorator or is_triple_string or next_line

    while True:

        try:

            if is_next_line():
                text = input(cache.hook.ps2)

            else:
                text = input(cache.hook.ps1)
                if text == '!exit':
                    return 0

            next_line = False
            in_decorator = False
            is_space = True

            i = 0

            while i < len(text):
                character = text[i]

                if character == '\\':
                    i += 1
                    character = text[i:i+1]

                    if character == '':
                        next_line = True
                        break

                    if in_string and character in '\'"':
                        i += 1

                elif character in '\'"':
                    bind_3 = text[i:i+3]

                    if is_triple_string:

                        if len(bind_3) == 3 and string_prefix * 3 == bind_3:
                            in_string = False
                            is_triple_string = False
                            i += 2

                    else:
                        if not in_string and bind_3 in ("'''", '"""'):
                            is_triple_string = True
                            i += 2

                        if in_string and string_prefix == character:
                            in_string = False
                        else:
                            string_prefix = character
                            in_string = True

                if not in_string:

                    if character == '#':
                        break

                    elif is_space and character == '@':
                        in_decorator = True

                    elif character in '([{':
                        parenthesis_level += 1

                    elif character in ')]}':
                        parenthesis_level -= 1

                    if not character.isspace():
                        is_space = False

                i += 1

            if in_string and not (next_line or is_triple_string):
                in_string = False
                parenthesis_level = 0

            if is_next_line():
                full_text += text + '\n'

            else:
                result = pys_runner(
                    file=PysFileBuffer(full_text + text, '<pyscript-shell-{}>'.format(line)),
                    mode='exec',
                    symbol_table=symbol_table,
                    flags=flags
                )

                flags = result.context.flags

                reset_next_line()

                if result.error and is_object_of(result.error.exception, SystemExit):
                    return result.error.exception.code

                code = handle_execute(result)
                if code == 0:
                    line += 1

        except KeyboardInterrupt:
            reset_next_line()
            print('\rKeyboardInterrupt. Type "exit" or "!exit" to exit the program.', file=sys.stderr)

        except EOFError:
            return 0