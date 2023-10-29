SearchNthNearestPointsOnNetwork
===

始点群と終点群、グラフを入力することで、始点群中の各始点について経路距離が小さい方からk個の終点とその終点までの距離を算出する。

## Description
1. toolbox.py (from https://github.com/ywnch/toolbox )　を用いて、各点を最近傍エッジとつなぎ、一つの大きなグラフを形成する
2. ダイクストラ法を用いて、各始点からN番目までの最も近い終点と、その点までの距離を取得する

## Requirement
- Ubuntu 20.04 on Windows
- python 3.6.13

kNNonNetwork
- pandas
- geopandas
- osmnx  # OpenStreetMapの道路網を用いる場合
- networkx
- heapq
- shapely

toolbox
- numpy
- pandas
- geopandas
- rtree
- itertools
- shapely

## Licence

[MIT](https://github.com/Kinutaku/kNNOnNetwork/blob/main/Licence)

## Reference
https://github.com/ywnch/toolbox
