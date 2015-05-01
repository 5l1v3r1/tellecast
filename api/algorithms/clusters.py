# -*- coding: utf-8 -*-

from math import asin, cos, radians, sin, sqrt

from numpy import array
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN, KMeans


def get_clusters(items):
    groups = {}
    length = len(items)
    if not length:
        return groups.values()
    co_ordinates = array([[item[1].x, item[1].y] for item in items])
    distances = squareform(pdist(co_ordinates, (lambda one, two: get_distance(one[0], one[1], two[0], two[1]))))
    resource = DBSCAN(algorithm='ball_tree', eps=10, min_samples=1)
    indices = resource.fit_predict(distances).tolist()
    for key, value in enumerate(indices):
        if value not in groups:
            groups[value] = []
        groups[value].append(items[key])
    return groups.values()


def get_clusters_old(items):
    groups = {}
    length = len(items)
    if not length:
        return groups.values()
    co_ordinates = array([[item[1].x, item[1].y] for item in items])
    distances = squareform(pdist(co_ordinates, (lambda one, two: get_distance(one[0], one[1], two[0], two[1]))))
    resource = KMeans(n_clusters=16 if length >= 16 else length, precompute_distances=True)
    indices = resource.fit_predict(distances).tolist()
    for key, value in enumerate(indices):
        if value not in groups:
            groups[value] = []
        groups[value].append(items[key])
    return groups.values()


def get_distance(x_1, y_1, x_2, y_2):
    x_1, y_1, x_2, y_2 = map(radians, [x_1, y_1, x_2, y_2])
    return (
        2 * asin(sqrt(sin((y_2 - y_1) / 2) ** 2 + cos(y_1) * cos(y_2) * sin((x_2 - x_1) / 2) ** 2))
    ) * (
        6371 * 1000 * 3.281
    )
