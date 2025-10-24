iway-certbot-dns-auth

Certbot hook for DNS challenge using iWay Portal API.

Dependencies

To use this module the certbot is required of course :-)

You can install certbot directly by your OS (e.g. Debian) and install
iway-certbot-dns-auth with:

    pip install iway-certbot-dns-auth

To install the iway-certbot-dns-auth in your users home use:

    pip install --user iway-certbot-dns-auth

This will install the module hooks under
$HOME/.local/bin/iway-certbot-auth-hook and
$HOME/.local/bin/iway-certbot-cleanup-hook. Don’t forget to expand your
PATH environment variable to PATH=$PATH:$HOME/.local/bin.

Or, better install certbot in a Python virtual environment together with
iway-certbot-dns-auth.

Config

The hook default config file is /etc/iway-certbot-dns-auth.yml but can
be change with the environment variable IWAY_CERTBOT_DNS_AUTH_CFG.

    IWAY_CERTBOT_DNS_AUTH_CFG=/etc/my-config.yml

The file have to contain a account section with

-   username - customer number or person username
-   password - password

Further it can contain a logging section with:

-   syslog - enable Syslog (default false)
-   level - log level (default "INFO")
-   address - Syslog address (default /dev/log)
-   facility - Syslog facility (default local0)
-   format - log format (default
    "%(asctime)s %(levelname)s %(name)s: %(message)s")

Example /etc/iway-certbot-dns-auth.yml:

    account:
      username: 12345
      password: 'changeme'
    logging:
      syslog: true

Usage

Create a new cert for your domain my-domain.com with:

    certbot \
      certonly \
      --email me@gmail.com \
      --no-eff-email \
      --agree-tos \
      --preferred-challenges dns \
      --manual \
      --manual-auth-hook /usr/local/bin/iway-certbot-auth-hook \
      --manual-cleanup-hook /usr/local/bin/iway-certbot-cleanup-hook \
      --domain my-domain.com

Renew cert with:

    certbot renew
