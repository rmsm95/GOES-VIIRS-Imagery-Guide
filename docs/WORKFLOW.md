# Fluxo recomendado

## 1. Visualizar primeiro

Use o [visualizador GOES no Google Earth Engine](https://ruimota16.users.earthengine.app/view/testapp) para escolher:

- GOES-18 ou GOES-19;
- Full Disk ou Mesoscale;
- data e hora UTC;
- visualização ou produto.

O objetivo é confirmar a área, hora e fenómeno antes de descarregar ficheiros grandes.

## 2. Descarregar apenas o necessário

Abra o [GOES & JPSS Data Downloader](https://rmsm95.github.io/GOES-NESDIS_downlaoder/).

Para GOES:

- selecione o mesmo satélite, domínio, data e hora;
- descarregue todos os canais exigidos pelo RGB;
- confirme que os nomes têm o mesmo instante de início (`_s...`).

Para VIIRS:

- escolha Suomi NPP, NOAA-20 ou NOAA-21;
- descarregue as bandas espectrais necessárias;
- acrescente a geolocalização correspondente.

## 3. Geolocalização VIIRS

Os dados VIIRS SDR são swaths: as coordenadas não estão necessariamente dentro do mesmo ficheiro da banda.

Para dados recentes, use preferencialmente:

- `GITCO`: geolocalização corrigida pelo terreno para bandas I;
- `GMTCO`: geolocalização corrigida pelo terreno para bandas M;
- `GDNBO`: geolocalização da Day/Night Band.

Desde 24 de fevereiro de 2025, a NOAA direciona os utilizadores para geolocalização corrigida pelo terreno (`GITCO`/`GMTCO`) na distribuição operacional. Consulte o [aviso NOAA CLASS](https://www.class.noaa.gov/search/VIIRS_SDR).

Mantenha os ficheiros da banda e da geolocalização da mesma passagem no mesmo diretório. O leitor `viirs_sdr` do Satpy associa-os através dos metadados.

## 4. Confirmar composites disponíveis

Antes de renderizar:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --list-composites
```

Se um RGB não aparecer, falta pelo menos uma banda, geolocalização ou ficheiro auxiliar.

## 5. Renderizar e validar

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "dados/viirs/*.h5" \
  --composite true_color \
  --output output/viirs_true_color.png
```

Valide:

- data e hora UTC;
- satélite e sensor;
- extensão geográfica;
- presença de linhas, deslocamentos ou áreas sem dados;
- significado físico das cores;
- unidades e realces utilizados.
