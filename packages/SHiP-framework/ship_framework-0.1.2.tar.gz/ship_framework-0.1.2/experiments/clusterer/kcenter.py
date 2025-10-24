from sklearn.metrics import pairwise_distances
from sklearn.neighbors import NearestNeighbors

def maxindex(dist, n): 
    mi = 0
    for i in range(n): 
        if (dist[i] > dist[mi]): 
            mi = i 
    return mi 
  
def selectKcities(n, weights, k): 
    dist = [0]*n 
    centers = [] 
  
    for i in range(n): 
        dist[i] = 10**9
          
    # index of city having the 
    # maximum distance to it's 
    # closest center 
    max = 0
    for i in range(k): 
        centers.append(max) 
        for j in range(n): 
  
            # updating the distance 
            # of the cities to their 
            # closest centers 
            dist[j] = min(dist[j], weights[max][j]) 
  
        # updating the index of the 
        # city with the maximum 
        # distance to it's closest center 
        max = maxindex(dist, n) 
  
    # Printing the maximum distance 
    # of a city to a center 
    # that is our answer 
    # print() 
    # print(dist[max]) 
  
    # Printing the cities that 
    # were chosen to be made 
    # centers 
    return centers


def one_nn(X, centers):
    nbrs = NearestNeighbors(n_neighbors=1).fit(centers)
    dists, inds = nbrs.kneighbors(X)
    return inds


def kcenter(X, k):
    pdist = pairwise_distances(X)
    center_ids = selectKcities(len(X), pdist, k)
    centers = [X[center_id] for center_id in center_ids]
    return one_nn(X, centers)
