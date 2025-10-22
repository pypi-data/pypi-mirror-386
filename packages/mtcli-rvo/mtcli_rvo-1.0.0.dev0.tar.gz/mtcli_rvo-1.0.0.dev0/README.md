# mtcli-rvo
  
mtcli-rvo é um plugin para o ecossistema MTCLI, desenvolvido para calcular e exibir o Indicador de Volume Relativo (RVO – Relative Volume Oscillator) diretamente no terminal, com suporte a exportação de dados e integração nativa ao MetaTrader 5.
     --
     
Instalação
----------
  
Clone ou copie o repositório do plugin e, dentro da pasta principal, execute:
  
```bash
pip install -e .
```
  
--
    
Dependências principais:
  - MetaTrader5
- click
- pandas
- mtcli
  
  --
    
Uso via terminal
----------------
  
Comando principal:

bash```
mt rvo [OPTIONS]
```
  
Parâmetros principais:
- --volume / -v: tipo de volume (tick ou real)
- --period / -p: timeframe (ex: M5, M15)
- --bars / -b: número de barras para média de volume
- --historico / -h: número de candles no histórico
- --export / -e: exporta CSV
- --json / -j: exporta JSON
  
  
