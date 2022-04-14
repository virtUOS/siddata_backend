# siddata_backend AI Integration

## Requirements

* python=3.8.0
* tensorflow=2.2.3
* tf-estimator-nightly=2.4.0.dev2020092601 
* tf-models-nightly=2.3.0.dev20200926   
* tf-nightly=2.4.0.dev20200926

### Configuration

* config/settings.py
    * CHECK_POINT_PATH : Path of the trained_model
    * model_name : Name of model, i.e First sub directory of trained_model
    * model_type : Type of model, set 1 if legacy_bert (tf1) else 2 for hugging face (tf2)
    * number_of_classes : set top number of DDC classes needs to extracted
 
### Structure

* Entry point : bert_utils.py
* Model creation and loading weights : bert_model -> neo_bert.py

There are 2 types of models, Hugging face bert model which is tensorflow 2 and Legacy bert model which is 
tensorflow 1 (converted into tensorflow 2 using [conversion](https://github.com/tensorflow/models/blob/master/official/nlp/bert/tf2_encoder_checkpoint_converter.py)) 
Use settings.py for changing path of model according to your local path, by default settings are for legacy bert so give path
of legacy_bert_tf2_model.
