import os
import json
from argparse import ArgumentParser
from pathlib import Path

global HAS_RUAMEL

try:
    import ruamel.yaml
    from ruamel.yaml import YAML
    HAS_RUAMEL = True
except ImportError:
    HAS_RUAMEL = False
    print("Require ruamel library for converting json to yaml")

from ..core import readYaml


def is_valid(filepath: str) -> bool:
    """_summary_

    Parameters
    ----------
    filepath : str
        _description_

    Returns
    -------
    bool
        _description_
    """
    rc = False
    try:
        readYaml(str(filepath))
        rc = True
    except Exception as e:
        print(f"output yaml is not valid \n {e}")
    return rc


def process(input_file: str):
    """_summary_

    Parameters
    ----------
    input_file : str
        _description_
    """
    if not HAS_RUAMEL:
        print("Require ruamel library for converting json to yaml")
        print("Install ruamel before continuing")
        return

    input_file = Path(input_file).absolute()
    out_file = Path(input_file.parent,
                    input_file.name.replace('.json', '.yaml'))

    with open(input_file, 'r') as inp:
        config = json.load(inp, object_pairs_hook=ruamel.yaml.comments.CommentedMap)

    yaml = YAML()
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = 1000 # # following are needed to make output yaml compatible with mini-yaml
    yaml.indent(mapping=2, sequence=4, offset=2)
    ruamel.yaml.scalarstring.walk_tree(config)

    with open(out_file, 'w') as out:
        yaml.dump(config, out)

    with open(out_file, 'r') as out:
        # following are needed to make output yaml compatible with mini-yaml
        contents = out.read().replace("\t", " ")
        contents = contents.replace("\u2212", "-")
        contents = contents.replace("|+", "|")
        contents = contents.replace("''", "")

    with open(out_file, 'w') as out:
        out.write(contents)

    if not is_valid(out_file):
        os.remove(out_file)


if __name__ == "__main__":
    parser = ArgumentParser("convert JSON to YAML")
    parser.add_argument('--input_file', type=str, dest='input_file',
                        required=True, help='path of input file')
    args = parser.parse_args()

    process(args.input_file)