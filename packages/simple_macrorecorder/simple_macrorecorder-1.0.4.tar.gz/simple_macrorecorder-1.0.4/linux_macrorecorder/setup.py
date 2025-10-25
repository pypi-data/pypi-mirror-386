from setuptools import setup
import os

VERSION = "1.0.4"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="linux_macrorecorder",
    description="linux_macrorecorder is now simple_macrorecorder",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    version=VERSION,
    install_requires=["simple_macrorecorder"],
    classifiers=["Development Status :: 7 - Inactive"],
)
