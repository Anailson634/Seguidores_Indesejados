# Script de Verificação de Seguidores

## Propósito
Este script permite verificar quem está seguindo você de volta no Instagram. Ele coleta suas listas de **seguidores** e **seguindo**, processa os dados e salva informações úteis sobre usuários que não te seguem de volta.

## Dependências
O script utiliza as seguintes bibliotecas Python:

1. [Selenium](https://pypi.org/project/selenium/) – para automatizar a navegação no Instagram  
2. `json` – para salvar e carregar os dados coletados  
3. `time` – para controlar delays e scrolls  

> Certifique-se de ter o Chrome e o Chromedriver compatíveis instalados.

## Como Usar
1. Abra o arquivo `Main.py`.  
2. Insira seu **usuário** e **senha** nos campos `nome` e `senha`.  
3. Execute o script.  
   - Durante a execução, sempre que aparecerem pop-ups de perfis, faça **scroll manual** até o final da lista.  
4. Após finalizar, abra `processa.py` e execute para processar os dados.  
5. Ao final, o arquivo `Exec.json` conterá informações úteis:  
   - Usuários que não te seguem de volta.  
   - Possibilidade de adicionar exceções para perfis.  

## Observações 
- Evite fechar o navegador manualmente durante a execução do script para não perder a sessão.  
- Para listas muito grandes de seguidores/seguindo, aguarde o scroll carregar todos os usuários antes de processar os dados.
