'''
Fontawesome Latex Generator
'''
__version__ = '1.0.0'
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
    'disable_existing_loggers': False,
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
logger = logging.getLogger()

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


packages = {
    'regular': {
        'name': 'fontawesomefree',
        'desc': '{date} {version} Font Awesome 5 Free Regular',
        'font': 'Font Awesome 5 Free-Regular-400',
        'class': 'fontawesome-free',
        'short': 'fa',
        'cmd': 'faicon',
        'file': 'fontawesomefree'
    },
    'solid': {
        'name': 'fontawesomefreesolid',
        'desc': '{date} {version} Font Awesome 5 Free Solid',
        'font': 'Font Awesome 5 Free-Solid-900',
        'class': 'fontawesome-free-solid',
        'short': 'fas',
        'cmd': 'fasicon',
        'file': 'fontawesomefreesolid'
    },
    'brands': {
        'name': 'fontawesomebrandsregular',
        'desc': '{date} {version} Font Awesome 5 Brands Regular',
        'font': 'Font Awesome 5 Brands-Regular-400',
        'class': 'fontawesome-brands-regular',
        'short': 'fab',
        'cmd': 'fabicon',
        'file': 'fontawesomebrandsregular'
    }
}

styles = [name for name in packages]


class ReleaseException(Exception):
    pass


def choice(text, default='N'):
    ''' Request a y/N answer from the user. '''
    try:
        return strtobool(input(text))
    except ValueError:
        return strtobool(default)


def getReleaseInfo(version=None):
    ''' Download the specified release from profile/repo.
    If no release is specified, downloads the latest zip file.'''

    apiURL = 'https://api.github.com/repos/FortAwesome/Font-Awesome/releases'

    if version is None:
        release = '/latest'
    else:
        release = '/tags/' + version

    url = apiURL + release

    logger.debug('Looking for a release in ' + url)

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
        logger.warn('Cannot determine browser download url from assets. '
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
        logger.debug(e)
        if getattr(e, 'response'):
            logger.debug('Release exception: ' + e.response)

        raise

    logger.debug('Found a release! ' + url)

    return url


def downloadFile(url, filename=None, output_dir=''):
    ''' Download a resource using requests
    Track progress using tqdm. '''
    if filename is None:
        filename = url.split('/')[-1]
    filename = os.path.join(output_dir, filename)

    logger.debug('Downloading {} as {}'.format(
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


def unzip(filename, target=''):
    ''' Unzip a file into the target directory.
    Do some basic checks along the way. '''
    if not zipfile.is_zipfile(filename):
        raise FileNotFoundError(filename + ' is not a zip file!')

    desc = 'unzipping ' + filename
    with zipfile.ZipFile(filename, 'r') as z, \
            tqdm(desc=desc) as t:
        files = z.infolist()
        total = len(files)
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

    os.makedirs(output_dir, exist_ok=True)

    for font in fonts:
        font = os.path.join(font_dir, font)
        logger.debug('Copying Font {} to {}'.format(
            font,
            output_dir
        ))
        path = shutil.copy(font, output_dir)
        logger.debug('Copied {} to {}'.format(
            font,
            path
        ))


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
    logger.debug('Looking for version in: ' + readme)

    version = None
    with open(readme, 'r') as f:
        for line in f:
            logger.debug('Searching: ' + line)
            version = re.search(
                r'([0-9]{1,2}).([0-9]{1,2}).([0-9]{2,3})',
                line
            ).group()
            if 'Font Awesome' in line and version is not None:
                logger.debug('Version: ' + version)
                break
        else:
            logger.warn('Could not find a version!')

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
                logger.debug('Replaced {} to {} in {}'.format(
                    item[0],
                    item[1],
                    text
                ))

    words = []
    for word in text.split(' '):
        words.append(word.capitalize())

    return ''.join(words)


def genIcons(data, style):
    ''' Take in a metadata dictionary of icons.
    Returns a dictionary of icons with minimal information. '''
    icons = []
    for item in sorted(data.items()):
        if style in item[1]['styles']:
            logger.debug('Processing {} labeled {}'.format(
                item[0],
                item[1]['label']
            ))
            name = item[0]
            if name in problematic_icons:
                logger.debug(
                    'Caught problematic icon {}, renamed to {}'.format(
                        item[0],
                        name
                    )
                )
                name = problematic_icons[item[0]]
            icon = {}
            icon['name'] = name
            icon['label'] = formatLabel(item[1]['label'])
            icon['unicode'] = item[1]['unicode'].upper()
            icons.append(icon)
            logger.debug('Processed ' + icon['label'])

    return icons


def genTemplate(template, **kwargs):
    ''' Generate a jinja2 template and pass **args to it.
    Returns the rendered template. '''
    logger.debug('Generating template: ' + template)
    template = jinja_env.get_template(template)

    return template.render(**kwargs)


def styTemplate(icons, package):
    ''' Generate a sty template from a list of icons '''
    return genTemplate('fontawesome.sty', package=package, icons=icons)


def texTemplate(icons, package, fonts_dir):
    ''' Generate a tex template from a list of icons '''
    return genTemplate(
        'fontawesome.tex',
        package=package,
        icons=icons,
        fonts_dir=fonts_dir
    )


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

    logger.debug('Opening {} in {} for writing'.format(
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
@click.option('--style', type=click.Choice(['all'] + styles),
              default='all', help='Font Awesome font style')
@click.option('--debug', is_flag=True,
              help='Enable debug output')
@click.option('--yes', is_flag=True,
              help='Yes for all prompts')
def main(version, download_dir, output_dir, fonts_dir,
         local_file, style, zipped_dir, debug, yes):
    ''' Process CLI arguments accordingly.
    Download, unzip, load metadata, and create the templates. '''

    # Enable debugging

    if debug:
        logger.root.setLevel(logging.DEBUG)
        args = locals()
        for key in args:
            logger.debug('{}: {}'.format(key, args[key]))

    # Some variables that may change in the future

    metadata_file = 'icons.yml'
    metadata_dir = 'metadata'
    font_dir = 'use-on-desktop'

    # Handle download

    response = local_file

    if response is None and zipped_dir is None:
        logger.debug('No local zip or zipped dir specified. Downloading...')
        try:
            release = getAndCheckRelease(version)
        except ReleaseException:
            if version is not None:
                logger.warn('Release version %s was not found.' % version)
                if choice('Download latest release? [y/N]') or yes:
                    release = getAndCheckRelease()
        response = downloadFile(release, output_dir=download_dir)

    # Handle zip archive

    if zipped_dir is None:
        logger.debug('No zipped dir specified. Unzipping {}'.format(response))
        files = unzip(response, download_dir)
        dirs = [f.filename for f in files if f.file_size == 0]
    else:
        logger.debug('Zipped dir specified! Unzipping {}'.format(response))
        dirs = [
            d[0].replace(download_dir + '/', '', 1)
            for d in os.walk(download_dir)
            if d[0] != download_dir
        ]

    logger.debug('Found the following dirs: {}'.format(dirs))

    zip_dir = dirs[0].split('/')[0]

    # Process Fonts

    fonts_dir = os.path.join(output_dir, fonts_dir)

    font_dirs = [
        os.path.join(download_dir, d) for d in dirs if font_dir in d
    ]
    logger.debug('font_dirs: '.format(font_dirs))

    if len(font_dirs) == 1:
        copyFonts(font_dirs[0], fonts_dir)
    else:
        logger.error(
            'Cannot find the fonts dir in the Font Awesome zip! '
            'Typically it is tmp/fontawesome-free-x.x.xx/use-on-desktop.'
        )
        if not choice('Continue without fonts? [y/N]', yes):
            logger.error('Aborting!')
            sys.exit(1)

    # Load Metadata

    metadata_dirs = [
        os.path.join(download_dir, d) for d in dirs if metadata_dir in d
    ]
    logger.debug('metadata_dirs: {}'.format(metadata_dirs))

    data = loadMetadata(metadata_dirs, metadata_file)

    # Process Font Styles

    if style == 'all':
        queue = [(s, packages[s]) for s in styles]
    else:
        queue = [(style, packages[style])]

    d = date.today().strftime('%Y/%m/%d')
    readme_path = os.path.join(download_dir, zip_dir, 'README.md')
    fa_version = getVersion(readme_path)

    for name, package in queue:
        package['desc'] = package['desc'].format(date=d, version=fa_version)
        icons = genIcons(data, name)
        templates = {
            'sty': styTemplate(icons, package),
            'tex': texTemplate(icons, package, fonts_dir)
        }
        for extension, template in templates.items():
            output_file = '{}.{}'.format(package['name'], extension)
            logger.debug('Building '.format(output_file))
            try:
                saveFile(template, output_file, output_dir, yes)
            except FileExistsError:
                output = os.path.join(output_dir, output_file)
                if choice('{} exists! Overwrite? [y/N]'.format(output)):
                    saveFile(template, output_file, output_dir, True)
                else:
                    logger.info('Skipping ' + output)

    logger.info('Templates built! Check {}'.format(
        os.path.abspath(output_dir)
    ))


if __name__ == '__main__':
    main()
