<p align="center">
<a href="examples/fontawesome.pdf"><img src="examples/example.png" /></a>
</p>

# Fontawesome 5 LaTeX Generator

This repo houses the ability to map FontAwesome font variants to a respective TeX binding.  
This was built to run on a Linux-based OS. Feel free to submit a PR for Windows + OSx support.  

This ONLY supports FontAwesome releases 5.0 and up.

Now supporting FontAwesome 5 Pro!

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

Simply download the [**latest release**](https://github.com/mynameiscosmo/fontawesome-latex/releases/latest) and extract the archive.

Check out the [**examples**](examples) directory for a pre-built PDF, .sty, and .tex.

### Pro

If you have *Font Awesome 5 Pro*, all you need to do is copy the fonts from `FontAwesome-Pro-x.x.x/use-on-destop` to the `fonts/` directory
extracted from the zip archive, and specify the `[pro]` flag when loading the FontAwesome icons, like so: `\RequirePackage[pro]{fontawesome}`


## Nomenclature

These mappings try to follow [Font Awesome's Prefixes](https://fontawesome.com/how-to-use/upgrading-from-4#icon-name-changes)  
You can use icons in the generated mappings with the following calls:
```
\faThumbsUp % generates a regular Thumbs Up
\farThumbsUp % generates a regular Thumbs Up
\fasThumbsUp % generates a solid Thumbs Up
\falThumbsUp % generates a light Thumbs Up (pro)
\textbf\faThumbsUp % generates a solid Thumbs Up
\textit\faThumbsUp % generates a light Thumbs Up (pro)
```


## Building

This utility will download a FontAwesome release zip, unzip it, locate metadata, and generate a TeX mapping using Jinja templates.

The following set of commands will create a *virtualenv*, run the python script, generate the pdfs, display them,
then package them into a release.zip.

```console
make env
source .env/bin/activate
make
make pdf
make display
make release
```

### Advanced Usage

The script will automagically detect if you're using FontAwesome *Free* or *Pro*, and build the templates accordingly.

- Using a local zip archive:
    ```console
    python3 fontawesome-latex.py --local-file tmp/fontawesome-pro-5.0.13.zip
    ```
- Using a local extracted zip folder:
    ```console
    python3 fontawesome-latex.py --zipped-dir tmp/fontawesome-pro-5.0.13
    ```
- For more usage details, check out:
    ```console
    python3 fontawesome-latex.py --help
    ```

## Why?

I wanted the most recent FontAwesome icons in my resume... :robot:  
There are other tools out there, but they weren't quite as automated as one would hope.  
Some of the tools even strip out many icons.

With FontAwesome 5 including metadata, it's super easy to read an icon list from the metadata file,
find their respective font style (free/pro, regular/solid/light), and map them to a template.

## Contributing

Check out the existing [*issues*](https://github.com/mynameiscosmo/fontawesome-latex/issues) and check out any *help_wanted* or
*enhancement* tags.
