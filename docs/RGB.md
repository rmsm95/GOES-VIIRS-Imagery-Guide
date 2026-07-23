# Como construir um RGB

Uma composição RGB coloca três matrizes normalizadas nos canais vermelho, verde e azul de uma imagem:

```text
imagem_rgb = stack(vermelho, verde, azul)
```

Cada entrada pode ser:

- a refletância de uma banda visível ou infravermelha próxima;
- a temperatura de brilho de uma banda térmica;
- a diferença entre duas temperaturas de brilho;
- uma combinação sintética de várias bandas.

## Passos fundamentais

1. Reunir ficheiros da mesma observação.
2. Ler os valores físicos e remover preenchimentos ou píxeis inválidos.
3. Reamostrar todos os canais para a mesma grelha.
4. Aplicar a receita: banda simples, combinação ou diferença.
5. Limitar cada componente ao intervalo físico escolhido.
6. Normalizar cada componente para `0–1`.
7. Inverter componentes quando a receita o exige.
8. Aplicar correção gama e combinar R, G e B.

Para um valor `x`, limites `mínimo` e `máximo`, a normalização básica é:

```python
normalizado = clip((x - mínimo) / (máximo - mínimo), 0, 1)
```

A correção gama é:

```python
corrigido = normalizado ** (1 / gama)
```

O Satpy já contém receitas, calibração, reamostragem e realces. Por isso, o exemplo deste repositório pede o nome do RGB em vez de repetir manualmente todas essas operações.

## GOES ABI: True Color com verde sintético

O ABI tem azul (`C01`, 0,47 µm), vermelho (`C02`, 0,64 µm) e vegetação (`C03`, 0,86 µm), mas não possui uma banda verde pura.

A receita CIMSS aproxima o verde assim:

```text
R = C02
G = 0,45 × C02 + 0,10 × C03 + 0,45 × C01
B = C01
```

É uma composição diurna: depende da luz solar. O processamento completo pode ainda corrigir dispersão de Rayleigh e aplicar realces.

Fonte: [NOAA/CIMSS Natural True Color Quick Guide](https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_CIMSSRGB_v2.pdf).

## GOES ABI: Day Land Cloud / Natural Color

Esta receita usa:

```text
R = C05 (1,6 µm)
G = C03 (0,86 µm)
B = C02 (0,64 µm)
```

Interpretação típica:

- vegetação: verde;
- solo seco ou vegetação inativa: castanho;
- nuvens de água: cinzento ou branco;
- gelo, neve e nuvens altas: ciano.

Também é uma composição diurna. A banda de 1,6 µm absorve fortemente em gelo, criando separação entre nuvens de água e gelo.

Fonte: [NOAA Day Land Cloud RGB Quick Guide](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_daylandcloudRGB_final.pdf).

## GOES ABI: Nighttime Microphysics

Esta composição usa diferenças de temperatura de brilho:

```text
R = C15 (12,4 µm) − C13 (10,3 µm)
G = C13 (10,3 µm) − C07 (3,9 µm)
B = C13 (10,3 µm)
```

Ajuda a separar nevoeiro, nuvens baixas, nuvens de água e nuvens de gelo durante a noite. Os limites, inversões e realces são parte essencial da receita; use o composite `night_microphysics` do Satpy.

Fonte: [NOAA Nighttime Microphysics RGB Quick Guide](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_NtMicroRGB_final.pdf).

## GOES ABI: Air Mass RGB

Combina diferenças de vapor de água, ozono e uma banda de vapor de água:

```text
R = C08 (6,2 µm) − C10 (7,3 µm)
G = C12 (9,6 µm) − C13 (10,3 µm)
B = C08 (6,2 µm)
```

É usada para analisar características da troposfera superior, intrusões de ar seco e diferenças entre massas de ar. Use o composite `airmass` do Satpy para manter os limites e inversões padronizados.

Fonte: [NOAA Air Mass RGB Quick Guide](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_AirMassRGB_final.pdf).

## VIIRS: True Color

As bandas moderadas VIIRS incluem canais próximos do vermelho, verde e azul:

```text
R = M05 (0,67 µm)
G = M04 (0,55 µm)
B = M03 (0,49 µm)
```

Ao contrário do ABI, não é necessário sintetizar o verde. O Satpy pode aplicar correção atmosférica e criar o composite `true_color`.

## VIIRS: falso colorido de vegetação, neve e nuvens

Com as bandas de imagem de 375 m:

```text
R = I03 (1,61 µm)
G = I02 (0,87 µm)
B = I01 (0,64 µm)
```

É um falso colorido: as cores não correspondem à visão humana. A banda de 1,61 µm ajuda a distinguir água líquida, gelo e neve.

## Erros frequentes

- Misturar bandas de horas ou varrimentos diferentes.
- Processar VIIRS sem o ficheiro de geolocalização correspondente.
- Combinar refletância e temperatura sem aplicar a receita correta.
- Ignorar valores de preenchimento ou píxeis inválidos.
- Tratar `Full Disk`, `CONUS` e `Mesoscale` como se fossem a mesma grelha.
- Aplicar True Color à noite.
- Comparar cores entre imagens com limites ou gama diferentes.

Para verificar o que pode ser criado com os ficheiros disponíveis, execute `render_satellite.py --list-composites`.
