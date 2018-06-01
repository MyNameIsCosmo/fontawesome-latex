# https://api.github.com/repos/FortAwesome/Font-Awesome/releases/latest

import click
import logging
import os
import requests
import sys
import yaml
import zipfile
from distutils.util import strtobool
from logging.config import dictConfig
from tqdm import tqdm

tqdm_kb = {
    'unit': 'B',
    'unit_scale': True,
    'unit_divisor': 1024,
    'miniters': 1
}

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': logging.INFO
        }
    },
    'root': {
        'handlers': ['console'],
        'level': logging.INFO,
    }
}

dictConfig(logging_config)
logger = logging.getLogger()


class ReleaseException(Exception):
    pass


def choice(text, default='Y', timeout=10):
    ''' Request a Y/n answer from the user. '''
    try:
        return strtobool(input(text))
    except ValueError:
        return strtobool(default)


def getReleaseInfo(version=None):
    ''' Download the specified release from profile/repo.
    If no release is specified, downloads the latest zip file, if there is one.'''

    apiURL = 'https://api.github.com/repos/FortAwesome/Font-Awesome/releases'

    if version is None:
        release = '/latest'
    else:
        release = '/tags/' + version

    url = apiURL + release

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    return data


def checkReleaseInfo(info):
    ''' Checks if a release exists and if it has a zip file. '''
    if 'message' in info and info['message'] == "Not Found":
        raise ReleaseException('Release Not Found')
    if 'assets' not in info:
        raise Exception('Could not determine release download')
    if len(info['assets']) < 1 or 'browser_download_url' not in info['assets'][0]:
        logger.warn('Cannot determine browser download url from assets. '
                    'Checking zipball_url.')
        if 'zipball_url' not in info:
            raise Exception('Could not find a suitable zip file in the release.')
        return info['browser_download_url']

    url = info['assets'][0]['browser_download_url']
    if url[-4:] == ".zip":
        return url

    raise ReleaseException('Could not find a suitable zip file in the release.')


def getAndCheckRelease(version=None):
    info = getReleaseInfo(version)
    try:
        url = checkReleaseInfo(info)
    except ReleaseException:
        if version is not None:
            logger.warn('Release version %s was not found.')
            if choice('Download latest release?'):
                return getAndCheckRelease()
        logger.error('No release candidate. Aborting.')
        sys.exit(1)
    return url


def downloadFile(url, filename=None, output_dir=''):
    ''' Download a resource using requests
    Track progress using tqdm. '''
    if filename is None:
        filename = url.split('/')[-1]
    filename = os.path.join(output_dir, filename)

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

    desc = "unzipping " + filename
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


def loadMetadata(metadata_dirs, metadata_file):
    ''' Load a metadata file and parse it.
    Supports yaml and json parsing.

    For recent FontAwesome releases, there are metadata files for shims, icons,
    and categories located in /fontawesome-.../advanced-options/metadata '''

    if len(metadata_dirs) == 0:
        raise ValueError("No metadata folder in unzipped archive! Aborting.")
    elif len(metadata_dirs) > 1:
        raise ValueError("More than 1 metadata folder found in unzipped archive!"
                         "Directory traversing may be implemented soon.")

    metadata = metadata_dirs[0] + metadata_file

    with open(metadata) as f:
        data = yaml.safe_load(f)

    return data


@click.command()
@click.argument('version', required=False)
@click.option('--metadata-file', default='icons.yml',
              help="Name of the metadata file to be loaded.")
@click.option('--metadata-dir', default='metadata',
              help="Name of the metadata directory in the archive.")
@click.option('--output-dir', default='tmp',
              help="Directory to put downloaded files.")
@click.option('--local-file', default=None,
              help="Use a local zipped file")
def main(version, metadata_file, metadata_dir, output_dir, local_file):
    response = local_file

    if response is None:
        release = getAndCheckRelease(version)
        response = downloadFile(release, output_dir=output_dir)

    files = unzip(response, output_dir)
    dirs = [f.filename for f in files if f.file_size == 0]
    metadata_dirs = [os.path.join(output_dir, d) for d in dirs if metadata_dir in d]

    data = loadMetadata(metadata_dirs, metadata_file)
    print(data)


if __name__ == "__main__":
    main()
