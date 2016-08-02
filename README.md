# Let's Encrypt Gandi Plugin

Obtain certificates from [Let's Encrypt](https://letsencrypt.org/) and use them with [Gandi](https://www.gandi.net) products.

## Requirements

* You need to have the `letsencrypt` client [installed on your computer](https://letsencrypt.org/howitworks/)
* You'll need a [Gandi API Key](https://wiki.gandi.net/xml-api/activate), which you can get from your [Gandi Account](https://www.gandi.net/admin/api_key)

## Installation

* Clone the plugin's repository, or download it from a Zip file, into a local folder on your computer
* Enter the directory and use the `pip` executable distributed with `letsencrypt` to install the plugin

```
~ $ git clone https://github.com/Gandi/letsencrypt-gandi.git
~ $ cd letsencrypt-gandi
~/letsencrypt-gandi $ ~/.local/share/letsencrypt/bin/pip install -e .
```

## Usage

### Simple Hosting

#### Requirements

* You must have a ["M"-sized (or greater) Simple Hosting instance](https://www.gandi.net/hosting/simple/power) to enable SSL
* You must [add the certificate's domain name to your instance's VHOSTS](https://wiki.gandi.net/simple/shs-dns_config)
* You need to have [SSH Key authentication](https://wiki.gandi.net/en/simple/ssh_key) setup on the Simple Hosting instance
* Your SSH Key must be added to your local `ssh-agent` (use `ssh-add /path/to/key` to add it)

#### Limitations

* Currently, **only PHP, Ruby and Python instances are supported** by the plugin. Node.js instances are not yet supported by the plugin, but you can refer to [this tutorial  for a walkthrough](https://wiki.gandi.net/tutorials/letsencrypt).

##### Limitations of Python instances

Python applications are handled through a [WSGI application in Gandi](https://wiki.gandi.net/en/simple/instance/python) so to get this plugin to worki, you need to configure your application to serve a directory called **.well-known** staticaly from the application folder.

If you are using Django, you can get this adding this line to your **urls.py** file:

```python
    url(r'^\.well-known/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '.well-known'}),
```

After doing that in your application and deploying it to gandi, you can use this plugin to get and deploy a letsencrypt
certificate.

#### Instructions

Run the following command from your computer and make sure you replace the placeholders with your own information.

* `SHS-NAME`: the name of the instance
* `VHOST`: the domain name for the certificate and of the Simple Hosting VHOST
* `API-KEY`: your Gandi API key

```
~/letsencrypt $ ./letsencrypt-auto run --domains VHOST \
            --authenticator letsencrypt-gandi:gandi-shs \
                --letsencrypt-gandi:gandi-shs-name SHS-NAME \
                --letsencrypt-gandi:gandi-shs-vhost VHOST \
                --letsencrypt-gandi:gandi-shs-api-key API-KEY \
            --installer letsencrypt-gandi:gandi-shs
```

Simply follow the steps presented on the screen to complete the process.

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

## Development / Advanced usage

Here are some examples that are especially useful if you are developing the plugin itself.

### Setting the API key in the environment

You can also set your API key in an environment variable. This way you don't need to use the `--letsencrypt-gandi:gandi-shs-api-key` flag.

```
export GANDI_API_KEY="l00km4im1nth3nv"
```

### `certonly` command

To only generate and download the certs from Let's Encrypt to your computer, you can use the `certonly` command with the `letsencrypt-gandi:gandi-shs` authenticator.

```
~/letsencrypt $ ./letsencrypt-auto certonly --domains VHOST \
            --authenticator letsencrypt-gandi:gandi-shs \
                --letsencrypt-gandi:gandi-shs-name SHS-NAME \
                --letsencrypt-gandi:gandi-shs-vhost VHOST \
                --letsencrypt-gandi:gandi-shs-api-key API-KEY \
```

### `install` command

To only install the certs downloaded to your computer on Simple hosting, you can use the `install` command and the `letsencrypt-gandi:gandi-shs` installer.

```
~/letsencrypt $ ./letsencrypt-auto install --domains VHOST \
            --cert-path /path/to/cert
            --installer letsencrypt-gandi:gandi-shs \
              --letsencrypt-gandi:gandi-shs-name SHS-NAME \
              --letsencrypt-gandi:gandi-shs-vhost VHOST \
              --letsencrypt-gandi:gandi-shs-api-key API-KEY \
```

### Debugging

With the following additional flags, you'll be able to use LE's staging server and control where your local files are kept. The log file created in `~/.letsencrypt/letsencrypt.log` may contain more information about your problem.

```
~/letsencrypt $ ./letsencrypt-auto --config-dir $HOME/.letsencrypt \
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
