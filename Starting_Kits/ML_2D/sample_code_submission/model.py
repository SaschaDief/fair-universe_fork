import pickle
from os.path import isfile
import numpy as np
import pandas as pd
from sklearn.utils import shuffle
from copy import deepcopy
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import RidgeClassifier
from GDA import GaussianDiscriminativeAnalysisClassifier


MODEL_CONSTANT = "Constant"
MODEL_NB = "NB"
MODEL_LDA = "LDA"
MODEL_RR = "RR"
MODEL_GDA = "GDA"


PREPROCESS_TRANSLATION = "translation"
PREPROCESS_SCALING = "scaling"

AUGMENTATION_TRANSLATION = "translation"
AUGMENTATION_TRANSLATION_SCALING = "translation-scaling"


# ------------------------------
# Baseline Model
# ------------------------------
class Model:

    def __init__(self,
                 model_name=MODEL_NB,
                 X_train=None,
                 Y_train=None,
                 X_test=None,
                 preprocessing=False,
                 preprocessing_method=PREPROCESS_TRANSLATION,
                 data_augmentation=False,
                 data_augmentation_type=AUGMENTATION_TRANSLATION,
                 case=None,
                 thetas=None
                 ):

        self.model_name = model_name
        self.X_train = X_train
        self.Y_train = Y_train
        self.X_test = X_test

        self.preprocessing = preprocessing
        self.preprocessing_method = preprocessing_method
        self.data_augmentation = data_augmentation
        self.data_augmentation_type = data_augmentation_type

        if case is None:
            self.case = case
        else:
            self.case = case - 1

        self.thetas = thetas

        self._set_model()

    def _set_model(self):

        if self.model_name == MODEL_CONSTANT:
            self.clf = None 
        if self.model_name == MODEL_NB:
            self.clf = GaussianNB()
        if self.model_name == MODEL_LDA:
            self.clf = LinearDiscriminantAnalysis()
        if self.model_name == MODEL_RR:
            self.clf = RidgeClassifier()
        if self.model_name == MODEL_GDA:
            self.clf = GaussianDiscriminativeAnalysisClassifier()

        self.is_trained = False

    def _preprocess_translation(self, X):

        train_mean = np.mean(self.X_train).values
        test_mean = np.mean(self.X_test).values

        translation = test_mean - train_mean
        return (X - translation)

    def _preprocess_scaling(self, X):

        train_mean = np.mean(self.X_train).values
        test_mean = np.mean(self.X_test).values

        train_std = np.std(self.X_train).values
        test_std = np.std(self.X_test).values

        translation = test_mean - train_mean
        scaling = test_std/train_std

        return (X - translation)/scaling

    def _augment_data_translation(self):

        random_state = 42
        size = 1000

        # Mean of Train and Test
        train_mean = np.mean(self.X_train, axis=0).values
        test_mean = np.mean(self.X_test, axis=0).values

        # Esitmate z0
        translation = test_mean - train_mean

        train_data_augmented, train_labels_augmented = [], []
        for i in range(0, 5):
            # randomly choose an alpha

            alphas = np.repeat(np.random.uniform(-3.0, 3.0, size=size).reshape(-1,1), 2, axis=1 )

            # transform z0 by alpha
            translation_ = translation * alphas

            np.random.RandomState(random_state)
            train_df = deepcopy(self.X_train)
            train_df["labels"] = self.Y_train

            df_sampled = train_df.sample(n=size, random_state=random_state, replace=True)
            data_sampled = df_sampled.drop("labels", axis=1)
            labels_sampled = df_sampled["labels"].values

            train_data_augmented.append(data_sampled + translation_)
            train_labels_augmented.append(labels_sampled)

        augmented_data = pd.concat(train_data_augmented)
        augmented_labels = np.concatenate(train_labels_augmented)

        augmented_data = shuffle(augmented_data, random_state=random_state)
        augmented_labels = shuffle(augmented_labels, random_state=random_state)

        return augmented_data, augmented_labels

    def _augment_data_scaling(self):

        random_state = 42
        size = 1000

        # Mean of Train and Test
        train_mean = np.mean(self.X_train, axis=0).values
        test_mean = np.mean(self.X_test, axis=0).values

        train_std = np.std(self.X_train, axis=0).values
        test_std = np.std(self.X_test, axis=0).values

        # Esitmate z0
        translation = test_mean - train_mean
        scaling = test_std/train_std

        train_data_augmented, train_labels_augmented = [], []
        for i in range(0, 5):

            # uniformly choose alpha between -3 and 3
            alphas = np.repeat(np.random.uniform(-3.0, 3.0, size=size).reshape(-1, 1), 2, axis=1)

            # uniformly choose beta between 1 and 1.5
            betas = np.repeat(np.random.uniform(1.0, 1.5, size=size).reshape(-1, 1), 2, axis=1)

            # translation
            translation_ = translation * alphas
            # sclaing
            scaling_ = scaling * betas

            np.random.RandomState(random_state)
            train_df = deepcopy(self.X_train)
            train_df["labels"] = self.Y_train

            df_sampled = train_df.sample(n=size, random_state=random_state, replace=True)
            data_sampled = df_sampled.drop("labels", axis=1)
            labels_sampled = df_sampled["labels"].values

            transformed_train_data = (data_sampled + translation_)*scaling_

            train_data_augmented.append(transformed_train_data)
            train_labels_augmented.append(labels_sampled)

        augmented_data = pd.concat(train_data_augmented)
        augmented_labels = np.concatenate(train_labels_augmented)

        augmented_data = shuffle(augmented_data, random_state=random_state)
        augmented_labels = shuffle(augmented_labels, random_state=random_state)

        return augmented_data, augmented_labels

    def fit(self, X=None, y=None):

        if self.model_name != MODEL_CONSTANT:

            if X is None:
                X = self.X_train
            if y is None:
                y = self.Y_train

            if self.data_augmentation:
                if self.data_augmentation_type == AUGMENTATION_TRANSLATION:
                    X, y = self._augment_data_translation()
                else:
                    X, y = self._augment_data_scaling()

            self.clf.fit(X, y)
            self.is_trained = True

    # def predict(self, X=None, preprocess=True):

    #     if X is None:
    #         X = self.X_test

    

    #     if self.model_name == MODEL_CONSTANT:
    #         return np.zeros(X.shape[0])

    #     if self.preprocessing & preprocess:
    #         if self.preprocessing_method == PREPROCESS_TRANSLATION:
    #             X = self._preprocess_translation(X)
    #         else:
    #             X = self._preprocess_scaling(X)
          

    #     return self.clf.predict(X)

    # def decision_function(self, X=None, preprocess=True):
        
    #     if X is None:
    #         X = self.X_test

    #     if self.model_name == MODEL_CONSTANT:
    #         return np.zeros(X.shape[0])
        
    #     if self.preprocessing and preprocess:
    #         if self.preprocessing_method == PREPROCESS_TRANSLATION:
    #             X = self._preprocess_translation(X)
    #         else:
    #             X = self._preprocess_scaling(X)

    #     if self.model_name == MODEL_NB:
    #         predicted_score = self.clf.predict_proba(X)
    #         # Transform with log
    #         epsilon = np.finfo(float).eps
    #         predicted_score = -np.log((1/(predicted_score+epsilon))-1)
    #         return predicted_score[:, 1]
    #     else:
    #         return self.clf.decision_function(X)

    def predict(self, X=None, preprocess=True):

        if X is None:
            X = self.X_test


        if self.model_name == MODEL_CONSTANT:
            return np.zeros(X.shape[0])

        if self.preprocessing & preprocess:
            if self.preprocessing_method == PREPROCESS_TRANSLATION:
                X = self._preprocess_translation(X)
            else:
                X = self._preprocess_scaling(X)

        if self.case is None:
            return self.clf.predict(X)
        else:

            # if decision function  > theta --> class 1 
            # else --> class 0
            predictions = np.zeros(X.shape[0])
            decisions = self.decision_function(X)

            predictions = (decisions > self.thetas[self.case]).astype(int)
            return predictions

    def decision_function(self, X=None, preprocess=True):

        if X is None:
            X = self.X_test

        if self.model_name == MODEL_CONSTANT:
            return np.zeros(X.shape[0])

        if self.preprocessing and preprocess:
            if self.preprocessing_method == PREPROCESS_TRANSLATION:
                X = self._preprocess_translation(X)
            else:
                X = self._preprocess_scaling(X)

        if self.model_name in [MODEL_NB, MODEL_GDA]:
            predicted_score = self.clf.predict_proba(X)
            # Transform with log
            epsilon = np.finfo(float).eps
            predicted_score = -np.log((1/(predicted_score+epsilon))-1)
            decisions = predicted_score[:, 1]
        else:
            decisions = self.clf.decision_function(X)
        if self.case is None:
            return decisions
        else:
            # decision function = decision function - theta
            return decisions - self.thetas[self.case]

    def save(self, name):
        pickle.dump(self.clf, open(name + '.pickle', "wb"))

    def load(self, name):
        modelfile = name + '.pickle'
        if isfile(modelfile):
            with open(modelfile, 'rb') as f:
                self = pickle.load(f)
            print("Model reloaded from: " + modelfile)
        return self
