# Fontawesome LaTeX Generator

This repo houses the ability to map FontAwesome font variants to a respective TeX binding.  
This was built to run on a Linux-based OS. Feel free to submit a PR for Windows + OSx support.  

Currently supported bindings:
- Xelatex
- Lualatex
- PDFLatex

## Releases
Check out the [Releases](#) for a pre-built files for **FontAwesome 5.0.13** mappings.

## Usage
This utility will download a FontAwesome release zip, unzip it, locate metadata, and generate a TeX mapping using Jinja templates.

### Requirements
- Python 3
    - PyYaml
    - Requests
    - tqdm
    - jinja2

```console
pip3 install -r requirements.txt
```

### Running
This utility should do all the work for you.
Just run:
```console
make
```

Alternatively, you can run the Python script directly:
```console
python3 fontawesome-latex.py
```

## Contributing
