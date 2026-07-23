# Exemplos executáveis

Os três exemplos cobrem situações diferentes:

| Exemplo | Dados | Resultado |
|---|---|---|
| `demo_goes_true_color.py` | Descarrega automaticamente um conjunto GOES ABI oficial do Satpy | `output/demo_goes_true_color.png` |
| `demo_viirs_true_color.py` | Descarrega automaticamente uma passagem Suomi NPP com bandas I/M e geolocalização | `output/demo_viirs_true_color.png` |
| `render_satellite.py` | Usa os seus próprios ficheiros NOAA | PNG com o composite escolhido |

## Demo 1 — GOES True Color

```bash
python examples/demo_goes_true_color.py
```

O exemplo:

1. descarrega dados GOES-16 ABI de 14 de março de 2019;
2. abre os ficheiros com o leitor `abi_l1b`;
3. cria `true_color` ou `true_color_raw`, conforme a versão do Satpy;
4. reamostra os canais para uma grelha comum;
5. grava `output/demo_goes_true_color.png`.

Pode escolher outros diretórios:

```bash
python examples/demo_goes_true_color.py \
  --data-dir data/goes-cyclone \
  --output output/goes_cyclone.png
```

## Demo 2 — Suomi NPP VIIRS True Color

```bash
python examples/demo_viirs_true_color.py
```

O exemplo descarrega apenas uma granule e os canais necessários:

- `M03`, `M04`, `M05`: azul, verde e vermelho;
- `I01`, `I02`: detalhe de maior resolução para o ratio sharpening;
- geolocalização corrigida pelo terreno incluída pelo conjunto de demonstração.

Depois combina as bandas com o leitor `viirs_sdr`, reamostra as resoluções I/M e grava `output/demo_viirs_true_color.png`.

## Exemplo 3 — ficheiros descarregados pelo utilizador

### GOES True Color

No downloader, escolha os canais `C01`, `C02` e `C03` da mesma hora e domínio:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/OR_ABI-L1b-RadF-M6C0[123]*.nc" \
  --composite true_color \
  --domain full-disk \
  --output output/meu_goes_true_color.png
```

### GOES Day Land Cloud

Descarregue `C02`, `C03` e `C05`:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/OR_ABI-L1b-RadF-M6C0[235]*.nc" \
  --composite natural_color \
  --output output/goes_day_land_cloud.png
```

### GOES Nighttime Microphysics

Descarregue `C07`, `C13` e `C15`:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/*.nc" \
  --composite night_microphysics \
  --output output/goes_night_microphysics.png
```

### VIIRS True Color

Junte as bandas e a geolocalização da mesma passagem:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --composite true_color \
  --domain azores \
  --output output/meu_viirs_true_color.png
```

Também pode indicar limites próprios:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --composite true_color \
  --domain custom \
  --bbox -31 36 -24 40 \
  --output output/viirs_area_personalizada.png
```

Se o composite não aparecer:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --list-composites
```

Isto permite distinguir entre um nome de composite incorreto e a ausência de bandas ou geolocalização.
