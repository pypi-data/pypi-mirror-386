#   /bin/env loadAsHashTag.later

__version__ = "1.0"

pyModuleType = "facter"

import getpass


def facterMain(
        *args,
        **kwargs,
):
    print(f"Running facterMain() As a LoadedAsCS:")
    print(f"args :: {args}")
    print(f"facterMain(KWArgs):")
    print(f"{kwargs}")

    for key, value in kwargs.items():
      print(key, "->", value)

    userName = getpass.getuser()


    print(f"{userName} using import getpass is in facterMain")


def facterCliParams ():
    return [
        (
        "facterParName",  # parCliName
        "Facter Parameter Name",  # parName
        "Full Description of Parameter Comes Here", # parDescription
        "Int", # parDataType
        22, # parDefault
        [3,22,99] # parChoices
        )
    ]
