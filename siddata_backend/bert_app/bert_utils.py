import logging

import tensorflow as tf
import transformers
import pandas as pd
from os.path import abspath, join, dirname, isfile, isdir
import os
import contextlib

from django.conf import settings
from bert_app.model_downloader_seafile import get_read_account_data, SeafileModelSyncer, model_downloader_logger


@contextlib.contextmanager
def urllib_shutup():
    level_bkp = logging.getLogger("requests").level
    prop_bkp = logging.getLogger("urllib3").propagate
    logging.getLogger("urllib3").propagate = False
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    yield
    logging.getLogger("requests").setLevel(level_bkp)
    logging.getLogger("urllib3").setLevel(level_bkp)
    logging.getLogger("urllib3").propagate = prop_bkp


class BertPredictor:
    """
    this class loads the trained BERT model, and provide api to call the model to get relevant ddc codes.
    All interactions related to database lookup operations for course retrieval are handeled in
    recommender_backbone.py
    """

    def __init__(self):
        """
        Constructor of the class loads the trained model for prediction.
        Use configuration from BERT_CONF config.py to load the model
        """

        #load models
        self.base_path = abspath(join(dirname(__file__),'..','..'))
        self.file_path = join(self.base_path,'data','Sidbert')

        self.logger = logging.getLogger(self.__class__.__name__)
        if "LOG_LEVEL" in os.environ:
            self.logger.setLevel(int(os.environ["LOG_LEVEL"]))
            model_downloader_logger.setLevel(int(os.environ["LOG_LEVEL"])) #this sets the model_downloader-log-level to what you requested as argument/in the settings.
            # if you want to disable messages from the module, set to logging.WARNING. If you want it to be more verbose, set to logging.INFO
            # model_downloader_logger.setLevel(logging.INFO)

        # TODO: remove these lines once everbody savely moved to the new structure
        localpath = abspath(join(settings.BASE_DIR, "..", "data"))
        if isdir(join(localpath, "bert_files")) and isdir(join(localpath, "csv_files")) and not isdir(join(localpath, "Other")) and not isdir(join(localpath, "Sidbert")):
            if input("It seems like you just moved from the old modelsyncer to the new one. Do you want to automatically change the data-directory to the new structure? [y/n]").lower() == "y":
                os.rename(join(localpath, "bert_files"), join(localpath, "Sidbert"))
                os.mkdir(join(localpath, "Other"))
                os.rename(join(localpath, "csv_files"), join(localpath, "Other", "csv_files"))

        try:
            account, password, server, repoid, repopath, modelversions = get_read_account_data()
            if any([i is not None for i in modelversions.values()]):
                modelsyncer = SeafileModelSyncer(server, account, password, repoid, repopath)
                modelsyncer.warn_newfiles(localpath, modelversions)
        except Exception as e:
            if settings.SERVERSTART_IGNORE_MODELUPDOWN_ERRORS:
                logging.error(f"Seafile-Syncer Exception: {e.args[0]}")
            else:
                raise e

        # locate checkpoint files and class files for label lookup
        self.checkpoint_path = join(self.file_path,'bert_models','new_training_latest_architecture')
        if not isfile(self.checkpoint_path+".index"):
            raise FileNotFoundError(f"There is no checkpoint at {self.checkpoint_path}")
        self.classes = self.__load_classes_from_tsv(join(self.file_path,'bert_data','classes.tsv'))

        #create tokenizer and set sequence length:
        with urllib_shutup():
            self.tokenizer = self.tokenizer = transformers.BertTokenizer.from_pretrained('bert-base-multilingual-cased')
        self.max_length = 300

        # load trained model
        self.logger.debug("loading model")
        if "LOG_LEVEL" in os.environ:
            if int(os.environ["LOG_LEVEL"]) == logging.WARNING: transformers.logging.set_verbosity_warning()
            elif int(os.environ["LOG_LEVEL"]) == logging.ERROR: transformers.logging.set_verbosity_error()
        self.model = self.__load_model()

        # create label lookup table for label assignment from last classification layer
        self.sparse_label_codes = self.__create_sparse_label_lookup()

    def __load_classes_from_tsv(self, class_path):
        """
        loads all label IDs from the classes.tsv file
        :return: pandas dataframe object containing all label identities.
        :rtype: pandas dataframe object
        """
        classes_frame = pd.read_csv(class_path, delimiter='\t', names=['DDC'],dtype=str)
        classes_list = classes_frame['DDC'].values.tolist()
        return classes_list

    def __create_sparse_label_lookup(self):
        """
        creates a dictionary for label lookup. As output neurons from the network do not posess an inherent label,
        a lookup must be performed to assess the ddc class an input was associated with.
        :return: lookup dictionary
        :rtype: python 3 dictionary object
        """
        label_assoc = {}
        index = 0
        while index in range(len(self.classes)):
            label_assoc[self.classes[index]] = index
            index += 1
        return label_assoc

    def __load_model(self):
        """
        Constructs model topology and loads weights from Checkpoint file. Topology needs to be changed
        manually every time a new model version is installed into the backend.
        :return: Tensorflow 2 keras model object containing the model architecture
        :rtype: tensorflow.keras.Model object
        """
        #Construct model topology
        input_ids = tf.keras.layers.Input(shape=(300,), name='input_token', dtype='int32')
        input_masks_ids = tf.keras.layers.Input(shape=(300,), name='attention_mask', dtype='int32')
        input_type_ids = tf.keras.layers.Input(shape=(300,), name='token_type_ids',dtype='int32')
        with urllib_shutup():
            bert_model = transformers.TFBertModel.from_pretrained('bert-base-multilingual-cased')
        sequence_output, pooled_output = bert_model(input_ids, attention_mask=input_masks_ids, token_type_ids=input_type_ids)
        concat = tf.keras.layers.Dense(3000,activation='relu')(sequence_output)
        concat = tf.keras.layers.GlobalAveragePooling1D()(concat)
        dropout = tf.keras.layers.Dropout(0.35)(concat)
        dropout = tf.keras.layers.Dense(2048, activation='relu')(dropout)
        dropout = tf.keras.layers.Dropout(0.25)(dropout)
        output = tf.keras.layers.Dense(len(self.classes), activation="softmax")(dropout)
        model = tf.keras.models.Model(
            inputs=[input_ids, input_masks_ids, input_type_ids], outputs=output
        )

        #restore model weights from checkpoint file
        self._load_weights(model)
        return model

    def _load_weights(self, model):
        path = self.checkpoint_path
        model.load_weights(path)


    def predict_single_example(self, sequence, top_n = 1):
        """
        queries the SidBERT neural network to produce a DDC label assignment together with an associated probability
        sequence: String input that is to be classified
        top_n: number of DDC labels to be returned. Defaults to 1

        :return: dictionary with structure: key: DDC code value: probability
        :rtype: python 3 dictionary object
        """
        encoded_sequence = self.tokenizer.encode_plus(sequence, add_special_tokens=True, padding='max_length',
                                                      max_length=self.max_length, truncation=True, return_attention_mask=True,
                                                      return_token_type_ids=True, pad_to_max_length=True,
                                                      return_tensors="tf")

        prediction_result = self.model.predict(
            [encoded_sequence['input_ids'], encoded_sequence['attention_mask'], encoded_sequence['token_type_ids']])[0]
        max_classes = prediction_result.argsort()[::-1][:top_n]
        label_probability_assoc = {}
        for entry in max_classes:
            for key in self.sparse_label_codes.keys():
                if self.sparse_label_codes[key] == entry:
                    computed_label = key
                    break
            #TODO computed_label possibly doesn't exist here
            label_probability_assoc[str(computed_label)] = str(prediction_result[entry])
        return label_probability_assoc


    def predict(self,data: dict,top_n=1) -> dict:
        """
        wrapper function that reads in a number of courses / queries and produces an output dict / json file with DDC
        labels

        :param data: dictionary object containing a list of courses / resources / events to be classified
        :param top_n: how many labels should be assigned to the individual courses / resources / events in decreasing
        likelyhood order.
        :return: dictionary containing an associaton between input and ddc code.
        :rtype: python 3 dictionary object
        """
        out_file = {}
        for course in data:
            out_file[course] = self.predict_single_example(sequence=course, top_n=top_n)
        return out_file
