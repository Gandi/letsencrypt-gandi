"""GANDI Simple-Hosting Configuration for Let's Encrypt."""
# pylint: disable=too-many-lines
import logging
import os
import re
import xmlrpclib
import tempfile
import subprocess

import zope.interface

from acme import challenges
try:
    from letsencrypt import errors
    from letsencrypt import interfaces

    from letsencrypt.plugins import common
except ImportError:
    from certbot import errors
    from certbot import interfaces

    from certbot.plugins import common

logger = logging.getLogger(__name__)

UPSTREAM_URL = 'https://github.com/Gandi/letsencrypt-gandi'
GANDI_API_URL = 'https://rpc.gandi.net/xmlrpc/'

ACME_BASE_PATH = '.well-known/acme-challenge'

HTACCESS_PATCH = """
# Patch for Let's Encrypt
RewriteEngine off
"""


def get_user_environment():
    new_env = os.environ.copy()
    if 'SUDO_USER' in new_env:
        new_env['HOME'] = os.path.expanduser('~' + new_env['SUDO_USER'])
        new_env['USER'] = new_env['SUDO_USER']
        new_env['USERNAME'] = new_env['SUDO_USER']

    return new_env


class GandiSHSConfigurator(common.Plugin):
    # pylint: disable=too-many-instance-attributes,too-many-public-methods

    """GANDI Simple-Hosting configurator.

    :ivar config: Configuration.
    :type config: :class:`~letsencrypt.interfaces.IConfig`
    """

    zope.interface.implements(interfaces.IAuthenticator, interfaces.IInstaller)
    zope.interface.classProvides(interfaces.IPluginFactory)

    description = "Gandi Simple Hosting - Alpha"

    htaccess_content = None
    _shs_info = None

    @classmethod
    def add_parser_arguments(cls, add):
        add("api-key",
            help="GANDI api key.")
        add("name",
            help="shs name.")
        add("vhost", default='default',
            help="vhost")

    def __init__(self, *args, **kwargs):
        """Initialize an SHS Configurator.
        """
        self.version = kwargs.pop("version", None)
        super(GandiSHSConfigurator, self).__init__(*args, **kwargs)

    def _api(self):
        api = xmlrpclib.ServerProxy(GANDI_API_URL)
        return api

    @property
    def shs_info(self):
        if not hasattr(self, 'api_key'):
            raise errors.PluginError("Api key is missing")
        if not hasattr(self, 'shs_name'):
            raise errors.PluginError("Simple hosting name is missing")

        if self._shs_info:
            return self._shs_info

        api = self._api()

        list = api.paas.list(self.api_key, {'name': self.shs_name})
        if not list:
            raise errors.PluginError(
                "Couldn't find any match for {0}".format(self.shs_name))

        self._shs_info = api.paas.info(self.api_key, list[0]['id'])
        return self._shs_info

    #
    # Plugin Section
    #
    def prepare(self):
        """Prepare the plugin

        Get apikey and store in config
        """

        self.api_key = self._api_key_from_args() or\
            self._api_key_from_env() or\
            self._api_key_from_gandi_cli()

        if not self.api_key:
            raise errors.PluginError("Api key is missing, couldn't found from "
                                     "neither gandi.cli, environment"
                                     "(GANDI_API_KEY), nor --{0}"
                                     .format(self.option_name('api-key')))

        self.shs_name = self.conf('name')
        if not self.shs_name:
            raise errors.PluginError("--{0} is a required parameter,"
                                     "please provide a valid simple hosting "
                                     "name".format(self.option_name('name')))

        self.vhost = self.conf('vhost')

        if not re.match('^(php|ruby|python)', self.shs_info['type']):
            raise errors.PluginError(
                "Sorry, only php and ruby instances are supported for now, "
                "we're doing our best to get everything supported with "
                "Let's Encrypt. Please check {0} for newer versions."
                .format(UPSTREAM_URL))

    def _api_key_from_gandi_cli(self):
        """Got cli? grab it https://cli.gandi.net

        :returns: api key or none
        :rtype: (None, str)
        """
        logger.info('_api_key_from_gandi_cli')
        try:
            from gandi.cli.core.conf import GandiConfig
            GandiConfig.load_config()
            return GandiConfig.get('api.key')
        except ImportError:
            pass

    def _api_key_from_env(self):
        """Looks up key from environment
        use GANDI_API_KEY

        :returns: api key or none
        :rtype: (None, str)
        """
        logger.info('_api_key_from_env')
        key = os.environ.get('GANDI_API_KEY')
        if key:
            if re.match('^[a-zA-Z0-9]{24}$', key):
                # looks like a gandi api key
                return key

    def _api_key_from_args(self):
        """Looks up key from arguments

        :returns: api key or none
        :rtype: (None, str)
        """
        logger.info('_api_key_from_args')
        return self.conf('api-key')

    def more_info(self):
        """Human-readable string to help understand the module"""
        return (
            "Configures GANDI Simple-Hosting to authenticate and install"
            "HTTPS.{0}Version: {version}".format(
                os.linesep, version=".".join(str(i) for i in self.version))
        )

    #
    # Authenticator Section
    #
    def get_chall_pref(self, unused_domain):  # pylint: disable=no-self-use
        """Return list of challenge preferences."""
        return [challenges.HTTP01]

    def perform(self, achalls):
        """Perform the challenge with a file.
        """

        return [self._perform_single(achall) for achall in achalls]

    def _lookup_shs(self):
        paas = self.shs_info

        return paas['user'], paas['ftp_server']

    def _base_path(self):
        if re.match('^php', self.shs_info['type']):
            return 'vhosts/{vhost}/htdocs/'.format(vhost=self.vhost)
        elif re.match('^python', self.shs_info['type']):
            return 'vhosts/default'
        # if ruby
        return 'vhosts/default/public'

    def _intermediate_dirs(self):
        base_path = self._base_path()
        return [base_path + '/' + dir for dir in [
            '',
            '.well-known/',
            '.well-known/acme-challenge'
        ]]

    def _perform_single(self, achall):
        response, validation = achall.response_and_validation()

        path = achall.chall.encode("token")
        logger.info("Deploying Certificate %s: %s",
                    achall.chall.encode("token"), validation.encode())

        user, sftp_url = self._lookup_shs()

        dirs = self._intermediate_dirs()
        path = dirs[len(dirs) - 1]

        destfile = achall.chall.encode("token")

        try:
            tmpfile = tempfile.mkstemp(suffix='.letsencrypt.gandi.shs')
            logger.info("tmpfile = %s", tmpfile)
            os.write(tmpfile[0], validation.encode())
            self._try_shs_auth(user, sftp_url)
            self._upload_tmpfile(
                tmpfile[1], user, sftp_url, path, destfile, dirs)

            self.htaccess_content = self._patch_htaccess(
                self._base_path(), user, sftp_url)
            return response
        finally:
            os.close(tmpfile[0])
            os.remove(tmpfile[1])

    def _try_shs_auth(self, user, sftp_url):

        process = ['sftp',
                   '-o', 'UserKnownHostsFile={home}/.ssh/known_hosts'.format(home=get_user_environment()['HOME']),
                   '{user}@{sftp_url}'.format(user=user, sftp_url=sftp_url)]

        logger.info("sftp %s", process)

        sftp = subprocess.Popen(process, stdin=subprocess.PIPE, close_fds=True,
                                env=get_user_environment())

        print >> sftp.stdin, 'exit'

        ret = sftp.wait()

        if ret != 0:
            raise errors.PluginError("Couldn't connect to the instance at {url}"
                                     .format(url=sftp_url))

    def _upload_tmpfile(self, tmpfile, user, sftp_url, path, destfile, mkdir):

        process = ['sftp', '-b', '-',
                    '-o', 'UserKnownHostsFile={home}/.ssh/known_hosts'.format(home=get_user_environment()['HOME']),
                   '{user}@{sftp_url}'.format(user=user, sftp_url=sftp_url)]

        logger.info("sftp %s", process)

        sftp = subprocess.Popen(process, stdin=subprocess.PIPE, close_fds=True,
                                env=get_user_environment())

        for p in mkdir:
            # sftp will abort if any of the following commands fail:
            # get, put, reget, reput, rename, ln, rm, mkdir, chdir, ls, lchdir,
            # chmod, chown, chgrp, lpwd, df, symlink, and lmkdir.  Termination
            # on error can be suppressed on a command by command basis by
            # prefixing the command with a '-' character (for example,
            # -rm /tmp/blah*).

            print >> sftp.stdin, '-mkdir {path}'.format(path=p)

        print >> sftp.stdin, 'cd {path}'.format(path=path)
        print >> sftp.stdin, 'put {tmpfile} {destfile}'.format(
            tmpfile=tmpfile, destfile=destfile)
        print >> sftp.stdin, 'chmod 444 {destfile}'.format(destfile=destfile)
        print >> sftp.stdin, 'exit'

        ret = sftp.wait()

        if ret != 0:
            raise errors.PluginError("Couldn't place file in domain: {0}"
                                     .format(path))

    def _patch_htaccess(self, path, user, sftp_url):
        """Create or patch htaccess

        Add an exclusion for ACME_BASE_PATH
        :rtype: (None, str)
        """
        content = None

        process = ['sftp', '-b', '-',
                   '-o', 'UserKnownHostsFile={home}/.ssh/known_hosts'.format(home=get_user_environment()['HOME']),
                   '{user}@{sftp_url}'.format(user=user, sftp_url=sftp_url)]

        sftp = subprocess.Popen(process, stdin=subprocess.PIPE, close_fds=True,
                                env=get_user_environment())

        print >> sftp.stdin, 'cd {path}/.well-known'.format(path=path)
        try:
            tmpfile = tempfile.mkstemp(suffix='.letsencrypt.gandi.shs')
            print >> sftp.stdin, 'get .htaccess {tmpfile}'.format(
                tmpfile=tmpfile[1])
            print >> sftp.stdin, 'exit'
            sftp.wait()
            with open(tmpfile[1], 'r') as htaccess:
                content = htaccess.read()
        finally:
            os.close(tmpfile[0])
            os.remove(tmpfile[1])

        if content:
            new_content = content + HTACCESS_PATCH
        else:
            new_content = HTACCESS_PATCH

        sftp = subprocess.Popen(process, stdin=subprocess.PIPE, close_fds=True,
                                env=get_user_environment())

        print >> sftp.stdin, 'cd {path}/.well-known'.format(path=path)
        try:
            # Patch
            tmpfile = tempfile.mkstemp(suffix='.letsencrypt.gandi.shs')
            os.write(tmpfile[0], new_content)

            # Upload with patch
            print >> sftp.stdin, 'put {tmpfile} .htaccess'.format(
                tmpfile=tmpfile[1])
            print >> sftp.stdin, 'chmod 644 .htaccess'
            print >> sftp.stdin, 'exit'
            sftp.wait()
        finally:
            os.close(tmpfile[0])
            os.remove(tmpfile[1])

        return content

    def _unpatch_htaccess(self, path, user, sftp_url):
        """Remove patchs from htaccess

        :rtype: None
        """

        process = ['sftp', '-b', '-',
                   '-o', 'UserKnownHostsFile={home}/.ssh/known_hosts'.format(home=get_user_environment()['HOME']),
                   '{user}@{sftp_url}'.format(user=user, sftp_url=sftp_url)]

        sftp = subprocess.Popen(process, stdin=subprocess.PIPE, close_fds=True,
                                env=get_user_environment())

        if not self.htaccess_content:
            print >> sftp.stdin, 'cd {path}/.well-known'.format(path=path)
            print >> sftp.stdin, '-rm .htaccess'
            print >> sftp.stdin, 'exit'
            sftp.wait()
        else:
            print >> sftp.stdin, 'cd {path}/.well-known'.format(path=path)
            try:
                tmpfile = tempfile.mkstemp(suffix='.letsencrypt.gandi.shs')
                os.write(tmpfile[0], self.htaccess_content)
                print >> sftp.stdin, 'put {tmpfile} .htaccess'.format(
                    tmpfile=tmpfile[1])
                print >> sftp.stdin, 'exit'
                sftp.wait()
            finally:
                os.close(tmpfile[0])
                os.remove(tmpfile[1])

    def cleanup(self, achalls):
        """Revert all challenges."""
        user, sftp_url = self._lookup_shs()

        return [self._cleanup_one(achall, user, sftp_url)
                for achall in achalls]

    def _cleanup_one(self, achall, user, sftp_url):
        """Remove one challenge from the sftp server"""

        self._unpatch_htaccess(self._base_path(), user, sftp_url)

        dirs = self._intermediate_dirs()
        dirs.reverse()
        path = dirs[0] + "/" + achall.chall.encode("token")

        process = ['sftp', '-b', '-',
                   '-o', 'UserKnownHostsFile={home}/.ssh/known_hosts'.format(home=get_user_environment()['HOME']),
                   '{user}@{sftp_url}'.format(user=user, sftp_url=sftp_url)]

        logger.info("sftp %s", process)

        sftp = subprocess.Popen(process, stdin=subprocess.PIPE, close_fds=True,
                                env=get_user_environment())

        print >> sftp.stdin, 'rm {path}'.format(path=path)
        for p in dirs:
            # sftp will abort if any of the following commands fail:
            # get, put, reget, reput, rename, ln, rm, mkdir, chdir, ls, lchdir,
            # chmod, chown, chgrp, lpwd, df, symlink, and lmkdir.  Termination
            # on error can be suppressed on a command by command basis by
            # prefixing the command with a '-' character (for example,
            # -rm /tmp/blah*).

            print >> sftp.stdin, 'rmdir {path}'.format(path=p)

        print >> sftp.stdin, 'exit'

        sftp.wait()

    #
    # Installer Section
    #
    def get_all_names(self):
        """Returns all names that may be authenticated.

        :rtype: `list` of `str`

        """
        return [self.vhost]

    def deploy_cert(self, domain, cert_path, key_path, chain_path,
                    fullchain_path):
        """Deploy certificate.

        :param str domain: domain to deploy certificate file
        :param str cert_path: absolute path to the certificate file
        :param str key_path: absolute path to the private key file
        :param str chain_path: absolute path to the certificate chain file
        :param str fullchain_path: absolute path to the certificate fullchain
            file (cert plus chain)

        :raises .PluginError: when cert cannot be deployed

        """
        api = self._api()
        with open(cert_path, 'r') as cert:
            with open(key_path, 'r') as key:
                api.cert.hosted.create(self.api_key, {
                    'key': key.read(),
                    'crt': cert.read()
                })

    def enhance(self, domain, enhancement, options=None):
        """Perform a configuration enhancement.

        :param str domain: domain for which to provide enhancement
        :param str enhancement: An enhancement as defined in
            :const:`~letsencrypt.constants.ENHANCEMENTS`
        :param options: Flexible options parameter for enhancement.
            Check documentation of
            :const:`~letsencrypt.constants.ENHANCEMENTS`
            for expected options for each enhancement.

        :raises .PluginError: If Enhancement is not supported, or if
            an error occurs during the enhancement.

        """
        raise errors.PluginError(
            "Unsupported enhancement: {0}".format(enhancement))

    def supported_enhancements(self):
        """Returns a list of supported enhancements.

        :returns: supported enhancements which should be a subset of
            :const:`~letsencrypt.constants.ENHANCEMENTS`
        :rtype: :class:`list` of :class:`str`

        """
        return []

    def get_all_certs_keys(self):
        """Retrieve all certs and keys set in configuration.

        :returns: tuples with form `[(cert, key, path)]`, where:

            - `cert` - str path to certificate file
            - `key` - str path to associated key file
            - `path` - file path to configuration file

        :rtype: list

        """
        # TODO

    def save(self, title=None, temporary=False):
        """Saves all changes to the configuration files.

        Both title and temporary are needed because a save may be
        intended to be permanent, but the save is not ready to be a full
        checkpoint. If an exception is raised, it is assumed a new
        checkpoint was not created.

        :param str title: The title of the save. If a title is given, the
            configuration will be saved as a new checkpoint and put in a
            timestamped directory. `title` has no effect if temporary is true.

        :param bool temporary: Indicates whether the changes made will
            be quickly reversed in the future (challenges)

        :raises .PluginError: when save is unsuccessful

        """
        # TODO

    def rollback_checkpoints(self, rollback=1):
        """Revert `rollback` number of configuration checkpoints.

        :raises .PluginError: when configuration cannot be fully reverted

        """
        # TODO

    def recovery_routine(self):
        """Revert configuration to most recent finalized checkpoint.

        Remove all changes (temporary and permanent) that have not been
        finalized. This is useful to protect against crashes and other
        execution interruptions.

        :raises .errors.PluginError: If unable to recover the configuration

        """
        # TODO

    def view_config_changes(self):
        """Display all of the LE config changes.

        :raises .PluginError: when config changes cannot be parsed

        """
        pass

    def config_test(self):
        """Make sure the configuration is valid.

        :raises .MisconfigurationError: when the config is not in a usable
                                        state

        """
        pass

    def restart(self):
        """Restart or refresh the server content.

        :raises .PluginError: when server cannot be restarted

        """
        pass  # No restart can be implemented for web-accelerator
