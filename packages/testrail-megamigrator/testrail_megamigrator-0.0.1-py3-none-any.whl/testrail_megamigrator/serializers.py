
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.serializers import ModelSerializer
from testy.core.api.v1.serializers import ProjectSerializer as BaseProjectSerializer
from testy.tests_description.api.v1.serializers import TestSuiteSerializer as BaseTestSuiteSerializer
from testy.tests_representation.api.v1.serializers import TestPlanInputSerializer as BaseTestPlanSerializer
from testy.tests_representation.models import Parameter, Test
from testy.tests_representation.selectors.results import TestResultSelector


class ParameterSerializer(ModelSerializer):
    class Meta:
        model = Parameter
        fields = ('id', 'project', 'data', 'group_name')


class TestSerializer(ModelSerializer):
    url = HyperlinkedIdentityField(view_name='api:v1:test-detail')
    name = SerializerMethodField(read_only=True)
    last_status = SerializerMethodField(read_only=True)
    suite = SerializerMethodField(read_only=True)

    class Meta:
        model = Test
        fields = (
            'id', 'project', 'case', 'suite', 'name', 'last_status', 'plan', 'assignee', 'is_archive', 'created_at',
            'updated_at', 'url')

    def get_name(self, instance):
        return instance.case.name

    def get_last_status(self, instance):
        result = TestResultSelector().last_result_by_test_id(instance.id)
        if result:
            return result.get_status_display()

    @staticmethod
    def get_suite(instance):
        return instance.case.suite.id


class ProjectSerializer(BaseProjectSerializer):
    class Meta(BaseProjectSerializer.Meta):
        validators = []


class TestSuiteSerializer(BaseTestSuiteSerializer):
    class Meta(BaseTestSuiteSerializer.Meta):
        validators = []


class TestPlanInputSerializer(BaseTestPlanSerializer):
    class Meta(BaseTestPlanSerializer.Meta):
        validators = []
