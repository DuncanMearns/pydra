from pathlib import Path


def make_tutorial_doctree():

    outdir = Path("tutorial")
    if not outdir.exists():
        outdir.mkdir()

    path = Path("../../pydra/tutorial")
    for p in path.glob("*.py"):
        name = p.stem
        if not name.startswith("_"):
            n, *parts = name.split("_")
            title = " ".join(parts).capitalize()
            with open(outdir.joinpath(name + ".rst"), "w") as f:
                f.write("..\n  This file is auto-generated.\n\n")
                f.write(title + "\n")
                f.write("=" * len(title) + "\n\n")
                f.write(".. literalinclude:: ..\\" + str(p) + "\n")
                f.write("    :language: python\n")


if __name__ == "__main__":
    make_tutorial_doctree()
