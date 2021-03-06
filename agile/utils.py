import os
from datetime import date
import configparser

from pulsar import ImproperlyConfigured


def passthrough(manager, version):
    pass


def semantic_version(tag):
    '''Get a valid semantic version for tag
    '''
    try:
        version = list(map(int, tag.split('.')))
        assert len(version) == 3
        return tuple(version)
    except Exception:
        raise ImproperlyConfigured('Could not parse tag, please use '
                                   'MAJOR.MINOR.PATCH')


def get_auth():
    """Return a tuple for authenticating a user

    If not successful raise ``ImproperlyConfigured``.
    """
    home = os.path.expanduser("~")
    config = os.path.join(home, '.gitconfig')
    if not os.path.isfile(config):
        raise ImproperlyConfigured('.gitconfig file not available in %s'
                                   % home)

    parser = configparser.ConfigParser()
    parser.read(config)
    if 'user' in parser:
        user = parser['user']
        if 'username' not in user:
            raise ImproperlyConfigured('Specify username in %s user '
                                       'section' % config)
        if 'token' not in user:
            raise ImproperlyConfigured('Specify token in %s user section'
                                       % config)
        return (user['username'], user['token'])
    else:
        raise ImproperlyConfigured('No user section in %s' % config)


def change_version(manager, version):

    def _generate():
        with open(manager.cfg.version_file, 'r') as file:
            text = file.read()

        for line in text.split('\n'):
            if line.startswith('VERSION = '):
                yield 'VERSION = %s' % str(version)
            else:
                yield line

    text = '\n'.join(_generate())
    with open(manager.cfg.version_file, 'w') as file:
        file.write(text)


def write_notes(manager, release):
    history = os.path.join(manager.releases_path, 'history')
    if not os.path.isdir(history):
        return False
    dt = date.today()
    dt = dt.strftime('%Y-%b-%d')
    vv = release['tag_name']
    hist = '.'.join(vv.split('.')[:-1])
    filename = os.path.join(history, '%s.md' % hist)
    body = ['# Ver. %s - %s' % (release['tag_name'], dt),
            '',
            release['body']]

    add_file = True

    if os.path.isfile(filename):
        # We need to add the file
        add_file = False
        with open(filename, 'r') as file:
            body.append('')
            body.append(file.read())

    with open(filename, 'w') as file:
        file.write('\n'.join(body))

    manager.logger.info('Added notes to changelog')

    if add_file:
        yield from manager.git.add(filename)
