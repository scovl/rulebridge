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
   - Gera relatório no formato serif

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
   # Primeiro, gere a regra XML
   python main.py
   
   # Depois, execute a análise PMD
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
- `output.serif`: Resultado da análise do PMD
- `rules.json`: Regras no formato Sonarqube

## Importando no Sonarqube

O Sonar Scanner aceita relatórios de análise externa através dos parâmetros `sonar.externalIssuesReportPaths` 
ou `sonar.sarifReportPaths`. Para usar o relatório gerado:

```bash
sonar-scanner \
  -Dsonar.projectKey=meu-projeto \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=seu-token \
  -Dsonar.externalIssuesReportPaths=./rules.json
```

Ou, se preferir usar o formato SARIF:

```bash
sonar-scanner \
  -Dsonar.projectKey=meu-projeto \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=seu-token \
  -Dsonar.sarifReportPaths=./rules.json
```

Certifique-se de que:
- O arquivo rules.json está no formato correto de relatório externo
- O Sonarqube está configurado para aceitar relatórios externos
- As issues reportadas serão exibidas como issues externas no Sonarqube

## Limitações

- Atualmente suporta apenas regras baseadas em XPath
- Requer exemplos claros de código bom e ruim
- Depende da qualidade da resposta do Stackspot