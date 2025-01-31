import json
import re
import sys
from datetime import timedelta

from pyhocon import ConfigFactory
from pyhocon.config_tree import (
    ConfigQuotedString,
    ConfigSubstitution,
    ConfigTree,
    ConfigValues,
    NoneValue,
)

try:
    from dateutil.relativedelta import relativedelta
except Exception:
    relativedelta = None


class HOCONConverter:
    @classmethod
    def to_json(cls, config, compact=False, indent=2, level=0):
        """Convert HOCON input into a JSON output

        :return: JSON string representation
        :type return: str
        """
        lines = ""
        if isinstance(config, ConfigTree):
            if len(config) == 0:
                lines += "{}"
            else:
                lines += "{\n"
                bet_lines = []
                for key, item in config.items():
                    new_key = key.strip(
                        '"'
                    )  # for dotted keys enclosed with "" to not be interpreted as nested key
                    new_value = cls.to_json(item, compact, indent, level + 1)
                    bet_lines.append(
                        '{indent}"{key}": {value}'.format(
                            indent="".rjust((level + 1) * indent, " "),
                            key=new_key,
                            value=new_value,
                        )
                    )
                lines += ",\n".join(bet_lines)
                lines += "\n{indent}}}".format(indent="".rjust(level * indent, " "))
        elif isinstance(config, list):
            if len(config) == 0:
                lines += "[]"
            else:
                lines += "[\n"
                bet_lines = []
                for item in config:
                    bet_lines.append(
                        "{indent}{value}".format(
                            indent="".rjust((level + 1) * indent, " "),
                            value=cls.to_json(item, compact, indent, level + 1),
                        )
                    )
                lines += ",\n".join(bet_lines)
                lines += "\n{indent}]".format(indent="".rjust(level * indent, " "))
        elif cls._is_timedelta_like(config):
            lines += cls._timedelta_to_str(config)
        elif isinstance(config, str):
            lines = json.dumps(config, ensure_ascii=False)
        elif config is None or isinstance(config, NoneValue):
            lines = "null"
        elif config is True:
            lines = "true"
        elif config is False:
            lines = "false"
        else:
            lines = str(config)
        return lines

    @classmethod
    def to_hocon(cls, config, compact=False, indent=2, level=0):
        """Convert HOCON input into a HOCON output

        :return: JSON string representation
        :type return: str
        """
        lines = ""
        if isinstance(config, ConfigTree):
            if len(config) == 0:
                lines += "{}"
            else:
                if level > 0:  # don't display { at root level
                    lines += "{\n"
                bet_lines = []

                for key, item in config.items():
                    if compact:
                        full_key = key
                        while isinstance(item, ConfigTree) and len(item) == 1:
                            key, item = next(iter(item.items()))
                            full_key += "." + key
                    else:
                        full_key = key

                    bet_lines.append(
                        "{indent}{key}{assign_sign} {value}".format(
                            indent="".rjust(level * indent, " "),
                            key=full_key,
                            assign_sign="" if isinstance(item, dict) else " =",
                            value=cls.to_hocon(item, compact, indent, level + 1),
                        )
                    )
                lines += "\n".join(bet_lines)

                if level > 0:  # don't display { at root level
                    lines += "\n{indent}}}".format(
                        indent="".rjust((level - 1) * indent, " ")
                    )
        elif isinstance(config, list):
            if len(config) == 0:
                lines += "[]"
            else:
                lines += "[\n"
                bet_lines = []
                for item in config:
                    bet_lines.append(
                        "{indent}{value}".format(
                            indent="".rjust(level * indent, " "),
                            value=cls.to_hocon(item, compact, indent, level + 1),
                        )
                    )
                lines += "\n".join(bet_lines)
                lines += "\n{indent}]".format(
                    indent="".rjust((level - 1) * indent, " ")
                )
        elif isinstance(config, str):
            if "\n" in config and len(config) > 1:
                lines = f'"""{config}"""'  # multilines
            else:
                lines = f'"{cls.__escape_string(config)}"'
        elif isinstance(config, ConfigValues):
            lines = "".join(
                cls.to_hocon(o, compact, indent, level) for o in config.tokens
            )
        elif isinstance(config, ConfigSubstitution):
            lines = "${"
            if config.optional:
                lines += "?"
            lines += config.variable + "}" + config.ws
        elif isinstance(config, ConfigQuotedString):
            if "\n" in config.value and len(config.value) > 1:
                lines = f'"""{config.value}"""'  # multilines
            else:
                lines = f'"{cls.__escape_string(config.value)}"'
        elif cls._is_timedelta_like(config):
            lines += cls._timedelta_to_hocon(config)
        elif config is None or isinstance(config, NoneValue):
            lines = "null"
        elif config is True:
            lines = "true"
        elif config is False:
            lines = "false"
        else:
            lines = str(config)
        return lines

    @classmethod
    def to_yaml(cls, config, compact=False, indent=2, level=0):
        """Convert HOCON input into a YAML output

        :return: YAML string representation
        :type return: str
        """
        lines = ""
        if isinstance(config, ConfigTree):
            if len(config) > 0:
                if level > 0:
                    lines += "\n"
                bet_lines = []
                for key, item in config.items():
                    bet_lines.append(
                        "{indent}{key}: {value}".format(
                            indent="".rjust(level * indent, " "),
                            key=key.strip(
                                '"'
                            ),  # for dotted keys enclosed with "" to not be interpreted as nested key,
                            value=cls.to_yaml(item, compact, indent, level + 1),
                        )
                    )
                lines += "\n".join(bet_lines)
        elif isinstance(config, list):
            config_list = [line for line in config if line is not None]
            if len(config_list) == 0:
                lines += "[]"
            else:
                lines += "\n"
                bet_lines = []
                for item in config_list:
                    bet_lines.append(
                        "{indent}- {value}".format(
                            indent="".rjust(level * indent, " "),
                            value=cls.to_yaml(item, compact, indent, level + 1),
                        )
                    )
                lines += "\n".join(bet_lines)
        elif cls._is_timedelta_like(config):
            lines += cls._timedelta_to_str(config)
        elif isinstance(config, str):
            # if it contains a \n then it's multiline
            lines = config.split("\n")
            if len(lines) == 1:
                lines = config
            else:
                lines = "|\n" + "\n".join(
                    [line.rjust(level * indent, " ") for line in lines]
                )
        elif config is None or isinstance(config, NoneValue):
            lines = "null"
        elif config is True:
            lines = "true"
        elif config is False:
            lines = "false"
        else:
            lines = str(config)
        return lines

    @classmethod
    def to_properties(cls, config, compact=False, indent=2, key_stack=None):
        """Convert HOCON input into a .properties output

        :return: .properties string representation
        :type return: str
        :return:
        """
        key_stack = key_stack or []

        def escape_value(value):
            return (
                value.replace("=", "\\=")
                .replace("!", "\\!")
                .replace("#", "\\#")
                .replace("\n", "\\\n")
            )

        stripped_key_stack = [key.strip('"') for key in key_stack]
        lines = []
        if isinstance(config, ConfigTree):
            for key, item in config.items():
                if item is not None:
                    lines.append(
                        cls.to_properties(
                            item, compact, indent, stripped_key_stack + [key]
                        )
                    )
        elif isinstance(config, list):
            for index, item in enumerate(config):
                if item is not None:
                    lines.append(
                        cls.to_properties(
                            item, compact, indent, stripped_key_stack + [str(index)]
                        )
                    )
        elif cls._is_timedelta_like(config):
            lines.append(
                ".".join(stripped_key_stack) + " = " + cls._timedelta_to_str(config)
            )
        elif isinstance(config, str):
            lines.append(".".join(stripped_key_stack) + " = " + escape_value(config))
        elif config is True:
            lines.append(".".join(stripped_key_stack) + " = true")
        elif config is False:
            lines.append(".".join(stripped_key_stack) + " = false")
        elif config is None or isinstance(config, NoneValue):
            pass
        else:
            lines.append(".".join(stripped_key_stack) + " = " + str(config))
        return "\n".join([line for line in lines if len(line) > 0])

    @classmethod
    def convert(cls, config, output_format="json", indent=2, compact=False):
        converters = {
            "json": cls.to_json,
            "properties": cls.to_properties,
            "yaml": cls.to_yaml,
            "hocon": cls.to_hocon,
        }

        if output_format in converters:
            return converters[output_format](config, compact, indent)
        else:
            raise Exception(
                "Invalid format '{format}'. Format must be 'json', 'properties', 'yaml' or 'hocon'".format(
                    format=output_format
                )
            )

    @classmethod
    def convert_from_file(
        cls,
        input_file=None,
        output_file=None,
        output_format="json",
        indent=2,
        compact=False,
    ):
        """Convert to json, properties or yaml

        :param input_file: input file, if not specified stdin
        :param output_file: output file, if not specified stdout
        :param output_format: json, properties or yaml
        :return: json, properties or yaml string representation
        """

        if input_file is None:
            content = sys.stdin.read()
            config = ConfigFactory.parse_string(content)
        else:
            config = ConfigFactory.parse_file(input_file)

        res = cls.convert(config, output_format, indent, compact)
        if output_file is None:
            print(res)
        else:
            with open(output_file, "w") as fd:
                fd.write(res)

    @classmethod
    def __escape_match(cls, match):
        char = match.group(0)
        return {
            "\b": r"\b",
            "\t": r"\t",
            "\n": r"\n",
            "\f": r"\f",
            "\r": r"\r",
            '"': r"\"",
            "\\": r"\\",
        }.get(char) or (r"\u%04x" % ord(char))

    @classmethod
    def __escape_string(cls, string):
        return re.sub(r'[\x00-\x1F"\\]', cls.__escape_match, string)

    @classmethod
    def _is_timedelta_like(cls, config):
        return (
            isinstance(config, timedelta)
            or relativedelta is not None
            and isinstance(config, relativedelta)
        )

    @classmethod
    def _timedelta_to_str(cls, config):
        if (relativedelta is not None) and (isinstance(config, relativedelta)):
            time_delta = cls._relative_delta_to_timedelta(config)
        else:
            time_delta = config
        return str(int(time_delta.total_seconds() * 1000))

    @classmethod
    def _timedelta_to_hocon(cls, config):
        """
        :type config: timedelta
        """
        if relativedelta is not None and isinstance(config, relativedelta):
            if config.hours > 0:
                return str(config.hours) + " hours"
            elif config.minutes > 0:
                return str(config.minutes) + " minutes"

        if config.days > 0:
            return str(config.days) + " days"
        elif config.seconds > 0:
            return str(config.seconds) + " seconds"
        elif config.microseconds > 0:
            return str(config.microseconds) + " microseconds"
        else:
            return "0 seconds"

    @classmethod
    def _relative_delta_to_timedelta(cls, relative_delta):
        """
        :type relative_delta: relativedelta
        """
        return timedelta(
            days=relative_delta.days,
            hours=relative_delta.hours,
            minutes=relative_delta.minutes,
            seconds=relative_delta.seconds,
            microseconds=relative_delta.microseconds,
        )
