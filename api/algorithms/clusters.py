# -*- coding: utf-8 -*-

from collections import defaultdict
from math import asin, cos, radians, sin, sqrt

from numpy import array
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN


def get_clusters(items, eps):
    if not len(items):
        return []
    groups = defaultdict(list)
    for key, value in enumerate(
        DBSCAN(
            algorithm='ball_tree',
            eps=eps,
            min_samples=1,
        ).fit_predict(
            squareform(
                pdist(
                    array([[item[1].x, item[1].y] for item in items]),
                    (lambda one, two: get_distance(one[0], one[1], two[0], two[1]))
                )
            )
        ).tolist()
    ):
        groups[value].append(items[key])
    return groups.values()


def get_distance(x_1, y_1, x_2, y_2):
    x_1, y_1, x_2, y_2 = map(radians, [x_1, y_1, x_2, y_2])
    return (
        (2 * asin(sqrt((sin((y_2 - y_1) / 2) ** 2) + (cos(y_1) * cos(y_2) * (sin((x_2 - x_1) / 2) ** 2))))) *
        (6371 * 1000 * 3.281)
    )
