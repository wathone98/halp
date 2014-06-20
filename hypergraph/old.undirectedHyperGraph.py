from __future__ import absolute_import

from .hypergraph import HyperGraph
from copy import deepcopy

from .node import Node
from .hyperedge import Hyperedge, UndirectedHyperedge
import numpy as np
from numpy import linalg
import random

'''----------------------- UnDirected HyperGraph ---------------------------'''


class UndirectedHyperGraph(HyperGraph):

    @property
    def nodeIdList(self):
        '''
        Returns the name of the nodes
        '''
        return self._nodeIdList

    @nodeIdList.setter
    def nodeIdList(self, value):
        '''
        Sets the name of the nodes
        '''
        self._nodeIdList = value

    @property
    def H(self):
        '''
        Returns the incidence matrix
        '''
        return self._incidenceMatrix

    @H.setter
    def H(self, value):
        '''
        Stores the incidence matrix
        '''
        self._incidenceMatrix = value

    @property
    def edgeWeight(self):
        '''
        Returns a diagonal matrix containing the hyperedge weight
        '''
        return self._edgeWeight

    @edgeWeight.setter
    def edgeWeight(self, value):
        '''
        Stores a diagonal matrix containing the hyperedge weight
        '''
        self._edgeWeight = value

    def __init__(self, nodes=set(), hyperedges=set()):
        HyperGraph.__init__(self, nodes, hyperedges)
        self._nodeIdList = {}
        self._incidenceMatrix = []
        self._edgeWeight = []

    def printGraph(self):
        i = 1
        for h in self._hyperedges:
            print(
                "Edge {}: Nodes: {}, weight: {}".format(i, h.nodes, h.weight))
            i += 1

    def add_hyperedgeByNames(self, nodes=set(), weight=0):
        '''
        Adds a hyperedge to the graph by node names.
        '''
        # Create hypergraph from current line
        hyperedge = UndirectedHyperedge(set(), weight)

        # Read edge nodes
        for n in nodes:
            node = self.get_node_by_name(n)
            if (node is None):
                node = Node(n)
                self.add_node(node)
            hyperedge.nodes.add(node)

        self.add_hyperedge(hyperedge)

    def read(self, fileName, sep='\t', delim=','):
        '''
            Read an undirected hypergraph from file FileName
            each row is a hyperEdge.
            nodes and weight are separated by "sep"
            nodes within a hyperedge are separated by "delim"
        '''
        fin = open(fileName, 'r')

        # read first header line
        fin.readline()
        i = 1
        for line in fin.readlines():
            line = line.strip('\n')
            if line == "":
                continue   # skip empty lines
            words = line.split(sep)
            if not (1 <= len(words) <= 2):
                raise Exception('File format error at line {}'.format(i))
            i += 1
            nodes = words[0].split(delim)
            try:
                weight = float(words[1].split(delim)[0])
            except:
                '''
                --yaserkl
                The default weight should be 1 otherwise if it's zero it means
                that node is disconnected to this hyperedge
                '''
                weight = 1

            # Create hypergraph from current line
            self.add_hyperedge(nodes, weight)
        fin.close()

    def write(self, fileName, sep='\t', delim=','):
        '''
            write an undirected hypergraph to file FileName
            each row is a hyperEdge.
            Tail, head and weight are separated by "sep"
            nodes within a hypernode are separated by "delim"
        '''
        fout = open(fileName, 'w')

        # write first header line
        fout.write("Edge" + sep + "weight\n")

        for e in self.hyperedges:
            line = ""
            for n in e.nodes:
                line += n.name + delim
            line = line[:-1]    # remove last extra delim
            line += sep + str(e.weight) + "\n"
            fout.write(line)
        fout.close()

    '''
    NOTE: This is a naive way to implement this matrix.
          A better approach would be to use a sparce matrix.
    THIS IS THE MAIN FUNCTION IN THIS CLASS, EVERY TIME YOU CHANGE
    THE HYPERGRAPH YOU SHOULD CALL THIS FUNCTION TO GET THE CORRECT
    PROPERTIES OF HYPERGRAPH

    This function sets the following variable in this class:
    (I)   incidence matrix (self.H): contains the |V| by |E| incidence matrix
    (II)  nodeId list (self.nodeIdList): contains the mapping of each node name
          to a unique integer value (id)
          Note: This is a neccessary variable in both UndirectedGraph and
                DirectedGraph since every time that you wanna access the
                self.nodes and self.hyperedges variables, the order of nodes
                and hyperedges change. This is because of the way Python
                handles the Set and the only way to make sure that we are
               keeping track of the orders correctly is to track them, manually
    (III) edge weight (self.edgeWeight): contains the weights of each hyperedge
    '''
    def getIncidenceMatrix(self):
        edgeNumber = len(self.hyperedges)
        nodeNumber = len(self.nodes)

        incidenceMatrix = np.zeros((nodeNumber, edgeNumber), dtype=int)
        hyperedgeId = 0
        nodeId = 0
        self.nodeIdList = {}
        self.edgeWeight = np.zeros(edgeNumber, dtype=int)
        for e in self.hyperedges:
            for n in e.nodes:
                if n.name not in self.nodeIdList:
                    self.nodeIdList[n.name] = nodeId
                    nodeId = nodeId + 1
                incidenceMatrix[self.nodeIdList.get(n.name)][hyperedgeId] = 1
            self.edgeWeight[hyperedgeId] = e.weight
            hyperedgeId = hyperedgeId + 1
        self.H = incidenceMatrix

    '''
        Returns a diagonal matrix containing the node degrees
        which is basically the summation of the weights of each
        node's incident edges
    '''
    def getDiagonalNodeMatrix(self):
        if self.H.shape == (0, 0):
            self.getIncidenceMatrix(self)
        nodeNumber = len(self.nodes)
        edgeNumber = len(self.hyperedges)
        degrees = np.zeros(nodeNumber, dtype=int)
        for row in range(nodeNumber):
            for col in range(edgeNumber):
                if self.H[row][col] == 1:
                    degrees[row] = degrees[row] + self.edgeWeight[col]
        return np.diag(degrees)

    '''
        Returns a diagonal matrix containing the hyperedge weights
    '''
    def getDiagonalWeightMatrix(self):
        if self.H.shape == (0, 0):
            self.getIncidenceMatrix(self)
        return np.diag(self.edgeWeight)

    '''
        Returns a diagonal matrix containing the hyperedge degrees
    '''
    def getDiagonalEdgeMatrix(self):
        if self.H.shape == (0, 0):
            self.getIncidenceMatrix(self)
        degrees = np.sum(self.H, axis=0)
        return np.diag(degrees)

    '''
        Creates the transition matrix for the random walk
    '''
    def randomWalkMatrix(self):
        D_e = self.getDiagonalEdgeMatrix()
        D_v = self.getDiagonalNodeMatrix()
        W = self.getDiagonalWeightMatrix()
        D_v_inverse = linalg.inv(D_v)
        D_e_inverse = linalg.inv(D_e)
        H = self.H
        H_transpose = H.transpose()
        P = np.dot(D_v_inverse, H)
        P = np.dot(P, W)
        P = np.dot(P, D_e_inverse)
        P = np.dot(P, H_transpose)
        return P

    '''
        Creates a random vector as the starting point for doing the random walk
    '''
    def createRandomStarter(self):
        nodeNumber = len(self.nodes)
        pi = np.zeros(nodeNumber, dtype=float)
        for i in range(nodeNumber):
            pi[i] = random.random()
        summation = np.sum(pi)
        for i in range(nodeNumber):
            pi[i] = pi[i] / summation
        return pi

    '''
        Finds the stationary distribution of a hypergraph
    '''
    def stationaryDistribution(self, P):
        nodeNumber = len(self.nodes)
        pi = self.createRandomStarter()
        pi_star = self.createRandomStarter()
        while not self.converged(pi_star, pi):
            pi = pi_star
            pi_star = np.dot(pi, P)
        return pi_star

    '''
        Checks whether the stationary distribution converged
    '''
    def converged(self, pi_star, pi):
        nodeNumber = pi.shape[0]
        for i in range(nodeNumber):
            if pi[i] - pi_star[i] > 10e-5:
                return False
        return True

    '''
        Returns the square root of a given diagonal matrix
    '''
    def diagonal_matrix_sqrt(self, D):
        return np.diagflat(np.sqrt(np.diag(D)))

    '''
        Finds the Normalized Laplacian Matrix
    '''
    def normalizedLaplacian(self):
        nodeNumber = len(self.nodes)
        D_e = self.getDiagonalEdgeMatrix()
        D_v = self.getDiagonalNodeMatrix()
        D_v_sqrt_inverse = np.real(linalg.inv(self.diagonal_matrix_sqrt(D_v)))
        D_e_inverse = linalg.inv(D_e)
        W = self.getDiagonalWeightMatrix()
        H = self.H
        H_transpose = H.transpose()
        Theta = np.dot(D_v_sqrt_inverse, H)
        Theta = np.dot(Theta, W)
        Theta = np.dot(Theta, D_e_inverse)
        Theta = np.dot(Theta, H_transpose)
        Theta = np.dot(Theta, D_v_sqrt_inverse)
        I = np.eye(nodeNumber)
        Delta = np.subtract(I, Theta)
        return Delta

    '''
        Finds the index of second minimum value in a list
    '''
    def findSecondMinIndex(self, x):
        import operator
        min_index, min_value = min(enumerate(x), key=operator.itemgetter(1))
        max_index, max_value = max(enumerate(x), key=operator.itemgetter(1))
        second_min = max_value
        second_min_index = max_index
        for i in range(len(x)):
            if x[i] > min_value and x[i] < second_min:
                second_min = x[i]
                second_min_index = i
        return second_min_index

    '''
        Applies the Normalized MinCut algorithm.
        The result of this algorithm is a bipartition
        The return value is a two dimensional array containing
        the node names for the first and second partition
    '''

    def minCut(self, threshold):
        '''
        TODO: make sure that the hypergraph is connected
        '''
        Delta = self.normalizedLaplacian()
        eigens = linalg.eig(Delta)
        eigenValues = eigens[0]
        secondMinIndex = self.findSecondMinIndex(eigenValues)
        eigenVectors = eigens[1]
        secondEigenVector = eigenVectors[:, secondMinIndex]
        partitionIndex = [
            i for i in range(
                len(secondEigenVector)) if secondEigenVector[i] >= threshold]
        Partition = [list() for x in range(2)]
        for (key, value) in list(self.nodeIdList.items()):
            if value in partitionIndex:
                Partition[0].append(key)
            else:
                Partition[1].append(key)
        return Partition