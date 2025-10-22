from mcdplib.core.string import substring


def execute(code: str, context: dict) -> None:
    exec(code, dict(), context)


def evaluate(expression: str, context: dict) -> any:
    return eval(expression, dict(), context)


def evaluate_substrings(string: str, context: dict, expression_boundary_characters: str) -> str:
    formatted_string: str = ""
    expression: str = ""
    reading_expression: bool = False
    character_index: int = 0
    while character_index < string.__len__():
        if substring(string, character_index, expression_boundary_characters.__len__()) == expression_boundary_characters:
            if reading_expression:
                formatted_string += evaluate(expression, context).__str__()
                expression = ""
            reading_expression = not reading_expression
            character_index += expression_boundary_characters.__len__() - 1
        else:
            if reading_expression:
                expression += string[character_index]
            else:
                formatted_string += string[character_index]
        character_index += 1
    return formatted_string
