#!/bin/bash
# Created by Guillaume Leurquin, guillaume.leurquin@accenture.com

set -eu -o pipefail

if [ $# -ne 5 ];
then
  echo ""
  echo "Usage: "
  echo "  docker_peer COMMON_NAME ORGANISATION MSPID PORTS COUCHDBPORT"
  echo "  PORTS are comma separated of the form HOSTPORT:CONTAINERPORT"
  echo "  This script creates a docker file to be able to run a hyperledger"
  echo "  fabric peer"
  echo ""
  exit 1
fi

CN=$1
ORG=$2
MSPID=$3
PORTS=$(echo $4 | tr "," " ") # comma separated peers
COUCHDBPORT=$5
declare -a PORTS="( $PORTS )"
FOLDER=$GEN_PATH/docker
mkdir -p "$FOLDER"
FILE="$FOLDER/$CN.$ORG.yaml"

echo """
version: '2'

# This file has been auto-generated

services:
  $CN.$ORG:
    image:        hyperledger/fabric-peer
    container_name: $CN.$ORG
    working_dir:  /opt/gopath/src/github.com/hyperledger/fabric/peer
    command:      peer node start
#    logging:
#        driver: \"json-file\"
#        options:
#            max-size: \"200k\"
#            max-file: \"10\"
    environment:
      - CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock
      # the following setting starts chaincode containers on the same
      # bridge network as the peers
      # https://docs.docker.com/compose/networking/
      - CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=hyperledgerNet
      - CORE_LOGGING_LEVEL=INFO
      #- CORE_LOGGING_LEVEL=DEBUG
      - CORE_PEER_TLS_ENABLED=true
      - CORE_PEER_GOSSIP_USELEADERELECTION=true
      - CORE_PEER_GOSSIP_ORGLEADER=false
      - CORE_PEER_PROFILE_ENABLED=true
      - CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt
      - CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key
      - CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt

      - CORE_PEER_ID=$CN.$ORG
      - CORE_PEER_ADDRESS=$CN.$ORG:7051
      - CORE_PEER_GOSSIP_EXTERNALENDPOINT=$CN.$ORG:7051 
      # TODO GOSSIP_BOOTSTRAP
      - CORE_PEER_GOSSIP_BOOTSTRAP=$CN.$ORG:7051
      - CORE_PEER_LOCALMSPID=$MSPID
    ports:""" > $FILE


for ((i=0;i<${#PORTS[@]};i+=1))
do
  echo "      - ${PORTS[$i]}" >> $FILE
done

echo """    volumes:
        - /var/run/:/host/var/run/
        - /vagrant/crypto-config/peerOrganizations/$ORG/peers/$CN.$ORG/msp:/etc/hyperledger/fabric/msp
        - /vagrant/crypto-config/peerOrganizations/$ORG/peers/$CN.$ORG/tls:/etc/hyperledger/fabric/tls
        - $CN.$ORG:/var/hyperledger/production

networks:
  default:
    external:
      name: hyperledgerNet

volumes:
  $CN.$ORG:
      
""" >> $FILE
