# Fontawesome 5 LaTeX Generator

This repo houses the ability to map FontAwesome font variants to a respective TeX binding.  
This was built to run on a Linux-based OS. Feel free to submit a PR for Windows + OSx support.  

This ONLY supports FontAwesome releases 5.0 and up.

## Current bindings:
Binding | Supported | Reason
--- | --- | ---
Xelatex | Yes | -
Lualatex | No | Need templates
PDFLatex | No | Need templates
Sharelatex | No | Need templates

* I really only tested xelatex. The others might work.

## Releases
Check out the [Releases](https://github.com/mynameiscosmo/fontawesome-latex/releases) for pre-built **FontAwesome 5.0.13** mappings.

## Usage
This utility will download a FontAwesome release zip, unzip it, locate metadata, and generate a TeX mapping using Jinja templates.

```console
make env
source .env/bin/activate
make
make pdf
make display
make release
```

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
