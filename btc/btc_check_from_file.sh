#!/bin/bash

# Lee un archivo con líneas tipo:
# Address (BTC P2PKH): 1xxxx...
# Consulta UTXOs reales vía mempool.space y separa con/sin fondos

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
echo "   ANALIZANDO DIRECCIONES BTC (UTXO)"
echo "========================================"

while IFS= read -r line; do
    if [[ "$line" == Address* ]]; then
        # Último campo = dirección
        ADDRESS=$(echo "$line" | awk '{print $NF}')
        echo "Consultando: $ADDRESS"

        # UTXOs en mempool.space (BTC mainnet)
        UTXO_JSON=$(curl -s "https://mempool.space/api/address/$ADDRESS/utxo")

        # Si no hay respuesta, marcar como error/sin datos
        if [ -z "$UTXO_JSON" ]; then
            echo "$ADDRESS | Error al consultar" >> "$NO_FUNDS"
            echo "Error al consultar $ADDRESS"
            echo "----------------------------------------"
            continue
        fi

        # Sumar todos los 'value' de los UTXOs
        BALANCE=$(echo "$UTXO_JSON" \
            | grep -o '"value":[0-9]*' \
            | sed 's/[^0-9]//g' \
            | awk '{s+=$1} END {if (s=="") s=0; print s}')

        if [ "$BALANCE" -gt 0 ]; then
            echo "$ADDRESS | Balance: $BALANCE sats" | tee -a "$WITH_FUNDS"
        else
            echo "$ADDRESS | Balance: 0" >> "$NO_FUNDS"
        fi

        echo "----------------------------------------"
    fi
done < "$INPUT_FILE"

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
