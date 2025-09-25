# Inventário Rotativo – Painel de Contagem

Dashboard web para acompanhar o andamento das contagens de inventário rotativo, com backend em Flask para realizar cálculos de apoio e registrar os dados enviados pelo frontend.

## Recursos principais

- 11 cards com os indicadores principais da contagem, replicando o layout do painel de referência.
- Botão de configurações com modal para informar parâmetros de finalização e calcular automaticamente o total.
- Botão **Parâmetros dias** para consultar automaticamente os dias normais e úteis calculados a partir da previsão.
- Espaços reservados lado a lado para anexar gráficos ou imagens informativas.
- Integração com backend Flask que devolve a data de atualização e garante o cálculo do total configurado.
- Cálculo automático de dias úteis com base em feriados nacionais brasileiros (com possibilidade de incluir feriados extras).
- Cálculo automático de totais, metas e percentuais de avanço da contagem a partir das configurações.
- Upload rápido de imagens (PNG, JPG, SVG ou WEBP) nos placeholders de gráficos, com suporte a arrastar/soltar, clique direito + colar ou seleção manual.

## Pré-requisitos

- Python 3.9 ou superior
- Pip (geralmente já incluso na instalação do Python)

## Instalação

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execução do servidor

```powershell
python servidor.py
```

O aplicativo ficará disponível em `http://localhost:5000/`. O Flask atende o arquivo `componentes/index.html` e os demais assets diretamente.

## Fluxo de uso

1. Abra o navegador e acesse `http://localhost:5000/`.
2. Preencha os campos dos indicadores e, se necessário, registre parâmetros em **Configurações**.
3. Clique em **Salvar dashboard** para enviar os dados ao backend. Os valores enviados e a resposta do serviço aparecerão no console do navegador.
4. A data de atualização é calculada pelo servidor e preenchida automaticamente no card correspondente.

## Próximos passos sugeridos

- Persistir os dados em banco ou arquivo para histórico.
- Substituir os placeholders dos gráficos por componentes de visualização (por exemplo, Chart.js).
- Adicionar autenticação para controle de acesso aos dados.
