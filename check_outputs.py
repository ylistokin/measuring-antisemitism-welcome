"""Check that regenerated figures match the committed ones.

Run after the figure scripts:

    python check_outputs.py

Text outputs (CSV, SVG, JSON) must be byte-identical; `git diff` checks those. PNG files are compared
by their decoded pixels instead, because the compressed bytes depend on the zlib build of the
platform (e.g. Windows Pillow wheels ship zlib-ng) even when the image is identical. A PNG whose
pixels match is restored to the committed bytes, so afterwards `git status` is clean exactly when
every output reproduces. Exits with status 1 and lists the files otherwise.
"""

import io
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()


def git(*args: str, binary: bool = False):
    result = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, check=True)
    return result.stdout if binary else result.stdout.decode("utf-8")


def same_pixels(committed: bytes, path: str) -> bool:
    with Image.open(io.BytesIO(committed)) as a, Image.open(f"{ROOT}/{path}") as b:
        if a.mode != b.mode or a.size != b.size:
            return False
        diff = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA"))
        return diff.getbbox(alpha_only=False) is None  # default getbbox() inspects only the alpha channel


def main() -> int:
    changed = [p for p in git("diff", "--name-only", "-z").split("\0") if p]
    for path in [p for p in changed if p.lower().endswith(".png")]:
        if same_pixels(git("show", f":{path}", binary=True), path):  # the committed/staged version
            git("checkout", "--", path)
            print(f"pixel-identical: {path}")
    # Unstaged changes and untracked files only: anything here was produced by the run.
    remaining = [line for line in git("status", "--porcelain", "--untracked-files=all").splitlines()
                 if line and (line[1] != " " or line.startswith("??"))]
    if remaining:
        print("Outputs differ from the committed files:\n" + "\n".join(remaining))
        print(git("diff", "--stat"))
        return 1
    print("All outputs match the committed files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
