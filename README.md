# PeladAPP

Aplicativo web para sortear e balancear times de pelada.

## O que o app faz

- Cadastro de jogadores (nome, nota 1-7, intensidade alta/baixa, mensalista).
- Selecao de jogadores e quantidade de times.
- Gera duas opcoes de times balanceados e um texto pronto para WhatsApp.
- Salva automaticamente os jogadores em arquivo JSON.

## Como funciona o balanceamento

- Distribui jogadores de alta intensidade entre os times.
- Ajusta a forca media para reduzir a diferenca entre os times.
- Tenta varias combinacoes e retorna duas opcoes diferentes.

## Rodar localmente

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Acesse `http://localhost:8080` no navegador.

## Dados

- Os jogadores ficam em `players.json`.
- Para trocar o arquivo, defina a variavel `PLAYERS_FILE`.
