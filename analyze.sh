#!/bin/bash

# Verifica se o PMD está instalado
if ! command -v pmd &> /dev/null; then
    echo "PMD não está instalado"
    exit 1
fi

# Verifica se recebeu os argumentos necessários
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <caminho-do-xml> <caminho-do-codigo>"
    exit 1
fi

XML_RULE="$1"
SOURCE_PATH="$2"

# Verifica se o arquivo XML existe
if [ ! -f "$XML_RULE" ]; then
    echo "Arquivo de regra XML não encontrado: $XML_RULE"
    exit 1
fi

# Verifica se o diretório do código fonte existe
if [ ! -d "$SOURCE_PATH" ]; then
    echo "Diretório do código fonte não encontrado: $SOURCE_PATH"
    exit 1
fi

# Executa o PMD
echo "Executando análise PMD..."
pmd \
    -R "$XML_RULE" \
    -d "$SOURCE_PATH" \
    -f sarif \
    -r output.sarif

# Verifica se a execução foi bem sucedida
if [ $? -eq 0 ]; then
    echo "Análise concluída com sucesso. Resultado salvo em output.sarif"
    exit 0
else
    echo "Erro durante a análise PMD"
    exit 1
fi