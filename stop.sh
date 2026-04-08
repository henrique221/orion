#!/usr/bin/env bash

if pkill -f "python main.py"; then
    echo "Orion encerrado."
else
    echo "Orion nao esta rodando."
fi
