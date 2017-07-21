#import dbConnect
import datetime

import numpy as np
import pandas as pd
from id3 import Id3Estimator, export_graphviz
from sklearn import tree
from sklearn.metrics import accuracy_score
from sklearn.utils import shuffle
from sklearn.metrics import confusion_matrix
import random

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

    def get_test_and_train_data(self, X, Y):
        size  = len(X.index)
        boundary = int(size * 0.9)
        return (X[:boundary], X[boundary:], Y[:boundary], Y[boundary:])

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

    def set_self_usage_percent(self):
        if self._target_value=='cpu':
            self.usage_percent='cpu_usage_percent'
        elif self._target_value=='memory':
            self.usage_percent='memory_usage_percent'
        elif self._target_value=='disk':
            self.usage_percent='disk_usage_percent'


    def get_fake_label(self,row):
        self.set_self_usage_percent()
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

    def get_mock_label_by_timestamp(self, row):
        #print(df)
        label = 0
        if row["hour_minute_class"] < 18  and random.randint(0,3)%2 ==0 :
           label = 1
        elif row["hour_minute_class"] > 20 and random.randint(0,3)%2 ==0 :
            label = -1
        else :
            label = 0
        return label

    def mock_data(self):
        df = pd.read_csv("usage_data.csv", header=0)
        #admin_feature_name = 'admin_historic_decision_' + self._target_value
        # df[admin_feature_name] = df.apply(self.get_fake_label, axis =1 )
        df["hour_minute_class"] = df.apply(self.get_class_hour_minute, axis=1)
        label_list = ['admin_historic_decision_cpu', 'admin_historic_decision_memory', 'admin_historic_decision_disk']
        for label in label_list :
            df[label] = df.apply(self.get_mock_label_by_timestamp, axis=1)

        df.to_csv("df.csv")
        #df = self.get_mock_label_by_timestamp(df)

    def get_data_from_csv(self):
        df = pd.read_csv("usage_data.csv", header=0)
        admin_feature_name = 'admin_historic_decision_'+self._target_value
        #df[admin_feature_name] = df.apply(self.get_fake_label, axis =1 )
        df["hour_minute_class"] = df.apply(self.get_class_hour_minute, axis =1)
        label_list = ['admin_historic_decision_cpu', 'admin_historic_decision_memory', 'admin_historic_decision_disk']
        for label in label_list:
            df[label] = df.apply(self.get_mock_label_by_timestamp, axis=1)
        df[:-1].to_csv("fake_label_data.csv")
        feature_names = ["vm_id_map", "hour_minute_class", admin_feature_name]
        df = df[feature_names]
        #df[admin_feature_name] = df.apply(self.get_mock_label_by_timestamp, axis=1)
        #print df
        df = shuffle(df)
        X = df[feature_names[:-1]]
        Y = df[admin_feature_name]

        return (X,Y)

    def get_prediction_stats(self, test_Y, pred_Y):

        confusion_matrix_ = confusion_matrix(test_Y, pred_Y)
        accuracy_score_ = accuracy_score(test_Y, pred_Y)

        #print("confusion matrix ")
        #print (confusion_matrix_)

        return (accuracy_score_, confusion_matrix_ )

    def decision_cross_val(self):
        (X,Y) = self.get_data_from_csv()
        (train_X, test_X, train_Y, test_Y) = self.get_test_and_train_data(X, Y)
        #params= {'max_depth': range(3,20)}
        clf_tree = tree.DecisionTreeClassifier()
        clf_tree.fit(train_X,train_Y)
        #print("predicting for label ", self._target_value)
        pred_Y = clf_tree.predict(test_X)

        (accuracy_score_ , _) =self.get_prediction_stats(test_Y, pred_Y)
        tree.export_graphviz(clf_tree, out_file=self._target_value+'_tree.dot')
        return (clf_tree, test_X,  accuracy_score_, pred_Y)

    def cpu_decision_cross_val(self):
        self._target_value='cpu'
        return self.decision_cross_val()

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
            #print prediction_table
    return prediction_table


def get_prediction_table_with_test_data(vm_id):
    dt = DecisionTrees()
    (cpu_tree,test_X, accuracy_score_cpu, pred_Y_cpu) = dt.cpu_decision_cross_val()
    (_,_ , accuracy_score_mem, pred_Y_mem) = dt.memory_decision_cross_val()
    (_,_ , accuracy_score_disk, pred_Y_disk) = dt.disk_decision_cross_val()
    prediction_table =  np.column_stack([ test_X, pred_Y_cpu, pred_Y_disk, pred_Y_mem])
    accuracy_list = np.array([accuracy_score_cpu, accuracy_score_mem, accuracy_score_disk])

    #print ("accuracy for cpu, mem, disk ")
    #print(accuracy_list)
    #print("average accuracy is ")
    #print (np.mean(accuracy_list))
    #print ("actual predicted data ")
    #print(prediction_table)

    pd.DataFrame(data=prediction_table).to_csv("predict_data.csv")
    #return (prediction_table[prediction_table[0, :] == vm_id])
    return prediction_table


def get_switch_table(vm_id):
    prediction_table = get_prediction_table_with_test_data(vm_id)
    df = pd.DataFrame(data= prediction_table, columns=['vm_id', 'hour', 'cpu', 'mem', 'disk'])
    #print df
    df = df[df['vm_id'] == vm_id]

    #df = pd.read_csv("fake_predicted.csv")
    #print df
    cpu_bump = 0
    mem_bump =0
    disk_bump=0
    bump_data = []
    time_inst = df['hour'].iloc[0]
    reset = False
    #print(df.dtypes)
    for index, row in df.iterrows():
        #all three zeroes , no more changes needed ,
        #print(row)
        #print(vm_id, time_inst, cpu_bump, mem_bump, disk_bump)
        if (row['cpu'] == 0 and row['mem'] == 0 and row['disk'] == 0) == True :
            if reset == True :
                bump_data.append([vm_id, time_inst, cpu_bump, mem_bump, disk_bump])
                cpu_bump = 0
                mem_bump = 0
                disk_bump = 0
                #time_inst = row['hour']
                reset = False
        else :
            if reset==False and (row['mem'] !=0 or row['disk'] != 0 or row['cpu'] != 0):
                reset= True
                time_inst = row['hour']
            cpu_bump += row['cpu']
            mem_bump += row['mem']
            disk_bump += row['disk']
            #reset = True

    if reset== True:
        bump_data.append([vm_id, time_inst, cpu_bump, mem_bump, disk_bump])

    return bump_data
    #print df


if __name__ == '__main__':
    #create_prediction_table()
   # get_prediction_table_with_test_data(1)
    get_switch_table(4)
    #dt = DecisionTrees()
    #dt.mock_data()
