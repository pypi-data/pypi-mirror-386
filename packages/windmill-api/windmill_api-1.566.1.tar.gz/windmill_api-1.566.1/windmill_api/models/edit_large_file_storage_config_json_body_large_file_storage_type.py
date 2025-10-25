from enum import Enum


class EditLargeFileStorageConfigJsonBodyLargeFileStorageType(str, Enum):
    AZUREBLOBSTORAGE = "AzureBlobStorage"
    AZUREWORKLOADIDENTITY = "AzureWorkloadIdentity"
    GOOGLECLOUDSTORAGE = "GoogleCloudStorage"
    S3AWSOIDC = "S3AwsOidc"
    S3STORAGE = "S3Storage"

    def __str__(self) -> str:
        return str(self.value)
