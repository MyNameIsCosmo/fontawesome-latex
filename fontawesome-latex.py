#!/usr/bin/env python3
'''
Fontawesome LaTeX Mapping Generator

This file will download, extract, analyze a FontAwesome archive,
and then build LaTeX mappings to use FontAwesome icons in your TeX document.

Check out https://github.com/mynameiscosmo/fontawesome-latex for more info.
'''
__version__ = '1.1.0'
__author__ = 'Cosmo Borsky'
__license__ = 'MIT License'
__copyright__ = 'Copyright (c) 2018 Cosmo Borsky'

import click
import logging
import jinja2
import os
import re
import requests
import shutil
import sys
import yaml
import zipfile
from datetime import date
from distutils.util import strtobool
from logging.config import dictConfig
from tqdm import tqdm

logging_config = {
    'version': 1,
    'disable_existing_logs': False,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'root': {
        'handlers': ['console'],
        'level': logging.INFO,
    }
}

tqdm_kb = {
    'unit': 'B',
    'unit_scale': True,
    'unit_divisor': 1024,
    'miniters': 1
}

dictConfig(logging_config)
log = logging.getLogger()

jinja_args = { # noqa: W605
    'block_start_string': '\BLOCK{',
    'block_end_string': '}',
    'variable_start_string': '\VAR{',
    'variable_end_string': '}',
    'comment_start_string':  '\#{',
    'comment_end_string':  '}',
    'line_statement_prefix':  '%%',
    'line_comment_prefix':  '%#',
    'trim_blocks':  True,
    'autoescape':  False,
    'loader':  jinja2.FileSystemLoader(os.path.abspath('./templates'))
}

jinja_env = jinja2.Environment(**jinja_args)

problematic_icons = {
    '500px': 'fivehundredpx'
}

renamed = {
    '500px': 'FiveHundredPX',
    'Amazon Web Services (AWS)': 'AmazonWebServices',
    'Büromöbel-Experte GmbH & Co. KG.': 'BuromobelExperte',
    'Creative Commons Noncommercial (Euro Sign)':
        'CreativeCommonsNonCommercialEuro',
    'Creative Commons Noncommercial (Yen Sign)':
        'CreativeCommonsNonCommercialYen',
    'Draft2digital': 'DraftToDigital',
    'Gratipay (Gittip)': 'Gratipay',
    'Sort Down (Descending)': 'SortDown',
    'Sort Up (Ascending)': 'SortUp',
    'Weixin (WeChat)': 'Weixin'
}

replace = [
    {
        '1/2': 'Half',
        '1/4': 'Quarter',
        '3/4': 'ThreeQuarters',
    },
    {
        '-': ' ',
        '.': ' ',
        ',': '',
        "'": '',
        '+': 'Plus',
        '0': 'Zero',
        '1': 'One',
        '2': 'Two',
        '3': 'Three',
        '4': 'Four',
        '5': 'Five',
        '6': 'Six',
        '7': 'Seven',
        '8': 'Eight',
        '9': 'Nine',
        '&': 'And',
        '(Hand)': 'Hand',
        '(JS)': 'JS',
        '(Old)': 'Old'
    }
]


package = {
    'desc': '{date} {version} Font Awesome 5 {fa_type}',
    'short': 'fa',
    'cmd': 'faicon',
    'file': 'fontawesome',
    'free': {
        'font': 'Font Awesome 5 Free',
        'regular': {
            'font': '-Regular-400',
            'prepend': '',
            'append': ''
        },
        'solid': {
            'font': '-Solid-900',
            'prepend': '',
            'append': 'Solid'
        }
    },
    'brands': {
        'font': 'Font Awesome 5 Brands-Regular-400',
        'prepend': 'b',
        'append': ''
    },
    'pro': {
        'font': 'Font Awesome 5 Pro',
        'regular': {
            'font': '-Regular-400',
            'prepend': '',
            'append': ''
        },
        'solid': {
            'font': '-Solid-900',
            'prepend': '',
            'append': 'Solid'
        },
        'light': {
            'font': '-Light-300',
            'prepend': '',
            'append': 'Light'
        }
    }
}


class ReleaseException(Exception):
    pass


def choice(text, default='N', append=' [{}/{}]'):
    ''' Request a y/N answer from the user. '''
    append = append.format(
        *(('Y', 'n') if strtobool(default) else ('y', 'N'))
    )
    try:
        return strtobool(input(text + append))
    except ValueError:
        return strtobool(default)


def promptError(text, default='N'):
    ''' Prompt the user and exit on no or exception '''
    if not choice(text, default):
        log.error('Aborting!')
        sys.exit(1)


def getReleaseInfo(version=None):
    ''' Download the specified release from profile/repo.
    If no release is specified, downloads the latest zip file.'''

    apiURL = 'https://api.github.com/repos/FortAwesome/Font-Awesome/releases'

    if version is None:
        release = '/latest'
    else:
        release = '/tags/' + version

    url = apiURL + release

    log.debug('Looking for a release in ' + url)

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    return data


def checkReleaseInfo(info):
    ''' Checks if a release exists and if it has a zip file. '''
    if 'message' in info and info['message'] == 'Not Found':
        raise ReleaseException('Release Not Found')
    if 'assets' not in info:
        raise ReleaseException('Could not determine release download')
    if (len(info['assets']) < 1 or
            'browser_download_url' not in info['assets'][0]):
        log.warn('Cannot determine browser download url from assets. '
                 'Checking zipball_url.')
        if 'zipball_url' in info and info['zipball_url'].endswith('.zip'):
            return info['zipball_url']
        raise ReleaseException('Could not find a suitable zip '
                               'file in the release.')

    url = info['assets'][0]['browser_download_url']
    if url.endswith('.zip'):
        return url

    raise ReleaseException('Could not find a suitable zip '
                           'file in the release.')


def getAndCheckRelease(version=None):
    try:
        info = getReleaseInfo(version)
        url = checkReleaseInfo(info)
    except (ReleaseException, requests.exceptions.HTTPError) as e:
        log.debug(e)
        if getattr(e, 'response'):
            log.debug('Release exception: ' + e.response)

        raise

    log.debug('Found a release! ' + url)

    return url


def downloadFile(url, filename=None, output_dir=''):
    ''' Download a resource using requests
    Track progress using tqdm. '''
    if filename is None:
        filename = url.split('/')[-1]
    filename = os.path.join(output_dir, filename)

    log.debug('Downloading {} as {}'.format(
        url,
        filename
    ))

    os.makedirs(output_dir, exist_ok=True)

    response = None
    block_size = 1024
    with requests.get(url, stream=True) as r, \
            open(filename, 'wb') as f, \
            tqdm(desc=filename, **tqdm_kb) as t:
        total_size = int(r.headers.get('content-length', 0))
        t.total = total_size
        for count, chunk in enumerate(r.iter_content(chunk_size=block_size)):
            if not chunk:
                break
            f.write(chunk)
            f.flush()
            t.update(count * block_size - t.n)

        response = r

    response.raise_for_status()

    return filename


def handleZipArchive(response, zipped_dir, download_dir):
    ''' Handle extracting an archive and getting a directory listing '''
    dirs = []
    if zipped_dir is None:
        log.debug('No zipped dir specified. Unzipping {}'.format(response))
        files = unzip(response, download_dir)
        dirs = [f.filename for f in files if f.file_size == 0]
    else:
        log.debug('Zipped dir specified! Unzipping {}'.format(response))
        dirs = [
            d[0].replace(download_dir + '/', '', 1)
            for d in os.walk(download_dir)
            if d[0] != download_dir
        ]

    return dirs


def unzip(filename, target=''):
    ''' Unzip a file into the target directory.
    Do some basic checks along the way. '''
    if not zipfile.is_zipfile(filename):
        raise FileNotFoundError(filename + ' is not a zip file!')

    desc = 'unzipping ' + filename
    with zipfile.ZipFile(filename, 'r') as z, \
            tqdm(desc=desc) as t:
        files = z.infolist()
        total = len(files) - 1
        t.total = total
        for count, f in enumerate(files):
            z.extract(f, target)
            t.update(count - t.n)
        # z.extractall(target)

    return files


def copyFonts(font_dir, output_dir):
    ''' Copy fonts from use-on-desktop to output_dir/fonts '''
    fonts = [f for f in os.listdir(font_dir) if f.endswith('.otf')]

    if len(fonts) < 1:
        raise Exception('No fonts found in ' + os.path.abspath(font_dir))

    log.debug('Found {} fonts in {}'.format(len(fonts), font_dir))

    os.makedirs(output_dir, exist_ok=True)

    for font in fonts:
        font = os.path.join(font_dir, font)
        log.debug('Copying Font {} to {}'.format(
            font,
            output_dir
        ))
        path = shutil.copy(font, output_dir)
        log.debug('Copied {} to {}'.format(
            font,
            path
        ))

    return fonts


def fontVersion(fonts):
    ''' Take in a list of fonts and check for 'pro' or 'free' '''
    pro = [f for f in fonts if 'Pro' in f]

    return 'pro' if len(pro) > 0 else 'free'


def loadMetadata(metadata_dirs, metadata_file):
    ''' Load a metadata file and parse it.
    Supports yaml and json parsing.

    For recent FontAwesome releases, there are metadata files for shims, icons,
    and categories located in /fontawesome-.../advanced-options/metadata '''
    if len(metadata_dirs) == 0:
        raise ValueError('No metadata folder in unzipped archive! Aborting.')
    elif len(metadata_dirs) > 1:
        raise ValueError('More than 1 metadata folder found in archive! '
                         'Directory traversing is not implemented yet.')

    metadata = os.path.join(metadata_dirs[0], metadata_file)

    with open(metadata) as f:
        data = yaml.safe_load(f)

    return data


def getVersion(readme):
    ''' Pull the Font Awesome version from the readme '''
    log.debug('Looking for version in: ' + readme)

    version = None
    with open(readme, 'r') as f:
        for line in f:
            log.debug('Searching: ' + line)
            version = re.search(
                r'([0-9]{1,2}).([0-9]{1,2}).([0-9]{2,3})',
                line
            ).group()
            if 'Font Awesome' in line and version is not None:
                log.debug('Version: ' + version)
                break
        else:
            log.warn('Could not find a version!')

    return version


def formatLabel(text):
    ''' Format the Label text.
    Replace characters like hypens and spaces,
    split the text at each space, then capitalize
    each word and return the joined string. '''
    if text in renamed:
        return renamed[text]

    for group in replace:
        for item in group.items():
            if item[0] in text:
                text = text.replace(item[0], item[1])
                log.debug('Replaced {} to {} in {}'.format(
                    item[0],
                    item[1],
                    text
                ))

    words = []
    for word in text.split(' '):
        words.append(word.capitalize())

    return ''.join(words)


def genIcons(data, package, fa_type):
    ''' Take in a metadata dictionary of icons.
    Returns a dictionary of icons with minimal information. '''
    icons = []
    for item in sorted(data.items()):
        for style in item[1]['styles']:
            if style == 'brands':
                pkg = package['brands']
            elif style in package[fa_type]:
                pkg = package[fa_type][style]
            else:
                continue
            log.debug('Processing {} labeled {}'.format(
                item[0],
                item[1]['label']
            ))
            name = item[0]
            if name in problematic_icons:
                log.debug(
                    'Caught problematic icon {}, renamed to {}'.format(
                        item[0],
                        name
                    )
                )
                name = problematic_icons[item[0]]
            modifier = ''
            if style == 'solid':
                modifier = '\\textbf'
            elif style == 'light':
                modifier = '\\textit'
            icon = {}
            icon['name'] = name
            icon['label'] = formatLabel(item[1]['label'])
            icon['type'] = fa_type
            icon['unicode'] = item[1]['unicode'].upper()
            icon['prepend'] = pkg['prepend']
            icon['append'] = pkg['append']
            icon['modifier'] = modifier
            icons.append(icon)
            log.debug('Processed {} for style {}'.format(icon['label'], style))

    return icons


def genTemplate(template, **kwargs):
    ''' Generate a jinja2 template and pass **args to it.
    Returns the rendered template. '''
    log.debug('Generating template: ' + template)
    template = jinja_env.get_template(template)

    return template.render(**kwargs)


def saveFile(data, filename, output_dir='', overwrite=False):
    ''' Save data to output_dir/filename '''
    filename = os.path.join(output_dir, filename)
    if (os.path.isfile(filename) and not overwrite):
        raise FileExistsError(filename + ' exists!')

    os.makedirs(output_dir, exist_ok=True)

    mode = 'w'

    if type(data) is bytes:
        mode = 'wb'
    elif type(data) is not str:
        raise TypeError('Data input is not a string or byte array!')

    log.debug('Opening {} in {} for writing'.format(
        filename,
        mode
    ))
    with open(filename, mode) as f:
        f.write(data)

    return filename


# TODO: main is complex
@click.command() # noqa: C901
@click.argument('version', required=False)
@click.option('--download-dir', default='tmp',
              help='Directory to put downloaded files.')
@click.option('--output-dir', default='output',
              help='Directory to put rendered files.')
@click.option('--fonts-dir', default='fonts',
              help='Directory to put related fonts.')
@click.option('--local-file', default=None,
              help='Use a local zipped file')
@click.option('--zipped-dir', default=None,
              help='Use a local unzipped dir')
@click.option('--debug', is_flag=True,
              help='Enable debug output')
@click.option('--yes', is_flag=True,
              help='Yes for all prompts')
def main(version, download_dir, output_dir, fonts_dir,
         local_file, zipped_dir, debug, yes):
    ''' Process CLI arguments accordingly.
    Download, unzip, load metadata, and create the templates. '''

    # Enable debugging

    if debug:
        log.root.setLevel(logging.DEBUG)
        args = locals()
        for key in args:
            log.debug('{}: {}'.format(key, args[key]))

    # Some variables that may change in the future

    metadata_file = 'icons.yml'
    metadata_dir = 'metadata'
    font_dir = 'use-on-desktop'

    # Handle download

    response = local_file

    if response is None and zipped_dir is None:
        log.debug('No local zip or zipped dir specified. Downloading...')
        try:
            release = getAndCheckRelease(version)
        except ReleaseException:
            if version is not None:
                log.warn('Release version %s was not found.' % version)
                if choice('Download latest release?') or yes:
                    release = getAndCheckRelease()
        response = downloadFile(release, output_dir=download_dir)

    # Handle zip archive

    dirs = handleZipArchive(response, zipped_dir, download_dir)

    log.debug('Found the following dirs: {}'.format(dirs))

    zip_dir = dirs[0].split('/')[0]

    # Process Fonts

    fonts_out_dir = os.path.join(output_dir, fonts_dir)

    font_dirs = [
        os.path.join(download_dir, d) for d in dirs if font_dir in d
    ]
    log.debug('font_dirs: '.format(font_dirs))

    fonts = []
    if len(font_dirs) == 1:
        fonts = copyFonts(font_dirs[0], fonts_out_dir)
    else:
        log.error(
            'Cannot find the fonts dir in the Font Awesome zip! '
            'Typically it is tmp/fontawesome-free-x.x.xx/use-on-desktop. '
        )
        promptError('Continue without fonts?', yes)

    if len(fonts) == 0:
        log.error(
            'Did not find any fonts in {}'.format(fonts_out_dir) +
            ' If you continue, you will have to manually install fonts'
            ' from fontawesome.zip/use-on-desktop to the fonts directory.'
        )
        promptError('Continue without fonts?', yes)

    fa_type = fontVersion(fonts)
    log.debug('Building for Font Awesome ' + fa_type)

    # Load Metadata

    metadata_dirs = [
        os.path.join(download_dir, d) for d in dirs if metadata_dir in d
    ]
    log.debug('metadata_dirs: {}'.format(metadata_dirs))

    data = loadMetadata(metadata_dirs, metadata_file)

    # Process Font Styles

    d = date.today().strftime('%Y/%m/%d')
    readme_path = os.path.join(download_dir, zip_dir, 'README.md')
    fa_version = getVersion(readme_path)

    fonts_dir = fonts_dir + '/' if fonts_dir[-1] != '/' else fonts_dir

    package['desc'] = package['desc'].format(
        date=d,
        version=fa_version,
        fa_type=fa_type.upper()
    )

    icons = genIcons(data, package, fa_type)

    templates = {
        'sty': genTemplate(
            'fontawesome.sty',
            icons=icons,
            package=package,
            fonts_dir=fonts_dir,
            fa_type=fa_type
        ),
        'tex': genTemplate(
            'fontawesome.tex',
            icons=icons,
            package=package,
            fonts_dir=fonts_dir,
            fa_type=fa_type
        )
    }
    for extension, template in templates.items():
        output_file = '{}.{}'.format(package['file'], extension)
        log.debug('Building '.format(output_file))
        try:
            saveFile(template, output_file, output_dir, yes)
        except FileExistsError:
            output = os.path.join(output_dir, output_file)
            if choice('{} exists! Overwrite?'.format(output)):
                saveFile(template, output_file, output_dir, True)
            else:
                log.info('Skipping ' + output)

    log.info('Templates built! Check {}'.format(
        os.path.abspath(output_dir)
    ))


if __name__ == '__main__':
    main()
