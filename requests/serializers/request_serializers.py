from rest_framework import serializers
from ..models import Applicant, Request, Bill

class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        exclude = ['created_at']

class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['statement_of_need']

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        exclude = ['request', 'approved', 'paid', 'paid_date', 'created_at']

class CreateRequestSerializer(serializers.Serializer):
    applicant = ApplicantSerializer()
    request = RequestSerializer()
    bills = BillSerializer(many=True)

    def create(self, validated_data):
        applicant_data = validated_data.pop('applicant')
        request_data = validated_data.pop('request')
        bills_data = validated_data.pop('bills')

        applicant = Applicant.objects.create(**applicant_data)

        user = self.context['request'].user
        is_test = user.is_staff

        request_obj = Request.objects.create(
            applicant=applicant,
            requested_by=user,
            is_test=is_test,
            **request_data
        )

        for bill_data in bills_data:
            Bill.objects.create(request=request_obj, **bill_data)

        return request_obj
