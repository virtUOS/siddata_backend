BackendConfig
from django.test import TestCase
#logging.info(os.getcwd())
from recommenders.RM_gettogether import RM_gettogether
from .models import Degree, Subject, SiddataUser, SiddataUserStudy, Goal, Category, Origin, GoalCategory

# Global constants
DEBUG = False
ROUND = 2


def create_test_database_fixed_size(config, goal_comparison=False):
    """
    Creates a database with a fixed size suitable for the unit testing for user-similarity functions.

    :param config: A configuration with 4-tuples, which specifies which sus to create.
    It is always a tuple of (index(user), index(degree), index(subject), semester)
    :return: A tuple of lists for the data structures
    """

    # config: configuration of the SiddataUserStudy fields:
    # (a, b, c, d)
    #    0 <= a <= 5, "name" of user
    #    b: 0 = bachelor, 1 = master, 2 = 2-fächer-bachelor, 3 = "Bachelor of Science", 4 = "Master of Science",
    #    5 = bachelor
    #    c:
    #      [0] "Ägyptologie/Koptologie"  # 113001
    #      [1] "Afrikanistik"  # 113002
    #      [2], [3] "Agrarwissenschaft; Landwirtschaft"  # 758003
    #      [4] "Klassische Philologie"  # 108005
    #    d >= 1: number of semester

    origins = [
        Origin.objects.create(name="uos", type="type", api_endpoint="abc"),
    ]

    degrees = [
        Degree.objects.create(name="Bachelor", origin=origins[0], degree_origin_id="abc"),
        Degree.objects.create(name="Master", origin=origins[0], degree_origin_id="abc"),
        Degree.objects.create(name="2-Fächer Bachelor", origin=origins[0], degree_origin_id="abc"),
        Degree.objects.create(name="Bachelor of Science", origin=origins[0], degree_origin_id="abc"),
        Degree.objects.create(name="Master of Science", origin=origins[0], degree_origin_id="abc"),
        Degree.objects.create(name="bachelor", origin=origins[0], degree_origin_id="abc"),
    ]
    subjects = [
        Subject.objects.create(name="Ägyptologie/Koptologie", origin=origins[0], subject_origin_id="abc", destatis_subject_id=123456),
        Subject.objects.create(name="Afrikanistik", origin=origins[0], subject_origin_id="abc", destatis_subject_id=123456),
        Subject.objects.create(name="Agrarwissenschaft", origin=origins[0], subject_origin_id="abc", destatis_subject_id=122333),
        Subject.objects.create(name="Landwirtschaft", origin=origins[0], subject_origin_id="abc", destatis_subject_id=133444),
        Subject.objects.create(name="Klassische Philologie", origin=origins[0], subject_origin_id="abc", destatis_subject_id=144333),
        Subject.objects.create(name="same_sub2", origin=origins[0], subject_origin_id="abc", destatis_subject_id=144666),
        Subject.objects.create(name="diff_cat", origin=origins[0], subject_origin_id="abc", destatis_subject_id=255444),
    ]

    users = []
    for i in range(7):
        users.append(SiddataUser.objects.get_or_create(
            origin=origins[0],
            user_origin_id="abc",
        ))

    sus = []
    for i in config:
        sus.append(SiddataUserStudy.objects.create(
            user=users[i[0]],
            degree=degrees[i[1]],
            subject=subjects[i[2]],
            semester=i[3],
        ))

    names = [
        Goal.objects.create(title="Informatik", user=users[0]),
        Goal.objects.create(title="Programmieren in Rust", user=users[1]),
        Goal.objects.create(title="Programmieren in Python", user=users[2]),
        Goal.objects.create(title="Landwirtschaft", user=users[3]),
        Goal.objects.create(title="Wirtschaft", user=users[4]),
        Goal.objects.create(title="Kunst", user=users[5])
    ]

    super_categories = [
        Category.objects.create(name="root0"),
        Category.objects.create(name="root1")
    ]

    categories = [
        Category.objects.create(name="same_cat0", super_category=super_categories[0]),
        Category.objects.create(name="same_cat1", super_category=super_categories[0]),
        Category.objects.create(name="Fachliche Interessen", super_category=super_categories[1])
    ]

    if not goal_comparison:
        goal_categories = [
            # goal 0 - 3 are Fachliches Interesse
            GoalCategory.objects.create(goal=goals[0], category=categories[2], belongs_to=True),
            GoalCategory.objects.create(goal=goals[1], category=categories[2], belongs_to=True),
            GoalCategory.objects.create(goal=goals[2], category=categories[2], belongs_to=True),
            GoalCategory.objects.create(goal=goals[3], category=categories[2], belongs_to=True),
            # goal 4 - 5 have the same super category
            GoalCategory.objects.create(goal=goals[4], category=categories[0], belongs_to=True),
            GoalCategory.objects.create(goal=goals[5], category=categories[1], belongs_to=True)
        ]
    else:
        # If goal comparison is set to True, all goals are Fachliches Interesse, which means they are string compared
        goal_categories = [
            GoalCategory.objects.create(goal=goals[0], category=categories[2], belongs_to=True),
            GoalCategory.objects.create(goal=goals[1], category=categories[2], belongs_to=True),
            GoalCategory.objects.create(goal=goals[2], category=categories[2], belongs_to=True),
            GoalCategory.objects.create(goal=goals[3], category=categories[2], belongs_to=True),
            # goal 4 - 5 have the same super category
            GoalCategory.objects.create(goal=goals[4], category=categories[2], belongs_to=True),
            GoalCategory.objects.create(goal=goals[5], category=categories[2], belongs_to=True)
        ]
    # return (users, degrees, subjects, sus, goals, super_categories, categories, goal_categories)

    return {
        "origins": origins,
        "users": users,
        "degrees": degrees,
        "subjects": subjects,
        "sus": sus,
        "goals": goals,
        "super_categories": super_categories,
        "categories": categories,
        "goal_categories": goal_categories,
    }

class TestSimilarityFunctions(TestCase):
    """
    A test class to test the similarity functions of the RM Gettogether
    """

    def test_semester_similarity(self):

        # The index 3 at each tuple is the semester value
        sus_config = [
            (0, 0, 0, 2),
            (1, 1, 0, 4),
            (2, 0, 0, 2),
            (3, 0, 1, 8),
        ]
        data = create_test_database_fixed_size(sus_config)
        users = data["users"]

        # Create an instance of RM_gettogether
        my_social_recommender = RM_gettogether()
        # Some unit tests to see if the comparison yields expected results.
        # Semester 2 and 4 result in 0.5, 2 and 2 in 1, 2 and 8 in 0.25 and 4 and 8 in 0.5
        semester_similarity = my_social_recommender.compare_users(users[0], users[1], criteria=["semester"])
        self.assertEqual(semester_similarity, 0.5)
        semester_similarity = my_social_recommender.compare_users(users[0], users[2], criteria=["semester"])
        self.assertEqual(semester_similarity, 1)
        semester_similarity = my_social_recommender.compare_users(users[0], users[3], criteria=["semester"])
        self.assertEqual(semester_similarity, 0.25)
        semester_similarity = my_social_recommender.compare_users(users[1], users[3], criteria=["semester"])
        self.assertEqual(semester_similarity, 0.5)

    def test_multiple_criteria_comparison(self):
        sus_config = [
            (0, 0, 0, 2),
            (1, 1, 0, 4),
            (2, 0, 0, 8),
            (3, 0, 1, 8),
            (4, 1, 0, 2),
        ]
        data = create_test_database_fixed_size(sus_config)
        users = data["users"]
        # Create an instance of RM_gettogether
        my_RM = RM_gettogether()

        # Some unit tests, NOTE: only valid as long as Degree similatity function D(u1, u2) -> {0, 1}
        similarity = my_RM.compare_users(users[0], users[1], criteria=["semester", "degree"])
        self.assertEqual(similarity, 0.25)
        similarity = my_RM.compare_users(users[2], users[3], criteria=["semester", "degree"])
        self.assertEqual(similarity, 1)
        similarity = my_RM.compare_users(users[0], users[2], criteria=["semester", "degree"])
        self.assertEqual(similarity, 0.625)
        similarity = my_RM.compare_users(users[0], users[4], criteria=["semester", "degree"])
        self.assertEqual(similarity, 0.5)

    def test_same_semester_different_degree_similarity(self):
        sus_config = [
            (0, 0, 0, 2),
            (1, 1, 0, 4),
            (2, 1, 0, 2),
            (3, 1, 1, 4),
        ]
        data = create_test_database_fixed_size(sus_config)
        users = data["users"]
        # Create an instance of RM_gettogether
        my_RM = RM_gettogether()
        similarity = my_RM.compare_users(users[0], users[1], criteria=["same_semester_different_degree"])
        self.assertEqual(similarity, 0)
        similarity = my_RM.compare_users(users[0], users[2], criteria=["same_semester_different_degree"])
        self.assertEqual(similarity, 1)
        similarity = my_RM.compare_users(users[1], users[3], criteria=["same_semester_different_degree"])
        self.assertEqual(similarity, 0)

    def test_compare_subject_strings(self):
        string1 = "Ägyptologie/Koptologie"              #113001
        string2 = "Afrikanistik"                        #113002
        string3 = "Agrarwissenschaft; Landwirtschaft"   #758003
        string4 = "Klassische Philologie"               #108005

        my_RM = RM_gettogether()
        similarity = my_RM.compare_subject_strings(string1, string2)
        self.assertEqual(similarity, 0.75)
        similarity = my_RM.compare_subject_strings(string2, string1)
        self.assertEqual(similarity, 0.75)
        similarity = my_RM.compare_subject_strings(string1, string3)
        self.assertEqual(similarity, 0)
        similarity = my_RM.compare_subject_strings(string1, string4)
        self.assertEqual(similarity, 0.25)

    def test_compare_users_by_subject(self):
        sus_config = [
            (0, 1, 0, 0),
            (1, 1, 1, 1),
            (2, 0, 2, 2),
            (3, 1, 3, 3),
            (4, 0, 4, 4),
            (5, 1, 4, 4),
        ]
        # Subject is the number at index 2
        # [0] "Ägyptologie/Koptologie"  # 113001
        # [1] "Afrikanistik"  # 113002
        # [2], [3] "Agrarwissenschaft; Landwirtschaft"  # 758003
        # [4] "Klassische Philologie"  # 108005
        data = create_test_database_fixed_size(sus_config)
        users = data["users"]
        # Create an instance of RM_gettogether
        my_RM = RM_gettogether()
        similarity = my_RM.compare_users(users[0], users[1], criteria=["subject"])
        self.assertEqual(similarity, 0.75)
        similarity = my_RM.compare_users(users[0], users[2], criteria=["subject"])
        self.assertEqual(similarity, 0)
        similarity = my_RM.compare_users(users[2], users[3], criteria=["subject"])
        self.assertEqual(similarity, 1)
        similarity = my_RM.compare_users(users[0], users[4], criteria=["subject"])
        self.assertEqual(similarity, 0.25)
        similarity = my_RM.compare_users(users[4], users[5], criteria=["subject"])
        self.assertEqual(similarity, 1)


class TestUserRecommendationFunctions(TestCase):
    """
    A test class to test get_similar_user functions
    """

    def test_get_similar_users_from_list(self):
        sus_config = [
            (0, 0, 0, 2),
            (1, 1, 0, 4),
            (2, 0, 0, 6),
            (3, 0, 1, 8),
            (4, 1, 0, 3),
        ]
        data = create_test_database_fixed_size(sus_config)
        users = data["users"]

        # Create an instance of RM_gettogether
        my_RM = RM_gettogether()

        similar_users = my_RM.get_similar_users_from_list(
            users[0],
            [users[1], users[2], users[3], users[4]],
            2,
            ["semester"]
        )
        # If get_similar_users_from_list works correctly, user[4] and user[1] should be returned as a list.
        self.assertEqual(similar_users, [users[4], users[1]])

    def test_least_similar_parameter(self):
        sus_config = [
            (0, 0, 0, 2),
            (1, 1, 0, 4),
            (2, 0, 0, 6),
            (3, 0, 1, 8),
            (4, 1, 0, 3),
        ]
        data = create_test_database_fixed_size(sus_config)
        users = data["users"]

        # Create an instance of RM_gettogether
        my_RM = RM_gettogether()

        similar_users = my_RM.get_similar_users_from_list(
            users[0],
            [users[1], users[2], users[3], users[4]],
            2,
            ["semester"],
            most_similar = False,
        )

        self.assertEqual(similar_users, [users[3], users[2]])

        similar_users = my_RM.get_similar_users_from_list(
            users[2],
            [users[0], users[1], users[3], users[4]],
            3,
            ["semester"],
        )

        self.assertEqual(similar_users, [users[3], users[1], users[4]])

    def test_get_similar_users(self):
        sus_config = [
            (0, 0, 0, 2),
            (1, 1, 0, 4),
            (2, 0, 0, 6),
            (3, 0, 1, 8),
            (4, 1, 0, 3),
        ]
        data = create_test_database_fixed_size(sus_config)
        users = data["users"]
        # Create an instance of RM_gettogether
        my_RM = RM_gettogether()
        similar_users = my_RM.get_similar_users(users[0], 1, ["semester"])
        # This should return the most similar user according to the semester number, which is user 4.
        self.assertEqual(similar_users, [users[4]])

        # Test for longer list
        similar_users = my_RM.get_similar_users(users[0], 2, ["semester"])
        # This should return the most similar user according to the semester number, which is user 4.
        self.assertEqual(similar_users, [users[4], users[1]])

        # Test longer list and most_similar=False
        similar_users = my_RM.get_similar_users(users[3], 4, ["semester"])
        # This should return the most similar user according to the semester number, which is user 4.
        self.assertEqual(similar_users, [users[2], users[1], users[4], users[0]])

    # def test_exceptional_behavior(self):
    #     sus_config = [
    #         (0, 0, 0, 2),
    #         (1, 1, 0, 4),
    #         (2, 0, 0, 6),
    #         (3, 0, 1, 8),
    #         (4, 1, 0, 3),
    #         (5, 1, 0, 3),
    #         (6, 1, 0, 3),
    #         (6, 1, 0, 3),
    #     ]
    #     data = create_test_database_fixed_size(sus_config)
    #     users = data["users"]
    #     # Create an instance of RM_gettogether
    #     my_RM = RM_gettogether()
