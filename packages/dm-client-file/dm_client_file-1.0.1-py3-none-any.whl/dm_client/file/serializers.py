from rest_framework import serializers
from rest_framework import status
from dm_client.file.service import FileClient
from .errors import GET_ERROR
import logging

logger = logging.getLogger()


class FileUploadSerializer(serializers.Serializer):

    upload_id = serializers.CharField(required=True, max_length=32)
    expires_at = serializers.DateTimeField(required=True)

    def update(self, validated_data, deprecated_file_id):
        upload_id = validated_data.get('upload_id')
        expires_at = validated_data.get('expires_at')
        deprecated_file_ids = [deprecated_file_id] if deprecated_file_id else []
        response, request = FileClient().core_internal_upload_complete(upload_id,
                                                                       expires_at,
                                                                       deprecated_file_ids)
        if response.status_code != status.HTTP_201_CREATED:
            logger.info(request.__dict__)
            logger.info(response.__dict__)
            raise serializers.ValidationError(detail=GET_ERROR('DMCLIENTFILE001'))
        else:
            return None if len(response.json()) != 1 else response.json()[0]

    def create(self, validated_data):
        upload_id = validated_data.get('upload_id')
        expires_at = validated_data.get('expires_at')
        deprecated_file_ids = []
        response, request = FileClient().core_internal_upload_complete(upload_id,
                                                                       expires_at,
                                                                       deprecated_file_ids)
        if response.status_code != status.HTTP_201_CREATED:
            logger.info(request.__dict__)
            logger.info(response.__dict__)
            raise serializers.ValidationError(detail=GET_ERROR('DMCLIENTFILE001'))
        else:
            return None if len(response.json()) != 1 else response.json()[0]
