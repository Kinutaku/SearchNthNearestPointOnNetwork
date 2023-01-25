import pandas as pd
import geopandas as gpd
import osmnx as ox
import numpy as np
import networkx as nx
import heapq
import random
import matplotlib.pyplot as plt
from shapely.geometry import Point

from toolbox import connect_poi


# kNNダイクストラ(G:グラフ, k:検索する近傍数, s:出発点, ends:終着点)
def kNNonGraph(G, k, s, ends):
    
    outs = {}
    count = 0
    
    n = nx.number_of_nodes(G)
    values = range(0,nx.number_of_nodes(G))
    keys = sorted(list(G.nodes))
    compare = dict(zip(keys,values))  # ノード番号を0から再ナンバリング
    d = [float('inf')]*n
    d[s] = 0
    used = [False]*n
    used[s] = True
    
    que = []
    for e in list(G.edges(s, data=True)):
        heapq.heappush(que, [e[2]["weight"],e[1]])  # heapq = [[次のノードまでの重さ、次のノードの番号]]
    while que:
        u, v = heapq.heappop(que)  # u,v = 次のノードまでの重さ、次のノードの番号
        #if u > 2000:
        #    break
        v_num = compare[v]
        if used[v_num]:   # vが到達済みならスキップ
            continue
        d[v_num] = u
        used[v_num] = True
        if v in ends:
            outs.update({v: d[v_num]})
            count += 1
            if count == k:
                return outs
        for e in G.edges(v, data=True):
            if not used[compare[e[1]]]:
                if d[compare[e[1]]] > e[2]["weight"]+d[v_num]:
                    heapq.heappush(que, [e[2]["weight"]+d[v_num],e[1]])
    # print(s,": num of available is under k or over 2000")
    outs.update({float('inf'): float('inf')})
    return outs


# if nodes and edges are still exist
nodes = gpd.read_file(filepath+'nodes.shp')
edges = gpd.read_file(filepath+'edges.shp')


### setting
neighbor = 1

# loading start points and end points
orgs_df = pd.read_csv("start_points.csv")  # csv file has longitude and latitude
orgs = gpd.GeoDataFrame(orgs_df, geometry=gpd.points_from_xy(orgs_df.x, orgs_df.y), crs="epsg:4326")

ends_df = pd.read_csv("end_points.csv")
ends = gpd.GeoDataFrame(ends_df, geometry=gpd.points_from_xy(ends_df.x, ends_df.y), crs="epsg:4301")

output_path = "output.csv"

# setting output file's columns according to the number of neighbors

cols = ['name', 'end1_d', 'end1']  # if neighbor = 1
# cols = ['name', 'avg', 'end1_d','end2_d','end3_d', 'end1','end2','end3']  # if neighbor = 3



####################################


# グラフのOSMからの取り込み
# query = "query script"
# G = ox.graph_from_place(query, network_type="all")
bbox = (36.8181932, 36.3198304264,137.7555972602,136.07816184) #NSEW
G = ox.graph_from_bbox(bbox[0], bbox[1],bbox[2],bbox[3], network_type='all')

# グラフのセーブと再読み込み
# filepath='filepath/'
#ox.save_graph_shapefile(G, filepath=filepath, encoding='utf-8')  # ノード、エッジを保存
### 時間かかるので一回読み込んだらコメントアウト
# nodes = gpd.read_file(filepath+'nodes.shp')
# edges = gpd.read_file(filepath+'edges.shp')


# 出発点の読み込み

orgs['lon'] = orgs['geometry'].apply(lambda p: p.x)
orgs['lat'] = orgs['geometry'].apply(lambda p: p.y)
# orgs = orgs[(orgs['lon'] >= bbox[3]) & (orgs['lon'] <= bbox[2]) & (orgs['lat'] >= bbox[1]) & (orgs['lat'] <= bbox[0])]
orgs['key'] = orgs.index # set a primary key column

# 目的地の読み込み

ends['lon'] = ends['geometry'].apply(lambda p: p.x)
ends['lat'] = ends['geometry'].apply(lambda p: p.y)
# ends = ends[(ends['lon'] >= bbox[3]) & (ends['lon'] <= bbox[2]) & (ends['lat'] >= bbox[1]) & (ends['lat'] <= bbox[0])]
ends['key'] = ends.index + len(orgs)  # set a primary key column

# 出発地点が被って消えるのを回避
random.seed(42)
if mesh_or_pbhouse == "pbhouse":
    orgs.geometry = orgs.geometry.map(lambda x:Point(tuple([x.coords[0][0]+random.randrange(-100,100)*10**(-8), x.coords[0][1] ])) if orgs.geometry.map(lambda x:x.coords[0]).isin([x.coords[0]]).sum() > 1 | ends.geometry.map(lambda x:x.coords[0]).isin([x.coords[0]]).any() else x)
else:
    orgs.geometry = orgs.geometry.map(lambda x:Point(tuple([x.coords[0][0]+random.randrange(-100,100)*10**(-8), x.coords[0][1] ])) if ends.geometry.map(lambda x:x.coords[0]).isin([x.coords[0]]).any() else x)

# geodataframeの座標設定
# orgs.crs=4326
# ends.crs=4326


# 出発点、目的地をグラフ上にスナップ
prim_key = len(orgs)
new_nodes, new_edges = connect_poi(orgs, nodes, edges, "org", key_col='key', threshold=100000, path=None)
new_nodes, new_edges = connect_poi(ends, new_nodes, new_edges, "end", prim_key = prim_key, key_col='key', threshold=100000, path=None)


# グラフの再構成
edges_dict = {"source": new_edges["from"], "target": new_edges["to"], "weight": new_edges["length"]}
edges_pd = pd.DataFrame(edges_dict)
G_n = nx.from_pandas_edgelist(edges_pd, edge_attr=True)

# pp と poiの座標が被ってpoiからppへのエッジが消えている場合の対応
n_oe = len(orgs)+len(ends)
n_o = len(orgs)
n_e = len(ends)

for i in range(n_o):
    if G_n.has_edge(i, i-n_o) or G_n.has_edge(i-n_o, i):
        continue
    else:
        G_n.add_edge(i,-n_o+i,weight=0.01)
for i in range(n_o, n_oe):
    if G_n.has_edge(i, i-n_oe-n_o) or G_n.has_edge(i-n_oe-n_o, i):
        continue
    else:
        G_n.add_edge(i,-n_oe-n_o+i,weight=0.01)

# 終着点判定用リストの作成
ends_list = list(range(n_o, n_oe))

# すべての出発点について、最寄りの終着点とそこまでの距離を計算
# result_list = [{終着点: 距離, 終着点:距離 ...},{},...]
result_list = [[]]*len(new_nodes[new_nodes.highway=="org"])
for s in new_nodes[new_nodes.highway=="org"].osmid.tolist():
    result_list[s] = kNNonGraph(G_n, neighbor, s, ends_list)

output = pd.DataFrame(columns=cols)
count = 0
for i in result_list:
    keys_l = []
    values_l = []
    for k in result_list[count]:
        keys_l.append(k)
    for v in result_list[count].values():
        values_l.append(v)
    if neighbor == 1:
        output = output.append({'name':orgs.Name[count], 'end1_d':values_l[0], 'end1':keys_l[0]}, ignore_index=True)
    elif neighbor == 3:
        output = output.append({'name':orgs.Name[count], 'avg':np.average(values_l), 'end1_d':values_l[0], 'end2_d':values_l[1], 'end3_d':values_l[2], 'end1':keys_l[0], 'end2':keys_l[1], 'end3':keys_l[2], 'x':orgs.lon[count], 'y':orgs.lat[count]}, ignore_index=True)
    count += 1
output.to_csv(output_path, index=False)