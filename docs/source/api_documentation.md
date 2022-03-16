# Siddata REST API
The Siddata Backend server provides a RESTful API which has been inspired by the [JSON-API](jsonapi.org) specification. In the following we describe the existing routes and their behavior. Note that the API was developed for communication with a [Stud.IP](https://www.studip.de/) instance. Some of the structures might be Stud.IP-specific and not feasible for other clients.

First every route gets preprocessed. Therefore the following URL parameters are necessary.
1. `origin`: The client's `api_endpoint`.
2. `api_key`: An authentication key given to the client. 

Now we describe the specific behavior of each route. 
1. `student`: This route handles `SiddataUser` objects.
   1. `GET`:
      1. URL Parameters:
         1. `user_origin_id`: The (native) ID the origin of a new user provides. 
         2. `include`: Include parameters: ['recommenders', 'courses_brain', 'courses_social', 'institutes_brain', 'institutes_social']
      2. Returned JSON structure:
        ```
        {
            "data": [
                {
                    "type": "SiddataUser",
                    "id": str,                      # The database ID of the `SiddataUser` object.
                    "attributes": {
                        "origin": str,              # The name of the related `Origin` object.
                        "user_origin_id": str,      # The (pseudonymized native) ID the origin of a user provides.
                        "data_donation": bool,      # True, if the user agrees to provide their usage data for research purposes.
                        "gender_brain": str,        # The gender the user agrees to share for research purposes.
                        "gender_social": str,       # The gender the user agrees to share with other users.
                    }, 
                    "relationships": {
                        "recommenders": {
                            "data": [
                                {
                                    "id": str,              # `Recommender` ID.
                                    "type": "Recommender"   # Respective object type string.
                                },
                            ]
                        }
                    }
                },
            ],
            "included": []                          # See respective routes for specific JSON structure.
        }
        ```
      3. Functionality: Always returns one `SiddataUser` object determined by the `user_origin_id`. If no object with the given `user_origin_id` was found, a new one is created.
   2. `DELETE`:
      1. URL Parameters:
         1. `user_origin_id`: The (native) ID the origin of a new user provides.
      2. Functionality: This route is meant to fully delete a `SiddataUser` object determined by the `user_origin_id`.
   3. `PATCH`:
      1. URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "id": str,                      # The (pseudonymized native) ID the origin of a user provides.
            "type": "SiddataUser",          # Respective object type string.
            "attributes": {
                "data_donation": bool,      # True, if the user agrees to provide their usage data for research purposes. 
                "gender_brain": str,        # The gender the user agrees to share for research purposes.
                "gender_social": str,       # The gender the user agrees to share with other users.
                "data_regulations": bool,   # TODO
            },
            "relationships": {
                "institutes_brain": {       # `Institute` objects the user belongs to which they agree to share for research purposes.
                    "data": [
                        {
                            "id": str,      # The (native) id of the institute.
                            "type": str,    # Respective object type string. 
                        },
                    ]
                },
                "institutes_social": {      # `Institute` objects the user belongs to which they agree to share with other users.
                    "data": [
                        {
                            "id": str,      # The (native) id of the institute.
                            "type": str,    # Respective object type string. 
                        },
                    ]
                },
                "courses_brain": {          # `InheritingCourse` objects the user applied to, which they want to share for research purposes. 
                    "data": [
                        {
                            "id": str,      # The (native) id of the course.
                            "type": str,    # Respective object type string.
                        },
                    ]
                },
                "courses_social": {         # `InheritingCourse` objects the user applied to, which they want to share with other users. 
                    "data": [
                        {
                            "id": str,      # The (native) id of the course.
                            "type": str,    # Respective object type string.
                        },
                    ]
                }
            }
        }
        ```
      3. Functionality: Updates a `SiddataUser` object with the given `user_origin_id` and inserts the given related information into the database.
2. `recommender`: This route handles `SiddataUserRecommender` objects. 
   1. `GET`: 
      1. URL Parameters:
         1. `user_origin_id`: The (native) ID the origin of a new user provides. 
      2. Returned JSON structure:
        ```
        {
            "data": [
                {
                    "type": "Recommender",
                    "id": str,                      # The database ID of the `Recommender` object.
                    "attributes": {
                        "name": str,                # Name.
                        "classname": str,           # Name of the specific subclass.
                        "description": str,         # Description
                        "image": str,               # Static URL to the recommender's image. 
                        "order": int,               # Display order.
                        "enabled": bool,            # True if the user has enabled this recommender.
                        "data_info": str            # Information about how the user's data will be used. 
                    }, 
                    "relationships": {
                        "goals": {
                            "data": [
                                {
                                    "id": str,              # Goal ID.
                                    "type": "Goal"          # Respective object type string. 
                                },
                            ]
                        },
                        "activities": {
                            "data": [
                                {
                                    "id": str,              # Activity ID.
                                    "type": "Activity"      # Respective object type string.
                                },
                            ]
                        },
                        "students": {
                            "data": [
                                {
                                    "id": str,              # SiddataUser ID.
                                    "type": "SiddataUser"   # Respective object type string.
                                }
                            ]
                        }
                    }
                },
            ],
            "included": []                          # Always includes `Recommender`'s `Student`, `Goal`s and their `Activity`s. See respective routes for specific JSON structure.
        }
        ```
      3. Functionality: Returns `SiddataUserRecommender` objects related to the user with the given `user_origin_id`. If the user is new, the initial recommenders, goals and activities are created.
      4. `recommender/<recommender_id>` returns a certain recommender.
   2. `PATCH`: 
      1. URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "id": str,                      # The recommender's ID.
            "type": "Recommender",          # Respective object type string.
            "attributes": {
                "enabled": bool             # True if the user has enabled this recommender.
            }
        }
        ```
      3. Functionality: Updates the `enabled` field of the `SiddataUserRecommender`.
3. `goal`: This route handles `Goal` objects.
   1. `GET`: 
      1. URL Parameters:
         1. `user_origin_id`: The (native) ID the origin of a new user provides. 
      2. Returned JSON structure:
        ```
        {
            "data": [
                {
                    "type": "Goal",
                    "id": str,                      # The database ID of the `Goal` object.
                    "attributes": {
                        "title": str,               # Title.
                        "description: str,          # Description.
                        "makedate": str,            # Datetime string.
                        "user": str,                # Property key of related `Siddatauser`.
                        "recommender": str,         # Name of related recommender.
                        "order: int,                # Display order.
                        "type": str                 # Specific goal type. 
                        "visible": bool             # True if the `Goal` shall be displayed in the frontend. If this is False, only the respective `Activity`s shall be displayed. 
                    }, 
                    "relationships": {
                        "activities": {
                            "data": [
                                {
                                    "id": str,              # Activity ID.
                                    "type": "Activity"      # Respective object type string.
                                },
                            ]
                        },
                        "goalproperties": {
                            "data": [
                                {
                                    "type": "GoalProperty",
                                    "id": str,              # `GoalProperty` ID. 
                                },
                            ]
                        },
                        "students": {
                            "data": [
                                {
                                    "id": str,              # ID of the related `SiddataUser` object. 
                                    "type": "SiddataUser"
                                }
                            ]
                        }
                    }
                },
            ],
            "included": [
                {
                    "type": "GoalProperty",                 # Respective object type string.
                    "id": str,                              # `GoalProperty` ID.
                    "attributes": {
                        "key": str,                         # Property key.
                        "value": str,                       # Property value. 
                    }
                },
            ]                          # See respective routes for specific JSON structure of further object types.
        }
        ```
      3. Functionality: Returns `Goal` objects related to the user with the given `user_origin_id`. 
      4. `goal/<goal_id>` returns a certain `Goal`.
   2. `PATCH/<goal_id>`:
      1. URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "id": str,                      # The goal's ID.
            "type": "Goal",                 # Respective object type string.
            "attributes": {
                "title": str,
                "description": str, 
                "order": int                # The order of display for this goal.
            }
        }
        ```
      3. Functionality: Updates `Goal` objects with user-specific changes.
   3. `DELETE/<goal_id>`: 
      1. URL Parameters: None
      2. Functionality: Deletes a certain `Goal`.
4. `activity`: This route handles `activity` objects.
   1. `GET`:
      1. URL Parameters:
         1. `user_origin_id`: The (native) ID the origin of a new user provides. 
      2. Returned JSON structure:
        ```
        {
            "data": [
                {
                    "type": "Activity",
                    "id": str,                          # The database ID of the `Recommender` object.
                    "attributes": {
                        "description": str,             # Description
                        "type": str,                    # `Activity` subtype.
                        "title": str,                   # Title. 
                        "status": str,                  # Status of the Activity. Options are ['new', 'snoozed', 'done', 'template', 'active', 'immortal', 'discarded']
                        "image": str,                   # Static URL to the activity's image. 
                        "order": int,                   # Display order.
                        "feedback_size": int,           # Size of the feedback scale.
                        "feedback_value": int,          # Given numerical feedback for that activity. 
                        "feedback_text": str,           # Given textual feedback for that activity.
                        "feedback_chdate": timestamp    # Timestamp of the given feedback.
                        "duedate": str,                 # String represenation of DateTimeFiled. 
                        "form": int,                    # ID of a group of `Activity` objects which this one belongs to.
                        "color_theme": str,             # Determines the display color theme. :w
                        "button_text": str,             # Text for the submit button. "~static" indicates that the button shall be hidden.
                        "rebirth": bool,                # Indicates if this `Activity` can be restored from a 'done' or 'discarded' state. 
                        "activation_time": timestamp    # Time of activiation of that activity.
                        "deactivation_time": timestamp  # Time of deactivation of that activity.
                        "interactions": int             # number of interactions with that activity.
                        "order": int                    # The order of display for this goal.
                        "anwers": str[]                 # Answers given for this activity if it is a Question.
                    }, 
                    "relationships": {
                        "course": {
                            "data": [
                                "id": str,              # Course ID.
                                "type": "Course"        # Respective object type string.
                            ]
                        },
                        "resource": {
                            "data": [
                                "id": str,              # Resource ID.
                                "type": "Resource"      # Respective object type string.
                            ]
                        },
                        "question": {
                            "data": [
                                "id": str,              # Question ID.
                                "type": "Question"      # Respective object type string.
                            ]
                        },
                        "event": {
                            "data": [
                                "id": str,              # Event ID.
                                "type": "Event"         # Respective object type string.
                            ]
                        },
                        "person": {
                            "data": [
                                "id": str,              # Person ID.
                                "type": "Person"        # Respective object type string.
                            ]
                        },
                    }
                },
            ],
            "included": [
                {
                    "type": "Resource",                 # Respective object type string.
                    "id": str,                          # Resource ID. 
                    "attributes": {
                        "title": str,                   # Resource title. 
                        "description": str,             # Description.
                        "url": str,                     # URL to the resource. 
                        "origin": str,                  # Name of the related `Origin` object. 
                        "creator": str,                 # Creator name. 
                        "format": str,                  # Format of the resource {'IMG': image, 'CRS': course, 'WEB', website, 'APP': application, 'TXT': text}. 
                    }
                },
                {
                    "type": "Question",                 # Respective object type string.
                    "id": str,                          # Question ID.
                    "attributes": {
                        "question_text": str,           # Question text.
                        "answer_type": str,             # Type string which indicates the answer type ['selection', 'text', 'checkbox', 'multitext', 'auto_completion', 'date', 'datetime'].
                    }
                },
                {
                    "type": "Person",                   # Respective object type string.
                    "id": str,                          # Person ID.
                    "attributes": {
                        "first_name": str,              # Ecrypted first name.
                        "surname": str,                 # Encrypted surname.
                        "title": str,                   # Title. 
                        "email": str,                   # Encrypted email address.
                        "role_description": str,        # Encrypted description.
                        "url": str,                     # URL to the persons profile. 
                        "image": str,                   # Profile image as a Base64 encoded string.
                        "editable": bool,               # If True, this object can be edited and sent back to the server via `PATCH`. 
                    }
                }
            ]                                           # Mostly includes related resources. For Course and Event strucutre see respective routes. 
        }
        ```
      3. Functionality: Returns `Activity` objects related to the user with the given `user_origin_id`. 
      4. `activity/<activity_id>` returns a certain `Activity`.
   2. `PATCH/<activity_id>`: 
      1. URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "data": {
                "id": str,                          # The goal's ID.
                "type": "Activity",                 # Respective object type string.
                "attributes": {
                    "title": str,
                    "description": str, 
                    "status": str,                  # Status of the Activity. Options are ['new', 'snoozed', 'done', 'template', 'active', 'immortal', 'discarded']
                    "feedback_value": int,          # Given numerical feedback for that activity. Has to be < `feedback_size`.
                    "feedback_text": str,           # Given textual feedback for that activity.
                    "feedback_chdate": timestamp    # Timestamp of the given feedback.
                    "activation_time": timestamp    # Time of activiation of that activity.
                    "deactivation_time": timestamp  # Time of deactivation of that activity.
                    "interactions": int             # number of interactions with that activity.
                    "order": int                    # The order of display for this goal.
                    "anwers": str[]                 # Answers given for this activity if it is a Question.
                }
            }
        }
        ```
      3. Functionality: Updates `Activity` objects with user-specific changes.
   3. `DELETE/<activity_id>`: 
      1. URL Parameters: None
      2. Functionality: Deletes a certain activity permanently.
5. `studycourse`: This route handles `SiddataUserStudy` objects. 
   1. `GET`:
      1. URL Parameters:
         1. `user_origin_id`: The (native) ID the origin of a new user provides. 
      2. Returned JSON structure:
        ```
        {
            "data": [
                {
                    "type": "Goal",
                    "id": str,                          # The database ID of the `Goal` object.
                    "attributes": {
                        "studip_id": str,               # native ID of the study course object
                        "semester": int,                # in which semester is the student applied to that study course
                        "share_subject_brain": bool     # Ture, if the user agrees to share their subject for research purposes. 
                        "share_subject_social": bool    # Ture, if the user agrees to share their subject with other users. 
                        "share_degree_brain": bool      # Ture, if the user agrees to share their degree for research purposes. 
                        "share_degree_social": bool     # Ture, if the user agrees to share their degree with other users. 
                        "share_semester_brain": bool    # Ture, if the user agrees to share their semester for research purposes. 
                        "share_semester_social": bool   # Ture, if the user agrees to share their semester with other users. 
                    }, 
                },
            ]
        }
        ```
      3. Functionality: Returns all `SiddataUserStudy` objects related to the given `user_origin_id`.
   2. `POST`: 
      1. URL Parameters: 
         1. `user_origin_id`: The (native) ID the origin of a new user provides. 
      2. Required JSON structure: 
        ```
        {
            "data": [
                {
                    "type": "UserStudyCourse",                 # Respective object type string.
                    "attributes": {
                        "studip_id": str,               # native ID of the study course object
                        "semester": int,                # in which semester is the student applied to that study course
                        "share_subject_brain": bool     # Ture, if the user agrees to share their subject for research purposes. 
                        "share_subject_social": bool    # Ture, if the user agrees to share their subject with other users. 
                        "share_degree_brain": bool      # Ture, if the user agrees to share their degree for research purposes. 
                        "share_degree_social": bool     # Ture, if the user agrees to share their degree with other users. 
                        "share_semester_brain": bool    # Ture, if the user agrees to share their semester for research purposes. 
                        "share_semester_social": bool   # Ture, if the user agrees to share their semester with other users. 
                    },
                    "relationships": {
                        "user": {
                            "data": [
                                {
                                    "type": "SiddataUser",
                                    "id": str                   # ID of the corresponding `SiddataUser` object.
                                }
                            ]
                        },
                        "subject": {
                            "data": [
                                {
                                    "type": "StudipSubject",
                                    "id": str                   # ID of the related `Subject` object (has to already exist in the database before study course is submitted)     
                                }
                            ]
                        },
                        "degree": {
                            "data": [
                                {
                                    "type": "StudipDegree",
                                    "id": str                   # ID of the related `Degree` object (has to already exist in the database before study course is submitted)     
                                }
                            ]
                        }
                    }
                }
            ]
        }
        ```
      3. Functionality: Post new (or update if existing already) `SiddataUserStudy` objects. 
6. `subject`: This route handles `Subject` objects.
   1. `POST`:
      1. URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "data": {
                "type": "Subject",                  # Respective object type string.
                "attributes": {
                    "name": str,                    # Name of the subject.
                    "description": str,             # Description of the subject.
                    "keywords": str,                # Keywords of the subject.
                    "studip_id": str                # Native ID of the subject.
                }
            }
        }
        ```
      3. Functionality: Post new (or update if existing already) `Subject` objects. 
7. `course`: This route handles `InheritingCourse` objects. Note: `StudipCourse` inherits from `InheritingCourse` which inherits from `EducationalResource`. 
   1. `POST`:
      1. URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "data": {
                "type": "Course",                   # Respective object type string.
                "attributes": {
                    "name": str,                    # Name of the course.
                    "description": str,             # Description of the course.
                    "place": str,                   # Place where the course is happening.
                    "start_time": int,              # Time stamp for the starting time of the course.
                    "end_time": int,                # Time stamp for the ending time of the course.
                    "start_semester": str           # Name of the where the course starts.
                    "end_semester": str             # Name of the semester where the course ends.
                    "url": str                      # URL to the course
                    "studip_id": str                # Native ID of the subject.
                },
                "relationships": {
                    "lecturers": {
                        "data": [
                            {
                                "type": "Person",
                                "id": str,          # `person_origin_id` of the `Person` object.
                            },
                        ]
                    },
                    "institute": {
                        "data": [
                            {
                                "type": "Institute",
                                "id": str           # Institute's ID
                            }
                        ]
                    }
                }
            }
        }
        ```
      3. Functionality: Post new (or update if existing already) `StudipCourse` objects. 
   2. `GET`: 
      1. URL Parameters: None
      2. Returned JSON structure:
        ```
        {
            "data": [
                {
                    "type": "Course",
                    "id": str,                          # The database ID of the `Goal` object.
                    "attributes": {
                        "title": str,                   # Course title.
                        "description": str,             # Course description.
                        "place": str,                   # Place where the course is happening.
                        "start_time": int,              # Time stamp for the starting time of the course.
                        "end_time": int,                # Time stamp for the ending time of the course.
                        "start_semester": str           # Name of the where the course starts.
                        "end_semester": str             # Name of the semester where the course ends.
                        "url": str                      # URL to the course
                        "studip_id": str                # Native ID of the subject.
                    }, 
                },
            ]
        }
        ```
      3. Functionality: Returns all `InheritingCourse` objects related to the given `origin`. 
      4. `GET/<course_origin_id>` returns a certain `StudipCourse` object addressed by its native ID.
8. `degree`:
   1. `POST`:
      1. URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "data": {
                "type": "Degree",                   # Respective object type string.
                "attributes": {
                    "name": str,                    # Name of the degree.
                    "description": str,             # Description of the degree.
                    "studip_id": str                # Native ID of the degree.
                }
            }
        }
        ```
      3. Functionality: Post new (or update if existing already) `Degree` objects. 
9.  `event`: This route handles `StudipEvent` objects.
   2. `POST`:
      1.  URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "data": {
                "type": "Event",                    # Respective object type string.
                "attributes": {
                    "start_time": int,              # Start time of the event.
                    "end_time": int,                # End time of the event.
                    "topic_title": str,             # Title of the event's topic. 
                    "topic_description: str,        # Description of the topic.
                    "studip_id": str                # Native ID of the event. 
                },
                "relationships": {
                    "course": {
                        "data": [
                            {
                                "type": "StudipCourse",
                                "id": str                   # Native ID of the corresponding course object.
                            }
                        ]
                    }
                }
            }
        }
        ```
      3. Functionality: Post new (or update if existing already) `StudipEvent` objects. 
10. `institute`: This route handles `Institute` objects.
   3.  `POST`:
      1.  URL Parameters: None
      2. Required JSON structure: 
        ```
        {
            "data": {
                "type": "Institute",                        # Respective object type string.
                "attributes": {
                    "name": str,                            # Name of the institute.
                    "url": str,                             # URL to the institute resource.
                    "studip_id": str                        # Native ID of the institute.
                }
            }
        }
        ```
      3. Functionality: Post new (or update if existing already) `Institute` objects. 
11. `person`: This route handles `Person` objects
    1.  `POST`:
      1. URL Parameters: None
      2. Required JSON structure (encryption algorithm is AES 128 CBC which takes its passphrase from `SIDDATA_KEY` and IV from `SIDDATA_IV`): 
        ```
        {
            "data": {
                "type": "Person" OR "Lecturer",             # Respective object type string.
                "attributes": {
                    "image": str,                           # Profile image as a Base64 encoded string.
                    "image_name": str,                      # File name of the image.
                    "first_name": str,                      # Ecrypted first name.
                    "surname": str,                         # Encrypted surname.
                    "description": str,                     # Encrypted description.
                    "email": str,                           # Encrypted email address.
                    "user_origin_id": str,                  # (Pseudonymized native) ID of the user which provided the `Person`. Not set if it is a `Lecturer`.
                    "person_origin_id": str,                # Native ID of the person object if it is a lecturer.
                    "title": str                            # Title. 
                }
            }
        }
        ```
      3. Functionality: Post new (or update if existing already) `Person` objects. 