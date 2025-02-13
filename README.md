# rulebridge

1. **Entrada do Usuário** (`entryPoint.yaml`)
   - Usuário descreve a regra em linguagem natural
   - Fornece exemplos de código bom e ruim
   - Define severidade e linguagem alvo

2. **Geração da Regra PMD**
   - Stackspot AI converte a descrição em expressão XPath
   - Gera arquivo `rule.xml` válido para o PMD

3. **Execução do PMD**
   - PMD executa a regra no código fonte via script shell
   - Gera relatório no formato SARIF

4. **Conversão para Sonarqube**
   - RuleBridge converte o relatório serif para JSON
   - Gera arquivo no formato do Sonarqube 9.9 LTS

## Como Usar

1. **Configure as Credenciais**
   ```python
   # config.py
   CLIENT_ID = "seu_client_id"
   CLIENT_KEY = "sua_client_key"
   REALM = "seu_realm"
   PROXIES = {}  # se necessário
   ```

2. **Crie sua Regra**
   ```yaml
   # entryPoint.yaml
   rule:
     name: "Nome da Regra"
     description: "Descrição clara da regra"
     language: "java"
     severity: 3  # 1-blocker até 5-info
     what_to_find: "Descreva em linguagem natural o que procurar"
     examples:
       good: |
         // Código que segue a regra
       bad: |
         // Código que viola a regra
   ```

3. **Execute o RuleBridge**
   ```bash
   # Dê permissão de execução ao script
   chmod +x analyze.sh
   
   # Primeiro, gere a regra XML
   python main.py
   
   # Depois, execute a análise PMD com o código fonte alvo
   ./analyze.sh rule.xml /caminho/do/codigo/fonte
   ```

## Requisitos

```
requests>=2.26.0
pyyaml>=5.4.1
pmd>=6.55.0  # Instalado separadamente
```

## Estrutura do Projeto

```
.
├── config.py           # Configurações e credenciais
├── entryPoint.yaml    # Entrada do usuário
├── main.py            # Código principal
├── analyze.sh         # Script de execução do PMD
├── requirements.txt   # Dependências
└── README.md          # Documentação
```

## Arquivos Gerados

- `rule.xml`: Regra no formato PMD
- `output.sarif`: Resultado da análise do PMD em formato SARIF
- `rules.json`: Regras no formato Sonarqube

## Importando no Sonarqube

O Sonar Scanner aceita relatórios de análise externa através do parâmetro `sonar.sarifReportPaths`. Para usar o relatório gerado:

```bash
sonar-scanner \
  -Dsonar.projectKey=meu-projeto \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=seu-token \
  -Dsonar.sarifReportPaths=./output.sarif
```

- O arquivo output.sarif está no formato SARIF v2.1.0

## Limitações

- Atualmente suporta apenas regras baseadas em XPath
- Requer exemplos claros de código bom e ruim
- Depende da qualidade da resposta do Stackspot