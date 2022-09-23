import sys
import fire

from redash_py.client import RedashAPIClient
from redash_py.exceptions import RedashPyException


def main():
    try:
        fire.Fire(RedashAPIClient)
    except RedashPyException as e:
        print(e)
        sys.exit(1)


if __name__ in '__main__':
    main()


