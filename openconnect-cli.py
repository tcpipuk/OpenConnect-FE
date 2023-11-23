#!/usr/bin/env python3

import argparse
from getpass import getpass
from time import sleep
import pexpect

# Set up argument parser
parser = argparse.ArgumentParser(prog='openconnect-cli', description='Automate logins to the OpenConnect SSL VPN client')

# Type of VPN to initiate
parser_type = parser.add_mutually_exclusive_group(required=False)
parser_type.add_argument('--anyconnect', action='store_true', default=False, help='Cisco AnyConnect SSL VPN')
parser_type.add_argument('--fortinet', action='store_true', default=False, help='Fortinet FortiClient SSL VPN')
parser_type.add_argument('--pulsesecure', action='store_true', default=False, help='Juniper Network Connect / Pulse Secure SSL VPN')
parser_type.add_argument('--paloalto', action='store_true', default=False, help='Palo Alto Networks (PAN) GlobalProtect SSL VPN')

# VPN server details
parser_dst = parser.add_argument_group('VPN Server Details', 'Any missing fields will be prompted on launch')
parser_dst.add_argument('--host', type=str, default=False, help='DNS hostname of SSL VPN server')
parser_dst.add_argument('--user', type=str, default=False, help='Username for SSL VPN account')
parser_dst.add_argument('--pw', type=str, default=False, help='Password for SSL VPN account')

# Import options, output help if none provided
args = vars(parser.parse_args())

def vpnTypePrompt():
    try:
        print('Please enter one of the following and press enter:')
        print('1 for Cisco AnyConnect')
        print('2 for Fortinet FortiClient')
        print('3 for Pulse Secure or Juniper Network Connect')
        print('4 for Palo Alto Networks GlobalProtect')
        protocol = int(input('SSL VPN Type: '))
        return {1: 'anyconnect', 2: 'fortinet', 3: 'nc', 4: 'gp'}.get(protocol)
    except:
        return False

# Determine VPN protocol
args['protocol'] = next((protocol for protocol, selected in args.items() if selected and protocol in ['anyconnect', 'fortinet', 'pulsesecure', 'paloalto']), False)
while not args['protocol']:
    args['protocol'] = vpnTypePrompt()

# Fields to prompt for when False
prompt_for = {
    'host': 'DNS hostname of SSL VPN server: ',
    'user': 'Username for SSL VPN account: ',
    'pw': 'Password for SSL VPN account: ' if args['protocol'] == 'gp' else None
}

# Iterate through fields and prompt for missing ones
for field, prompt in prompt_for.items():
    if prompt and (field not in args or not args[field]):
        args[field] = getpass(prompt) if field == 'pw' else input(prompt)

# Store the host in a separate variable
vpn_host = args.pop('host')

# Build OpenConnect command
openconnect_args = {
    'interface': 'vpn0',
    'script': '/usr/share/vpnc-scripts/vpnc-script',
    'protocol': args['protocol'],
    'user': args['user']
}

# Specific argument for Cisco AnyConnect
if args['protocol'] == 'anyconnect':
    openconnect_args['useragent'] = 'AnyConnect Windows 4.10.07061'

command_parts = ['sudo openconnect']
command_parts += [f'--{key}="{value}"' for key, value in openconnect_args.items() if value]
command_parts.append(vpn_host)  # Append the VPN host at the end
command = ' '.join(command_parts)

# Start process
process = pexpect.spawnu('/bin/bash', ['-c', command])

# Handle Palo Alto login
if args['protocol'] == 'gp':
    process.expect('Password: ')
    process.sendline(args['pw'])
    process.expect('GATEWAY: ')
    process.sendline('Primary GP')
    process.expect('anything else to view:')
    process.sendline('yes')
    process.expect('Password: ')
    process.sendline(args['pw'])

# Clear sensitive data
for field in ['pw', 'user']:
    args[field] = None
openconnect_args = None
command = None
vpn_host = None

# Hand over input to user and wait for process to end
process.interact()
while process.isalive():
    sleep(5)
