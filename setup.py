# coding=utf-8
import sys
import os
import logging

from setuptools import find_packages
from setuptools import setup

assert sys.version_info[0] == 3 and sys.version_info[1] >= 6, "hive requires Python 3.6 or newer"

VERSION = 'notag'
GIT_REVISION = 'nogitrev'
class GitRevisionProvider(object):
    """ Static class to provide version and git revision information"""
    logger = logging.getLogger('GitRevisionProvider')

    @classmethod
    def is_git_sha(cls, s):
        from re import fullmatch
        return fullmatch('^g[0-9a-f]{8}$', s) is not None

    @classmethod
    def get_git_revision(cls, s):
        git_revision = str(GIT_REVISION)
        if cls.is_git_sha(s):
            git_revision = s.lstrip('g')
        return git_revision

    @classmethod
    def get_commits_count(cls, s):
        commits = None
        try:
            commits = int(s)
        except:
            pass
        return commits

    @classmethod
    def provide_git_revision(cls):
        """ Evaluate version and git revision and save it to a version file
            Evaluation is based on VERSION variable and git describe if
            .git directory is present in tree.
            In case when .git is not available version and git_revision is taken
            from get_distribution call

        """
        version = str(VERSION)
        git_revision = str(GIT_REVISION)
        if os.path.exists(".git"):
            from subprocess import check_output
            command = 'git describe --tags --long --dirty'
            version_string = check_output(command.split()).decode('utf-8').strip()
            if version_string != 'fatal: No names found, cannot describe anything.':
                # git describe -> tag-commits-sha-dirty
                version_string = version_string.rstrip('-dirty')
                version_string = version_string.lstrip('v')   
                parts = version_string.split('-')
                parts_len = len(parts)
                # only tag or git sha
                if parts_len == 1:
                    if cls.is_git_sha(parts[0]):
                        git_revision = parts[0]
                        git_revision = git_revision.lstrip('g')
                    else:
                        version = parts[0]
                if parts_len == 2:
                    version = parts[0]
                    git_revision = cls.get_git_revision(parts[1])
                if parts_len > 2:
                    # git sha
                    git_revision = cls.get_git_revision(parts[-1])
                    # commits after given tag
                    commits = cls.get_commits_count(parts[-2])
                    # version based on tag
                    version = ''.join(parts[:-1])
                    if commits is not None:
                        version = ''.join(parts[:-2])
                    # normalize rc to rcN for PEP 440 compatibility
                    version = version.lower()
                    if version.endswith('rc'):
                        version += '0'
            else:
                cls.logger.warning("Git describe command failed for current git repository")
        else:
            from pkg_resources import get_distribution
            try:
                version, git_revision = get_distribution("hivemind").version.split("+")
            except:
                cls.logger.warning("Unable to get version and git revision from package data")
        cls._save_version_file(version, git_revision)
        return version, git_revision

    @classmethod
    def _save_version_file(cls, hivemind_version, git_revision):
        """ Helper method to save version.py with current version and git_revision """
        with open("hive/version.py", 'w') as version_file:
            version_file.write("# generated by setup.py\n")
            version_file.write("# contents will be overwritten\n")
            version_file.write("VERSION = '{}'\n".format(hivemind_version))
            version_file.write("GIT_REVISION = '{}'".format(git_revision))

VERSION, GIT_REVISION = GitRevisionProvider.provide_git_revision()
SQL_SCRIPTS_PATH = 'hive/db/sql_scripts/'
SQL_UPGRADE_PATH = 'hive/db/sql_scripts/upgrade/'

def get_sql_scripts(dir):
    from os import listdir
    from os.path import isfile, join
    return [join(dir, f) for f in listdir(dir) if isfile(join(dir, f))]

if __name__ == "__main__":
    setup(
        name='hivemind',
        version=VERSION + "+" + GIT_REVISION,
        description='Developer-friendly microservice powering social networks on the Steem blockchain.',
        long_description=open('README.md').read(),
        packages=find_packages(exclude=['scripts']),
        data_files=[(SQL_SCRIPTS_PATH, get_sql_scripts(SQL_SCRIPTS_PATH)), (SQL_UPGRADE_PATH, get_sql_scripts(SQL_UPGRADE_PATH))],
        setup_requires=[
            'pytest-runner'
        ],
        dependency_links=[
            'https://github.com/bcb/jsonrpcserver/tarball/8f3437a19b6d1a8f600ee2c9b112116c85f17827#egg=jsonrpcserver-4.1.3+8f3437a'
        ],
        install_requires=[
            'aiopg @ https://github.com/aio-libs/aiopg/tarball/862fff97e4ae465333451a4af2a838bfaa3dd0bc',
            'jsonrpcserver @ https://github.com/bcb/jsonrpcserver/tarball/8f3437a19b6d1a8f600ee2c9b112116c85f17827#egg=jsonrpcserver',
            'simplejson',
            'aiohttp',
            'certifi',
            'sqlalchemy',
            'funcy',
            'toolz',
            'maya',
            'ujson',
            'urllib3',
            'psycopg2-binary',
            'aiocache',
            'configargparse',
            'pdoc',
            'diff-match-patch',
            'prometheus-client',
            'psutil',
            'atomic',
            'python-dateutil>=2.8.1',
            'regex'
        ],
        extras_require={
            'dev': [
                'pyYAML',
                'prettytable'
            ]
        },
        entry_points={
            'console_scripts': [
                'hive=hive.cli:run',
            ]
        }
    )
