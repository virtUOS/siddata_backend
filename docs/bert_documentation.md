# BERT-App
The Bert-App serves SidBERT functionalities, a natural language processing neural network for Dewey Decimal Classification system classification.
## Requirements
The following libraries need to be installed for bert_app to function.
python >= 3.8
transformers == 3.1.0
tensorflow >= 2.8.0
pandas

Additionally, SidBERT model weights and SidBERT class names need to be present as files:
*model weights are stored in data/SidBERT/bert_models
*class names are stored in data/SidBERT/bert_data

If you are missing these files, please download them from the SIDDATA repository.

## Enabling / Disabling SidBERT functionalities
To enable SidBERT functionalities, simply add 'apps.bert_app.apps.BertAppConfig' to the INSTALLED_APPS variable within django settings. Conversely, comment out or remove 'apps.bert_app.apps.BertAppConfig' from your INSTALLED_APPS if you wish to deactivate SidBERT functionalities (This is recommended for prototyping).
Please note that certain functions rely on the Bert-App to be activated. These functions will not be executed as long as the Bert-App is deactivated. For a list of functions and programms depending on Bert-App, see 'Files and functions depending on Bert-App' section.

## bert_app files and architecture
If Bert-App is enabled in INSTALLED_APPS, it is loaded upon server startup:
bert_app/apps.py instanciates a SidBERT instance and loads the models weights from disk. Due to the Django startup routine, this may happen twice upon server startup.
bert_app/apps.py then serves as a reference for external programms to access SidBERT functions by instanciating an instance of recommender_backbone.ProfessionsRecommenderBackbone.
bert_app/recommender_backbone.ProfessionsRecommenderBackbone provides functional access to the SidBERT tensorflow model and handles scheduled task functions that activate at each semester change.
bert_app/bert_utils.py contains the SidBERT model class which defines, loads and provides the SidBERT tensorflow model. This class is instantiated by bert_app/apps.py during startup and is referenced whenever a module requests the predictor variable from bert_app/apps.py.

All functions revolving around SidBERT typically use the recommender_backbone.ProfessionsRecommenderBackbone class as an interface: This class is instantiated on-demand and itself references the always references the same SidBERT class loaded upon server startup.

## Files and functions depending on Bert-App
*recommenders/RM_professions instantiates a recommender_backbone.ProfessionsRecommenderBackbone class for generating matching educational resources for a given user query and filter settings.
*recommenders/RM_gettogether instantiates a recommender_backbone.ProfessionsRecommenderBackbone class to utilize its compare_strings_by_ddc function
*scheduled_tasks/db_tasks instantiates a recommender_backbone.ProfessionsRecommenderBackbone class to utilize its update_resources_bert function for a periodic classification of new educational resources

###### recommender_backbone.ProfessionsRecommenderBackbone
Wrapper class that provides functions to interface with the SidBERT model. It is instantiated within the recommenders/RM_professions.py and recommenders/RM_gettogether.py recommenders as well as in the scheduled_tasks/db_tasks.py file.
**Attributes**
*predictor: bert_app/bert_utils.SidBERT class retrieved from the bert_app/apps.py predictor reference.
*course_max: maximum number of resources to be retrieved from a resource retrieval request.
*current_semester: datetime object encoding the first day of the current semester (Per default, Semesters start on the first day of the first and third quartal of the year)
*next_semester: datetime object encoding the first day of the next semester (Per default, Semesters start on the first day of the first and third quartal of the year)
*now: timezone time object used to reference server timezone
*formats: list of available educational resource formats retrieved from the EducationalResource database object definition (See EducationalResource object attributes in backend/models.EducationalResource)
*types: list of available educational resource types retrieved from the EducationalResource database object definition (See EducationalResource object attributes in backend/models.EducationalResource)
**Functions**
*update_resources_bert: Checks for EducationalResource type objects in the database that do not possess an entry for their "ddc_code" attribute. Updates the ddc_code attribute entries for these objects by classifying them through SidBERT.
*check_current_semester: retrieves current semester
*check_next_semester: retrieves next semester
*set_new_semester: wrapper function to execute current and next semester check
*generate_ddc_label: sends an input string to the SidBERT class for ddc class classification.
*generate_sidbert_resources: generates a list of EducationalResource type objects that match a given input strings' ddc class and that are filtered for their type in correspondence to an input set of filter parameters.
*get_matching_campus_courses: filter function to retrieve courses from ones own university only.
*get_matching_events: filter function to retrieve LMS event type EducationalResource objects only.
*get_matching_oer: filter function to retrieve oers only.
*get_matching_extra_campus_courses: filter function to retrieve courses from foreign universities only.
*fetch_resources_sidbert: wrapper function that calls and loggs a resource Request.
*compare_strings_by_ddc: compares the semantic distance between two strings by classifying them with SidBERT and by calculating the number of steps necessary to navigate from one string's DDC class to the other strings's DDC class.

###### bert_utils.SidBERT
Class responsible for instantiating and providing the SidBERT model.
**Attributes**
*base_path: absolute path to the SIDDATA folder
*file_path parent: path for SidBERT files
*logger event logger: for displaying events on command line
*checkpoint_path: path to checkpoint files
*classes: pandas dataframe object containing DDC class labels
*tokenizer: transformers BERT tokenizer object from the huggingface transformers library. Used to tokenize an input sequence (title, sentence).
*max_length: maximum length of output sequence the tokenizer creates. Sequences with an output length of above 300 are cut off.
*model: tensorflow.keras.Model instance representing the SidBERT neural network model.
*sparse_label_codes: lookup dictionary used to link a one-hot SidBERT model output to its corresponding DDC class label.
**Functions**
*_load_classes_from_tsv: loads DDC class labels from disk.
*_create_sparse_label_lookup: creates lookup dictionary linking positional encodings from a one-hot output vector to a corresponding DDC class label.
*_load_model: creates SidBERT tensorflow.keras architecture and calls weight loading function.
*_load_weights: loads model weights from disk.
*predict_single_example: tokenizes an input sentence and performs a forward pass (prediction) through the SidBERT model. translates the SidBERT output vector into its corresponding DDC class label.
*predict: wrapper function that performs predict_single_example on multiple samples.

