# https://api.github.com/repos/FortAwesome/Font-Awesome/releases/latest

import sys
import requests
from tqdm import tqdm

tqdm_kb = {
    'unit': 'B',
    'unit_scale': True,
    'unit_divisor': 1024,
    'miniters': 1
}


def downloadFile(url, filename=None, outputDir=''):
    ''' Download a resource using requests
    Track progress using tqdm. '''
    if filename is None:
        filename = url.split('/')[-1]
    filename = outputDir + filename

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

    return response


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
    data = response.json()

    return data


if __name__ == "__main__":
    version = None
    if len(sys.argv) > 1:
        version = sys.argv[1]

    info = getReleaseInfo(version)
    if 'message' in info:
        if info['message'] == "Not Found":
            print('Version %s not found. ' % version +
                  'Trying the latest version.')
            info = getReleaseInfo()

    if 'assets' in info:
        downloadFile(info['assets'][0]['browser_download_url'])
    else:
        print('Did not find a download link or a message. Aborting.')
        print(info)
