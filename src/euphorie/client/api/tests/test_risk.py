from euphorie.deployment.tests.functional import EuphorieFunctionalTestCase
from Products.Five.testbrowser import Browser


def _setup_session(portal):
    from euphorie.content.tests.utils import BASIC_SURVEY
    from euphorie.client.tests.utils import addAccount
    from euphorie.client.tests.utils import addSurvey
    from euphorie.client.session import create_survey_session
    from euphorie.client.profile import set_session_profile
    addSurvey(portal, BASIC_SURVEY)
    survey = portal.client['nl']['ict']['software-development']
    account = addAccount(password='secret')
    survey_session = create_survey_session(u'Dummy session',
            survey, account)
    survey_session = set_session_profile(survey, survey_session, {})
    return (account, survey, survey_session)


class ViewTests(EuphorieFunctionalTestCase):
    def View(self, *a, **kw):
        from euphorie.client.api.risk import View
        return View(*a, **kw)

    def test_do_GET_minimal(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        risk = survey['1']['2']
        risk.title = u'Everything is under control.'
        risk.problem_description = u'Not everything under control.'
        risk.description = None
        risk.evaluation_method = 'direct'
        request = TestRequest()
        request.survey = survey
        risk = object_session(survey_session).query(Risk).first()
        view = self.View(risk, request)
        response = view.do_GET()
        self.assertEqual(
                set(response),
                set(['id', 'type', 'title', 'problem-description',
                     'show-not-applicable', 'evaluation-method',
                     'present', 'priority', 'comment']))
        self.assertEqual(response['id'], 2)
        self.assertEqual(response['type'], 'risk')
        self.assertEqual(
                response['title'],
                u'Everything is under control.')
        self.assertEqual(
                response['problem-description'],
                u'Not everything under control.')
        self.assertEqual(response['show-not-applicable'], False)
        self.assertEqual(response['evaluation-method'], 'direct')
        self.assertEqual(response['present'], None)
        self.assertEqual(response['priority'], u'high')

    def test_do_GET_full(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        risk = survey['1']['2']
        risk.description = u'<p>Simple description</p>'
        risk.legal_reference = u'<p>Catch 22</p>'
        risk.evaluation_method = 'calculated'
        request = TestRequest()
        request.survey = survey
        risk = object_session(survey_session).query(Risk).first()
        risk.skip_children = True
        view = self.View(risk, request)
        response = view.do_GET()
        self.assertEqual(
                set(response),
                set(['id', 'type', 'title', 'problem-description',
                     'show-not-applicable', 'evaluation-method',
                     'present', 'priority', 'comment',
                     'description', 'legal-reference',
                     'evaluation-algorithm',
                     'frequency', 'frequency-options',
                     'effect', 'effect-options',
                     'probability', 'probability-options',
                     ]))
        self.assertEqual(response['description'], u'<p>Simple description</p>')
        self.assertEqual(response['legal-reference'], u'<p>Catch 22</p>')


class IdentificationTests(EuphorieFunctionalTestCase):
    def Identification(self, *a, **kw):
        from euphorie.client.api.risk import Identification
        return Identification(*a, **kw)

    def test_do_POST_missing_present_value(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        request = TestRequest()
        request.survey = survey
        request.survey_session = survey_session
        risk = object_session(survey_session).query(Risk).first()
        view = self.Identification(risk, request)
        view.input = {}
        response = view.do_POST()
        self.assertEqual(response['type'], 'error')

    def test_do_POST_present_invalid_value(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        request = TestRequest()
        request.survey = survey
        request.survey_session = survey_session
        risk = object_session(survey_session).query(Risk).first()
        view = self.Identification(risk, request)
        view.input = {'present': 'foo'}
        response = view.do_POST()
        self.assertEqual(response['type'], 'error')

    def test_do_POST_keep_existing_comment(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        request = TestRequest()
        request.survey = survey
        request.survey_session = survey_session
        risk = object_session(survey_session).query(Risk).first()
        risk.comment = u'Original comment'
        view = self.Identification(risk, request)
        view.input = {'present': 'yes'}
        response = view.do_POST()
        self.assertEqual(response['comment'], u'Original comment')
        self.assertEqual(risk.comment, u'Original comment')


class EvaluationTests(EuphorieFunctionalTestCase):
    def Evaluation(self, *a, **kw):
        from euphorie.client.api.risk import Evaluation
        return Evaluation(*a, **kw)

    def test_do_POST_evaluate_top5_risk(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        risk = survey['1']['2']
        risk.type = 'top5'
        request = TestRequest()
        request.survey = survey
        request.survey_session = survey_session
        risk = object_session(survey_session).query(Risk).first()
        view = self.Evaluation(risk, request)
        view.input = {}
        response = view.do_POST()
        self.assertEqual(response['type'], 'error')

    def test_do_POST_direct_evaluation(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        risk = survey['1']['2']
        risk.type = 'risk'
        risk.evaluation_method = 'direct'
        request = TestRequest()
        request.survey = survey
        request.survey_session = survey_session
        risk = object_session(survey_session).query(Risk).first()
        view = self.Evaluation(risk, request)
        view.input = {'priority': 'high'}
        response = view.do_POST()
        self.assertEqual(response['priority'], 'high')
        self.assertEqual(risk.priority, 'high')

    def test_do_POST_invalid_priority(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        risk = survey['1']['2']
        risk.evaluation_method = 'direct'
        risk.type = 'risk'
        request = TestRequest()
        request.survey = survey
        request.survey_session = survey_session
        risk = object_session(survey_session).query(Risk).first()
        risk.priority = 'low'
        view = self.Evaluation(risk, request)
        view.input = {'priority': 'bad'}
        response = view.do_POST()
        self.assertEqual(response['result'], 'error')
        self.assertEqual(risk.priority, 'low')

    def test_do_POST_kinney_risk(self):
        from sqlalchemy.orm import object_session
        from zope.publisher.browser import TestRequest
        from euphorie.client.model import Risk
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        risk = survey['1']['2']
        risk.evaluation_method = 'calculated'
        risk.type = 'risk'
        request = TestRequest()
        request.survey = survey
        request.survey_session = survey_session
        risk = object_session(survey_session).query(Risk).first()
        risk.priority = 'low'
        view = self.Evaluation(risk, request)
        view.input = {'probability': 'large', 
                      'frequency': 'constant',
                      'effect': 'high'}
        response = view.do_POST()
        self.assertEqual(response['priority'], 'high')
        self.assertEqual(risk.priority, 'high')


class BrowserTests(EuphorieFunctionalTestCase):
    def test_get(self):
        import json
        from euphorie.client.api.authentication import generate_token
        self.loginAsPortalOwner()
        (account, survey, survey_session) = _setup_session(self.portal)
        browser = Browser()
        browser.addHeader('X-Euphorie-Token', generate_token(account))
        browser.open('http://nohost/plone/client/api/users/1/sessions/1/1/1')
        self.assertEqual(browser.headers['Content-Type'], 'application/json')
        response = json.loads(browser.contents)
        self.assertEqual(response['type'], 'risk')
