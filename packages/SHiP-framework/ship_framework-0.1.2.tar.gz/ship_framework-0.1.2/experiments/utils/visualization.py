# from distance_metric import get_dc_dist_matrix, get_reach_dists
from sklearn.decomposition import KernelPCA
import networkx as nx
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import numba as numba
from datetime import datetime
from matplotlib.widgets import Button
# from density_tree_nary import NaryDensityTree
# from kcentroids_nary import DCKCentroids as DCKCentroids_nary
# from density_tree_nary import make_n_tree
# from kneed import KneeLocator
import pandas as pd
from datetime import datetime
# matplotlib.use('TkAgg') #I installed python3-tk for this - needed to display via WSL 2

def plot_clustering_multi(embed_points, embed_labels, titles, main_title=None, dot_scale = 1, annotations=False, normalized_labels=False, save=False, save_name=None):
    '''
    Plots the provided points with as many embeddings as there are sets of lables and titles. Will highlight centers in k-means embeddings if provided.

    Parameters
    ----------

    embed_points : Numpy.Array
    embed_labels : List[Numpy.Array]
    titles : List[String]
    centers : Numpy.Array, default=None
    dot_scale : Float, default=1
    save : Boolean, default=False
    save_name : String, default=None
    '''
    dot_size = (plt.rcParams['lines.markersize'] ** 2) * dot_scale


    if len(embed_points[0].shape) == 1: # If one-dimensional points
        embed_points = np.stack((embed_points, np.zeros_like(embed_points)), -1)

    if not isinstance(embed_labels, list):
        embed_labels = [embed_labels]
    if not isinstance(titles, list):
        titles = [titles]
    assert len(embed_labels) == len(titles)
    if len(embed_labels) == 1:
        if len(embed_labels[0])== 1:
            fig, axes = plt.subplots(1)
            axes = [[axes]]  # Convert single Axes object to a list
        else:
            fig, axes = plt.subplots(1, len(embed_labels[0]))
            axes = [axes]  # Convert single Axes object to a list
    else:
        fig, axes = plt.subplots(len(embed_labels), len(embed_labels[0]))
        fig.set_figwidth(4 * len(embed_labels))
        if len(embed_labels[0]) == 1:
            axes = [[ax] for ax in axes]
    #print("embed_labels", embed_labels)
    

    for x, labelset in enumerate(embed_labels):
        #min_label = np.min(embed_labels)
        max_label = np.max(labelset)
        norm = mcolors.Normalize(vmin=0, vmax=max_label)
        for i, labels in enumerate(labelset):
            noise_points = np.array([point for i,point in enumerate(embed_points[x]) if labels[i] == -1])
            noise_labels = ["lightgrey" for point in noise_points]
            noise_edgecolors = ["darkgrey" for point in noise_points]

            real_points = np.array([point for i,point in enumerate(embed_points[x]) if labels[i] != -1])
            real_labels = [label for i,label in enumerate(labels) if labels[i] != -1]
            real_edgecolors = ["black" for point in real_points]

            #"Paired" is good and used for compound
            if normalized_labels:
                cmap = "gist_ncar"
            else:
                curr_k = len(np.unique(labels))
                if curr_k < 11:
                    cmap = "Paired" #Default is "viridis", other options are https://matplotlib.org/stable/users/explain/colors/colormaps.html
                elif curr_k >= 11 and curr_k < 21:
                    cmap = "tab20b"
                else:
                    cmap = "gist_ncar"

            real_color_labels = own_cmap(real_labels)

            if len(real_points) != 0:
                axes[x][i].scatter(real_points[:, 0], real_points[:, 1], c=real_color_labels, s=dot_size, edgecolor=real_edgecolors, zorder=1, linewidths=0.3)

            #Plot noise points on top
            if len(noise_points) != 0:
                axes[x][i].scatter(noise_points[:, 0], noise_points[:, 1], c=noise_labels, s=dot_size, edgecolor=noise_edgecolors, alpha=0.5, zorder=0)
            if x == 0:
                axes[x][i].set_title(titles[x][i], fontsize=12)
            axes[x][i].grid(alpha=0.2, zorder=0)

            # Assuming 'axes[x][i]' is your current axis object
            # Get current axis limits
            x_min, x_max = axes[x][i].get_xlim()
            y_min, y_max = axes[x][i].get_ylim()

            # Calculate the ranges
            x_range = x_max - x_min
            y_range = y_max - y_min

            # Make the ranges equal to get a square plot
            max_range = max(x_range, y_range)

            # Calculate the new limits to center the data
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2

            new_x_min = x_center - max_range / 2
            new_x_max = x_center + max_range / 2
            new_y_min = y_center - max_range / 2
            new_y_max = y_center + max_range / 2

            # Set the new limits
            axes[x][i].set_xlim(new_x_min, new_x_max)
            axes[x][i].set_ylim(new_y_min, new_y_max)


            axes[x][i].set_aspect('equal', adjustable='box')
            axes[x][i].tick_params(left = False, right = False , labelleft = False , 
                labelbottom = False, bottom = False)

            # Adding annotations for each point
            if annotations:
                for j, point in enumerate(embed_points[x]):
                    xx, y = point
                    axes[x][i].annotate(str(j+1), xy=(xx, y), xytext=(0, 0), textcoords='offset points', ha='center', va='center')
            
    if main_title is not None:
        fig.suptitle(main_title)
    if save:
        if save_name is None:
            save_name = str(datetime.now())
        plt.savefig("savefiles/images/"+save_name+"_embeddings.png") 
    plt.tight_layout() 

    num_rows = len(embed_labels)
    num_cols = len(embed_labels[0])

    
    plt.subplots_adjust(wspace=0.0, hspace=0.05) #CHANGE SPACING HERE BETWEEN THE CLUSTER PLOTS
    fig.canvas.manager.set_window_title('Clustering Plot')
    plt.show(block= False)


def visualize_scores(scoresets, dataset_types, clustering_methods, metrics, save_csv, avgs=True):
    '''
    Makes a table of metric scores for each clustering method on each dataset. num of metrics columns for each clustering method.
    The scoresets contains a list for each metric for each clustering method for each dataset type.
    The method interleaves these lists essentially and displays it.

    TODO: Export to csv file with merged cells and bold / underlined elements.
    This can be directly copied into https://www.tablesgenerator.com/ and generate latex table.
    
    '''
    num_metrics = len(metrics)
    num_datasets = len(dataset_types)
    num_methods = len(clustering_methods)
    # Combine them into a table format: I want a table of dimension datasets x (methods x metrics)
    #print("num_metircs", num_metrics, "num_datasets", num_datasets, "num_methods", num_methods)
    metricheaders = []
    rv = 3
    #Compute averages for each column and bests for each metric in each row
    averages = [0.0 for i in range(num_metrics*num_methods)]
    bests = [[0.0 for i in range(num_metrics)] for j in range(num_datasets+1)] #+1 for the avg
    for i in range(num_methods):
        for j in range(num_metrics):
            vals = []
            #print("i,j", i,j)
            for k in range(num_datasets):
                vals.append(scoresets[k][j][i])
                averages[j]
                bests[k][j%num_metrics] = max(bests[k][j%num_metrics], np.round(scoresets[k][j][i], rv))
            avg = np.round(np.mean(vals), rv)
            averages[i*num_metrics+j] = avg
            bests[k+1][j%num_metrics] = max(bests[k+1][j%num_metrics], avg)


    for method in clustering_methods:
        for i, metric in enumerate(metrics):
            metricheaders.append(metric)
            #col_colors.append(str((i+1)/(num_metrics)))

    
    group_headers = [""]*(num_methods*num_metrics)
    for i, method in enumerate(clustering_methods):
        group_headers[i*num_metrics] = method

    #print("scoresets:", np.round(scoresets,3))
    data = [[""]*(num_methods*num_metrics), metricheaders]
    data =  data + [[0 for x in range(len(scoresets[0])*len(clustering_methods))]for y in range(len(dataset_types))]
    cell_colors = [[str(1.0) for x in range(len(scoresets[0])*len(clustering_methods))]for y in range(len(dataset_types)+2)]
    if avgs:
        data = data + [averages]
        cell_colors = cell_colors + [[str(1.0) for x in range(len(scoresets[0])*len(clustering_methods))]]
        #print("data2:", data)
    num_rows = len(dataset_types) +1 if avgs else len(dataset_types) 
    for x in range(num_rows): #For each row
        if x < len(dataset_types):
            for i, scoreset in enumerate(scoresets[x]): #num_metrics
                for j, metricval in enumerate(scoreset): #num_scores
                    data[x+2][i+j*num_metrics] = np.round(metricval, rv)
                    cell_colors[x+2][i+j*num_metrics]  = str(((i+1)/num_metrics)*0.5 + 0.5)
        else:
            for i in range(num_metrics): #num_metrics
                for j, metricval in enumerate(scoreset): #num_scores
                    cell_colors[x+2][i+j*num_metrics]  = str(((i+1)/num_metrics)*0.5 + 0.5)
                    
    #print("data:", data)

    


    fig, ax = plt.subplots(2,1,figsize=(10,6))  # Adjust figure size as needed
    ax[1].axis('tight')
    ax[1].axis('off')
    ax = ax[0]
    ax.axis('tight')
    ax.axis('off')

    rowheaders = ["", ""]+dataset_types
    if avgs:
        rowheaders = rowheaders + ["Average"]
    
    table = ax.table(cellText=data, rowLabels=rowheaders, cellLoc='center', cellColours=cell_colors)
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    header_size = 17
    subheader_size = 15
    del table.get_celld()[(0,-1)]
    del table.get_celld()[(1,-1)]
    #print("bests:", bests)
    for key, cell in table.get_celld().items():
        if key[1] == -1:
            cell.set_fontsize(header_size) # The row headers
            if key[0] == 1:
                cell.set_facecolor('0.9')
        elif key[0] == 1:
            cell.set_fontsize(subheader_size) # Metric headers
            cell.set_facecolor('0.9')
        else:
            cell.set_fontsize(14)  # Set the font size (e.g., 14 points)
        if key[0] != 0 and key[0] != 1:
            #print("the str comp:",cell.get_text().get_text(), str(bests[key[0]-2][key[1]%num_metrics]) )
            if cell.get_text().get_text() == str(bests[key[0]-2][key[1]%num_metrics]):
                #print("key", key, "cell", cell)
                #print("best:", cell.get_text())
                cell.get_text().set_fontweight('bold')
    #ax.table(...,edges='open')
    header_table = ax.table(cellText=[clustering_methods], cellLoc='center') #Overlay the "merged multi column headers" on the full table
    header_table.auto_set_font_size(False)
    header_table.set_fontsize(header_size)

    tray = np.zeros(num_metrics*num_methods)
    csv_file = [["" if i % num_metrics != 0 else clustering_methods[int((i-i%num_metrics)/num_metrics)] for i,t in enumerate(tray) ]]
    csv_file = csv_file + data
    csv_file = [[""]+row if i<3 or i == len(csv_file)-1 else [dataset_types[i-3]]+row for i,row in enumerate(csv_file)]
    #print("csv headers", csv_file)
    df = pd.DataFrame(csv_file)

    savestring = "metric_save/metrics" + "_"+datetime.now().strftime("%H:%M:%S") + ".csv"
    if save_csv:
        df.to_csv(savestring, index=False, sep=';', header=False)

    plt.tight_layout()
    fig.canvas.manager.set_window_title('Metric scores')
    plt.show(block=False)
    return

def label_bars(ax, bar, times=None): 
    if times is not None:
        assert len(times) == len(bar)
    # attach some text labels
    for i, rect in enumerate(bar):
        height = rect.get_height()
        #if times is not None:
        #    height = times[i]
        ax.text(rect.get_x() + rect.get_width()/2., 1.01*height,
                '%.2f' %height,
                ha='center', va='bottom', c="grey")

def plot_histogram_multi(timesets, timinglabels, datasets, save_csv):
    '''
    Plots  a histogram with the given set of timinglabels for each timeset+dataset in the list timesets.

    Parameters
    ----------

    '''
    assert len(timesets[0]) == len(timinglabels)        
    if len(timesets) == 1:
        fig, axes = plt.subplots(len(timesets), 1)
        axes = [axes]  # Convert single Axes object to a list
    else:
        fig, axes = plt.subplots(len(timesets), 1)

    for x, timeset in enumerate(timesets):
        bar = axes[x].bar(timinglabels, timeset)
        axes[x].set_title(datasets[x], fontweight='bold', fontsize='large')
        axes[x].set_xlabel("Function", fontweight='bold', fontsize='large') 
        axes[x].set_ylabel('Time (m/s) (logarithmic)', fontweight='bold', fontsize='large') 
        axes[x].set_yscale('log')
        label_bars(axes[x], bar, timeset)
    fig.tight_layout()
    fig.canvas.manager.set_window_title('Cluster times')

    csv_file = [timinglabels]+timesets
    csv_file = [[""]+row if i<1 else [datasets[i-1]]+row for i,row in enumerate(csv_file)]
    #print("types", [[type(element) for element in sublist] for sublist in csv_file])
    #print("csv headers", csv_file)
    df = pd.DataFrame(csv_file)
    #print("df:", df)
    savestring = "metric_save/times" + "_" + datetime.now().strftime("%H:%M:%S") + ".csv"
    if save_csv:
        df.to_csv(savestring, index=False, sep=';', header=False)


    plt.show(block=False)


def plot_histogram_builds_multi(timesets, timinglabels, datasets):
    '''
    Plots  a histogram with the given set of timinglabels for each timeset+dataset in the list timesets.

    https://www.geeksforgeeks.org/bar-plot-in-matplotlib/

    Parameters
    ----------
    '''
    assert len(timesets) == len(datasets)    
    transpotimes = np.transpose(np.array(timesets))
    #print("timesets:", timesets)
    #print("transpos:", transpotimes)
    barwidth = 0.2
    fig, ax = plt.subplots(figsize =(12, 8)) 
    cmap = {0: "blue", 1: "red", 2:"green", 3:"brown"}


    old_bar = np.array([])
    for i, datasettime in enumerate(transpotimes):
        if i == 0:
            curr_bar = np.arange(len(datasettime))
        else:
            curr_bar = [x + barwidth for x in old_bar]
        
        bar = plt.bar(curr_bar, datasettime, color=cmap[i], width=barwidth, label=timinglabels[i])
        label_bars(plt, bar)
        old_bar = curr_bar

    plt.ylabel('Time (m/s) (logarithmic)', fontweight ='bold', fontsize = 15) 
    plt.xlabel('Dataset', fontweight ='bold', fontsize = 15) 

    # Adding Xticks 
    plt.xticks([r + barwidth for r in range(len(datasets))], 
            datasets)
    plt.yscale('log')
    plt.legend()
    fig.canvas.manager.set_window_title('Build times')
    plt.show(block=False)



def show_tree(points, minPts, k, version, labels=None):
    '''
     Visualizes the tree, provided the version. Either dc-tree, kmeans or kmedian tree. 
    '''
    active_tree, dc_dist_matrix = make_n_tree(points, None, min_points=minPts)
    if version == "kmeans":
        centroid = DCKCentroids_nary(k=k, min_pts=minPts, loss=version, noise_mode="none")
        active_tree = centroid.define_cluster_hierarchy_nary(points)
    elif version == "kmedian":
        centroid = DCKCentroids_nary(k=k, min_pts=minPts, loss=version, noise_mode="none")
        active_tree = centroid.define_cluster_hierarchy_nary(points)
    if labels is None:
        plot_tree_v2(active_tree)
    else:
        plot_tree_v2(active_tree, labels)


def visualize_embedding(points, labels=None, min_pts=3, metric="dc_dist"):
  '''
  Visualizes the distance measure in an embedded space using MDS
  '''
  fig, ax = plt.subplots()
  if labels is None:
    labels = np.arange(len(points))
  dists = get_dists(metric, points, min_pts=min_pts)

  model = KernelPCA(n_components=2, kernel="precomputed")
  mds_embedding = model.fit_transform(-0.5 * dists)
  ax.scatter(mds_embedding[:, 0], mds_embedding[:, 1], c="b")
  for i, name in enumerate(labels):
     ax.annotate(name, (mds_embedding[i][0], mds_embedding[i][1]))
  
  ax.set_title("2D embedding of the distances with  " + metric + " distance")
  plt.show()


def visualize(points, cluster_labels = None, distance="dc_dist", minPts=3, centers=None, save=False, save_name=None):
  '''
  Visualizes the complete graph G over the points with chosen distances on the edges.

  Parameters
  ----------
    points: Numpy.Array
      The points to be visualized in a numpy 2D array

    cluster_labels: Numpy.Array, default=None 
      This shows a distinct color for each ground truth cluster a point is a part of, should be a 1D array with a label for each point. If None, will make all points blue.
    
    distance : String, default="dc_dist"
      The distance function to be used in the visualization. "dc_dist", "euclidean", "mut_reach".
    
    minPts: Int, default=3
      The number of points for a point to be a core point, determines core distance.

    show_cdists : Boolean, default=False
      Will make a circle with cdist radius from each point if true. Will have a dotted line to circle's edge showing the cdist value.
    
    centers : Numpy.Array, default=None
      Positions of the centers to be highlighted. Needs 2d coordinates. 
    
    save : Boolean, default=False
      If true will save the plot under the save_name.
    
    save_name : String, default=None
      The name to save the plot under.
  '''
  cdist_entities = []
  cdists_visible = False

  def toggle_cdists(event):
    nonlocal cdist_entities, cdists_visible
    if not cdists_visible:
       #Draw cdists
       for i, pos in pos_dict.items():
        circle = plt.Circle(pos, radius=cdists[i-1], edgecolor="black", facecolor="none", alpha=0.5)
        ax.add_patch(circle)
        cdist_entities.append(circle) #Save the circles to possibly destroy them

        edge_pos = (pos[0], pos[1]+cdists[i-1])
        line = ax.plot([pos[0], edge_pos[0]], [pos[1], edge_pos[1]], color='blue', zorder=0, alpha=0.5, linestyle='dotted')[0]
        text = ax.text(pos[0], pos[1] + cdists[i-1]/2, str(np.round(cdists[i-1], 2)), ha='center', va='bottom', fontsize=6, color='black', rotation=90, bbox=None, zorder=1)
        cdist_entities.append(line)
        cdist_entities.append(text)

        plt.draw()
        cdists_visible = True
    else:
       #Destroy cdists
       for c in cdist_entities:
          c.remove()
       cdist_entities = []
       plt.draw()
       cdists_visible = False

  cdists = get_cdists(points, minPts)
  dists = get_dists(distance, points, minPts)
  
  fig, ax = plt.subplots(figsize=(16,9))
  ax.grid(True)
  ax.set_axisbelow(True)
  n = points.shape[0]
  G = nx.Graph()
  edges, edge_labels = create_edges(dists)
  G.add_edges_from(edges)

  labels = {node: str(node) for node in G.nodes()}
  pos_dict = {i+1:(points[i,0], points[i,1]) for i in range(points.shape[0])}

  if cluster_labels is not None:
    nx.draw_networkx_nodes(G, pos=pos_dict, node_color=cluster_labels, ax=ax)
  else:
    nx.draw_networkx_nodes(G, pos=pos_dict, node_color="skyblue", ax=ax)

  nx.draw_networkx_labels(G, pos=pos_dict, labels=labels, font_color="black", ax=ax)
  nx.draw_networkx_edges(G, pos=pos_dict, ax=ax, width=0.8)
  nx.draw_networkx_edge_labels(G, pos=pos_dict, edge_labels=edge_labels, ax=ax, font_size=8)

  #Code to highlight potential centers
  if centers is not None:
    print("highligthing centers")
    ax.scatter(centers[:, 0], centers[:,1], c="none", edgecolor="r", zorder=2, s=300)
     
  #Set perspective to be "real"
  ax.set_aspect('equal', adjustable='box')
  #This is needed to add axis values to the plot
  ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)

  ax.set_title("Complete graph with " + distance + " distance")

  if save:
        if save_name is None:
            save_name = str(datetime.now())
        plt.savefig("savefiles/images/"+save_name+"_graph.png")

  # Get the position and size of the plot's axes
  pos = ax.get_position()

  # Set the position and size of the button relative to the plot's axes
  button_width = 0.075
  button_height = 0.05
  button_spacing = 0.1
  button_x = pos.x0 - button_spacing
  button_y = pos.y0 + (pos.height - button_height) / 2 #This places it in the middle currently

  # Create a button
  button_ax = fig.add_axes([button_x, button_y, button_width, button_height]) #This defines the area on the plot that should be activated by the button widget
  cdist_button = Button(button_ax, 'Toggle cdists')

  # Attach the function to be called when the button is pressed
  cdist_button.on_clicked(toggle_cdists)

  plt.show()

  
@numba.njit(fastmath=True, parallel=True)
def get_dist_matrix(points, D, dim, num_points):
    '''
    Returns the Euclidean distance matrix of a 2D set of points. 

    Parameters
    ----------
    points : n x m 2D numpy array
    D : empty n x n numpy array
    dim : m
    num_points : n
    '''
    for i in numba.prange(num_points):
        x = points[i]
        for j in range(i+1, num_points):
            y = points[j]
            dist = 0
            for d in range(dim):
                dist += (x[d] - y[d]) ** 2
            dist = np.sqrt(dist)
            D[i, j] = dist
            D[j, i] = dist
    return D

#Dist types: "Euclidean", "dc_dist", "mut_reach"
def get_dists(dist_type, points, minPts=3):
  '''
    Outputs the pairwise distance matrix between a set of points, each point being a row in a 2D array. 

    Parameters
    ----------
    dist_type : String
      Options: "euclidean", "dc_dist", "mut_reach"

    points : 2D numpy array

    minPts : Int, default=3
      The number of points for the core distance in dc_dist and mut_reach. The minimal number of points for something to be a core-point.
  '''
  dists = None
  n = points.shape[0]

  #Euclidean distance
  if dist_type == "euclidean":
    D = np.zeros([n, n])
    dists = get_dist_matrix(points, D, int(points.shape[1]), n)
  #dc-distance
  elif dist_type == "dc_dist":
    dists = get_dc_dist_matrix(
        points,
        n_neighbors=minPts, #Unused parameter
        min_points=minPts
    )
  #Mutual reachability distance
  elif dist_type == "mut_reach": 
    D = np.zeros([n, n])
    D = get_dist_matrix(points, D, int(points.shape[1]), n)
    dists = get_reach_dists(D, minPts, n)
  return dists
  
  
def get_cdists(points, min_pts):
    '''
    Computes the core distances of a set of points, given a min_pts.
    '''
    num_points = points.shape[0]
    dim = int(points.shape[1])

    D = np.zeros([num_points, num_points])
    D = get_dist_matrix(points, D, dim, num_points)

    cdists = np.sort(D, axis=1)
    cdists = cdists[:, min_pts - 1] #These are the core-distances for each point.
    #print("cdists:", cdists)
    return cdists


#Currently creates edges for a complete graph
def create_edges(distance_matrix):
  #print("dist matrix:", distance_matrix)
  edges = []
  edge_labels = {}
  for i in range(0, distance_matrix.shape[0]-1):
     for j in range(i+1,distance_matrix.shape[1]):
        edges.append((i+1,j+1))
        edge_labels[(i+1,j+1)] = np.round(distance_matrix[i,j],2)
  return edges, edge_labels

######################################################
############# N-ary tree plotting tools ##############
######################################################

def find_node_positions_nary(root, width=1, vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None):
    if pos is None:
        pos = [[xcenter, vert_loc]]
    else:
        pos.append([xcenter, vert_loc])
    if root.has_children:
        dx = width / root.num_children
        curr_x = xcenter - (dx*(root.num_children-1)/2)
        for child in root.children:
          pos = find_node_positions_nary(
             child,
             width = dx,
             vert_gap=vert_gap,
             vert_loc=vert_loc-vert_gap,
             xcenter=curr_x,
             pos=pos,)
          curr_x += dx
    return pos


def make_node_lists_nary_v2(root, point_labels, parent_count, dist_list, edge_list, color_list, alpha_list, edgecolor_list, dist_dict, centers=None):
    count = parent_count
    if root.dist > 0:
        dist_list.append(root.dist)
    else: 
        dist_list.append(root.point_id)
    if root.is_leaf and root.point_id is not None:
        if root.point_id == -2:
            color_list.append(0)
        else:
            color_list.append(point_labels[root.point_id])
            alpha_list.append(1)
            if centers is not None:
                if root.point_id in centers:
                    edgecolor_list.append("red")
                elif point_labels[root.point_id] != -1:
                    edgecolor_list.append("black")
                else: 
                    edgecolor_list.append("yellow")
            else: 
                if point_labels[root.point_id] != -1: #Non-noise points
                    edgecolor_list.append("black")
                else: #Noise points:
                    edgecolor_list.append("yellow")
    else: #Internal node
        color_list.append("white")
        alpha_list.append(1)
        edgecolor_list.append("black")

    for tree in root.children:
        if tree is not None:
            edge_list.append((parent_count, count+1))
            count = make_node_lists_nary_v2(
                tree,
                point_labels,
                count+1,
                dist_list,
                edge_list,
                color_list,
                alpha_list,
                edgecolor_list,
                dist_dict,
                centers)
    return count

def plot_tree_v2(root, labels=None, centers=None, save=False, save_name=None, extra_annotations=None, node_size=900):
    '''
    Plots the dc-dist tree, optionally highligthing nodes chosen as centers with a red outline. Shows the node indexes on the leaves and dc-distances in the non-leaf nodes. The leaves are color-coded by the provided labels.
    A yellow outline means that a node was labelled noise. 
    Parameters
    ----------
    root : NaryDensityTree
    labels : Numpy.Array
    centers : Numpy.Array, default=None
    save : Boolean, default=False
    save_name : String, default=None
    extra_annotations : Numpy.Array, default=None
      The annotations should be provided in preorder traversal order over the binary tree.
    node_size : int, default=900
    '''
    if labels is None:
       labels = np.arange(root.size)
    dist_dict = {}
    edge_list = []
    dist_list = []
    color_list = []
    alpha_list = []
    edgecolor_list = []

    assert isinstance(root, NaryDensityTree), "is_binary is False so expected a root of class NaryDensityTree"
    make_node_lists_nary_v2(root, labels, 1, dist_list, edge_list, color_list, alpha_list, edgecolor_list, dist_dict, centers)
    pos_list = find_node_positions_nary(root, 10)

    G = nx.Graph()
    G.add_edges_from(edge_list)
    
    extra_dict = {}
    pos_dict = {}
    for i, node in enumerate(G.nodes):
        pos_dict[node] = pos_list[i]
        #+1 for {:.0f} as these are the node numbers which are 0 indexed from the point_ids in the tree, but are 1-indexed in the other visualizations.
        dist_dict[node] = '{:.1f}'.format(dist_list[i]) if dist_list[i] % 1 != 0 else '{:.0f}'.format(dist_list[i])

        if extra_annotations is not None: #Also for extra here
          extra_dict[node] = np.round(extra_annotations[i],2) 

    plt.title("n-ary dc-distance tree with " + str(len(labels)) + " points")

    # Identify internal nodes and leaf nodes
    internal_nodes = [node for node in G.nodes() if G.degree(node) > 1]
    leaf_nodes = [node for node in G.nodes() if G.degree(node) == 1]

    # Split color, alpha, and edgecolor lists
    internal_color_list = [color_list[node - 1] for node in internal_nodes]
    leaf_color_list = [color_list[node - 1] for node in leaf_nodes]
    #print("internal colors:", internal_color_list)
    #print("leaf_color_list:", leaf_color_list)

    internal_alpha_list = [alpha_list[node - 1] for node in internal_nodes]
    leaf_alpha_list = [alpha_list[node - 1] for node in leaf_nodes]

    internal_edgecolor_list = [edgecolor_list[node - 1] for node in internal_nodes]
    leaf_edgecolor_list = [edgecolor_list[node - 1] for node in leaf_nodes]

    noise_nodes = [node for node in G.nodes() if (G.degree(node) == 1 and color_list[node - 1] == -1)]
    noise_color_list = ["lightgrey" for node in noise_nodes]
    noise_alpha_list = [alpha_list[node - 1] for node in noise_nodes]
    noise_edgecolor_list = ["lightgrey" for node in noise_nodes]

    # Draw internal nodes
    nx.draw_networkx_nodes(G, pos=pos_dict, nodelist=internal_nodes, node_color=internal_color_list, alpha=internal_alpha_list, edgecolors=internal_edgecolor_list, linewidths=1.5, node_size=node_size)

    cmap = "Paired"
    # Draw leaf nodes
    nx.draw_networkx_nodes(G, pos=pos_dict, nodelist=leaf_nodes, node_color=leaf_color_list, alpha=leaf_alpha_list, edgecolors=leaf_edgecolor_list, linewidths=1.5, node_size=node_size, cmap=cmap)
    
    # Draw noise nodes
    if len(noise_nodes) != 0:
      nx.draw_networkx_nodes(G, pos=pos_dict, nodelist=noise_nodes, node_color=noise_color_list, alpha=noise_alpha_list, edgecolors=noise_edgecolor_list, linewidths=1.5, node_size=node_size)

    nx.draw_networkx_edges(G, pos=pos_dict)
    nx.draw_networkx_labels(G, pos=pos_dict, labels=dist_dict, font_size=max(6,int(node_size / 75)))
    
    if extra_annotations is not None:
      #New modification for optional annotations on the tree here.
      for node, (x, y) in pos_dict.items():
          #print("Node:", node)
          #First two are the positions of the extra text, the third is the actual text to add.
          val = 0
          if extra_dict[node] != 0.0:
             val = extra_dict[node]

          plt.text(x, y + 0.05, val, horizontalalignment='center', fontsize=max(6,int(node_size / 75)), bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2'))

    if save:
        if save_name is None:
            save_name = str(datetime.now())
        plt.savefig("savefiles/images/"+save_name+"_tree.png")

    plt.show()








def elbow_plot(elbow_data, names, method_names, elbow_n):
    for d, data in enumerate(elbow_data):
        curr_name = names[d]
        n = elbow_n[d]
        for i, series in enumerate(data):
            k = int(series[-1])
            print("k:", k)
            serie = series[:-1]
            maxval = np.max(serie)
            serie = [(s/maxval) for s in serie]
            print("len serie:", len(serie), "n", n)
            if len(serie) != n:
                serie += [0] * (n - len(serie) + 1)

            kvals = range(len(serie))
            kvals = [kval/len(serie) for kval in kvals]
            
            print("kval:", k)
            plt.gca().set_aspect('equal', adjustable='box')
            plt.plot(kvals, serie, label=curr_name+"_"+method_names[i], linewidth=2)
            if i == 0: #Only do this for the dc tree line
                plt.scatter(kvals[k], serie[k], edgecolors='red', facecolors='none', s=150, linewidth=2)  # s=100 controls dot size
        
        #break
    plt.xlabel('k-value')
    plt.ylabel('Cost')
    if len(names) == 1:
        plt.title("Dataset: " + names[i])
    else:
        plt.title('Elbow plot')
    plt.tick_params(left=False, right=False, top=False, bottom=False)
    plt.xticks([])  # Remove x-axis ticks
    plt.yticks([])  # Remove y-axis ticks
    plt.legend()
    plt.show()






def own_cmap(labels):
    new_labels = []
    for label in labels:
        if label % 30 == 0:
            new_labels.append("blue") #blue
        elif label % 30 == 1:
            new_labels.append("red") #red
        elif label % 30 == 2:
            new_labels.append("green") #green
        elif label % 30 == 3:
            new_labels.append("yellow") #yellow
        elif label % 30 == 4:
            new_labels.append("orange") #orange
        elif label % 30 == 5:
            new_labels.append("purple")
        elif label % 30 == 6:
            new_labels.append("brown")
        elif label % 30 == 7:
            new_labels.append("pink")
        elif label % 30 == 8:
            new_labels.append("cyan")
        elif label % 30 == 9:
            new_labels.append("magenta")
        elif label % 30 == 10:
            new_labels.append("lime")
        elif label % 30 == 11:
            new_labels.append("teal")
        elif label % 30 == 12:
            new_labels.append("lavender")
        elif label % 30 == 13:
            new_labels.append("beige")
        elif label % 30 == 14:
            new_labels.append("maroon")
        elif label % 30 == 15:
            new_labels.append("navy")
        elif label % 30 == 16:
            new_labels.append("olive")
        elif label % 30 == 17:
            new_labels.append("gold")
        elif label % 30 == 18:
            new_labels.append("silver")
        elif label % 30 == 19:
            new_labels.append("coral")
        elif label % 30 == 20:
            new_labels.append("salmon")
        elif label % 30 == 21:
            new_labels.append("plum")
        elif label % 30 == 22:
            new_labels.append("violet")
        elif label % 30 == 23:
            new_labels.append("khaki")
        elif label % 30 == 24:
            new_labels.append("ivory")
        elif label % 30 == 25:
            new_labels.append("lightcoral")
        elif label % 30 == 26:
            new_labels.append("aquamarine")
        elif label % 30 == 27:
            new_labels.append("darkkhaki")
        elif label % 30 == 28:
            new_labels.append("steelblue")
        elif label % 30 == 29:
            new_labels.append("turquoise")
    return new_labels
        


