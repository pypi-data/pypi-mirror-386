#   /bin/env loadAsHashTag.later

__version__ = "1.0"

pyModuleType = "generic"

import getpass


def genericMain(
        *args,
        **kwargs,
):
    print(f"Running genericMain() As a LoadedAsCS:")
    print(f"args :: {args}")
    print(f"genericMain(KWArgs):")
    print(f"{kwargs}")

    for key, value in kwargs.items():
      print(key, "->", value)

    userName = getpass.getuser()


    print(f"{userName} using import getpass is in genericMain")


def genericCliParams ():
    return [
        (
        "genericParName",  # parCliName
        "Generic Parameter Name",  # parName
        "Full Description of Parameter Comes Here", # parDescription
        "Int", # parDataType
        22, # parDefault
        [3,22,99] # parChoices
        )
    ]
