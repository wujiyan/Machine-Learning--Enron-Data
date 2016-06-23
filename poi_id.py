import pickle
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.feature_selection import SelectKBest
from sklearn.decomposition import PCA
from sklearn.feature_selection import chi2
from sklearn.preprocessing import MinMaxScaler
from sklearn import cross_validation
from sklearn import tree
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
import sklearn.pipeline

#define a function to make scatter plot
def scatter_plot(data, xname, yname, title, color = "blue"):
    ## input:
    # data: original dataset
    # xname: variable name used as x axis
    # yname: variable name used as y aixs
    # title: title of the plot
    ## output: scatterplot saved in local storage. 
    plt.figure()
    x = data[xname]
    y = data[yname]
    plt.scatter(x,y,c = color)
    plt.xlabel(xname)
    plt.ylabel(yname)
    plt.title(title.split(".")[0])
    plt.savefig(title, bbox_inches='tight')

#read dataset from local
with open("final_project_dataset.pkl", "r") as data_file:
    rawdata = pickle.load(data_file)

mydata = rawdata
#transfer data from dictionary to data frame. refer 1
mydata_df = pd.DataFrame.from_dict(data = mydata, orient = 'index')

print("show the list of column names:")
print(list(mydata_df.columns.values))
print("total number of data points:")
print(len(mydata))
#exploration

#plot relationship between total stock value and total payments
scatter_plot(mydata_df, "salary",
             "bonus","salary_vs_bonus.png")

#drop TOTAL, the outlier, and scatter again
#mydata.pop('TOTAL')
#mydata_df1 = pd.DataFrame.from_dict(data = mydata, orient = 'index')
mydata_df1 = mydata_df.drop("TOTAL")
scatter_plot(mydata_df1, "salary",
             "bonus","salary_vs_bonus2.png", color = mydata_df1['poi'])
print("scatter plot: salary vs bonus, has been done")

#plot scatter plot: total payments vs expenses
mydata_df_new = mydata_df1.drop("LAY KENNETH L")
scatter_plot(mydata_df_new, "total_payments",
             "expenses","total_payments_vs_expenses.png", color = mydata_df_new['poi'])
print("scatter plot: total_payments_vs_expenses, has been done")

#plot scatter plot: to_messages vs from_messages
scatter_plot(mydata_df1, "to_messages",
             "from_messages","to_messages_vs_from_messages.png", color = mydata_df1['poi'])
print("scatter plot: to_messages_vs_from_messages, has been done")

#add new features, fraction of sending to poi and fraction of receiving from poi
def create_feature(data, lab1, lab2, new_lab):
    ## input:
    # data: original dataset
    # lab1: variable name in the original dataset that would be used
    # lab2: variable name in the original dataset that would be used
    # new_lab: new variable name
    ## output: new dataset with the new variable
    for names in data.keys():
        if data[names][lab1] == 'NaN' or data[names][lab2] == 'NaN':
            data[names][new_lab] = 0
        else:
            data[names][new_lab] = float(data[names][lab1])/float(data[names][lab2])
    return data

mydata = create_feature(mydata, "from_this_person_to_poi",\
                        "from_messages","fraction_to_poi")
mydata = create_feature(mydata, "from_poi_to_this_person",\
                        "to_messages", "fraction_from_poi")
print("features have been added")

#plot scatter plot: fraction to poi vs fraction from poi
mydata_df2 = pd.DataFrame.from_dict(data = mydata, orient = 'index')
scatter_plot(mydata_df2, "fraction_to_poi",
             "fraction_from_poi","fraction_to_poi_vs_fraction_from_poi.png", color = mydata_df2['poi'])
print("scatter plot: fraction_to_poi_vs_fraction_from_poi, has been done")

#count NaN number
mydata_df3 = mydata_df2.drop(["email_address",'poi','fraction_from_poi','fraction_to_poi'],1)
missing_number = {}
for column in mydata_df3.columns.values:
    v = len(mydata_df3[mydata_df3[column] == 'NaN'])
    missing_number[column] = v
missing_number_df = pd.DataFrame.from_dict(data = missing_number, orient = 'index')
print("show the number of missing values:")
print(missing_number_df)

#set up feature list. include all first
#this is the original features
features_list = ['salary','deferral_payments','deferred_income','director_fees',
                 'exercised_stock_options','expenses',
                 'fraction_from_poi','fraction_to_poi','from_messages',
                 'from_poi_to_this_person','from_this_person_to_poi',
                 'loan_advances','long_term_incentive','other','poi',
                 'restricted_stock','restricted_stock_deferred','salary',
                 'shared_receipt_with_poi','to_messages','total_payments',
                 'total_stock_value']
#this is the simplified features. How they were selected are explained in pdf report.
features_list_sim = ['salary', 'exercised_stock_options','expenses',
                 'fraction_from_poi','fraction_to_poi',
                 'long_term_incentive','other','poi','restricted_stock',
                 'salary','shared_receipt_with_poi',
                 'total_payments','total_stock_value']
#change data format, shifting NaN into 0. remove keys without valid values
#extract poi labels and features
def change_format(data, features):
    ##input: 
    # data: original data
    # features: features that you wish to choose
    ##output: 
    # dataset 1: pure data without poi
    # dataset 2: poi label
    ## its function is to split into poi label and other data with selected features.
    final_list = []
    label_list = []
    for names in data.keys():
        temp_list = []
        for feature in features:
            try:
                data[names][feature]
            except KeyError:
                print "error:",names,feature,"not present"
                return
            value = data[names][feature]
            if feature == "poi":      # seperate poi label 
                label_list.append(float(value))
                continue
            elif value == "NaN":     #change NaN value into 0
                value = 0
            elif value < 0:
                value = -value     #change negative values into positive ones.
            temp_list.append(float(value))
        final_list.append(np.array(temp_list))
    return np.array(final_list), np.array(label_list)

features_data, labels_data= change_format(mydata, features_list)
features_data_sim, labels_data_sim = change_format(mydata, features_list_sim)

#scale data
scaler = MinMaxScaler()
mydata_scl = scaler.fit_transform(features_data)
mydata_scl_sim = scaler.fit_transform(features_data_sim)

#select top 10 features having the closest relationship with poi label
def select_best_features(features_data, labels, features_list, number = 10):
    f1 = SelectKBest(chi2, k = number)
    f2 = f1.fit_transform(features_data, labels)
    scores = f1.scores_
    dic = {}
    features_list.remove("poi")
    for feature, score in zip(features_list, scores):
        dic[feature] = score
    new_dic = sorted(dic.iteritems(), key=lambda d:d[1], reverse = True)
    return f2, new_dic[0:12]

best_features, best_data= select_best_features(mydata_scl, labels_data, features_list)
best_features_sim, best_data_sim = select_best_features(mydata_scl_sim, labels_data_sim, features_list_sim)
print("show features by score")
print(list(best_data_sim))

#features I selected
features = ["poi","fraction_to_poi","fraction_from_poi","shared_receipt_with_poi"]

clf1 = RandomForestClassifier(random_state = 50,min_samples_split=5)
clf2 = GaussianNB()
clf3 = tree.DecisionTreeClassifier(random_state = 6,min_samples_split = 6)
#get pure data and poi labels
feature, labels = change_format(mydata, features)
#scale the data
scaler = MinMaxScaler()
feature_scl = scaler.fit_transform(feature)
#split data into train and test set.
features_train, features_test, labels_train, labels_test = \
cross_validation.train_test_split(feature_scl, labels, test_size=0.3, random_state = 134)

#define a function to train and test, returning performance report
def report(clf, features_train, features_test, labels_train, labels_test):
    ##input: 
    # clf: classifier you set
    ##output: accuracy, recall, precision and f1 score you have got.
    steps = [('classifier', clf)]

    pipeline = sklearn.pipeline.Pipeline(steps)

    pipeline.fit(features_train, labels_train)

    y_prediction = pipeline.predict( features_test )

    report = sklearn.metrics.classification_report( labels_test, y_prediction )

    return report

#print out report
print("Random Forest Report")
print(report(clf1,features_train, features_test, labels_train, labels_test))
print("Gaussian Naive Base Report")
print(report(clf2,features_train, features_test, labels_train, labels_test))
print("Decision Tree Report")
print(report(clf3,features_train, features_test, labels_train, labels_test))

#Given selected features, complete labels and feature extraction, processing
#PCA, for the following classification.
#features = ["fraction_to_poi", "exercised_stock_options","poi"]
#def clf_prepare(data, features):
#    feature, labels = change_format(data, features)
#    scaler = MinMaxScaler()
#    feature_scl = scaler.fit_transform(feature)
#    pca = PCA(n_components = len(features)-1)
#    scl = pca.fit_transform(feature_scl)
#    scores = pca.explained_variance_ratio_
#    return scl, labels, scores
#feature_scl, labels, scores = clf_prepare(mydata, features)

#split samples into training group and test group
#features_train, features_test, labels_train, labels_test = \
#cross_validation.train_test_split(feature_scl, labels, test_size=0.3, random_state = 1)

#deploy machine learning
#define a function, returning accuracy, precision and recall rate
#def ml_basic(clf, features_train, features_test, labels_train, labels_test):
#    clf.fit(features_train, labels_train)
#    pred = clf.predict(features_test)
#    score = clf.score(features_test, labels_test)
#    precision = precision_score(labels_test, pred)
#    recall = recall_score(labels_test, pred)
#    return score, precision, recall

#def ml_deploy(features_train, features_test, labels_train, labels_test):
#    ml_result = {}
#    tem1 = {}
#    tem2 = {}
#    tem3 = {}
#    tem4 = {}
#    #decision tree
#    clf1 = tree.DecisionTreeClassifier(random_state = 13)
#    accuracy, precision, recall = ml_basic(clf1,features_train, features_test, labels_train, labels_test)
##    tem1["accuracy"] = accuracy
 #   tem1["precision"] = precision
#   tem1["recall"] = recall
#    ml_result['decision_tree'] = tem1
#    #gaussian naive base
#    clf2 = GaussianNB()
#    accuracy, precision, recall = \
#              ml_basic(clf2,features_train, features_test, labels_train, labels_test)
#    tem2["accuracy"] = accuracy
#    tem2["precision"] = precision
#    tem2["recall"] = recall
#    ml_result['gaussianNB'] = tem2
#    #random forest
#    clf3 =  RandomForestClassifier(random_state = 10)
#    accuracy, precision, recall = \
#              ml_basic(clf3,features_train, features_test, labels_train, labels_test)
#    tem3["accuracy"] = accuracy
#    tem3["precision"] = precision
#    tem3["recall"] = recall
#    ml_result['random_forest'] = tem3
#    #support vector machine
#    clf4 = SVC()
#    accuracy, precision, recall = \
#              ml_basic(clf4,features_train, features_test, labels_train, labels_test)
#    tem4["accuracy"] = accuracy
#    tem4["precision"] = precision
#    tem4["recall"] = recall
#    ml_result['svm'] = tem4
#    
#    return ml_result

#ml_result = ml_deploy(features_train, features_test, labels_train, labels_test)

#test another group of features
#features = ["fraction_to_poi", "total_payments","poi"]
#feature_scl, labels, scores = clf_prepare(mydata, features)
#features_train, features_test, labels_train, labels_test = \
#cross_validation.train_test_split(feature_scl, labels, test_size=0.3, random_state = 1)
#ml_result = ml_deploy(features_train, features_test, labels_train, labels_test)

#test another group of features
#features = ["fraction_to_poi", "total_payments","total_stock_value","poi"]
#feature_scl, labels, scores = clf_prepare(mydata, features)
#features_train, features_test, labels_train, labels_test = \
#cross_validation.train_test_split(feature_scl, labels, test_size=0.3, random_state = 1)
#ml_result = ml_deploy(features_train, features_test, labels_train, labels_test)

#test another group of features
#features = ["fraction_to_poi", "salary","poi"]
#feature_scl, labels, scores = clf_prepare(mydata, features)
##features_train, features_test, labels_train, labels_test = \
#cross_validation.train_test_split(feature_scl, labels, test_size=0.3, random_state = 1)
#ml_result = ml_deploy(features_train, features_test, labels_train, labels_test)
##ml_result_df = pd.DataFrame.from_dict(data = ml_result, orient = 'index')
#print("features selected")
#print(features)
#print("show metrics")
#print(ml_result_df)
#test another group of features
#features = ["fraction_to_poi", "salary","shared_receipt_with_poi","poi"]
#feature_scl, labels, scores = clf_prepare(mydata, features)
#features_train, features_test, labels_train, labels_test = \
#cross_validation.train_test_split(feature_scl, labels, test_size=0.3, random_state = 1)
#ml_result = ml_deploy(features_train, features_test, labels_train, labels_test)

### dump your classifier, dataset and features_list so
### anyone can run/check your results
clf = clf3.fit(features_train, labels_train)
data_dict = mydata
pickle.dump(clf, open("my_classifier.pkl", "w") )
pickle.dump(data_dict, open("my_dataset.pkl", "w") )
pickle.dump(features, open("my_feature_list.pkl", "w") )
