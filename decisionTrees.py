import dbConnect
import numpy as np
from id3 import Id3Estimator, export_graphviz

class DecisionTrees():

    def __init__(self, secure_data=False):
        self.secure_data = secure_data
        self.private_only = False

    def secureDataClassifier(self):
        if self.secure_data:
            self.private_only=True

    def cpuUsageDecisionTree(self):
        db_connector = dbConnect.DBConnector()
        cpu_features = db_connector.get_cpu_features()
        cpu_features_list = [row[:3] for row in cpu_features]
        feature_names = ["vm_id", "timestamp", "cpu_usage"]
        X = np.array(cpu_features_list)
        Y = np.array([str(row[-1]) for row in cpu_features])
        print X
        print Y
        clf = Id3Estimator()
        clf.fit(X, Y, check_input=True)
        #export_graphviz(clf.tree_, "out.dot", feature_names)

if __name__ == '__main__':
    dt = DecisionTrees()
    dt.cpuUsageDecisionTree()
