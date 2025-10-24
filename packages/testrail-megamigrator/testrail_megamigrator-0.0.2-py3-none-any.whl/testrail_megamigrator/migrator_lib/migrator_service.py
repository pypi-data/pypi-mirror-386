
from datetime import datetime
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from testy.core.models import Project
from testy.core.services.attachments import AttachmentService
from testy.core.services.projects import ProjectService
from testy.tests_description.models import TestCase, TestCaseStep, TestSuite
from testy.tests_description.selectors.cases import TestCaseSelector
from testy.tests_description.services.cases import TestCaseService
from testy.tests_description.services.suites import TestSuiteService
from testy.tests_representation.models import (Parameter, Test, TestPlan,
                                               TestResult, TestStepResult)
from testy.tests_representation.services.parameters import ParameterService
from testy.tests_representation.services.results import TestResultService
from testy.tests_representation.services.testplans import TestPlanService
from testy.tests_representation.services.tests import TestService

from testrail_megamigrator.serializers import ProjectSerializer

UserModel = get_user_model()


class MigratorService:
    @staticmethod
    def suite_create(data) -> TestSuite:
        non_side_effect_fields = TestSuiteService.non_side_effect_fields
        suite = TestSuite.model_create(
            fields=non_side_effect_fields,
            data=data,
        )
        return suite

    @staticmethod
    def step_update(step, data) -> TestCaseStep:
        non_side_effect_fields = TestCaseService.non_side_effect_fields
        step, _ = step.model_update(
            fields=non_side_effect_fields,
            data=data,
        )
        return step

    @staticmethod
    def suites_bulk_create(data_list):
        suites = []
        non_side_effect_fields = TestSuiteService.non_side_effect_fields
        for data in data_list:
            test_suite = TestSuite.model_create(non_side_effect_fields, data=data, commit=False)
            test_suite.lft = 0
            test_suite.rght = 0
            test_suite.tree_id = 0
            test_suite.level = 0
            suites.append(test_suite)
        TestSuite.objects.rebuild()
        return TestSuite.objects.bulk_create(suites)

    def step_create(self, data: Dict[str, Any]) -> TestCaseStep:
        data['name'] = data['name'][:254] if len(data['name']) > 255 else data['name']
        step: TestCaseStep = TestCaseStep.model_create(
            fields=TestCaseService.step_non_side_effect_fields,
            data=data
        )

        for attachment in data.get('attachments', []):
            AttachmentService().attachment_set_content_object(attachment, step)

        return step

    @transaction.atomic
    def case_with_steps_create(self, data: Dict[str, Any]) -> TestCase:
        case = self.case_create(data)

        for step in data.pop('steps', []):
            step['test_case'] = case
            step['project'] = case.project
            step['test_case_history_id'] = case.history.first().history_id
            self.step_create(step)
        return case

    def case_create(self, data: Dict[str, Any]) -> TestCase:

        case: TestCase = TestCase.model_create(
            fields=TestCaseService.case_non_side_effect_fields,
            data=data,
            commit=False
        )
        case.updated_at = timezone.make_aware(datetime.fromtimestamp(data['updated_at']), timezone.utc)
        case.created_at = timezone.make_aware(datetime.fromtimestamp(data['created_at']), timezone.utc)
        case.save()
        for attachment in data.get('attachments', []):
            AttachmentService().attachment_set_content_object(attachment, case)
        return case

    @staticmethod
    def case_update(case: TestCase, data) -> TestCase:
        non_side_effect_fields = TestCaseService.case_non_side_effect_fields
        case, _ = case.model_update(
            fields=non_side_effect_fields,
            data=data,
        )
        return case

    @staticmethod
    def parameter_bulk_create(data_list):
        non_side_effect_fields = ParameterService.non_side_effect_fields
        parameters = [Parameter.model_create(fields=non_side_effect_fields, data=data, commit=False) for data in
                      data_list]
        return Parameter.objects.bulk_create(parameters)

    def testplan_bulk_create_with_tests(self, data_list):
        test_plans = []
        for data in data_list:
            parameters = data.get('parameters', [])
            test_plans.append(
                self.make_testplan_model(
                    data,
                    parameters=[Parameter.objects.get(pk=parameter) for parameter in parameters]
                )
            )
        TestPlan.objects.rebuild()
        created_tests = []
        for test_plan, data in zip(test_plans, data_list):
            if data.get('test_cases'):
                created_tests.extend(TestService().bulk_test_create([test_plan], data['test_cases']))
        return created_tests, test_plans

    @staticmethod
    @transaction.atomic
    def result_create(data: Dict[str, Any], user) -> TestResult:
        test_result: TestResult = TestResult.model_create(
            fields=TestResultService.non_side_effect_fields,
            data=data,
            commit=False,
        )
        test_result.user = user
        test_result.project = test_result.test.case.project
        test_result.test_case_version = TestCaseSelector().case_version(test_result.test.case)
        test_result.full_clean()
        test_result.updated_at = data['updated_at']
        test_result.created_at = data['created_at']
        test_result.save()

        for attachment in data.get('attachments', []):
            AttachmentService().attachment_set_content_object(attachment, test_result)

        for steps_results in data.get('steps_results', []):
            steps_results['test_result'] = test_result
            steps_results['project'] = test_result.project
            TestStepResult.model_create(
                fields=TestResultService.step_non_side_effect_fields,
                data=steps_results
            )

        return test_result

    def testplan_bulk_create(self, validated_data):
        test_plans = []
        for data in validated_data:
            test_plans.append(self.make_testplan_model(data))
        TestPlan.objects.rebuild()

        return test_plans

    @staticmethod
    def create_project(project) -> Project:
        data = {
            'name': project['name'],
            'description': project['announcement'] if project['announcement'] else ''
        }
        serializer = ProjectSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return ProjectService().project_create(serializer.validated_data)

    @staticmethod
    def tests_bulk_create_by_data_list(data_list):
        non_side_effect_fields = TestService.non_side_effect_fields
        test_objects = [Test.model_create(fields=non_side_effect_fields, data=data, commit=False) for data in
                        data_list]
        return Test.objects.bulk_create(test_objects)

    @staticmethod
    def user_create(data) -> UserModel:
        user, _ = UserModel.objects.get_or_create(
            username__iexact=data['username'],
            defaults=data
        )

        return user

    @staticmethod
    def make_testplan_model(data, parameters=None):
        testplan = TestPlan.model_create(
            fields=TestPlanService.non_side_effect_fields,
            data=data,
            commit=False
        )
        testplan.lft = 0
        testplan.rght = 0
        testplan.tree_id = 0
        testplan.level = 0

        testplan.save()
        if parameters:
            testplan.parameters.set(parameters)

        return testplan
