from backend import models
from recommenders.RM_BASE import RM_BASE
import json
import logging


class RM_learning_orga(RM_BASE):
    """ Processes activities related to going abroad.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Lernorganisation"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Mit dieser Funktion kannst du dein Lernverhalten reflektieren und nachhaltige " \
                           "Lernstrategien einüben."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Was ist dein Ziel im Studium? Kurzfristig für Prüfungen lernen? Oder auch langfristig " \
                           "Wissen und Können aufbauen? Auch wenn es auf den ersten Blick aufwendig erscheint: Auf " \
                           "lange Sicht profitierst du, wenn du nicht nur kurz vor den Prüfungen „büffelst“, sondern " \
                           "dein Lernen vor allem auch vorausschauend planst und proaktiv gestaltest. Lerne nicht " \
                           "nur „auf Sicht“, sondern auch „auf lange Sicht“. Die folgenden Empfehlungen helfen " \
                           "dir dabei."
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "lernbegleitung.png"
        # determines arrangement in Frontend
        self.ORDER = 7
        # This string tells the user which data is required for this recommender
        self.DATA_INFO = "Diese Funktion speichert diejenigen Daten, die du aktiv eingibst."
        # Reference to the database object, can be used as value vor recommender attribute in goals.
        self.recommender = models.Recommender.objects.get_or_create(
            name=self.get_name(),
            description=self.DESCRIPTION,
            classname=self.__class__.__name__,
            image=self.IMAGE,
            order=self.ORDER,
            data_info=self.DATA_INFO,
        )[0]

        self.LIST_questions = ["Ich gehe meine Aufzeichnungen durch und mache mir dazu eine Gliederung mit den "
                               "wichtigsten Punkten.",
                               "Ich stelle mir aus Mitschrift, Skript oder Literatur kurze Zusammenfassungen mit den "
                               "Hauptideen zusammen.",
                               "Ich stelle wichtige Fachausdrücke und Definitionen in eigenen Listen zusammen.",
                               "Ich versuche, neue Begriffe oder Theorien auf mir bereits bekannte Begriffe und "
                               "Theorien zu beziehen.",
                               "Ich denke mir konkrete Beispiele zu bestimmten Lerninhalten aus.",
                               "Ich beziehe das, was ich lerne, auf meine eigenen Erfahrungen.",
                               "Ich frage mich, ob der Text, den ich gerade durcharbeite, wirklich überzeugend ist.",
                               "Ich gehe an die meisten Texte kritisch heran.",
                               "Das was ich lerne, prüfe ich auch kritisch. ",
                               "Ich lerne eine selbst erstellte Übersicht mit den wichtigsten Fachtermini auswendig.",
                               "Ich lerne Regeln, Fachbegriffe oder Formeln auswendig.",
                               "Ich lerne den Lernstoff anhand von Skripten oder andere Aufzeichnungen möglichst "
                               "auswendig.",
                               "Ich formuliere Lernziele, an denen ich dann mein Lernen ausrichte.",
                               "Ich mache mir vor dem Lernen Gedanken, wie ich lernen will. ",
                               "Ich plane mein Vorgehen beim Lernen nicht.",
                               "Um Wissenslücken festzustellen, rekapituliere ich die wichtigsten Inhalte, ohne meine "
                               "Unterlagen zu Hilfe zu nehmen.",
                               "Ich stelle mir Fragen zum Stoff, um zu überprüfen, ob ich alles verstanden habe.",
                               "Falls im Lernstoff Fragen oder Test enthalten sind, nutze ich diese, um mich selbst zu "
                               "überprüfen. ",
                               "Ich verändere meine Lerntechnik, wenn ich auf Schwierigkeiten stoße.",
                               "Ich verändere meine Lernpläne, wenn ich merke, dass sie sich nicht umsetzen lassen.",
                               "Wenn ich merke, dass mein Vorgehen beim Lernen nicht erfolgreich ist, verändere ich "
                               "es.",
                               "Es fällt mir schwer, bei der Sache zu bleiben.",
                               "Beim Lernen merke ich, dass meine Gedanken abschweifen.",
                               "Wenn ich lerne, bin ich leicht abzulenken.",
                               "Wenn ich mir ein bestimmtes Pensum zum Lernen vorgenommen habe, bemühe ich mich, "
                               "es auch zu schaffen.",
                               "Ich gebe nicht auf, auch wenn der Stoff sehr schwierig oder komplex ist.",
                               "Wenn es sein muss, lerne ich auch spätabends und am Wochenende.",
                               "Beim Lernen halte ich mich an einen bestimmten Zeitplan.",
                               "Ich lege die Stunden, die ich täglich mit Lernen verbringe, durch einen Zeitplan fest.",
                               "Ich lege vor jeder Lernphase eine bestimmte Zeitdauer fest.",
                               "Ich gestalte meine Umgebung so, dass ich möglichst wenig vom Lernen abgelenkt werde.",
                               "Zum Lernen sitze ich immer am selben Platz.",
                               "Mein Arbeitsplatz ist so gestaltet, dass ich alles schnell finden kann.",
                               "Ich bearbeite Texte oder Aufgaben zusammen mit meinen Studienkolleg*innen.",
                               "Ich nehme mir Zeit, um mit Studienkolleg*innen über den Stoff zu diskutieren.",
                               "Wenn mir etwas nicht klar ist, so frage ich einen Studienkollegen um Rat.",
                               "Ich suche nach weiterführender Literatur, wenn mir bestimmte Inhalte noch nicht ganz "
                               "klar sind.",
                               "Fehlende Informationen suche ich mir aus verschiedenen Quellen zusammen (z.B. "
                               "Mitschriften, Bücher, Fachzeitschriften).",
                               "Ich ziehe zusätzlich Literatur heran, wenn meine Aufzeichnungen unvollständig sind."]

    def get_likert_scale(self, items):

        if items == 4:
            likert_scale_answers_4 = [
                "trifft nicht zu",
                "trifft eher nicht zu",
                "trifft eher zu",
                "trifft zu"]
            return likert_scale_answers_4

        elif items == 5:
            likert_scale_answers_5 = [
                "trifft nicht zu",
                "trifft eher nicht zu",
                "teils - teils",
                "trifft eher zu",
                "trifft zu"]
            return likert_scale_answers_5

        elif items == 7:
            likert_scale_answers_7 = [
                "trifft überhaupt nicht zu",
                "trifft wenig zu",
                "trifft eher nicht zu",
                "teils teils",
                "trifft eher zu",
                "trifft viel zu",
                "trifft vollständig zu"]
            return likert_scale_answers_7

        else:
            return "no scale for {}".format(items)

    def get_scale_value(self, items):
        """
        transfer the value of likert scale from words into numbers
        """
        if items == 4:
            scale_value_dic_4 = {
                "trifft nicht zu": 1,
                "trifft eher nicht zu": 2,
                "trifft eher zu": 3,
                "trifft zu": 4}
            return scale_value_dic_4

        elif items == 5:
            scale_value_dic_5 = {
                "trifft nicht zu": 1,
                "trifft eher nicht zu": 2,
                "teils - teils": 3,
                "trifft eher zu": 4,
                "trifft zu": 5}
            return scale_value_dic_5

        elif items == 7:
            scale_value_dic_7 = {
                "trifft überhaupt nicht zu": 1,
                "trifft wenig zu": 2,
                "trifft eher nicht zu": 3,
                "teils teils": 4,
                "trifft eher zu": 5,
                "trifft viel zu": 6,
                "trifft vollständig zu": 7}
            return scale_value_dic_7

        else:
            return "no scale for {}".format(items)

    # FEEDBACK FUNCTIONS TO PROCESS INPUT OF LIST QUESTIONNAIRE #
    def get_feedback_ksor(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p>Kurze Wiederholung: <strong>Kognitive Strategien</strong> umfassen diejenigen Prozesse, " \
                       "die du einsetzt, um dir den Lernstoff zu erarbeiten und zu merken. " \
                       "Dazu gehören unter anderem <strong>Organisieren</strong>, <strong>Elaborieren</strong>, " \
                       "<strong>Kritisches Prüfen</strong> sowie <strong>Wiederholen</strong>.</p>" \
                       "<p><strong>1. Organisieren</strong><br>Diese Strategie weist darauf hin, " \
                       "dass es hilfreich sein kann, " \
                       "den Stoff, mit dem du dich beschäftigst, in geeigneter Weise für dich aufzubereiten.</p> " \
                       "<p>Es könnte dir helfen, wenn du den Stoff, " \
                       "mit dem du dich beschäftigst, systematisch " \
                       "aufbereiten würdest: Du könntest dir Zusammenfassungen und Gliederungen anfertigen " \
                       "und deinen Lernstoff so ordnen, dass du ihn dir gut einprägen kannst.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p>Kurze Wiederholung: <strong>Kognitive Strategien</strong> umfassen diejenigen Prozesse, " \
                       "die du einsetzt, um dir den Lernstoff zu erarbeiten und zu merken. " \
                       "Dazu gehören unter anderem <strong>Organisieren</strong>, <strong>Elaborieren</strong>, " \
                       "<strong>Kritisches Prüfen</strong> sowie <strong>Wiederholen</strong>.</p>" \
                       "<p><strong>1. Organisieren</strong><br>Diese Strategie weist darauf hin, dass es hilfreich " \
                       "sein kann, " \
                       "den Stoff, mit dem du dich beschäftigst, in geeigneter Weise für dich aufzubereiten.</p>" \
                       "<p>Du könntest dich noch darin verbessern, " \
                       "den Stoff, mit dem du dich beschäftigst, systematisch aufzuarbeiten, " \
                       "indem du dir regelmäßiger Zusammenfassungen und Gliederungen anfertigst und deinen " \
                       "Lernstoff so ordnest, dass du ihn dir gut einprägen kannst.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p>Kurze Wiederholung: <strong>Kognitive Strategien</strong> umfassen diejenigen Prozesse, " \
                       "die du einsetzt, um dir den Lernstoff zu erarbeiten und zu merken. " \
                       "Dazu gehören unter anderem <strong>Organisieren</strong>, <strong>Elaborieren</strong>, " \
                       "<strong>Kritisches Prüfen</strong> sowie <strong>Wiederholen</strong>.</p>" \
                       "<p><strong>1. Organisieren</strong><br>Diese Strategie weist darauf hin, " \
                       "dass es hilfreich sein kann, " \
                       "den Stoff, mit dem du dich beschäftigst, in geeigneter Weise für dich aufzubereiten.</p>" \
                       "<p>Prima! Du arbeitest den Stoff, " \
                       "mit dem du dich beschäftigst, systematisch auf.</p>"
            return feedback

    def get_feedback_ksel(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>2. Elaborieren</strong><br>" \
                       "Diese Strategie weist darauf hin, dass es hilfreich sein kann, beim Lernen neuen Stoff " \
                       "in ein Netzwerk umfassenderer Bezüge einzubinden.</p>" \
                       "<p>Du bindest deinen Lernstoff noch nicht in größere Zusammenhänge ein. Folgende " \
                       "Empfehlungen könnten dir helfen.<br> " \
                       "1. Frage dich vor dem Lernen, was du schon über das Thema weißt." + "<br>" + \
                       "2. Versuche den Stoff mit deinem Vorwissen zu verknüpfen.<br>" \
                       "3. Suche nach Beispielen, Bildern oder eigenen Erfahrungen.<br>" \
                       "4. Frage dich, ob es Ähnlichkeiten zu anderen Themen gibt, die dir schon vertraut sind. " \
                       "</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>2. Elaborieren</strong><br>" \
                       "Diese Strategie weist darauf hin, dass es hilfreich sein kann, beim Lernen neuen Stoff " \
                       "in ein Netzwerk umfassenderer Bezüge einzubinden.</p>" \
                       "<p>Du könntest dich noch darin verbessern, " \
                       "deinen Lernstoff in größere Zusammenhänge einzubinden, indem du regelmäßiger " \
                       "vor dem Lernen schaust, was du schon über das Thema weißt, neues Wissen mit deinem " \
                       "Vorwissen verknüpfst und systematisch nach Beispielen, Bildern oder eigenen Erfahrungen " \
                       "für deinen Lernstoff suchst.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>2. Elaborieren</strong><br>" \
                       "Diese Strategie weist darauf hin, dass es hilfreich sein kann, beim Lernen neuen Stoff " \
                       "in ein Netzwerk umfassenderer Bezüge einzubinden.</p>" \
                       "<p>Prima! Du bindest deinen Lernstoff in " \
                       "größere Zusammenhänge ein.</p>"
            return feedback

    def get_feedback_kskp(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>3. Kritisches Prüfen</strong><br>Diese Strategie weist darauf hin, " \
                       "dass du dein Verständnis für den Stoff durch kritisches Hinterfragen " \
                       "von Aussagen und Begründungszusammenhängen vertiefen kannst.</p>" \
                       "<p>Du nimmst den Lernstoff noch ungeprüft zur Kenntnis. Du solltest versuchen, Aussagen " \
                       "und Begründungszusammenhänge stärker zu hinterfragen:<br> " \
                       "1. Sind die Aussagen, Interpretationen und Schlussfolgerungen plausibel?<br> " \
                       "2. Erscheint dir etwas widersprüchlich?<br> " \
                       "3. Welche kritischen Nachfragen könntest du stellen?</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>3. Kritisches Prüfen</strong><br>Diese Strategie weist darauf hin, " \
                       "dass du dein Verständnis für den Stoff durch kritisches Hinterfragen " \
                       "von Aussagen und Begründungszusammenhängen vertiefen kannst.</p> " \
                       "<p>Du könntest dich noch darin verbessern, den Stoff, mit dem du dich beschäftigst, kritisch " \
                       "zu prüfen. Frage dich, ob Behauptungen und Schlussfolgerungen ausreichend belegt sind, " \
                       "stelle kritische Nachfragen und vergleiche Vor- und Nachteile " \
                       "verschiedener theoretischer Konzeptionen.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>3. Kritisches Prüfen</strong><br>Diese Strategie weist darauf hin, " \
                       "dass du dein Verständnis für den Stoff durch kritisches Hinterfragen " \
                       "von Aussagen und Begründungszusammenhängen vertiefen kannst.</p> " \
                       "<p>Prima! Du vertiefst dein Verständnis für den Stoff durch ein kritisches Hinterfragen " \
                       "von Aussagen und Begründungszusammenhängen.</p>"
            return feedback

    def get_feedback_kswh(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>4. Wiederholen</strong><br>Diese Strategie weist darauf hin, " \
                       "dass es hilfreich sein kann, dir wichtige Fakten und Regeln durch Wiederholen " \
                       "einzuprägen.</p><p>Du verzichtest auf reines Wiederholen und Auswendiglernen. " \
                       "Allerdings solltest du dafür Sorge tragen, dass du dir wichtige Fachbegriffe, " \
                       "Formeln oder Regeln sorgfältig einprägst. Achte außerdem darauf " \
                       "(sofern du es nicht ohnehin schon machst), dir die zugrundeliegenden " \
                       "Zusammenhänge klarzumachen und immer mal wieder ins Gedächtnis zu rufen.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>4. Wiederholen</strong><br>Diese Strategie weist darauf hin, " \
                       "dass es hilfreich sein kann, dir wichtige Fakten und Regeln durch Wiederholen " \
                       "einzuprägen.</p><p>Du tendierst dazu, dir Fakten und Regeln durch reines Wiederholen und " \
                       "Auswendiglernen einzuprägen. Achte aber auch darauf, dir die zugrundeliegenden " \
                       "Zusammenhänge klarzumachen.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>4. Wiederholen</strong><br>Diese Strategie weist darauf hin, " \
                       "dass es hilfreich sein kann, dir wichtige Fakten und Regeln durch Wiederholen " \
                       "einzuprägen.</p><p>Du prägst dir Fakten und Regeln durch reines Wiederholen und " \
                       "Auswendiglernen ein. Achte künftig auch darauf, dir die dahinter liegenden " \
                       "Zusammenhänge klarzumachen.</p>"
            return feedback

    def get_feedback_msp(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p>Kurze Wiederholung: <strong>Metakognitive Strategien</strong> dienen dazu, " \
                       "das eigene Lernen bewusst zu <strong>planen</strong>, " \
                       "zu <strong>überwachen</strong> und" \
                       " zu <strong>regulieren</strong>.</p>" \
                       "<p><strong>1. Planung</strong><br>" \
                       "Du achtest noch nicht darauf, deine Lernschritte zu planen. Du solltest versuchen, " \
                       "dir Gedanken über die Auswahl und den Umfang deines Lernstoffes und über die Reihenfolge " \
                       "der Lernschritte zu machen.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p>Kurze Wiederholung: <strong>Metakognitive Strategien</strong> dienen dazu, " \
                       "das eigene Lernen bewusst zu <strong>planen</strong>, " \
                       "zu <strong>überwachen</strong> und" \
                       " zu <strong>regulieren</strong>.</p>" \
                       "<p><strong>1. Planung</strong><br>" \
                       "Du könntest noch stärker darauf achten, dass du deine Lernschritte gut " \
                       "planst. Du könntest regelmäßiger deine Lernziele formulieren und dir noch stärker Gedanken " \
                       "über die Auswahl und Umfang des zu lernenden Stoffes und über die Reihenfolge " \
                       "der Lernschritte zu machen.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p>Kurze Wiederholung: <strong>Metakognitive Strategien</strong> dienen dazu, " \
                       "das eigene Lernen bewusst zu <strong>planen</strong>, " \
                       "zu <strong>überwachen</strong> und" \
                       " zu <strong>regulieren</strong>.</p>" \
                       "<p><strong>1. Planung</strong><br>" \
                       "Prima! Du planst deine Lernprozesse und formulierst für dich Lernziele. Wenn du es nicht " \
                       "sowieso schon tust, könntest du dir auch Gedanken über die Auswahl und den Umfang des " \
                       "zu lernenden Stoffes machen und die Reihenfolge der Lernschritte festlegen.</p>"
            return feedback

    def get_feedback_msu(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>2. Überwachung</strong><br>" \
                       "Du achtest noch nicht darauf, deinen Lernfortschritt zu kontrollieren." \
                       "Während des Lernens könntest du darauf achten, " \
                       "ob du auch wirklich alles gut verstanden hast, indem du dir Fragen überlegst, " \
                       "die du anschließend selbst beantwortest, den Stoff jemand anderem erklärst, oder den Stoff " \
                       "rekapitulierst, ohne in deine Unterlagen zu schauen.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>2. Überwachung</strong><br>" \
                       "Du könntest noch stärker darauf achten, dass du deinen Lernfortschritt kontrollierst." \
                       " Du könntest während des Lernens noch stärker darauf achten, ob du auch wirklich " \
                       "alles gut verstanden hast, indem du dir Fragen überlegst, die du anschließend selbst" \
                       " beantwortest, oder den Stoff rekapitulierst, ohne in deine Unterlagen zu schauen.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>2. Überwachung</strong><br>" \
                       "Prima! Du überwachst deinen Lernprozess gut, indem du kontrollierst, ob du auch alles " \
                       "wirklich verstanden hast.</p>"
            return feedback

    def get_feedback_msr(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>3. Regulation</strong><br>" \
                       "Du achtest noch nicht darauf, dein Lernverhalten flexibel an die jeweiligen " \
                       "Anforderungen anzupassen. Du solltest dein " \
                       "Lernverhalten in schwierigen oder anspruchsvollen Situationen anpassen, " \
                       "indem du z.B. langsamer vorgehst und genau darauf achtest, was du noch " \
                       "nicht verstanden hast, oder dein Lernverhalten noch einmal überdenkst.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>3. Regulation</strong><br>" \
                       "Du könntest noch stärker darauf achten, dass du dein Lernverhalten flexibel an " \
                       "die jeweiligen Anforderungen anpasst. " \
                       "Du könntest dich darin verbessern, dein Lernverhalten in schwierigen oder " \
                       "anspruchsvollen Situationen anzupassen, indem du langsamer vorgehst und genau darauf " \
                       "achtest, was du noch nicht verstanden hast, oder dein Lernverhalten noch " \
                       "einmal überdenkst.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>3. Regulation</strong><br>" \
                       "Prima! Du passt dein Lernverhalten an die jeweiligen Lernanforderungen an. Wenn du es nicht " \
                       "sowieso schon tust, könntest du bei schwierigen oder anspruchsvollen Situationen " \
                       "langsamer vorgehen und genau darauf achten, was du noch nicht verstanden hast.</p>"
            return feedback

    def get_feedback_iram(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p>Kurze Wiederholung: <strong>Interne Ressourcen</strong>, bezeichnen deine Potentiale, " \
                       "die du für dein Lernen mobilisierst. Dazu gehören unter anderen " \
                       "<strong>Aufmerksamkeit</strong>, <strong>Anstrengung</strong>, und " \
                       "<strong>Zeitmanagement</strong>.</p>" \
                       "<p><strong>1. Aufmerksamkeit</strong><br>" \
                       "Prima! Du bist beim Lernen gut konzentriert.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p>Kurze Wiederholung: <strong>Interne Ressourcen</strong>, bezeichnen deine Potentiale, " \
                       "die du für dein Lernen mobilisierst. Dazu gehören unter anderen " \
                       "<strong>Aufmerksamkeit</strong>, <strong>Anstrengung</strong>, und " \
                       "<strong>Zeitmanagement</strong>.</p>" \
                       "<p><strong>1. Aufmerksamkeit</strong><br>" \
                       "Du könntest deine Konzentrationsfähigkeit noch verbessern.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p>Kurze Wiederholung: <strong>Interne Ressourcen</strong>, bezeichnen deine Potentiale, " \
                       "die du für dein Lernen mobilisierst. Dazu gehören unter anderen " \
                       "<strong>Aufmerksamkeit</strong>, <strong>Anstrengung</strong>, und " \
                       "<strong>Zeitmanagement</strong>.</p>" \
                       "<p><strong>1. Aufmerksamkeit</strong><br> " \
                       "Du bist beim Lernen unkonzentriert.</p>"
            return feedback

    def get_feedback_irag(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>2. Anstrengung</strong><br>" \
                       "Du bist noch nicht bereit oder in der Lage, beim Lernen besondere Anstrengungen auf " \
                       "dich zu nehmen. Damit mobilisierst du aber noch nicht genügend Potentiale, " \
                       "um deine Lern- und Studienziele zu erreichen.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>2. Anstrengung</strong><br>" \
                       "Du könntest deine Bereitschaft oder deine Fähigkeiten, beim Lernen besondere Anstrengungen " \
                       "auf dich zu nehmen, noch optimieren.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>2. Anstrengung</strong><br>" \
                       "Prima! Du nimmst vermehrte Anstrengungen in Kauf, " \
                       "um deine Studien- und Lernziele zu erreichen.</p>"
            return feedback

    def get_feedback_irzm(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>3. Zeitmanagement</strong><br>" \
                       "Dein Zeitmanagement ist beim Lernen noch nicht optimal.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>3. Zeitmanagement</strong><br>" \
                       "Du könntest dein Zeitmanagement beim Lernen noch verbessern.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>3. Zeitmanagement</strong><br>" \
                       "Prima! Du hast beim Lernen ein gutes Zeitmanagement.</p>"
            return feedback

    def get_feedback_erlg(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p>Kurze Wiederholung: <strong>Externe Ressourcen</strong>, bezeichnen " \
                       "günstige Rahmenbedingungen, die du dir für dein Lernen schaffst, " \
                       "insbesondere, deine <strong>Lernumgebung</strong>, <strong>Lernen mit " \
                       "Studienkolleg*innen</strong> und <strong>Literaturrecherche</strong>.</p>" \
                       "<p><strong>1. Lernumgebung</strong><br>" \
                       "Deine Lernumgebung ermöglicht dir noch nicht, konzentriert und effektiv zu arbeiten.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p>Kurze Wiederholung: <strong>Externe Ressourcen</strong>, bezeichnen " \
                       "günstige Rahmenbedingungen, die du dir für dein Lernen schaffst, " \
                       "insbesondere, deine <strong>Lernumgebung</strong>, <strong>Lernen mit " \
                       "Studienkolleg*innen</strong> und <strong>Literaturrecherche</strong>.</p>" \
                       "<p><strong>1. Lernumgebung</strong><br>" \
                       "Du kannst deine Lernumgebung noch verbessern, um konzentriert und effektiv zu arbeiten.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p>Kurze Wiederholung: <strong>Externe Ressourcen</strong>, bezeichnen " \
                       "günstige Rahmenbedingungen, die du dir für dein Lernen schaffst, " \
                       "insbesondere, deine <strong>Lernumgebung</strong>, <strong>Lernen mit " \
                       "Studienkolleg*innen</strong> und <strong>Literaturrecherche</strong>.</p>" \
                       "<p><strong>1. Lernumgebung</strong><br>" \
                       "Prima! Du schaffst dir eine äußere Lernumgebung die dir ein konzentriertes und " \
                       "effektives Arbeiten ermöglicht.</p>"
            return feedback

    def get_feedback_erms(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>2. Lernen mit Studienkolleg*innen</strong><br>" \
                       "Du arbeitest wenig mit deinen Studienkolleg*innen zusammen. " \
                       "Wenn du dich mit deinen Studienkolleg*innen mehr vernetzen würdest, " \
                       "könntest du darüber in deinem Studium noch mehr Unterstützung erfahren.<br>" \
                       "Dazu kannst du auch die Funktion „get together“ nutzen.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>2. Lernen mit Studienkolleg*innen</strong><br>" \
                       "Du könntest dich noch mehr mit deinen Studienkolleg*innen vernetzen und darüber " \
                       "noch mehr Unterstützung in deinem Studium erfahren.<br>" \
                       "Dazu kannst du auch die Funktion „get together“ nutzen.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>2. Lernen mit Studienkolleg*innen</strong><br>" \
                       "Prima! Du arbeitest mit deinen Studienkolleg*innen zusammen und erfährst damit " \
                       "Unterstützung in deinem Studium.<br>" \
                       "Falls du darüber hinaus noch an weiteren Kontakten interessiert bist, " \
                       "kannst du auch die Funktion „get together“ nutzen.</p>"
            return feedback

    def get_feedback_erlr(self, value):
        """
        :param value: the value of specific strategy in the questionnaire
        :return: return a corresponding feedback to the specific strategy
        """
        if value <= 7.5:
            feedback = "<p><strong>3. Literaturrecherche</strong><br>" \
                       "Du greifst bei Verständnisproblemen noch nicht auf zusätzliche Literatur zurück. " \
                       "Ein Studium bedeutet aber auch, viel und selbständig zu lesen.</p>"
            return feedback

        elif 7.5 < value < 12:
            feedback = "<p><strong>3. Literaturrecherche</strong><br>" \
                       "Du könntest noch etwas stärker auf zusätzliche Literatur zurückgreifen – immerhin " \
                       "bedeutet ein Studium, viel und selbständig zu lesen.</p>"
            return feedback

        elif value >= 12:
            feedback = "<p><strong>3. Literaturrecherche</strong><br>" \
                       "Prima! Bei Kenntnislücken oder Verstehensproblemen versuchst du dir durch zusätzliche " \
                       "Literatur zu helfen. Damit setzt du um, was ein Studium bedeutet: " \
                       "viel und selbständig zu lesen.</p>"
            return feedback

    def initialize_templates(self):
        """
        Creates and updates all templates of this recommender
        Is executed at server startup
        """
        super().initialize_templates()

        order = 2000

        # Initial question
        initial_question = models.Question.objects.create(
            question_text="Du kannst dich hier mit folgenden Themen und Fragestellungen beschäftigen:",
            answer_type="checkbox",
            selection_answers=["Wie erarbeite ich mir meinen Lernstoff?",
                               "Lernstoff wiederholen und festigen.",
                               "Mein Lernen organisieren."]
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("initial_question"),
            defaults={
                "title": "Allgemeine Informationen",
                "description": "Allgemeine Informationen",
                "type": "question",
                "status": "template",
                "question": initial_question,
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("lernstoff_erarbeiten_initial"),
            defaults={
                "title": "Lernstoff erarbeiten",
                "description": "Im ersten Schritt geht es darum, wie du dir den Lernstoff effektiv erarbeiten "
                          "kannst. Zunächst solltest du dir einen Überblick über das Material verschaffen, das "
                          "du bearbeiten willst (survey). Fang also nicht gleich an, einen Text von vorne bis "
                          "hinten zu lesen, sondern orientierte dich zunächst am Titel, an Zusammenfassungen "
                          "(Abstract), an den Zwischenüberschriften, an der Einleitung, am Fazit und an weiteren "
                          "strukturierenden Textbestandteilen (Bilder, Tabellen, Kästchen etc.). Bei ganzen "
                          "Büchern liest du zunächst die Umschlagsrückseite und schaust dir das Inhaltsverzeichnis "
                          "an, dann blätterst du die einzelnen Kapitel erst einmal nur durch und liest die "
                          "Zwischenüberschriften und Kapitelzusammenfassungen. Dieser Schritt dauert 5 - "
                          "10 Minuten. Auf diese Weise bekommst du einen Eindruck davon, was du anschließend "
                          "lesen wirst. Außerdem kannst du dabei schon einmal die Grundgedanken identifizieren "
                          "und erste Fragen formulieren (vgl. den nächsten Schritt). Wenn du mehrere Bücher oder "
                          "Fachartikel lesen musst, kannst du auf diese Weise auch schon Wichtiges und Unwichtiges "
                          "sortieren.",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("wiederholen_festigen_initial"),
            defaults={
                "title": "Wiederholen und Festigen",
                "description": "Ein wichtiger Punkt beim Lernen ist das Wiederholen und Festigen. Neuen Lernstoff solltest "
                          "du am Anfang in kurzen Abständen widerholen, anschließend in größer werdenden Abständen: "
                          "zunächst nach einem Tag, dann nach ein paar Tagen, noch einmal nach einer Woche, und "
                          "schließlich noch einmal nach einem Monat (Wiederholungsintervalle). Wichtig dabei ist: "
                          "Beim Wiederholen nicht mechanisch abspulen, sondern mit eigenen Worten aus dem Gedächtnis "
                          "abrufen. Du kannst dir dabei in einem inneren Dialog Fragen stellen und den Inhalt anhand "
                          "von Beispielen erläutern. Wenn du dabei entdeckst, dass du etwas vergessen oder doch nicht "
                          "gut verstanden hast, notiere dir dies und arbeite es zu gegebener Zeit nach.",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("organisation_lernen_initial"),
            defaults={
                "title": "Organisation des Lernens",
                "description": "Zum Lernen gehört, dass du deinen Lernprozess effektiv organisierst. Insbesondere solltest "
                          "du beim Lernen ausdrücklich eine Zeitplanung vornehmen, indem du Zeitfenster für das Lernen "
                          "definierst. Mach eine schriftliche Aufstellung – für den Tag und für die Woche:"
                          "<ul>"
                          "<li>To-do-Liste: Welches Lernmaterial muss ich konkret bearbeiten? Welche Texte muss ich "
                          "lesen?</li>"
                          "<li>Wie viel Zeit benötige ich dafür?</li>"
                          "<li>Welche festen Termine habe ich heute / diese Woche?</li>"
                          "<li>Wo sind Zeitfenster zum Lernen?</li>"
                          "<li>Trage deine Lernaktivitäten in geeignete Zeitfenster ein – lege damit fest, was du zu "
                          "welcher Zeit machen wirst.</li>"
                          "<li>Prüfe abends, ob du deinen Tagesplan eingehalten hast, und prüfe am Samstag, ob du "
                          "deinen Wochenplan eingehalten hast.</li>"
                          "<li>Falls du deine Pläne nicht eingehalten hast: Warum nicht? Was kannst du ändern?</li>"
                          "</ul>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )
        order += 1

        # initialize the LIST question entry question
        initial_LIST_question = models.Question.objects.create(
            question_text="<p>Hier kannst du deine Strategien überprüfen, die du beim Lernen anwendest. "
                          "Anschließend bekommst du ein Feedback mit weiteren Empfehlungen. Das Ausfüllen des "
                          "Fragebogens dauert <strong>ca. 10 Minuten</strong>. Der Fragebogen beruht auf der "
                          "Kurzversion des LIST – Fragebogen zu Lernstrategien im Studium (Wild / Schiefele 1994, "
                          "Klingsieck 2018).</p> <p><strong>Möchtest du den Fragebogen ausfüllen?</strong></p>",
            answer_type="selection",
            selection_answers=["Ja", "Nein"]
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("initial_LIST_question"),
            defaults={
                "title": "Lernstrategien-Fragebogen",
                "description": "Lernstrategien-Fragebogen",
                "type": "question",
                "status": "template",
                "question": initial_LIST_question,
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        # initialize LIST questionnaire using form-attribute
        likert_scale = self.get_likert_scale(5)
        n_item = 1

        for element in self.LIST_questions:
            q = models.Question.objects.get_or_create(
                question_text=element,
                answer_type="likert",
                selection_answers=likert_scale
            )[0]
            q.save()

            t = models.ActivityTemplate.objects.update_or_create(
                template_id=self.get_template_id("item_{}".format(n_item)),
                defaults={
                    "title": "Fragebogen",
                    "description": n_item,
                    "type": "question",
                    "status": "template",
                    "question": q,
                    "order": 1000000000 + n_item,
                    "feedback_size": 0,
                    "form": 10,
                }
            )[0]
            t.save()
            n_item += 1


    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param siddatauser_id: Id of the user who logged in for the first time.
        :return: True if successful
        """
        goal = self.activate_recommender_for_user_and_create_first_goal(user)
        goal.order = 1
        goal.save()

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("initial_question"),
            goal=goal,
        )

        LIST_goal = models.Goal.objects.get_or_create(
            title="Lernstrategien",
            description="Hier kannst du dein Lernverhalten reflektieren.",
            userrecommender=goal.userrecommender,
            order=2,
        )[0]
        LIST_goal.save()

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("initial_LIST_question"),
            goal=LIST_goal,
        )

        return True

    def initialize_questionnaire(self, goal):

        n_item = 1
        for element in self.LIST_questions:

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("item_{}".format(n_item)),
                goal=goal,
            )
            n_item += 1

        return True

    def process_activity(self, activity):
        """
        This function processes the incoming activities which were processed by the user.
        :param activity:  activity
        :return: True if successful
        """

        if activity.has_template(self.get_template_id("initial_LIST_question")):
            if "Ja" in activity.answers:
                self.initialize_questionnaire(activity.goal)

        if "Wie erarbeite ich mir meinen Lernstoff?" in activity.answers:
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("lernstoff_erarbeiten_initial"),
                goal=activity.goal,
            )

        if "Lernstoff wiederholen und festigen." in activity.answers:
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("wiederholen_festigen_initial"),
                goal=activity.goal,
            )

        if "Mein Lernen organisieren." in activity.answers:
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("organisation_lernen_initial"),
                goal=activity.goal,
            )

        #########################################################################
        """Hier kommt neuer Code"""

        if activity.title == "Fragebogen":

            results_learningstr = activity.goal.get_property(
                key="results_learningstr"
            )

            if results_learningstr is None:
                results_learningstr = {"ksor": [],
                                       "ksel": [],
                                       "kskp": [],
                                       "kswh": [],
                                       "msp": [],
                                       "msu": [],
                                       "msr": [],
                                       "iram": [],
                                       "irag": [],
                                       "irzm": [],
                                       "erlg": [],
                                       "erlms": [],
                                       "erlr": [],
                                       "count": 0,
                                       }
            else:
                results_learningstr = json.loads(results_learningstr)

            results_learningstr["count"] += 1

            # 5 likert scale
            likert_scale_5_dic = self.get_scale_value(5)

            # negative polarized items
            negative_item = [15]

            # categorize items into corresponding attributes
            ksor = [1, 2, 3]
            ksel = [4, 5, 6]
            kskp = [7, 8, 9]
            kswh = [10, 11, 12]
            msp = [13, 14, 15]
            msu = [16, 17, 18]
            msr = [19, 20, 21]
            iram = [22, 23, 24]
            irag = [25, 26, 27]
            irzm = [28, 29, 30]
            erlg = [31, 32, 33]
            erlms = [34, 35, 36]
            erlr = [37, 38, 39]

            n_item = int(activity.description)

            # reverse negatively polarized items
            if n_item in negative_item:
                n_item_val = 6 - likert_scale_5_dic[activity.answers[0]]
            else:
                n_item_val = likert_scale_5_dic[activity.answers[0]]

            if n_item in ksor:
                
                if not results_learningstr["ksor"]:
                    results_learningstr["ksor"] = [n_item_val]
                else:
                    results_learningstr["ksor"][0] + n_item_val
                    
            elif n_item in ksel:
                
                if not results_learningstr["ksel"]:
                    results_learningstr["ksel"] = [n_item_val]
                else:
                    results_learningstr["ksel"][0] + n_item_val
                    
            elif n_item in kskp:
                
                if not results_learningstr["kskp"]:
                    results_learningstr["kskp"] = [n_item_val]
                else:
                    results_learningstr["kskp"][0] + n_item_val
                    
            elif n_item in kswh:
                
                if not results_learningstr["kswh"]:
                    results_learningstr["kswh"] = [n_item_val]
                else:
                    results_learningstr["kswh"][0] + n_item_val
                    
            elif n_item in msp:
                
                if not results_learningstr["msp"]:
                    results_learningstr["msp"] = [n_item_val]
                else:
                    results_learningstr["msp"][0] + n_item_val
                    
            elif n_item in msu:
                
                if not results_learningstr["msu"]:
                    results_learningstr["msu"] = [n_item_val]
                else:
                    results_learningstr["msu"][0] + n_item_val
                    
            elif n_item in msr:
                
                if not results_learningstr["msr"]:
                    results_learningstr["msr"] = [n_item_val]
                else:
                    results_learningstr["msr"][0] + n_item_val

            elif n_item in iram:

                if not results_learningstr["iram"]:
                    results_learningstr["iram"] = [n_item_val]
                else:
                    results_learningstr["iram"][0] + n_item_val

            elif n_item in irag:

                if not results_learningstr["irag"]:
                    results_learningstr["irag"] = [n_item_val]
                else:
                    results_learningstr["irag"][0] + n_item_val

            elif n_item in irzm:

                if not results_learningstr["irzm"]:
                    results_learningstr["irzm"] = [n_item_val]
                else:
                    results_learningstr["irzm"][0] + n_item_val

            elif n_item in erlg:

                if not results_learningstr["erlg"]:
                    results_learningstr["erlg"] = [n_item_val]
                else:
                    results_learningstr["erlg"][0] + n_item_val

            elif n_item in erlms:

                if not results_learningstr["erlms"]:
                    results_learningstr["erlms"] = [n_item_val]
                else:
                    results_learningstr["erlms"][0] + n_item_val

            elif n_item in erlr:

                if not results_learningstr["erlr"]:
                    results_learningstr["erlr"] = [n_item_val]
                else:
                    results_learningstr["erlr"][0] + n_item_val

            activity.goal.set_property(
                key="results_learningstr",
                value=json.dumps(results_learningstr)
            )

            if results_learningstr["count"] == 38:
                self.generate_recommendations(results_learningstr, activity.goal)

    def generate_recommendations(self, results_learningstr, goal):
        """
        show recommendations for learning strategies
        :param results_learningstr: Dictionary with values for all measured latent variables
        :param goal: Goal object which the feedback Activities will be added
        :return: Activities with recommendations
        """
        logging.info("Generierte Empfehlungen für: {}".format(results_learningstr))

        """
        goal = models.Goal.objects.create(
            title=self.get_name(),
            userrecommender=activity.goal.userrecommender,
        )
        goal.save()
        """

        description = "<p>Du hast mit dem Fragebogen deine Lernstrategien in vier Dimensionen evaluiert:" \
                      " <strong>Kognitive Strategien</strong>, <strong>Metakognitive " \
                      "Strategien</strong>, " \
                      "<strong>Interne Ressourcen</strong> und <strong>Externe Ressourcen</strong>.</p> " \
                      "<p>Kognitive Strategien umfassen diejenigen Prozesse, die du " \
                      "einsetzt, " \
                      "um dir den Lernstoff  zu erarbeiten und zu merken. " \
                      "Dazu gehören unter anderem <strong>Organisieren</strong>, " \
                      "<strong>Elaborieren</strong>, " \
                      "<strong>Kritisches Prüfen</strong> sowie <strong>Wiederholen</strong>. " \
                      "Elaborieren umfasst Studientätigkeiten, die auf ein " \
                      "tieferes Verstehen des " \
                      "Stoffes ausgerichtet sind.</p> " \
                      "<p>Metakognitive Strategien dienen dazu, das eigene Lernen" \
                      " zu <strong>planen</strong>, zu <strong>überwachen</strong> und zu " \
                      "<strong>regulieren</strong>.</p> " \
                      "<p>Interne Ressourcen bezeichnen deine Potentiale, " \
                      "die du für dein Lernen mobilisierst. " \
                      "Dazu gehören unter anderen <strong>Aufmerksamkeit</strong>, " \
                      "<strong>Anstrengung</strong>, und " \
                      "<strong>Zeitmanagement</strong>.</p> <p>Externe Ressourcen " \
                      "bezeichnen günstige Rahmenbedingungen, " \
                      "die du dir für dein Lernen schaffst, " \
                      "insbesondere, deine <strong>Lernumgebung</strong>, " \
                      "<strong>Lernen mit Studienkolleg*innen</strong> und " \
                      "<strong>Literaturrecherche</strong>.</p> " \
                      "<p>Im folgenden siehst du, wie du deinen Einsatz dieser Strategien " \
                      "selbst eingeschätzt hast. Außerdem findest Empfehlungen für den künftigen Einsatz " \
                      "dieser Strategien.</p>"

        feedbackGA = models.Activity.objects.get_or_create(
            title="Lernstrategien-Fragebogen: Allgemeines Feedback",
            goal=goal,
            type="todo",
            status="new",
            description=description,
            image=self.IMAGE,
            order=2890,
            feedback_size=0,
        )[0]
        feedbackGA.save()

        des1 = self.get_feedback_ksor(results_learningstr["ksor"][0])
        des2 = self.get_feedback_ksel(results_learningstr["ksel"][0])
        des3 = self.get_feedback_kskp(results_learningstr["kskp"][0])
        des4 = self.get_feedback_kswh(results_learningstr["kswh"][0])

        feedbackG = models.Activity.objects.get_or_create(
            title="Feedback: Kognitive Strategien",
            goal=goal,
            type="todo",
            status="new",
            description=des1 + des2 + des3 + des4,
            image=self.IMAGE,
            order=2891,
            feedback_size=0,
        )[0]
        feedbackG.save()

        des1 = self.get_feedback_msp(results_learningstr["msp"][0])
        des2 = self.get_feedback_msu(results_learningstr["msu"][0])
        des3 = self.get_feedback_msr(results_learningstr["msr"][0])

        feedbackms = models.Activity.objects.get_or_create(
            title="Feedback: Metakognitive Strategien",
            goal=goal,
            type="todo",
            status="new",
            description=des1 + des2 + des3,
            image=self.IMAGE,
            order=2892,
            feedback_size=0,
        )[0]
        feedbackms.save()

        desir1 = self.get_feedback_iram(results_learningstr["iram"][0])
        desir2 = self.get_feedback_irag(results_learningstr["irag"][0])
        desir3 = self.get_feedback_irzm(results_learningstr["irzm"][0])

        feedbackir = models.Activity.objects.get_or_create(
            title="Feedback: Interne Ressourcen",
            goal=goal,
            type="todo",
            status="new",
            description=desir1 + desir2 + desir3,
            image=self.IMAGE,
            order=2893,
            feedback_size=0,
        )[0]
        feedbackir.save()

        deser1 = self.get_feedback_erlg(results_learningstr["erlg"][0])
        deser2 = self.get_feedback_erms(results_learningstr["erlms"][0])
        deser3 = self.get_feedback_erlr(results_learningstr["erlr"][0])

        feedbacker = models.Activity.objects.get_or_create(
            title="Feedback: Externe Ressourcen",
            goal=goal,
            type="todo",
            status="new",
            description=deser1 + deser2 + deser3,
            image=self.IMAGE,
            order=2894,
            feedback_size=0,
        )[0]
        feedbacker.save()
