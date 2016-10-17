# Let's Encrypt Gandi Plugin

**letsencrypt-gandi** is a plugin for [certbot](https://certbot.eff.org/) that allows you to obtain certificates from [Let's Encrypt](https://letsencrypt.org/) and use them with [Gandi](https://www.gandi.net) products such as [Simple Hosting](https://gandi.net/hosting/simple).

## Requirements

* [**certbot**](https://https://certbot.eff.org/) installed on your computer
* A [Gandi API Key](https://wiki.gandi.net/xml-api/activate), which you can get from your [Gandi Account](https://www.gandi.net/admin/api_key)
* Root privileges may be required to use **certbot** on your system (read the "Avoiding sudo" section to try to work around this limitation).

## Installation

The way you install the plugin will depend on how you installed **certbot** on your system.

In general terms, after you have installed and configured **certbot** itself, you'll have to clone the plugin's repository into a local folder on your computer (or [download it and extract it from a Zip file](https://github.com/Gandi/letsencrypt-gandi/archive/master.zip)). Then, you'll have to run the appropriate command to install it on your system.

The examples below will show you how to install the plugin in different scenarios.

### When using certbot from its repository

If you've cloned the [certbot repository](https://github.com/certbot/certbot) on your computer, you'll need to use the `pip` executable distributed with it to install the plugin.

First, run ``./certbot-auto --help`` from inside the cloned repository's folder to ensure that the necessary files are installed on your system.

Then, proceed to downloading and installing the **letsencrypt-gandi** plugin.

```
~ $ git clone https://github.com/Gandi/letsencrypt-gandi.git
~ $ cd letsencrypt-gandi
~/letsencrypt-gandi $ ~/.local/share/letsencrypt/bin/pip install -e .
```

Note that the `.` at the end of `pip install` command is important.

Also note that you might have to run **certbot** from within its own directory, using the `certbot-auto` executable. In this case, replace `[sudo] certbot` by `./certbot-auto` in the usage instructions and examples provided below.

### When using a packaged version of certbot (Linux distributions)

If you installed **certbot** using your Linux distribution's package manager, you'll need to install and use [pip](https://pypi.python.org/pypi/pip) to install this plugin.

Search the Web for instructions on how to install **pip** on your system. Once **pip** is installed, you should then be able to install the plugin with a simple command as exemplified below.

```
~ $ git clone https://github.com/Gandi/letsencrypt-gandi.git
~ $ cd letsencrypt-gandi
~/letsencrypt-gandi $ pip install -e .
```

Note that the `.` at the end of `pip install -e .` command is important.

### When using certbot from Homebrew on Mac OS X

If you installed **certbot** using the [Homebrew](http://brew.sh) package manager on Mac OS X, you'll need to run some (ugly) commands to install the plugin inside the correct directory.

First, locate the correct directory **certbot** by reading the `PYTHONPATH` environment variable included in the executable.

```
$ cat $(which certbot) | grep PYTHONPATH
PYTHONPATH="/usr/local/Cellar/certbot/0.8.0/libexec/lib/python2.7/site-packages:/usr/local/Cellar/certbot/0.8.0/libexec/vendor/lib/python2.7/site-packages" exec "/usr/local/Cellar/certbot/0.8.0/libexec/bin/certbot" "$@"
```

The path we're looking for is the one that includes the `libexec/` folder. In the example above, the path is:

```
/usr/local/Cellar/certbot/0.8.0/libexec/lib/python2.7/site-packages
```

Now you'll need to run `python setup.py install --install-purelib /path/that/you/identified`, making sure you set the `PYTHONPATH` environment variable with that same path for that command. For example:

```
~ $ git clone https://github.com/Gandi/letsencrypt-gandi.git
~ $ cd letsencrypt-gandi
~/letsencrypt-gandi $ export CERTBOT_LIB="/usr/local/Cellar/certbot/0.8.0/libexec/lib/python2.7/site-packages"
~/letsencrypt-gandi $ PYTHONPATH=$CERTBOT_LIB python setup.py install --install-purelib $CERTBOT_LIB
```

Keep in mind that every time certbot is upgraded by Homebrew, the plugin needs to be reinstalled. As of version 0.9.3 of certbot, you can just execute the command again after replacing the correct version number to the path. Replace 'CERTBOT_VERSION_NUMBER' with the number of the last version installed by Homebrew on your system (for example '0.9.3').

```
~/letsencrypt-gandi $ export CERTBOT_LIB="/usr/local/Cellar/certbot/CERTBOT_VERSION_NUMBER/libexec/lib/python2.7/site-packages"
~/letsencrypt-gandi $ PYTHONPATH=$CERTBOT_LIB python setup.py install --install-purelib $CERTBOT_LIB
```

## Usage

You'll be able to tell whether the plugin was successfully installed by running the `certbot plugins` command and looking for `letsencrypt-gandi` in the  output, as in the following example:

```
$ [sudo] certbot plugins
* letsencrypt-gandi:gandi-shs
Description: Gandi Simple Hosting - Alpha
Interfaces: IAuthenticator, IInstaller, IPlugin
Entry point: gandi-shs = letsencrypt_gandi.shs:GandiSHSConfigurator

* [...]
```

If the plugin was correctly installed, you can proceed to using it.

### Simple Hosting

#### Requirements

* You must have a ["M"-sized (or greater) Simple Hosting instance](https://www.gandi.net/hosting/simple/power) to enable SSL
* You must [add the certificate's domain name to your instance's VHOSTS](https://wiki.gandi.net/simple/shs-dns_config)
* You need to have [SSH Key authentication](https://wiki.gandi.net/en/simple/ssh_key) setup on the Simple Hosting instance
* Your SSH Key must be added to your local `ssh-agent` (use `ssh-add /path/to/key` to add it)
* The RSA key for certificates to be used with Simple Hosting can only be of 2048 bits.

#### Limitations

* Currently, **only PHP, Ruby and Python instances are supported** by the plugin. Node.js instances are not yet supported by the plugin, but you can refer to [our tutorial  for a walkthrough](https://wiki.gandi.net/tutorials/letsencrypt).

##### Limitations of Python instances

Python applications are handled through a [WSGI application in Gandi](https://wiki.gandi.net/en/simple/instance/python) so to get this plugin to work, you need to configure your application to serve a directory called `.well-known` statically from the application folder.

If you are using Django, you can do this by adding a route to your **urls.py** file:

```python
    url(r'^\.well-known/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '.well-known'}),
```

After doing that, deploy your application to your Simple Hosting instance and use this plugin to obtain and install a certificate.

#### Instructions

Run the following command from your computer and make sure you replace the placeholders with your own information.

* `SHS-NAME`: the name of the instance
* `VHOST`: the domain name for the certificate and of the Simple Hosting VHOST
* `API-KEY`: your Gandi API key

```
$ [sudo] certbot run --domains VHOST \
            --authenticator letsencrypt-gandi:gandi-shs \
                --letsencrypt-gandi:gandi-shs-name SHS-NAME \
                --letsencrypt-gandi:gandi-shs-vhost VHOST \
                --letsencrypt-gandi:gandi-shs-api-key API-KEY \
            --installer letsencrypt-gandi:gandi-shs
```

Simply follow the steps presented on the screen to complete the process.


For certificate **renewal** execute the same command, but change the option 'run' to 'certonly':
```
$ [sudo] certbot certonly --domains VHOST \
            --authenticator letsencrypt-gandi:gandi-shs \
                --letsencrypt-gandi:gandi-shs-name SHS-NAME \
                --letsencrypt-gandi:gandi-shs-vhost VHOST \
                --letsencrypt-gandi:gandi-shs-api-key API-KEY \
            --installer letsencrypt-gandi:gandi-shs
```

#### Scripting 

You can also create scripts to make this process easier for certificate creation and renewal. 

[Here's an example script](https://gist.github.com/internationils/7abdfdeec2c7af6011a4f0c94252f40a) created by @internationils, a Gandi customer.

#### Troubleshooting

##### Authentication issues

If you experience authentication issues, make sure you can connect to the instance via `sftp` from your terminal with your SSH Key and without a password.

If the connection via `sftp` works, but the script still has authentication issues, make sure you have added your SSH Key to `ssh-agent` on your computer (see the Requirements section for instructions).

In case everything seems to be set correctly, but the script is still not able to authenticate, try to run the above commands with `sudo` and re-run the script.

##### Other issues

You can also check previously reported [Issues](https://github.com/Gandi/letsencrypt-gandi/issues/) or create a new one if you need any help.

### Other products

Support for other Gandi products, such as [Web Accelerators](https://www.gandi.net/hosting/iaas/rproxy) and [Servers](https://www.gandi.net/hosting/iaas/), is not yet available through the plugin but may be added in the future.

[You can still use Let's Encrypt certificates with any Gandi product](http://wiki.gandi.net/tutorials/letsencrypt).

## Advanced usage

Here are some examples that are especially useful if you are developing the plugin itself.

### Setting the API key in the environment

You can also set your API key in an environment variable. This way you don't need to use the `--letsencrypt-gandi:gandi-shs-api-key` flag.

```
export GANDI_API_KEY="l00km4im1nth3nv"
```

### Avoiding `sudo`

**certbot** might require root privileges to run.

You can work around this requirement by specifiying different paths than the one it uses by default.

For example:

```
$ certbot --config-dir ~/some/path \
          -- work-dir ~/some/other/path \
          -- log-dir ~/yet/another/path \
          ...

More information can be found in [certbot's documentation](https://certbot.eff.org/docs/using.html#system-requirements).

### `certonly` command

To only generate and download the certs from Let's Encrypt to your computer, you can use the `certonly` command with the `letsencrypt-gandi:gandi-shs` authenticator.

```
$ [sudo] certbot certonly --domains VHOST \
            --authenticator letsencrypt-gandi:gandi-shs \
                --letsencrypt-gandi:gandi-shs-name SHS-NAME \
                --letsencrypt-gandi:gandi-shs-vhost VHOST \
                --letsencrypt-gandi:gandi-shs-api-key API-KEY \
```

### `install` command

To only install the certs downloaded to your computer on Simple hosting, you can use the `install` command and the `letsencrypt-gandi:gandi-shs` installer.

```
$ [sudo] certbot install --domains VHOST \
            --cert-path /path/to/cert
            --installer letsencrypt-gandi:gandi-shs \
              --letsencrypt-gandi:gandi-shs-name SHS-NAME \
              --letsencrypt-gandi:gandi-shs-vhost VHOST \
              --letsencrypt-gandi:gandi-shs-api-key API-KEY \
```

### Debugging

With the following additional flags, you'll be able to use LE's staging server and control where your local files are kept. The log file created in `~/.letsencrypt/letsencrypt.log` may contain more information about your problem.

```
$ [sudo] certbot --config-dir $HOME/.letsencrypt \
            --work-dir $HOME/.letsencrypt \
            --logs-dir $HOME/.letsencrypt \
            run --domains VHOST \
            --server https://acme-staging.api.letsencrypt.org/directory --break-my-certs \
            --authenticator letsencrypt-gandi:gandi-shs \
                --letsencrypt-gandi:gandi-shs-name SHS-NAME \
                --letsencrypt-gandi:gandi-shs-vhost VHOST \
                --letsencrypt-gandi:gandi-shs-api-key API-KEY \
            --installer letsencrypt-gandi:gandi-shs
```
