import sys

from .stackjoiner import StackJoiner
from .yaml_loader import YamlLoader


def main():
    file_path = sys.argv[1]
    out_put_path = sys.argv[2]

    stack = StackJoiner(file_path)
    stack.merge()
    with open(out_put_path, "w+", encoding="utf-8") as file:
        YamlLoader.dump(stack.template, file)


if __name__ == "__main__":
    main()
