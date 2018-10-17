#!/bin/bash
# Created by Guillaume Leurquin, guillaume.leurquin@accenture.com

set -eu -o pipefail

if [ $# -ne 4 ];
then
  echo ""
  echo "Usage: "
  echo "  docker_orderer COMMON_NAME ORGANISATION MSPID PEERS ORGS PORT"
    echo "  PEERS and ORGS are comma separated"
  echo "  This script creates a docker file to be able to run a hyperledger"
  echo "  fabric orderer"
  echo ""
  exit 1
fi

CN=$1
ORG=$2
MSPID=$3
Port=$4
FOLDER=$GEN_PATH/docker
mkdir -p "$FOLDER"
FILE="$FOLDER/$CN.$ORG.yaml"

# echo "Peers=${Peers[@]}"
# echo "Orgs=${Orgs[@]}"

echo -n """
version: '2'

# This file has been auto-generated

services:
  $CN.$ORG:
    image:        hyperledger/fabric-orderer
    container_name: $CN.$ORG
    working_dir: /opt/gopath/src/github.com/hyperledger/fabric
    command: orderer
    ports:
      - $Port:7050
    logging:
#      driver: \"json-file\"
#      options:
#        max-size: \"200k\"
#        max-file: \"10\"
    environment:
      - ORDERER_GENERAL_LOGLEVEL=DEBUG
#      - ORDERER_GENERAL_LOGLEVEL=INFO
      - ORDERER_GENERAL_LISTENADDRESS=0.0.0.0
      - ORDERER_GENERAL_GENESISMETHOD=file
      - ORDERER_GENERAL_GENESISFILE=/var/hyperledger/orderer/orderer.genesis.block
      - ORDERER_GENERAL_LOCALMSPID=$MSPID
      - ORDERER_GENERAL_LOCALMSPDIR=/var/hyperledger/orderer/msp
      # enabled TLS
      - ORDERER_GENERAL_TLS_ENABLED=true
      - ORDERER_GENERAL_TLS_PRIVATEKEY=/var/hyperledger/orderer/tls/server.key
      - ORDERER_GENERAL_TLS_CERTIFICATE=/var/hyperledger/orderer/tls/server.crt
      - ORDERER_GENERAL_TLS_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt]
    volumes:
    - /vagrant/channel-artifacts/genesis.block:/var/hyperledger/orderer/orderer.genesis.block
    - /vagrant/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp:/var/hyperledger/orderer/msp
    - /vagrant/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/tls/:/var/hyperledger/orderer/tls
    - $CN.$ORG:/var/hyperledger/production/orderer

networks:
  default:
    external:
      name: hyperledgerNet

volumes:
  $CN.$ORG:
      
""" > $FILE
