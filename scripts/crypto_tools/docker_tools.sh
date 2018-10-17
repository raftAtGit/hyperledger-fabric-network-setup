#!/bin/bash
# Created by Guillaume Leurquin, guillaume.leurquin@accenture.com

set -eu -o pipefail

if [ $# -ne 3 ];
then
  echo ""
  echo "Usage: "
  echo "  docker_tools ORG PEER MSPID"
  echo "  This script creates a docker file to be able to run a hyperledger"
  echo "  fabric tools CLI"
  echo ""
  exit 1
fi

ORG=$1
# CHANNEL=$2 # Not used currently
PEER=$2
MSPID=$3
FOLDER=$GEN_PATH/docker
mkdir -p "$FOLDER"
FILE="$FOLDER/tools.$ORG.yaml"

echo """
version: '2'

# This file has been auto-generated

services:
  tools.$ORG:
    image:        hyperledger/fabric-tools
    tty:          true
    stdin_open: true
    working_dir: /opt/gopath/src/github.com/hyperledger/fabric/peer
    container_name: tools.$ORG
    command: /bin/bash
    # logging:
    #     driver: \"json-file\"
    #     options:
    #         max-size: \"200k\"
    #         max-file: \"10\"
    environment:
      - CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=hyperledgerNet
      - GOPATH=/opt/gopath
      - CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock
      - CORE_LOGGING_LEVEL=DEBUG
      #- CORE_LOGGING_LEVEL=INFO
      - CORE_PEER_ID=cli
      - CORE_PEER_ADDRESS=$PEER.$ORG:7051
      - CORE_PEER_LOCALMSPID=$MSPID
      - CORE_PEER_TLS_ENABLED=true
      - CORE_PEER_TLS_CERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/$ORG/peers/$PEER.$ORG/tls/server.crt
      - CORE_PEER_TLS_KEY_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/$ORG/peers/$PEER.$ORG/tls/server.key
      - CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/$ORG/peers/$PEER.$ORG/tls/ca.crt
      - CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/$ORG/users/Admin@$ORG/msp
    volumes:
        - /var/run/:/host/var/run/
        - /vagrant/chaincode/:/opt/gopath/src/github.com/chaincode
        - /vagrant/crypto-config:/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/
        # - ./scripts:/opt/gopath/src/github.com/hyperledger/fabric/peer/scripts/
        - /vagrant/channel-artifacts:/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts

      # - /vagrant/channel/:/etc/hyperledger/configtx
      # - /vagrant/crypto-config/:/etc/hyperledger/crypto-config/
      # - /vagrant/shared/:/etc/hyperledger/
        - /vagrant/ssh/:/root/.ssh/

networks:
  default:
    external:
      name: hyperledgerNet

""" > $FILE
