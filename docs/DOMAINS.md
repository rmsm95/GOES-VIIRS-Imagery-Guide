# Selecionar o domínio ou área

Há duas decisões diferentes:

1. escolher a cobertura do ficheiro original;
2. recortar a imagem final para uma região geográfica.

O recorte não cria dados que não existam no ficheiro de origem.

## GOES: cobertura do produto

No downloader, os produtos ABI terminam normalmente em:

| Sufixo | Cobertura | Exemplo |
|---|---|---|
| `F` | Full Disk | `ABI-L1b-RadF` |
| `C` | CONUS | `ABI-L1b-RadC` |
| `M` | Mesoscale | `ABI-L1b-RadM` |

Para obter Full Disk, descarregue um produto `F`. Um ficheiro CONUS ou Mesoscale não pode ser transformado em Full Disk.

Para manter toda a cobertura do ficheiro Full Disk:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/full-disk/*.nc" \
  --composite true_color \
  --domain full-disk \
  --output output/goes_full_disk.png
```

Para manter todo o domínio móvel de um produto Mesoscale:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/mesoscale/*.nc" \
  --composite true_color \
  --domain mesoscale \
  --output output/goes_mesoscale.png
```

## Presets geográficos

O parâmetro `--domain` também pode recortar GOES ou VIIRS:

| Domínio | Limites aproximados `(oeste, sul, este, norte)` |
|---|---|
| `conus` | `(-125, 24, -66, 50)` |
| `azores` | `(-33.5, 34, -21, 42.5)` |
| `iberia` | `(-11, 35, 5, 45)` |
| `north-atlantic` | `(-70, 10, 20, 70)` |

Exemplo GOES Full Disk recortado para os Açores:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/full-disk/*.nc" \
  --composite true_color \
  --domain azores \
  --output output/goes_acores.png
```

## Área personalizada

Use `--bbox OESTE SUL ESTE NORTE` em graus:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "dados/goes/full-disk/*.nc" \
  --composite true_color \
  --domain custom \
  --bbox -35 32 -18 45 \
  --output output/goes_area_personalizada.png
```

`--bbox` tem prioridade sobre qualquer preset indicado em `--domain`.

## VIIRS

VIIRS observa faixas orbitais. A área selecionada tem de intersectar a passagem descarregada e os ficheiros de geolocalização devem estar presentes.

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --composite true_color \
  --domain azores \
  --output output/viirs_acores.png
```

Ou com limites próprios:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --composite true_color \
  --domain custom \
  --bbox -31 36 -24 40 \
  --output output/viirs_area_personalizada.png
```

O recorte reduz o processamento e o tamanho da imagem resultante, mas não reduz os bytes já descarregados. Para evitar passagens VIIRS que não cobrem a região, é necessário consultar previamente a órbita ou a geolocalização de cada granule.
