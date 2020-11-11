#!/usr/bin/env python3

import argparse, pexpect
from getpass import getpass
from time import sleep

# Set up argument parser
parser = argparse.ArgumentParser(prog='openconnect-cli', description='Automate logins to the OpenConnect SSL VPN client')

# Type of VPN to initiate
parser_type = parser.add_mutually_exclusive_group(required=False)
parser_type.add_argument('--anyconnect', action='store_true', default=False, help='Cisco AnyConnect SSL VPN')
parser_type.add_argument('--pulsesecure', action='store_true', default=False, help='Juniper Network Connect / Pulse Secure SSL VPN')
parser_type.add_argument('--paloalto', action='store_true', default=False, help='Palo Alto Networks (PAN) GlobalProtect SSL VPN')

# VPN server details
parser_dst = parser.add_argument_group('VPN Server Details', 'Any missing fields will be prompted on launch')
parser_dst.add_argument('--host', type=str, default=False, help='DNS hostname of SSL VPN server')
parser_dst.add_argument('--user', type=str, default=False, help='Username for SSL VPN account')
parser_dst.add_argument('--pw', type=str, default=False, help='Password for SSL VPN account')
parser_dst.add_argument('--group', type=str, default=False, help='User group for SSL VPN account (not always required)')

# Import options, output help if none provided
args = vars(parser.parse_args())
#args = vars(parser.parse_args(args=None if sys.argv[1:] else ['--help']))

def vpnTypePrompt():
  try:
    print('Please enter one of the following and press enter:')
    print('1 for Cisco AnyConnect')
    print('2 for Pulse Secure or Juniper Network Connect')
    print('3 for Palo Alto Networks GlobalProtect')
    protocol = int(input('SSL VPN Type: '))
    if protocol == 1:
      return 'anyconnect'
    elif protocol == 2:
      return 'nc'
    elif protocol == 3:
      return 'gp'
    else:
      return False
  except:
    return False

if 'anyconnect' in args and args['anyconnect']:
  args['protocol'] = 'anyconnect'
elif 'pulsesecure' in args and args['pulsesecure']:
  args['protocol'] = 'nc'
elif 'paloalto' in args and args['paloalto']:
  args['protocol'] = 'gp'
else:
  args['protocol'] = False
  while args['protocol'] == False:
    args['protocol'] = vpnTypePrompt()

# Fields to prompt for when False
prompt_for = {
  'host': 'DNS hostname of SSL VPN server: ',
  'user': 'Username for SSL VPN account: ',
  'pw': 'Password for SSL VPN account: '
}

if args['protocol'] == 'anyconnect':
  prompt_for['group'] = 'User group for SSL VPN account: '

# Interate through fields and prompt for missing ones
if 'help' not in args:
  for field,prompt in prompt_for.items():
    if str(field) not in args or not args[field]:
      while args[field] == False:
        try:
          if field == 'pw':
            args[field] = getpass(prompt)
          else:
            args[field] = input(prompt)
        except:
          pass

# Collate arguments for command
command = [
  'sudo openconnect',
    '--interface=vpn0',
    '--script=/usr/share/vpnc-scripts/vpnc-script',
    '--protocol="' + args['protocol'] + '"',
    '--user="' + args['user'] + '"'
]

# Add usergroup for Cisco AnyConnect VPN
if args['protocol'] == 'anyconnect':
  command.append('--usergroup="' + args['group'] + '"')

# Compile command
command = ' '.join(command + [ args['host'] ])

# Start process
process = pexpect.spawnu('/bin/bash', ['-c', command])

# Automate login process for Palo Alto GlobalProtect
if args['protocol'] == 'gp':
  process.expect('Password: ')
  process.sendline(args['pw'])
  process.expect('GATEWAY: ')
  process.sendline('Primary GP')
  process.expect('Password: ')
  process.sendline(args['pw'])

# Clear remaining private data
args = None
command = None

# Hand over input to user, wait for process to end if interactive mode ends
process.interact()
while process.isalive():
  sleep(5)