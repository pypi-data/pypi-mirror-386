<div align="center">
  
[![PyPI - Version](https://img.shields.io/pypi/v/meteofetch)](https://pypi.org/project/meteofetch/)
[![conda-forge](https://anaconda.org/conda-forge/meteofetch/badges/version.svg)](https://anaconda.org/conda-forge/meteofetch)
[![Documentation Status](https://img.shields.io/readthedocs/meteofetch?logo=read-the-docs)](https://meteofetch.readthedocs.io)
[![Unit tests](https://github.com/CyrilJl/meteofetch/actions/workflows/pytest.yml/badge.svg)](https://github.com/CyrilJl/meteofetch/actions/workflows/pytest.yml)

  <a href="https://github.com/CyrilJl/meteofetch">
    <img src="https://raw.githubusercontent.com/CyrilJl/MeteoFetch/main/_static/logo.svg" alt="Logo" width="250"/>
  </a>

</div>

``MeteoFetch`` est un client python qui permet de récupérer **sans clé d'API** les dernières prévisions de :

- MétéoFrance : Arome (0.025°, 0.01°, et les cinq domaines Outre-Mer), Arpege (0.25° et 0.1°) et modèle de vague MFWAM (0,025° et 0.1°): plus de précisions sur <https://meteo.data.gouv.fr>
- l'ECMWF : IFS, chaîne ``ope``, deux runs par jour : plus de précisions sur <https://www.ecmwf.int/en/forecasts/datasets/open-data>

L'utilisateur peut choisir de :

- télécharger les fichiers grib correspondant dans le dossier de son choix
- charger les données de son choix dans un dictionnaire de ``xr.DataArray`` prêts pour l'analyse (les fichiers grib sont téléchargés dans un dossier temporaire et supprimés après chargement des données souhaitées). Les ``xr.DataArrays``  [respectent le standard CF](https://cfchecker.ncas.ac.uk/) ([Climate and Forecast](https://cfconventions.org/))

Pour connaître les champs téléchargeables pour chaque modèle, des nomenclatures sont disponibles à <https://meteofetch.readthedocs.io>.

# Installation

Le package est disponible sur Pypi :

```console
pip install meteofetch
```

Le package est également disponible sur conda-forge :

```console
conda install -c conda-forge meteofetch
```

Ou :

```console
mamba install meteofetch
```

# Utilisation rapide

```python
from meteofetch import Arome0025

datasets = Arome0025.get_latest_forecast(paquet='SP3')
datasets['ssr']
```

# Disponibilité

Il est possible de vérifier la disponibilité des derniers runs de prévision pour un modèle donné.

```python
from meteofetch import Arome0025

Arome0025.availability()
```

<div align="center">

|                     |   SP1 |   SP2 |   SP3 |   IP1 |   IP2 |   IP3 |   IP4 |   IP5 |   HP1 |   HP2 |   HP3 |
|:--------------------|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|
| 2024-05-21 18:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |
| 2024-05-21 15:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |
| 2024-05-21 12:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |
| 2024-05-21 09:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |
| 2024-05-21 06:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |
| 2024-05-21 03:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |
| 2024-05-21 00:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |
| 2024-05-20 21:00:00 |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |  True |

</div>

Ou de récupérer la date du dernier run de prévision disponible pour un paquet donné.

```python
from meteofetch import Arome0025

Arome0025.get_latest_forecast_time(paquet="SP1")
```

```text
Timestamp('2024-05-21 18:00:00+0000', tz='UTC')
```

Par défaut, ``meteofetch`` sert à l'utilisateur toutes les variables contenues dans le paquet requêté.
Il est cependant conseillée de préciser les variables voulues pour limiter l'usage mémoire :

```python
from meteofetch import Arome001

datasets = Arome001.get_latest_forecast(paquet='SP1', variables=('u10', 'v10'))
datasets['u10']

datasets = Arome001.get_latest_forecast(paquet='SP2', variables='sp')
datasets['sp']
```

Vous pouvez ensuite utiliser les méthodes usuelles proposées par ``xarray`` pour traiter les ``DataArray`` :

```python
import xarray as xr
import matplotlib.pyplot as plt
from meteofetch import Arpege01

dim = "points"
coords = ["Paris", "Edimbourg"]
x = xr.DataArray([2.33, -3.18], dims=dim)
y = xr.DataArray([48.9, 55.95], dims=dim)

datasets = Arpege01.get_latest_forecast(paquet="SP1", variables="t2m")

plt.figure(figsize=(8, 3))
datasets["t2m"].sel(lon=x, lat=y, method="nearest").assign_coords(
    {dim: coords}
).plot.line(x="time")
```

![output_code_1](https://raw.githubusercontent.com/CyrilJl/MeteoFetch/main/_static/time_series.png)

Ou encore :

```python
from meteofetch import Arome001

datasets = Arome001.get_latest_forecast(paquet='SP3', variables='h')

datasets['h'].plot(cmap='Spectral_r', vmin=0, vmax=3000)
```

![output_code_2](https://raw.githubusercontent.com/CyrilJl/MeteoFetch/main/_static/plot_map.png)

Les domaines Outre-Mer sont également disponibles :

```python
from meteofetch import (
    AromeOutreMerAntilles,
    AromeOutreMerGuyane,
    AromeOutreMerIndien,
    AromeOutreMerNouvelleCaledonie,
    AromeOutreMerPolynesie,
)

datasets = AromeOutreMerIndien.get_latest_forecast(paquet="SP1")
datasets["t2m"].mean(dim="time").plot(cmap="Spectral_r")
```
![output_code_3](https://raw.githubusercontent.com/CyrilJl/MeteoFetch/main/_static/plot_map_indien.png)

Vous pouvez également combiner ``meteofetch`` avec ``mapflow``, ma [librairie de visualisation de cartes](https://github.com/CyrilJl/mapflow) :

```python
from mapflow import animate
from meteofetch import Arome0025

datasets = Arome0025.get_latest_forecast(paquet="SP1")
animate(da=datasets['t2m'], path="run_t2m.mp4")
```

https://github.com/user-attachments/assets/ad9667f8-f5e6-4e2e-9b7c-cf5770945c42

``meteofetch`` permet également de charger les fichiers gribs de la prévision souhaitée à l'endroit où le souhaite l'utilisateur.

```python
from meteofetch import Ifs

path = 'your/folder/'
Ifs.get_latest_forecast(path=path, return_data=False)
```
