#!/usr/bin/env python
"""Loopia IP Updater: Another dynamic DNS service
When you don't have a static IP from your ISP but need to make sure that
your Loopia domain names always point to the current external IP.
Put in your server crontab and run as often as you see fit.

Username and password can also be specified in a file, ~/.loopiaapi.ini,
in standard INI-format, i.e:

    [credentials]
    username = USERNAME
    password = PASSWORD

Don't forget to add @loopiaapi to the end of your username.
"""
from __future__ import print_function
import argparse
import os
import re
import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


try:
    import xmlrpc.client as xmlrpc_client
except:
    import xmlrpclib as xmlrpc_client

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


def expand_filepath(filepath):
    return os.path.abspath(os.path.expanduser(filepath))

LOOPIA_API_ENDPOINT = 'https://api.loopia.se/RPCSERV'
EXTERNAL_IP_CHECK_URL = 'http://checkip.dyndns.org'
CONFIG_LOCATION = expand_filepath('~/.loopiaapi.ini')
EXTERNAL_IP_FILEPATH = expand_filepath('~/.loopiaapi-externalip')


def get_credentials(path=CONFIG_LOCATION):
    config = configparser.ConfigParser()
    config.read(expand_filepath(path))
    auth = []
    for item in ('username', 'password'):
        auth.append(config.get('credentials', item).strip())
    return tuple(auth)


def get_last_ip():
    if not os.path.exists(EXTERNAL_IP_FILEPATH):
        return None
    with open(EXTERNAL_IP_FILEPATH) as fh:
        return fh.read().strip()


def set_last_ip(current_ip):
    with open(EXTERNAL_IP_FILEPATH, 'w+') as fh:
        fh.write(current_ip.strip())


def whats_my_ip():
    resp = urlopen(EXTERNAL_IP_CHECK_URL).read().decode()
    match = re.search('(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})', resp)
    return match.groups()[0].strip() if match else None


def get_rpc_client(endpoint):
    return xmlrpc_client.ServerProxy(uri=endpoint, encoding='utf-8')


def validate_login_credentials(client, username, password):
    AUTH_ERROR = 'AUTH_ERROR'
    resp = client.getDomains(username, password)
    if isinstance(resp, list) and len(resp) and resp[0] == AUTH_ERROR:
        sys.exit('Invalid system credentials (Got {})'.format(AUTH_ERROR))


def update_domain(domain, username, password, ip_address,
                  api_endpoint=LOOPIA_API_ENDPOINT, **kwargs):
    sub, main_domain = parse_domain(domain)
    client = get_rpc_client(api_endpoint)
    validate_login_credentials(client, username, password)
    zone_records = client.getZoneRecords(username, password, main_domain, sub)

    for zone_record in zone_records:
        if zone_record['type'] != 'A':
            continue
        old_ip = zone_record['rdata']
        zone_record['rdata'] = ip_address
        client.updateZoneRecord(username, password, main_domain, sub,
                                zone_record)
        print('Zone record updated for {}. (Old ip: {}. '
              'New ip: {}).'.format(domain, old_ip, ip_address))


def update_domains(*domains, **kwargs):
    for domain in domains:
        update_domain(domain, **kwargs)


def parse_domain(domain):
    """ Return sub-domain + main domain as a tuple """
    count = domain.count('.')
    if not count:
        sys.exit("Domain {} doesn't seem to be valid...".format(domain))
    if count == 1:
        sub = '@'
    else:
        # TODO: Support more than one level of subdomains?
        sub, sep, domain = domain.partition('.')
    return (sub, domain)


def is_outdated(current_ip):
    """ The logic for whether the IP should be changed or not """
    last_ip = get_last_ip()

    if not last_ip:
        return False
    if current_ip == last_ip:
        return False
    else:
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'domains',
        nargs='+',
        help="The domains to update when server's IP changes.")
    parser.add_argument(
        '-e',
        '--api-endpoint',
        default=LOOPIA_API_ENDPOINT,
        help='The URL at which the Loopia XML-RPC API exists.')
    parser.add_argument(
        '-u',
        '--username',
        help='Username if not supplied in file.')
    parser.add_argument(
        '-p',
        '--password',
        help='Password if not supplied in file.')
    parser.add_argument(
        '-c',
        '--config',
        default=CONFIG_LOCATION,
        help='Manually specify config location.')
    parser.add_argument(
        '-i',
        '--ip-address',
        help='Specify to manually update to this ip.')
    parser.add_argument(
        '-f',
        '--force-update',
        default=False,
        action='store_const',
        const=True,
        help='Force update of domains, even if no new IP was encountered.')
    args = parser.parse_args()

    file_username, file_password = get_credentials()
    args.username = args.username or file_username
    args.password = args.password or file_password

    current_ip = whats_my_ip()

    if args.force_update is True or args.ip_address \
       or is_outdated(current_ip):
        args.ip_address = args.ip_address or current_ip
        set_last_ip(args.ip_address)
        update_domains(*args.domains, **vars(args))
    else:
        print('Everything looks fine')
