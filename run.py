# Run as follows: `run.py method_name dataset_dir dataset_name`
# For example, `run.py nlm graph_closeness`
from __future__ import division
import sys
from svm import train_svm, test_svm
import naive_bayes as NB
from graph_method import GraphMethod
from import_datasets import get_dataset
from preprocess import tokenize, lemmatize, stem, remove_stopwords
from feature_extraction import extract_features, extract_features_test, get_vec_differences, get_vec_differences_train
from evaluation import evaluate_on_each_doc, evaluate_one_doc
import cPickle as pickle

valid_methods = set(['NB', 'graph_closeness', 'text_rank', 'svm', 'svm_ranking'])
valid_datasets = set(['semeval', 'nlm', 'js'])

def graph_closeness(data_path):
    graph_method = GraphMethod(data_path)
    accuracy, recall = graph_method.get_accuracy_from_closeness_rank()
    return {'accuracy': accuracy,
            'recall': recall}

def text_rank(data_path):
    graph_method = GraphMethod(data_path)
    accuracy, recall = graph_method.get_accuracy_from_text_rank()
    return {'accuracy': accuracy,
            'recall': recall}

def naive_bayes(train_docs, train_keys, test_docs, test_keys,model_file, N):
    X_train, y_train, phrase_list_train, idf_vec= extract_features(train_docs, train_keys)
    #X_test, y_test, fl_test, junk = extract_features(test_docs, test_keys)
    #print y_train
    print "--Feature matrices calculated, NB now training..."
    clf = NB.train(X_train, y_train)
    print "--Saving model..."
    with open(model_file, 'w') as f:
        pickle.dump(clf, f)
    with open(model_file+'.phrase_list', 'w') as f:
        pickle.dump(phrase_list_train, f)
    with open(model_file+'.idf_vec', 'w') as f:
        pickle.dump(idf_vec, f)
    with open(model_file+'.training_size', 'w') as f:
        pickle.dump(len(train_docs), f)
    print "--NB trained, NB now testing..."
    #accuracy = NB.score(clf, X_test, y_test)
    accuracy = 0

    precisions = []
    recalls = []
    for doc, true_keys in zip(test_docs, test_keys):
        candidates, features = extract_candidates_doc(doc, phrase_list_train, idf_vec, len(train_docs))
        precision, recall = evaluate_one_doc('NB', clf, candidates, features, true_keys, N)
        precisions.append(precision)
        recalls.append(recall)
    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)
    #features_doc, labels_doc, phrase_idx_doc, phrase_list = extract_features_test(test_docs, test_keys)
    #avg_precision, avg_recall = evaluate_on_each_doc('NB', clf, features_doc, labels_doc, phrase_idx_doc, phrase_list, test_keys, 10)
    return {'accuracy': accuracy,
            'recall': avg_recall,
            'precision': avg_precision}

def svm(train_docs, train_keys, test_docs, test_keys, model_file, N):
    X_train, y_train, phrase_list_train, idf_vec = extract_features(train_docs, train_keys)
    #X_test, y_test, fl_test, junk = extract_features(test_docs, test_keys)
    #print y_train
    print "--Feature matrices calculated, SVM now training..."
    clf = train_svm(X_train, y_train)
    print "--Saving model..."
    with open(model_file, 'w') as f:
        pickle.dump(model_file, f)
    print "--SVM trained, SVM now testing..."
    accuracy = 0

    precisions = []
    recalls = []
    for doc, true_keys in zip(test_docs, test_keys):
        candidates, features = extract_candidates_doc(doc, phrase_list_train, idf_vec, len(train_docs))
        precision, recall = evaluate_one_doc('svm', clf, candidates, features, true_keys, N)
        precisions.append(precision)
        recalls.append(recall)
    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)


    '''
    accuracy = test_svm(svm, X_test, y_test)
    features_doc, labels_doc, phrase_idx_doc, phrase_list = extract_features_test(test_docs, test_keys)
    avg_precision, avg_recall = evaluate_on_each_doc('svm', svm, features_doc, labels_doc, phrase_idx_doc, phrase_list, test_keys)
    '''
    return {'accuracy': accuracy,
            'recall': avg_recall,
            'precision': avg_precision}

def svm_ranking(train_docs, train_keys, test_docs, test_keys):
    X_train_vec, y_train_vec = extract_features(train_docs, train_keys)
    X_train, y_train = get_vec_differences_train(X_train_vec, y_train_vec)

    X_test_vec, y_test_vec = extract_features(test_docs, test_keys)
    X_test, y_test = get_vec_differences_train(X_test_vec, y_test_vec)
    print "--Training SVM"
    svm = train_svm(X_train, y_train)
    # The test_svm function needs to be replaced for this method
    # so it finds the diff. of test vectors, classifies those
    # differences, and ranks using those classifications
    print "--Testing SVM"
    accuracy = test_svm(svm, X_test, y_test)
    avg_recall = 0
    avg_precision = 0
    return {'accuracy': accuracy,
            'recall': avg_recall,
            'precision': avg_precision}

    # # Get train set vectors, X contains features for one phrase
    # # in each row
    # # y contains lablel of 1 for keyword and 0 for non-keyword
    # X_train_vec, y_train_vec = extract_features(train_docs, train_keys)
    # X_test_vec, y_test_vec = extract_features(test_docs, test_keys)
    # # Use RankSVM to learn the =model
    # print "--Trainnig rankning SVM"
    # rank_svm = RankSVM().fit(X_train_vec, y_train_vec)

    # accuracy = rank_svm.score(X_test_vec, y_test_vec)
    # predict = rank_svm.predict(X_test_vec)
    # sorted_idx = [x for (ordx, x) in sorted(zip(predict, range(len(y_test_vec))))]
    # # sorted_idx_y = [ordx for (ordx, x) in sorted(zip(predict, range(len(y_test_vec))))]
    # recall_count = 0
    # positive_all = sum(y_test_vec)
    # RANGE = 100
    # for idx in range(RANGE):
    #     if y_test_vec[sorted_idx[idx]] == 1:
    #         recall_count =+ 1
    # avg_recall = recall_count / positive_all
    # avg_precision = recall_count / RANGE
    # return {'accuracy': accuracy,
    #         'recall': avg_recall,
    #         'precision': avg_precision}

def print_performance(performance):
    print '\n--Performance:'
    #print '--accuracy:', str(performance['accuracy'])
    print '--precision:', str(performance['precision'])
    print '--recall:', str(performance['recall'])

def main():
    method_name, data_dir, dataset_name, model_file, N = sys.argv[1:] # Assign last three args to method, data_dir, dataset
    N = int(N)
    if (method_name not in valid_methods) or (dataset_name not in valid_datasets):
        print '--Invalid arguments, exiting!'
        sys.exit()
    # Graph methods
    if method_name == 'graph_closeness':
        performance = graph_closeness(data_dir + '/' + dataset_name + '/')
    elif method_name == 'text_rank':
        performance = text_rank(data_dir + '/' + dataset_name + '/')
    # Other methods
    else:
        train, test = get_dataset(data_dir, dataset_name)
        train_keys, train_docs = zip(*train.values())
        test_keys, test_docs = zip(*test.values())
        ##
        print '--Number of train docs:', len(train_docs)
        print '--Number of test docs:', len(test_docs)
        ##
        if method_name == 'NB':
            performance = naive_bayes(train_docs, train_keys, test_docs, test_keys, model_file, N)
        elif method_name == 'svm':
            performance = svm(train_docs, train_keys, test_docs, test_keys, model_file, N)
        elif method_name == 'svm_ranking':
            performance = svm_ranking(train_docs, train_keys, test_docs, test_keys)

    print_performance(performance)

if __name__ == '__main__':
    if len(sys.argv) == 6:
        main()
    else:
        print "usage: python run.py <method_name> <data_dir> <dataset_name> <model_file> N (#keywords extracting from doc)"
