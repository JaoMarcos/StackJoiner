import sys

import yaml

from stackjoiner.stackjoiner import StackJoiner
from stackjoiner.yaml_loader import YamlLoader


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    file_path = sys.argv[1]
    out_put_path = sys.argv[2]

    stack = StackJoiner(file_path)
    stack.merge()
    with open(out_put_path,'w+') as file:
        YamlLoader.dump(stack.template, file)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
