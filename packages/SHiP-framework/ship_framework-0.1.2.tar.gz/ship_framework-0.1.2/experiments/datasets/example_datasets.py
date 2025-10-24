import numpy as np
import os
from .abstract_datasets import AbstractDatasets, standardize

from urllib.request import urlopen
from scipy.io import arff
from io import StringIO


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
DATASETS_FOLDER = f"{CURRENT_DIRECTORY}"


### Datasets ###


class Datasets(AbstractDatasets):
    d31 = "d31"
    compound_left = "compound_left"
    # aggregation_2 = "aggregation_2"
    noisy = "noisy"
    
    adipose = "adipose"
    airway= "airway"
    lactate = "lactate"

    jain= "jain"
    pathbased = "pathbased"
    # spiral = "spiral"
    boxes3 = "boxes3"

    def load_dataset(self):
        match self:
            case self.d31:
                return load_txt_datasets("d31")
            case self.compound_left:
                X, l = download_dataset("compound")
                return X[142:], l[142:]
            # case self.aggregation_2:
            #     return download_dataset("aggregation")
            case self.noisy:
                X = np.load('datasets/data/Synthetic/clusterable_data.npy')
                from sklearn.cluster import HDBSCAN
                hdbscan = HDBSCAN(min_cluster_size=15)
                l = hdbscan.fit(X).labels_
                return X, l
            case self.adipose:
                # https://singlecell.broadinstitute.org/single_cell/study/SCP1376/a-single-cell-atlas-of-human-and-mouse-white-adipose-tissue#study-download
                return load_cell_dataset("MmMes.umap.scp") #n=14947
            case self.airway:
                # https://singlecell.broadinstitute.org/single_cell/study/SCP64/a-single-cell-atlas-of-the-airway-epithelium-reveals-the-cftr-rich-pulmonary-ionocyte#study-visualize
                return load_cell_dataset("xy_mouse_all_v2") #n=14163
            case self.lactate: 
                # https://singlecell.broadinstitute.org/single_cell/study/SCP1671/cellular-and-transcriptional-diversity-over-the-course-of-human-lactation#study-visualize
                return load_cell_dataset("cluster_epi__umap") #n=39825
            case self.jain:
                return load_txt_datasets("jain")
            case self.pathbased:
                return load_txt_datasets("pathbased")
            # case self.spiral:
            #     return load_txt_datasets("spiral")
            case self.boxes3:
                # https://www.kaggle.com/datasets/joonasyoon/clustering-exercises/data
                return load_txt_datasets("boxes3")
            case _:
                raise AttributeError

    def standardize_dataset(self, X, l):
        return standardize(X, l, axis=0)


def download_dataset(dataset_name):
    github_url = f"https://raw.githubusercontent.com/deric/clustering-benchmark/master/src/main/resources/datasets/artificial/{dataset_name}.arff"
    arff_data = urlopen(github_url).read().decode("utf-8")
    arff_data = arff_data.replace("noise", "-1")
    arff_data_file_object = StringIO(arff_data)
    data, _meta = arff.loadarff(arff_data_file_object)
    np_data = np.array(data.tolist(), dtype=float)
    X, l = np.hsplit(np_data, [-1])
    return X, l.reshape(-1)


def load_txt_datasets(dataset):
    '''
    Currently only works for 2d points with or without ground truth labels.
    '''
    points, labels = [],[]

    data = []
    path = os.path.join("datasets", "data", "Synthetic", dataset + ".txt")

    with open(path, "r") as data:
        for point in data:
            #print("line:", point)
            dims = point.strip().split()
            if len(dims)== 1:
                dims = point.split(",")
                print("dims:", dims)
                points.append(list(map(float, dims[:-1])))
                labels.append(int(dims[2]))
                print("label:", labels[0])
            if len(dims) == 3:
                points.append(list(map(float, dims[:-1])))
                labels.append(int(dims[2]))
            else:
                points.append(list(map(float, dims)))
    if len(labels) != len(points):
        labels = np.zeros(len(points))
    return np.array(points), np.array(labels)



def load_cell_dataset(name):
    import pandas as pd
    path = os.path.join("datasets", "data", "Cells", name+".txt")
    data = pd.read_csv(path, sep='\t', header=[0,1]) #The single-cell datasets contain two rows of headers
    #print("cols:", data.columns)
    points = data[["X","Y"]].to_numpy()
    labels = []
    if len(data.columns) > 3: #The format for the single-cell datasets are ID, X, Y, Group* - if Group exists.. So we just check if there is a fourth row or not. 
        labels = data.iloc[:,3].factorize()[0]
    else:
        labels = data.iloc[:,0].map(lambda str: str.split('-')[0]).factorize()[0]
        # labels = np.arange(len(points))
    points = np.ascontiguousarray(points) #This is needed because the pandas dataframe to numpy returns column major memory allocation.

    return points, labels

