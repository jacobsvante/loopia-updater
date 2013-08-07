# Loopia IP Updater: Another dynamic DNS service

When you don't have a static IP from your ISP but need to make sure that your Loopia domain names always point to the current external IP.
Put in your server crontab and run as often as you see fit.

API username and password ([which you need to create here](https://customerzone.loopia.se/settings/loopia-api/)) can either be specified as arguments, or in ~/.loopiaapi.ini, in standard INI-format:

    [credentials]
    username = USERNAME
    password = PASSWORD

Don't forget to add @loopiaapi to the end of your username.

## Requirements

Python 2.7+ or Python 3.3+ (No support for older versions right now, mostly because I'm lazy. I'm of course open to pull requests.)

## Example usage

### Crontab entry

Check for IP changes every 5 minutes, update zone-records `@`, `*` for `jacobian.se`. Write any errors that occur to `~/loopia_updater.log`

    */5 * * * * python /path/to/loopia_updater.py jacobian.se *.jacobian.se 2>> ~/loopia_updater.log

### Force update

Force update of IP, might be useful on the first run as Loopia's API is never hit unless the IP is changed from the last check (last external IP is stored in `~/.loopiaapi-externalip`.)

   python /path/to/loopia_updater.py jacobian.se -u USERNAME -p PASSWORD -f
