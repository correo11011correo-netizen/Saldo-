#!/bin/bash

# Script para consultar balance BTC real usando Blockstream API
# Uso: ./btc_balance_check.sh DIRECCION_BTC

ADDRESS="$1"

if [ -z "$ADDRESS" ]; then
    echo "Uso: $0 DIRECCION_BTC"
    exit 1
fi

URL="https://blockstream.info/api/address/$ADDRESS"

# Obtener datos JSON
DATA=$(curl -s "$URL")

if [ -z "$DATA" ]; then
    echo "Error: no se pudo obtener información."
    exit 1
fi

# Extraer valores usando grep + sed (sin jq)
CONFIRMED=$(echo "$DATA" | grep -o '"funded_txo_sum":[0-9]*' | head -1 | sed 's/[^0-9]//g')
SPENT=$(echo "$DATA" | grep -o '"spent_txo_sum":[0-9]*' | head -1 | sed 's/[^0-9]//g')

CONFIRMED_BALANCE=$((CONFIRMED - SPENT))

echo "========================================"
echo " Dirección BTC: $ADDRESS"
echo "========================================"
echo " Balance confirmado (satoshis): $CONFIRMED_BALANCE"
echo " Balance confirmado (BTC): $(echo "scale=8; $CONFIRMED_BALANCE/100000000" | bc)"
echo "========================================"
