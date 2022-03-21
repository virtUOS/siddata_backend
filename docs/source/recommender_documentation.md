# Recommenders

A Siddata recommender is a module which takes care of a certain topic, the user might be interested in, and makes 
recommendations for the user regarding that topic. Recommenders can be freely defined and added to the system. 
In the following the procedure needed to add a recommender is described.

## Adding a recommender to Siddata
In the following a few general steps are described for creating a new recommender. For further information please refer 
to the already existing recommenders as examples and to the documentation of the `recommenders` module.

1. **Create a new file** in the `recommenders` folder. Its name has to be "RM_<recommender_name>.py". The recommender name 
has to be lowercase.
2. Now in that file **define a class** which inherits from the `RM_BASE` class. Its name has to be "RM_<recommender_name>".
Again, the recommender name has to be lowercase.
3. In the **constructor** define at least the attributes `self.NAME`, `self.DESCRIPTION`, `self.TEASER_TEXT` and
`self.DATA_INFO`. `self.TEASER_TEXT` is a short text with which the recommender will be advertised on the start page. 
Based on that users will decide whether to use the recommender or not. `self.DATA_INFO` is a short description of what 
data the recommender will use and for what purpose. Further, you should set `self.ACTIVE` to `True`, so that the 
will be shown to the user. 
5. In `initialize_templates()` **define `ActivityTemplate` instances** using the `update_or_create()` django function. 
These objects will be non-user-related templates for the user-related `Activity` instances created later on. 
6. In `initialize()` **define user-related `Goal` and `Activity` instances**. The first goal should be created via the 
function `self.activate_recommender_for_user_and_create_first_goal()`. The `Activity` instances should be created 
using `Activity.create_activity_from_template()`. 
7. In `process_activity()` **define how the defined activities shall be processed** after submission by the user. 