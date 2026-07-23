# Visualizar GOES e VIIRS

Guia prático, em português, para transformar ficheiros NOAA em imagens e composições RGB.

Este repositório complementa o [GOES & JPSS Data Downloader](https://rmsm95.github.io/GOES-NESDIS_downlaoder/): primeiro pode visualizar GOES no Google Earth Engine, depois descarregar os ficheiros necessários e criar imagens localmente.

## Começar em 5 minutos

### 1. Visualizar GOES antes do download

Abra o [visualizador GOES no Google Earth Engine](https://ruimota16.users.earthengine.app/view/testapp). Permite escolher satélite, domínio, data/hora e produto antes de descarregar os dados.

### 2. Preparar o ambiente Python

Requer Python 3.11 ou mais recente.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Criar uma imagem GOES True Color

Descarregue os canais ABI `C01`, `C02` e `C03` da mesma observação. Depois execute:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/*.nc" \
  --composite true_color \
  --output output/goes_true_color.png
```

O GOES ABI não possui um canal verde puro. O verde é sintetizado a partir dos canais azul, vermelho e vegetação.

### 4. Criar uma imagem VIIRS True Color

Para VIIRS, guarde no mesmo diretório os canais necessários e os ficheiros de geolocalização correspondentes:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --composite true_color \
  --output output/viirs_true_color.png
```

Os produtos recentes usam preferencialmente geolocalização corrigida pelo terreno: `GITCO` para bandas I e `GMTCO` para bandas M.

## Descobrir os RGB disponíveis

Os RGB disponíveis dependem dos canais presentes nos ficheiros:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/*.nc" \
  --list-composites
```

Alguns exemplos comuns:

- `true_color`: aparência próxima da visão humana durante o dia;
- `natural_color`: realça vegetação, solo, neve e tipos de nuvem;
- `airmass`: ajuda a interpretar massas de ar e dinâmica de níveis altos;
- `night_microphysics`: separa nevoeiro, nuvens baixas e nuvens de gelo à noite.

Consulte [Como construir um RGB](docs/RGB.md) para compreender os canais, diferenças térmicas, normalização e gama.

## Exemplos completos

Não tem ficheiros preparados? Estes exemplos descarregam dados públicos de demonstração e criam a imagem:

- [GOES ABI True Color](examples/demo_goes_true_color.py) — descarrega o exemplo GOES oficial do Satpy e produz um PNG;
- [Suomi NPP VIIRS True Color](examples/demo_viirs_true_color.py) — descarrega uma passagem, bandas I/M e geolocalização;
- [Explicação passo a passo e comandos](examples/README.md) — mostra também como usar ficheiros descarregados neste site.

```bash
python examples/demo_goes_true_color.py
python examples/demo_viirs_true_color.py
```

Os downloads de demonstração podem ter centenas de megabytes. Os ficheiros ficam em `data/demo-*` e não são adicionados ao Git.

## Estrutura

```text
.
├── docs/
│   ├── RGB.md
│   └── WORKFLOW.md
├── examples/
│   ├── README.md
│   ├── demo_goes_true_color.py
│   ├── demo_viirs_true_color.py
│   └── render_satellite.py
├── tests/
│   └── test_render_satellite.py
└── requirements.txt
```

## Fontes técnicas

- [Satpy: leitura remota de GOES ABI](https://satpy.readthedocs.io/en/stable/remote_reading.html)
- [Satpy: leitor VIIRS SDR](https://satpy.readthedocs.io/en/stable/api/satpy.readers.viirs_sdr.html)
- [NOAA: guia CIMSS Natural True Color](https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_CIMSSRGB_v2.pdf)
- [NOAA: guia Day Land Cloud RGB](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_daylandcloudRGB_final.pdf)
- [NOAA CLASS: VIIRS SDR e geolocalização](https://www.class.noaa.gov/search/VIIRS_SDR)

Os dados continuam a pertencer aos respetivos produtores. Verifique sempre as condições e avisos operacionais das fontes NOAA.

## Licença

Código disponibilizado sob a [licença MIT](LICENSE). A licença não altera os termos dos dados, imagens ou documentação externos.
