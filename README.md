# rulebridge

1. **Entrada do Usuário** (`entryPoint.yaml`)
   - Usuário descreve a regra em linguagem natural
   - Fornece exemplos de código bom e ruim
   - Define severidade e linguagem alvo

2. **Geração da Regra PMD**
   - Stackspot AI converte a descrição em expressão XPath
   - Gera arquivo `rule.xml` válido para o PMD

3. **Execução do PMD**
   - PMD executa a regra no código fonte
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
   python main.py
   ```

## Requisitos

```
requests>=2.26.0
pyyaml>=5.4.1
```

## Estrutura do Projeto

```
.
├── config.py           # Configurações e credenciais
├── entryPoint.yaml    # Entrada do usuário
├── main.py            # Código principal
├── requirements.txt   # Dependências
└── README.md          # Documentação
```

## Arquivos Gerados

- `rule.xml`: Regra no formato PMD
- `output.serif`: Resultado da análise do PMD
- `rules.json`: Regras no formato Sonarqube

## Exemplo de Uso

1. **Defina uma Regra**
   ```yaml
   rule:
     name: "Detectar Strings Literais Duplicadas"
     description: "Encontrar strings literais que são repetidas no código"
     language: "java"
     severity: 3
     what_to_find: "Procure por strings literais que aparecem mais de uma vez no código"
     examples:
       good: |
         public class BomExemplo {
             private static final String MENSAGEM = "Olá Mundo";
             void metodo() {
                 System.out.println(MENSAGEM);
             }
         }
       bad: |
         public class ExemploRuim {
             void metodo() {
                 System.out.println("Olá Mundo");
                 System.out.println("Olá Mundo");  // Duplicado
             }
         }
   ```

2. **Execute e Obtenha os Resultados**
   - O sistema gerará a regra PMD correspondente
   - Executará a análise
   - Converterá para o formato Sonarqube

## Notas

- A ferramenta requer acesso à API do Stackspot
- PMD deve estar instalado no sistema
- As regras geradas são compatíveis com Sonarqube 9.9 LTS

## Limitações

- Atualmente suporta apenas regras baseadas em XPath
- Requer exemplos claros de código bom e ruim
- Depende da qualidade da resposta do Stackspot
