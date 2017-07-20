import dbConnect
import numpy as np
import datetime
from id3 import Id3Estimator, export_graphviz
from decimal import Decimal
from sklearn import tree
from sklearn import grid_search
import pandas as pd
from sklearn.model_selection import cross_val_score

class DecisionTrees():

    def __init__(self, secure_data=False):
        self.secure_data = secure_data
        self.private_only = False

    def secureDataClassifier(self):
        if self.secure_data:
            self.private_only=True

    def get_data_and_labels(self):
        db_connector = dbConnect.DBConnector()
        cpu_features = db_connector.get_cpu_features()
        cpu_features_list = [[row[0], (row[1]-datetime.datetime.utcfromtimestamp(0)).total_seconds()*1000.0, row[2]] for row in cpu_features]
        feature_names = ["vm_id_map", "timestamp", "cpu_usage"]
        X = np.array(cpu_features_list)
        Y = np.array([row[-1] for row in cpu_features])
        return (X,Y)

    def cpuUsageDecisionTree(self):
        (X,Y) = self.get_data_from_csv()
        feature_names = ["vm_id_map", "timestamp_new", "cpu_usage_percent", "admin_historic_decision_cpu"]
        clf = Id3Estimator()
        clf.fit(X, Y, check_input=True)
        export_graphviz(clf.tree_, "out.dot", feature_names)

    def get_epoch_time_from_datetime(self,row):
        return (datetime.datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M")-datetime.datetime.utcfromtimestamp(0)).total_seconds()*1000.0

    def get_class_hour_minute(self, row):
        t = datetime.datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M")
        return float(t.hour)

    def flip_label(self, df):
        for index, row in df.iterrows():
            if row['vm_id_map'] == 4:
                print "found !" , row["vm_id_map"], row["hour_minute_class"]
                print row["admin_historic_decision_cpu"]
                row["admin_historic_decision_cpu"] = row["admin_historic_decision_cpu"] * -1
                print row["admin_historic_decision_cpu"]

    def get_fake_label(self,row):
        if self._target_value=='cpu':
            self.usage_percent='cpu_usage_percent'
        elif self._target_value=='memory':
            self.usage_percent='memory_usage_percent'
        elif self._target_value=='disk':
            self.usage_percent='disk_usage_percent'
        label = 0
        if row["vm_id_map"] == 4:
            if row[self.usage_percent] > 80:
                label = -1
            if row[self.usage_percent]  < 10:
                label = 1
        else:
            if row[self.usage_percent] > 80:
                label = 1
            if row[self.usage_percent]  < 10:
                label = -1
        return label

    def get_data_from_csv(self):
        df = pd.read_csv("usage_data.csv", header=0)
        #print df["timestamp"]
        admin_feature_name = 'admin_historic_decision_'+self._target_value
        print df.dtypes
        df[admin_feature_name] = df.apply(self.get_fake_label, axis =1 )
        df.to_csv("fake_data.csv", index=False)
        #df["timestamp_new"] = df.apply(self.get_epoch_time_from_datetime, axis =1)
        df["hour_minute_class"] = df.apply(self.get_class_hour_minute, axis =1)
        #self.flip_label(df)
        feature_names = ["vm_id_map", "hour_minute_class", admin_feature_name]
        df = df[feature_names]
        X = df[feature_names[:-1]]

        Y = df[admin_feature_name]
        #print X
        #print Y
        df.to_csv("fake_data.csv")
        return (X,Y)

    def decision_cross_val(self):
        (X,Y) = self.get_data_from_csv()
        params= {'max_depth': range(3,20)}
        clf_tree = tree.DecisionTreeClassifier()
        clf_tree.fit(X,Y)
        tree.export_graphviz(clf_tree, out_file=self._target_value+'_tree.dot')
        return clf_tree

    def cpu_decision_cross_val(self):
        self._target_value='cpu'
        return self.decision_cross_val()
        #(X,Y) = self.get_data_from_csv()
        #params= {'max_depth': range(3,20)}
        #clf_tree = tree.DecisionTreeClassifier()
        #clf = grid_search.GridSearchCV(clf_tree, params, n_jobs=4)
        #clf.fit(X = X , y = Y)
        #tree_model = clf.best_estimator_
        #print clf.best_score_, clf.best_params_
        #clf_tree.fit(X,Y)
        #print clf_tree.predict([3, 21.4])
        #print(cross_val_score(clf_tree, X, Y, cv=10))
        #tree.export_graphviz(clf_tree, out_file='cpu_tree.dot')

    def memory_decision_cross_val(self):
        self._target_value='memory'
        return self.decision_cross_val()

    def disk_decision_cross_val(self):
        self._target_value='disk'
        return self.decision_cross_val()

def create_prediction_table():
    dt = DecisionTrees()
    cpu_tree = dt.cpu_decision_cross_val()
    memory_tree = dt.memory_decision_cross_val()
    disk_tree = dt.disk_decision_cross_val()
    prediction_table = []
    for j in range(1,5):
        for i in range(0, 24):
            cpu_prdct = cpu_tree.predict([j, i])
            memory_prdct = memory_tree.predict([j, i])
            disk_prdct = disk_tree.predict([j, i])
            prediction_table.append(['vm_%d' %(j), i, cpu_prdct[0], memory_prdct[0], disk_prdct[0]])
            print prediction_table
    return prediction_table




if __name__ == '__main__':
    create_prediction_table()
