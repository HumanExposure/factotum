import glob

from setuptools import setup

# Concatenate all fixtures into a single fixture
files = glob.glob("dashboard/fixtures/*.yaml")
files.sort()
with open("dashboard/fixtures/dashboard.yaml", "w") as outfile:
    for file in files:
        with open(file, "r") as infile:
            outfile.write(infile.read())
            outfile.write("\n")

setup(
    name="dashboard",
    packages=["dashboard.models", "dashboard.migrations"],
    py_modules=["dashboard.apps", "dashboard.utils"],
    install_requires=[
        "Django>=2.2,<2.3",
        "django-model-utils>=3.1",
        "django-taggit<1",
        "six>=1.12.0,<1.13.0",
        "zipstream==1.1.4",
    ],
    include_package_data=True,
    package_data={"dashboard.models": ["../fixtures/dashboard.yaml"]},
)
