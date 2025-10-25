# Safe Move Tool

A Python tool for safely moving or copying files with intelligent conflict resolution.

## Features

- Safely move or copy files between directories
- Intelligent handling of filename conflicts
- Interactive prompts for conflict resolution
- Preserves file metadata when possible

## Installation

```bash
pip install .
```

## Usage

```bash
safemove [source] [destination]
```

Options:
- `-x` or `--move`: Move files (default mode)
- `-c` or `--copy`: Copy files instead of moving them
- `-s` or `--strict`: Enable strict mode (byte-by-byte file comparison)

## Example

```bash
# Move a file
safemove -x ./file.txt /home/user/documents/

# Copy a file
safemove -c ./file.txt /home/user/documents/

# Move with strict mode
safemove -x -s ./file.txt /home/user/documents/
```

## License

MIT License