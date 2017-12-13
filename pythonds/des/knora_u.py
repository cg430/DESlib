# coding=utf-8

# Author: Rafael Menelau Oliveira e Cruz <rafaelmenelau@gmail.com>
#
# License: BSD 3 clause

import collections

import numpy as np

from pythonds.des.base import DES


# TODO Work on the weighted versions.
class KNORAU(DES):
    """k-Nearest Oracles Union (KNORAU).
    
    This method works selects all classifiers that correctly classified at least
    one sample belonging to the region of competence of the test sample x. Each 
    selected classifier has a number of votes equals to the number of samples in the
    region of competence that it predicts the correct label.

    Parameters
    ----------
    pool_classifiers : type, the generated_pool of classifiers trained for the corresponding
    classification problem.

    k : int (Default = 7), Number of neighbors used to estimate the competence of the base classifiers.

    DFP : Boolean (Default = False), Determines if the dynamic frienemy prunning is applied.

    with_IH : Boolean (Default = False), Whether the hardness level of the region of competence is used to decide
    between using the DS algorithm or the KNN for classification of a given query sample.

    safe_k : int (default = None), the size of the indecision region.

    IH_rate : float (default = 0.3), Hardness threshold. If the hardness level of the competence region is lower than
    the IH_rate the KNN classifier is used. Otherwise, the DS algorithm is used for classification.

    weighted : Boolean (Default = False), Determines whether the distance between neighbors and the query
    sample are used to weight the decision of each selected classifier. The outputs of the selected ensemble
    is therefore combined using a weighted majority voting scheme.

    aknn : Boolean (Default = False), Determines the type of KNN algorithm that is used. set
    to true for the A-KNN method.

    References
    ----------
    Ko, Albert HR, Robert Sabourin, and Alceu Souza Britto Jr. "From dynamic classifier selection to dynamic ensemble
    selection." Pattern Recognition 41.5 (2008): 1718-1731.   

    Britto, Alceu S., Robert Sabourin, and Luiz ES Oliveira. "Dynamic selection of classifiers—a comprehensive review."
    Pattern Recognition 47.11 (2014): 3665-3680.

    R. M. O. Cruz, R. Sabourin, and G. D. Cavalcanti, “Dynamic classifier selection: Recent advances and perspectives,”
    Information Fusion, vol. 41, pp. 195 – 216, 2018.
    """

    def __init__(self, pool_classifiers, k=7, DFP=False, with_IH=False, safe_k=None,
                 IH_rate=0.30,
                 aknn=False,
                 weighted=False):

        super(KNORAU, self).__init__(pool_classifiers, k, DFP=DFP, with_IH=with_IH, safe_k=safe_k, IH_rate=IH_rate,
                                     aknn=aknn)
        self.weighted = weighted
        self.name = 'k-Nearest Oracles Union'

    def estimate_competence(self, query):
        """In this method, the competence of the base classifiers is simply computed as the number of samples
        in the region of competence that it correctly classified.

        Returns an array containing the level of competence estimated.
        The size of the array is equals to the size of the generated_pool of classifiers.

        Parameters
        ----------
        query : array containing the test sample = [n_features]

        Returns
        -------
        competences : array = [n_classifiers] containing the competence level estimated
        for each base classifier
        """
        dists, idx_neighbors = self._get_region_competence(query)
        competences = np.zeros(self.n_classifiers)

        for clf_index in range(self.n_classifiers):
            # Check if the dynamic frienemy pruning (DFP) should be used used
            if self.mask[clf_index]:
                tmp = [self.processed_dsel[index][clf_index] for index in idx_neighbors]
                competences[clf_index] = np.sum(tmp)

        return competences.astype(dtype=int)

    def select(self, query):
        """Select the base classifiers for the classification of the query sample.

        Each base classifier can be selected more than once. The number of times a base classifier is selected (votes)
        is equals to the number of samples it correctly classified in the region of competence.

        Parameters
        ----------
        query : array containing the test sample = [n_features]

        Returns
        -------
        The predicted label of the query
        """
        weights = self.estimate_competence(query)
        # If all weights is equals to zero, it means that no classifier was selected. Hence, use all of them
        if all(weight == 0 for weight in weights):
            weights = np.ones(self.n_classifiers, dtype=int)
        votes = np.array([], dtype=int)
        for clf_idx, clf in enumerate(self.pool_classifiers):
            votes = np.hstack((votes, np.ones(weights[clf_idx], dtype=int) * clf.predict(query)[0]))

        return votes

    def classify_instance(self, query):
        """Predicts the label of the corresponding query sample.
        Returns the predicted label.

        The prediction is made aggregating the votes obtained by all selected base classifiers. The predicted label
        is the class that obtained the highest number of votes

        Parameters
        ----------
        query : array containing the test sample = [n_features]

        Returns
        -------
        The predicted label of the query
        """
        votes = self.select(query)
        counter = collections.Counter(votes)
        predicted_label = counter.most_common()[0][0]
        return predicted_label