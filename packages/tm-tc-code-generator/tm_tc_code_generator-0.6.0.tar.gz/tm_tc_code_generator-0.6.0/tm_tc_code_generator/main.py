import json
import re
import importlib.resources
import pathlib

import click
import jinja2


def camel_to_snake(name):
    # Replace uppercase letters with an underscore followed by the lowercase version
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    return name


def upper_first_letter(string):
    return string[0].upper() + string[1:]


def generate_telecommand_base_header(template, telecommand, output_dir):
    snake = camel_to_snake(telecommand['name'])
    uppercase_name = snake.upper()
    camel_case = upper_first_letter(telecommand['name'])
    if 'return' in telecommand:
        if telecommand['return']['type'] == 'string':
            return_name = telecommand['return']['name']
            string_length = telecommand['return']['stringLength']
            returns = f'char {return_name}[{string_length}];'
        else:
            returns = telecommand['return']['type'] + ' ' + telecommand['return']['name'] + ';'
    else:
        returns = None
    arguments = telecommand['arguments'] if 'arguments' in telecommand else None
    enums = {}
    if arguments:
        for argument in arguments:
            if argument['type'] == 'enum':
                enum_name = upper_first_letter(argument['enumName'])
                values = []
                for value in argument['values']:
                    values.append(uppercase_name + '_' + camel_to_snake(enum_name).upper() + '_' + value)
                enums[enum_name] =  values
                argument['type'] = f'{camel_case}{enum_name}_t'
    output = template.render(uppercase_name=uppercase_name,
                             camel_case=camel_case,
                             returns=returns,
                             arguments=arguments,
                             enums=enums,
                             snake_case=snake)
    with open(output_dir / f'{snake}_base.h', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telecommand_base_source(template, telecommand, output_dir):
    snake = camel_to_snake(telecommand['name'])
    uppercase_name = snake.upper()
    operation = telecommand['id']
    camel_case = upper_first_letter(telecommand['name'])
    output = template.render(uppercase_name=uppercase_name,
                             camel_case=camel_case,
                             operation=operation,
                             snake_case=snake)
    with open(output_dir / f'{snake}_base.c', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telemetry_base_header(template, telemetry, output_dir):
    snake = camel_to_snake(telemetry['name'])
    uppercase_name = snake.upper()
    camel_case = upper_first_letter(telemetry['name'])
    output = template.render(uppercase_name=uppercase_name,
                             camel_case=camel_case,
                             snake_case=snake)
    with open(output_dir / f'tm_{snake}_base.h', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telemetry_base_source(template, telemetry, output_dir):
    snake = camel_to_snake(telemetry['name'])
    uppercase_name = snake.upper()
    operation = telemetry['id']
    camel_case = upper_first_letter(telemetry['name'])
    output = template.render(uppercase_name=uppercase_name,
                             camel_case=camel_case,
                             operation=operation,
                             snake_case=snake)
    with open(output_dir / f'tm_{snake}_base.c', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telecommand_auto_source(template, telecommand, output_dir):
    snake = camel_to_snake(telecommand['name'])
    camel_case = upper_first_letter(telecommand['name'])
    output = template.render(camel_case=camel_case,
                             snake_case=snake)
    with open(output_dir / f'{snake}_auto.c', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telemetry_auto_source(template, telemetry, output_dir):
    snake = camel_to_snake(telemetry['name'])
    camel_case = upper_first_letter(telemetry['name'])
    output = template.render(camel_case=camel_case,
                             snake_case=snake)
    with open(output_dir / f'tm_{snake}_auto.c', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telecommand_header(template, telecommand, output_dir):
    snake = camel_to_snake(telecommand['name'])
    uppercase_name = snake.upper()
    camel_case = upper_first_letter(telecommand['name'])
    output = template.render(uppercase_name=uppercase_name,
                             camel_case=camel_case,
                             snake_case=snake)
    with open(output_dir / f'{snake}.h', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telemetry_header(template, telemetry, output_dir):
    snake = camel_to_snake(telemetry['name'])
    uppercase_name = snake.upper()
    camel_case = upper_first_letter(telemetry['name'])
    enums = {}
    parameters = telemetry['parameters']
    for parameter in parameters:
        if parameter['type'] == 'enum':
            enum_name = upper_first_letter(parameter['enumName'])
            values = []
            for value in parameter['values']:
                values.append(uppercase_name + '_' + camel_to_snake(enum_name).upper() + '_' + value)
            enums[enum_name] =  values
            parameter['name'] = f'{camel_case}{enum_name}_t'
        elif parameter['type'] == 'string':
            string_name = parameter['name']
            string_length = parameter['size']
            parameter['name'] = f'char {string_name}[{string_length}]'

    output = template.render(uppercase_name=uppercase_name,
                             camel_case=camel_case,
                             parameters=parameters,
                             enums=enums,
                             snake_case=snake)
    with open(output_dir / f'tm_{snake}.h', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telecommand_source(template, telecommand, output_dir):
    snake = camel_to_snake(telecommand['name'])
    camel_case = upper_first_letter(telecommand['name'])
    output = template.render(camel_case=camel_case,
                             snake_case=snake)
    with open(output_dir / f'{snake}.c', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telemetry_source(template, telemetry, output_dir):
    snake = camel_to_snake(telemetry['name'])
    camel_case = upper_first_letter(telemetry['name'])
    output = template.render(camel_case=camel_case,
                             snake_case=snake)
    with open(output_dir / f'tm_{snake}.c', 'w') as file_handler:
        print(output, file=file_handler)


def generate_telecommand_class(template, telecommand, output_dir):
    class_name = camel_to_snake(telecommand['name'])

    # Prepare the data for the template
    template_data = {
        'class_name': class_name,
        'telecommand_name': camel_to_snake(telecommand['name']),
        'operation_id': telecommand['id'],
        'num_inputs': len(telecommand.get('arguments', [])),
        'arguments': telecommand.get('arguments', []),
        'return_type': telecommand.get('return', {}).get('type', None),
        'return_name': telecommand.get('return', {}).get('name', None)
    }

    # Render the template with data
    class_code = template.render(template_data, enumerate=enumerate)

    # Write the generated class code to a Python file
    with open(output_dir / f'{class_name}.py', 'w') as file_handler:
        print(class_code, file=file_handler)


def generate_package_initializer(env, telecommands, output_dir):
    package_initializer_template = env.get_template('package_initializer.jinja')
    commands_snake = [camel_to_snake(command['name']) for command in telecommands]
    output = package_initializer_template.render(commands=commands_snake)
    with open(output_dir / f'__init__.py', 'w') as file_handler:
        print(output, file=file_handler)


def generate_pyproject(env, app_name, output_dir):
    pyproject_template = env.get_template('pyproject.toml.jinja')
    app_name_snake = app_name.replace('-', '_')
    output = pyproject_template.render(app_name=app_name, app_name_snake=app_name_snake)
    with open(output_dir / f'pyproject.toml', 'w') as file_handler:
        print(output, file=file_handler)


@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('output_dir', type=click.Path(exists=False, file_okay=False, path_type=pathlib.Path))
@click.argument('app_name')
def main(input_file: pathlib.Path, output_dir: pathlib.Path, app_name: str):
    # Parse JSON file
    with open(input_file) as file_handler:
        file_contents = file_handler.read()
    parsed_json = json.loads(file_contents)

    py_tm_output_dir = output_dir / 'py' / 'tm'
    py_tc_base_output_dir = output_dir / 'py' / 'tc'
    py_tc_output_dir = output_dir / 'py' / 'tc' / app_name.replace('-', '_')
    c_tm_output_dir = output_dir / 'c' / 'tm'
    c_tc_output_dir = output_dir / 'c' / 'tc'

    output_dir.mkdir(parents=True, exist_ok=True)
    py_tm_output_dir.mkdir(parents=True, exist_ok=True)
    py_tc_output_dir.mkdir(parents=True, exist_ok=True)
    c_tm_output_dir.mkdir(parents=True, exist_ok=True)
    c_tc_output_dir.mkdir(parents=True, exist_ok=True)

    with importlib.resources.path('tm_tc_code_generator', 'templates') as templates_path:
        # Load the environment
        env_python = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_path))
        # TODO: Update template to use same env for both C and Python
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_path))
        env.trim_blocks = True
        env.lstrip_blocks = True

    # Loading the templates
    telecommand_base_header_template = env.get_template('telecommand_base_header.jinja')
    telecommand_base_source_template = env.get_template('telecommand_base_source.jinja')
    telecommand_auto_source_template = env.get_template('telecommand_auto_source.jinja')
    telecommand_header_template = env.get_template('telecommand_header.jinja')
    telecommand_source_template = env.get_template('telecommand_source.jinja')
    telecommand_python_template = env_python.get_template("telecommand_python.jinja")

    telecommands = parsed_json['telecommands']

    generate_package_initializer(env_python, telecommands, py_tc_output_dir)
    generate_pyproject(env_python, app_name, py_tc_base_output_dir)

    for telecommand in telecommands:
        generate_telecommand_class(telecommand_python_template, telecommand, py_tc_output_dir)
        generate_telecommand_base_header(telecommand_base_header_template, telecommand, c_tc_output_dir)
        generate_telecommand_base_source(telecommand_base_source_template, telecommand, c_tc_output_dir)
        generate_telecommand_auto_source(telecommand_auto_source_template, telecommand, c_tc_output_dir)
        generate_telecommand_header(telecommand_header_template, telecommand, c_tc_output_dir)
        generate_telecommand_source(telecommand_source_template, telecommand, c_tc_output_dir)

    telemetry_base_header_template = env.get_template('telemetry_base_header.jinja')
    telemetry_base_source_template = env.get_template('telemetry_base_source.jinja')
    telemetry_auto_source_template = env.get_template('telemetry_auto_source.jinja')
    telemetry_header_template = env.get_template('telemetry_header.jinja')
    telemetry_source_template = env.get_template('telemetry_source.jinja')

    telemetries = parsed_json['telemetries'] if 'telemetries' in parsed_json else []
    for telemetry in telemetries:
        generate_telemetry_base_header(telemetry_base_header_template, telemetry, c_tm_output_dir)
        generate_telemetry_base_source(telemetry_base_source_template, telemetry, c_tm_output_dir)
        generate_telemetry_auto_source(telemetry_auto_source_template, telemetry, c_tm_output_dir)
        generate_telemetry_header(telemetry_header_template, telemetry, c_tm_output_dir)
        generate_telemetry_source(telemetry_source_template, telemetry, c_tm_output_dir)


if __name__ == '__main__':
    main()
