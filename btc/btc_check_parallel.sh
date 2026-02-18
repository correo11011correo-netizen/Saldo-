#!/bin/bash

INPUT_FILE="$1"

if [ -z "$INPUT_FILE" ]; then
    echo "Uso: $0 btc_keys_50.txt"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: archivo no encontrado."
    exit 1
fi

WITH_FUNDS="with_funds.txt"
NO_FUNDS="no_funds.txt"

> "$WITH_FUNDS"
> "$NO_FUNDS"

echo "========================================"
echo "   ANALIZANDO DIRECCIONES BTC (50 HILOS)"
echo "========================================"

# Extraer direcciones (último campo de cada línea Address)
ADDRESSES=($(grep "^Address" "$INPUT_FILE" | awk '{print $NF}'))

check_balance() {
    ADDRESS="$1"

    JSON=$(curl -s "https://mempool.space/api/address/$ADDRESS/utxo")

    BALANCE=$(echo "$JSON" \
        | grep -o '"value":[0-9]*' \
        | sed 's/[^0-9]//g' \
        | awk '{s+=$1} END {if (s=="") s=0; print s}')

    if [ "$BALANCE" -gt 0 ]; then
        echo "$ADDRESS | Balance: $BALANCE sats" >> "$WITH_FUNDS"
    else
        echo "$ADDRESS | Balance: 0" >> "$NO_FUNDS"
    fi
}

export -f check_balance
export WITH_FUNDS
export NO_FUNDS

# Ejecutar 50 hilos en paralelo
printf "%s\n" "${ADDRESSES[@]}" | xargs -n1 -P50 -I{} bash -c 'check_balance "$@"' _ {}

echo ""
echo "========================================"
echo " DIRECCIONES CON FONDOS:"
echo "========================================"
cat "$WITH_FUNDS"

echo ""
echo "========================================"
echo " DIRECCIONES SIN FONDOS:"
echo "========================================"
cat "$NO_FUNDS"
