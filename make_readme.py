def read(path):
    text = ""
    with open(path, "r") as f:
        for line in f:
            text += line
    text += "\n\n"
    return text


def make_readme():

    readme_path = "README.rst"

    about = read("./docs/source/about.rst")
    installation = read("./docs/source/getting_started/installation.rst")
    using_pydra = read("./docs/source/getting_started/using_pydra.rst")

    with open(readme_path, "w") as f:
        # Include about
        f.write(about)
        # Add contents
        f.write("Contents:\n\n")
        f.write("1. `Installation`_\n")
        f.write("2. `Using Pydra`_\n\n")
        f.write("Read the complete user guide `here <https://duncanmearns.github.io/pydra/>`_.\n\n")
        # Include installation guide
        f.write(installation)
        # Include using pydra guide
        f.write(using_pydra)
        # Add link to complete guide
        f.write("For more details about using pydra, see the complete "
                "`User Guide <https://duncanmearns.github.io/pydra/>`_.\n\n")


if __name__ == "__main__":
    make_readme()
