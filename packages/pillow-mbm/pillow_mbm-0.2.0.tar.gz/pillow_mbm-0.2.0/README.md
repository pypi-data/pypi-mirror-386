# Pillow-mbm
Pillow-mbm is a plugin for [pillow](https://pillow.readthedocs.io/en/stable/) 
that adds support for KSP's proprietary MBM texture format.

test/swis_mesh.mbm from [Coatl](https://forum.kerbalspaceprogram.com/topic/131145-wip-coatl-aerospace-probesplus-dev-thread-beta-10192020-18-110/) redistributed under CC-BY-NC-SA 4.0

## Installation

Install and update with [pip](https://pip.pypa.io/en/stable/getting-started/):

```shell
$ pip install -U pillow-mbm
```

Or with [uv](https://docs.astral.sh/uv/getting-started/):

```shell
$ uv tool install pillow-mbm
```

## Usage

To decode MBM files, use the `convert-mbm` command, along with a glob or a
list of files to decode. By default, it will convert to png in place.

```
Usage: convert-mbm [OPTIONS] [FILENAMES]...

  Decode Kerbal Space Program MBM files

Options:
  -f, --flip / -F, --no-flip  Vertically flip image after converting.
  -r, --remove                Remove input images after converting.
  -s, --suffix TEXT           Suffix to append to output file(s). Ignored if
                              output is a single file.

  -x, --extension TEXT        Extension to use for output. Ignored if output
                              is a single file. Output filetype is deduced
                              from this  [default: .png]

  -o, --output PATH           Output file or directory. If outputting to a
                              file, input filenames must be only a single
                              item. By default, files are decoded in place.

  --version                   Show the version and exit.
  --help                      Show this message and exit.
```