# RELATORIO DE SINAL RX DE ONUS PELO ZABBIX

Script python para coletar valores dos itens de coleta no Zabbix e salvar o relatorio `.csv`.

___

Para o uso do script precisará das bibliotecas a baixo:
   - python-dotenv==1.0.0
   - pyzabbix==1.3.0
   - requests==2.31.0
   - tqdm==4.66.0

Instale as bibliotecas com o comando abaixo. 
```bash
python -m pip install -r requirements.txt
```
&nbsp;

O link e as credenciais do Zabbix deverão ser adiconadas no aquivo `.env`.
Crie o arquivo no mesmo diretorio onde o script está.  
```bash
touch .env
```
&nbsp;
Abra o arvivo `.env` com o editor de sua prefenecia e adicone as variaveis abaixo.

|                 |        |                                           |
| :-------------- | :----: | :---------------------------------------- |
| `URL`           | string | Obrigatorio                               |
| `ZBX_USERNAME`  | string | Não é necessairo caso ultilize TOKEN      |
| `ZBX_PASSWD`    | string | Não é necessairo caso ultilize TOKEN      |
| `ZBX_TOKEN_API` | string | Não é necessairo caso ultilize user/senha |

```bash
URL = 
ZBX_USERNAME = 
ZBX_PASSWD = 
ZBX_TOKEN_API =
```
&nbsp;
Os filtros são colocados no `get_items.py`. Altere de acordo com a configuração do seu Zabbix.
```python
search_host = {"name": "OLT"}

item_tags = [
    {"tag": "ONU", "value": "Sinal"}, 
    {"tag": "ONU", "value": "PON"}
    ]
```
&nbsp;
Execute o comando para rota o script e agurde. 
```bash
python get_items.py
```
Exemplo:
```bash
Connected to Zabbix API Version 6.0.19.
Collecting the hosts
Collecting item info from 428 hosts
100%|███████████████████████████████| 428/428 [37:41<00:00,  5.28s/it]
Organizing the collected information (406).
100%|███████████████████████████████| 406/406 [04:34<00:00,  1.48it/s]
Preparing the info for writing
100%|██████████████████████████████| 406/406 [00:01<00:00, 305.21it/s]
406
Saving the file onu_sinal_2023-08-16
100%|█████████████████████| 454110/454110 [00:02<00:00, 183184.24it/s]
```
