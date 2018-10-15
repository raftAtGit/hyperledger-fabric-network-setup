#!/usr/bin/env python2

"""
    hyperledgerNetworkTool -h

    Main tool for creation of hyperledger network artifacts,
    and for the creating of the network on AWS
"""

import os
import sys
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from argparse import Namespace
from argparse import Action

install_script = "https://raw.githubusercontent.com/Kunstmaan/hyperledger-fabric-network-setup/master/scripts/install.sh?token=AG6ftlJwD7jEr7kZph_QEsqncTTeroBFks5aZc1pwA%3D%3D"
DEBUG = True
PWD = os.path.dirname(os.path.realpath(__file__))

def to_pwd(script):
    """Converts the script path to the correct path"""
    return PWD + "/" + script

def fail(msg):
    """Prints the error message and exits"""
    sys.stderr.write('\033[91m' + msg + '\033[0m\n')
    exit(1)

def call(script, *args):
    """Calls the given script using the args"""

    cmd = "/bin/bash -c \"" + (script + " " + " ".join(args)) + "\""
    if DEBUG:
        print cmd
    if os.system(cmd) != 0:
        fail("ERROR: An error occured while executing " + cmd + ". See above for details.")

def install_fabric_tools():
    print "Installing fabric tools..."
    call(to_pwd('provisioning/install_fabric_tools.sh'))
    print "Done"

def gen_cryptographic_material(parsed_args):
    if parsed_args.onlyChannelArtifacts:
        gen_channel_artifacts(parsed_args)
        exit(0)
    crypto_config = parsed_args.crypto_config
    gen_path = os.path.abspath(parsed_args.genPath)
    install_fabric_tools()

    configtxbase = parsed_args.configtxBase
    no_override = parsed_args.noOverride
    if configtxbase:
        configtxbase = '--configtxBase {0}'.format(configtxbase)
    else:
        configtxbase = ''

    if not no_override:
        print "Cleaning pre-existing generated files..."
        call('rm -rfd {0}'.format(gen_path))
        call('mkdir -p {0}'.format(gen_path))
        no_override = ''
    else:
        no_override = '--noOverride'

    user = ''
    name = ''
    org = ''
    attributes = ''
    if parsed_args.user:
        print "Creating a user certificate"
        user = '--user'
        name = '--name {0}'.format(parsed_args.name)
        org = '--org {0}'.format(parsed_args.org)
        if parsed_args.user_attrs:
            attr_values = [k+"="+str(v) for k, v in parsed_args.user_attrs.items()]
            attributes = '--attributes  {0}'.format(",".join(attr_values))

    print "Generating cryptographic material..."
    call('export GEN_PATH={0} &&'.format(gen_path), to_pwd('crypto_tools/cryptogen.py'), crypto_config, no_override, configtxbase, user, name, org, attributes)
    # This also generates the channel artifacts, if changes were made.
    print "Done"

def gen_channel_artifacts(parsed_args):
    """Forces generation of channel artifacts"""
    crypto_config = parsed_args.crypto_config
    gen_path = os.path.abspath(parsed_args.genPath)
    configtxbase = parsed_args.configtxBase
    if configtxbase:
        configtxbase = '--configtxBase {0}'.format(configtxbase)
    else:
        configtxbase = ''

    print 'USING configtx: '+configtxbase

    install_fabric_tools()
    print "Generating channel artifacts..."
    call('export GEN_PATH={0} &&'.format(gen_path), to_pwd('fabric_artifacts/gen_configtx.py'), crypto_config, configtxbase)
    print "Done"


def network_down(parsed_args):
    aws_config = os.path.abspath(parsed_args.aws_config)
    gen_path = os.path.abspath(parsed_args.genPath)
    print 'May ask sudo password at this point to clean /etc/hosts file of previously created entries. If you never brought the network up, this won\'t make any changes'
    clean_hosts = gen_path + '/scripts/clean_hosts.sh'
    if os.path.isfile(clean_hosts):
        call(clean_hosts)
    call('export AWS_CONFIG={0} && export GEN_PATH={1} && pushd {2} && vagrant destroy -f && popd'.format(aws_config, gen_path, PWD))

def network_up(parsed_args):
    crypto_config = os.path.abspath(parsed_args.crypto_config)
    aws_config = os.path.abspath(parsed_args.aws_config)
    gen_path = os.path.abspath(parsed_args.genPath)
    print 'May ask sudo password at this point to edit /etc/hosts file with the names of the nodes, to be able to resolve them to public ips.'
    call('export GEN_PATH={0} &&'.format(gen_path), to_pwd('get_hosts_scripts.py'), aws_config, 'False') # To get the private ips
    call('export AWS_CONFIG={0} && export GEN_PATH={1} && pushd {2} && vagrant up && popd'.format(aws_config, gen_path, PWD))
    call('export GEN_PATH={0} &&'.format(gen_path), to_pwd('get_hosts_scripts.py'), aws_config, 'True') # To get the public ips
    call('export GEN_PATH={0} &&'.format(gen_path), to_pwd('create_remote_scripts.py'), crypto_config, aws_config)
    call(gen_path + '/scripts/set_hosts_public.sh')
    call(gen_path + '/scripts/create_and_join_channels_remote.sh')
    call(gen_path + '/scripts/update_remote_chaincodes.sh')


def update_chaincodes(parsed_args):
    gen_path = os.path.abspath(parsed_args.genPath)

    call(gen_path + '/scripts/update_remote_chaincodes.sh')

def bootstrap(parsed_args):
    base_path = os.path.normpath(os.path.join('.', parsed_args.path))
    conf_path = os.path.join(base_path, 'configuration')
    gen_path = os.path.join(base_path, 'generated')
    call('rm -rfd', conf_path)
    call('cp -r', to_pwd('../configuration'), conf_path)
    print 'You can start modifying the files inside {0} and then generate all the artifacts using "kuma-hf-network generate {1} --genPath {2}"'.format(conf_path, os.path.join(conf_path, 'crypto_config.yaml'), gen_path)

def update_tool(parsed_args):
    call("curl -fsSL", install_script, " | bash")

PARSER = ArgumentParser(description="""This tool allows you to create a certificate structure for hyperledger fabric,
and then to use that structure to boot a multinode network on Amazon Web Services.
Once the network is running, this tool also allows you to remotely upgrade
chaincode running on the network.
""", formatter_class=RawTextHelpFormatter)
SUBPARSERS = PARSER.add_subparsers()

#######################################
#           BOOTSTRAP
#######################################
PARSER_BOOTSTRAP = SUBPARSERS.add_parser('bootstrap', help="""generate example configuration.""")
PARSER_BOOTSTRAP.add_argument('path', type=str, help='the path where the example configuration should be bootstrapped.', default='.')

PARSER_BOOTSTRAP.set_defaults(func=bootstrap)

#######################################
#           GENERATE
#######################################
PARSER_GEN = SUBPARSERS.add_parser('generate', help="""generate certificate structure, initial channel blocks,
hyperledger fabric artifacts and docker configurations.""")
PARSER_GEN.add_argument('crypto_config', type=str, help='cryptographic configuration of the network, as YAML file. See the provided example for details.')

PARSER_GEN.add_argument('--genPath', '-g', type=str, help='Where the generated files should be saved (default: ./generated)', default='./generated')
PARSER_GEN.add_argument('--noOverride', help='Do not override existing files (default: override files). Useful if you want to add more users. If this is not set, will delete the generated folder and generate everything from scratch', action='store_true')
PARSER_GEN.add_argument('--onlyChannelArtifacts', help='Only generate hyperledger fabric channel artifacts. Will not generate the certificate structure, assumes this exists already.  Only use this if you made manual changes to the generated folder, which requires new channel artifacts to be generated.', action='store_true')
PARSER_GEN.add_argument('--configtxBase', '-c', help='path to configtx hyperledger fabric config file, without the organisations and profiles (they will be generated). Defaults to a simple orderer configuration.', action='store')
PARSER_GEN.set_defaults(user=False)
PARSER_GEN.set_defaults(func=gen_cryptographic_material)

#######################################
#           GENERATE USER
#######################################
user_attrs = {}
class StoreDictKeyPair(Action):
     def __call__(self, parser, namespace, values, option_string=None):
         for kv in values.split(","):
             k,v = kv.split("=")
             user_attrs[k] = v
         setattr(namespace, self.dest, user_attrs)

PARSER_GEN = SUBPARSERS.add_parser('generate-user', help='generate certificate structure for a new user')
PARSER_GEN.add_argument('name', type=str, help='the name of the user')
PARSER_GEN.add_argument('org', type=str, help='the organisation of the user')
PARSER_GEN.add_argument('crypto_config', type=str, help='cryptographic configuration of the network, as YAML file. See the provided example for details.')

PARSER_GEN.add_argument('--genPath', '-g', type=str, help='Where the generated files should be saved (default: ./generated)', default='./generated')
PARSER_GEN.add_argument('--attributes', help='the attributes for the user certificate', dest="user_attrs", action=StoreDictKeyPair, metavar="KEY1=VAL1,KEY2=VAL2...", default={})
PARSER_GEN.set_defaults(user=True)
PARSER_GEN.set_defaults(onlyChannelArtifacts=False)
PARSER_GEN.set_defaults(configtxBase=None)
PARSER_GEN.set_defaults(noOverride=True)
PARSER_GEN.set_defaults(func=gen_cryptographic_material)

#######################################
#           NETWORK-UP
#######################################
PARSER_UP = SUBPARSERS.add_parser('network-up', help="""Bring the network up. Requires the artifacts to be generated
     does:
         * vagrant up
         * modifies /etc/hosts to resolve hostnames
         * installs hyperledger fabric channels
         * installs first version of chaincode""")
PARSER_UP.add_argument('crypto_config', type=str, help='cryptographic configuration of the network, as YAML file.')
PARSER_UP.add_argument('aws_config', type=str, help='AWS network configuration, as JSON file.')
PARSER_UP.add_argument('--genPath', '-g', type=str, help='Where the generated files are (default: ./generated)', default='./generated')
PARSER_UP.set_defaults(func=network_up)

#######################################
#           NETWORK-DOWN
#######################################
PARSER_DOWN = SUBPARSERS.add_parser('network-down', help="""Bring the network down.
     does:
         * vagrant destroy -f
         * cleans /etc/hosts""")
PARSER_DOWN.add_argument('aws_config', type=str, help='AWS network configuration, as JSON file.')
PARSER_DOWN.add_argument('--genPath', '-g', type=str, help='Where the generated files are (default: ./generated)', default='./generated')
PARSER_DOWN.set_defaults(func=network_down)

#######################################
#          UPDATE-CHAINCODES
#######################################
PARSER_UPDATE_CHAINCODES = SUBPARSERS.add_parser('update-chaincodes', help='Updates chaincodes on the network. Only run this if the network is up')
PARSER_UPDATE_CHAINCODES.add_argument('--genPath', '-g', type=str, help='Where the generated files are (default: ./generated)', default='./generated')
PARSER_UPDATE_CHAINCODES.set_defaults(func=update_chaincodes)

#######################################
#          UPDATE-CHAINCODES
#######################################
PARSER_UPDATE = SUBPARSERS.add_parser('update', help='Update the tool')
PARSER_UPDATE.set_defaults(func=update_tool)


ARGS = PARSER.parse_args()
ARGS.func(ARGS)
