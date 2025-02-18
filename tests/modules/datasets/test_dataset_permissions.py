from dataall.base.context import set_context, RequestContext
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.base.db.exceptions import ResourceUnauthorized
from dataall.core.permissions.permissions import TENANT_ALL
from dataall.modules.datasets.services.dataset_permissions import DATASET_WRITE, UPDATE_DATASET, MANAGE_DATASETS, \
    DATASET_READ
from dataall.modules.datasets.services.dataset_service import DatasetService
from dataall.modules.datasets_base.db.dataset_models import Dataset
from dataall.modules.datasets_base.services.permissions import DATASET_TABLE_READ

from tests.core.permissions.test_permission import *
from dataall.core.organizations.db.organization_repositories import Organization


def test_attach_resource_policy(db, user, group, dataset_fixture):
    permissions(db, ENVIRONMENT_ALL + ORGANIZATION_ALL + DATASET_READ + DATASET_WRITE + DATASET_TABLE_READ)
    with db.scoped_session() as session:
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group.name,
            permissions=DATASET_WRITE,
            resource_uri=dataset_fixture.datasetUri,
            resource_type=Dataset.__name__,
        )
        assert ResourcePolicy.check_user_resource_permission(
            session=session,
            username=user.username,
            groups=[group.name],
            permission_name=UPDATE_DATASET,
            resource_uri=dataset_fixture.datasetUri,
        )


def test_attach_tenant_policy(
    db, user, group, dataset_fixture, permissions, tenant
):
    with db.scoped_session() as session:
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=[MANAGE_DATASETS],
            tenant_name='dataall',
        )

        assert TenantPolicy.check_user_tenant_permission(
            session=session,
            username=user.username,
            groups=[group.name],
            permission_name=MANAGE_DATASETS,
            tenant_name='dataall',
        )


def test_unauthorized_resource_policy(
    db, user, group, dataset_fixture, permissions
):
    with pytest.raises(ResourceUnauthorized):
        with db.scoped_session() as session:
            assert ResourcePolicy.check_user_resource_permission(
                session=session,
                username=user.username,
                groups=[group.name],
                permission_name='UNKNOWN_PERMISSION',
                resource_uri=dataset_fixture.datasetUri,
            )


def test_create_dataset(db, user, group, dataset_fixture, permissions, tenant):
    with db.scoped_session() as session:
        set_context(RequestContext(db, user.username, [group.name], user_id=user.username))

        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=TENANT_ALL,
            tenant_name='dataall',
        )
        org_with_perm = Organization.create_organization(
            session=session,
            data={
                'label': 'OrgWithPerm',
                'SamlGroupName': group.name,
                'description': 'desc',
                'tags': [],
            },
        )
        env_with_perm = EnvironmentService.create_environment(
            session=session,
            uri=org_with_perm.organizationUri,
            data={
                'label': 'EnvWithPerm',
                'organizationUri': org_with_perm.organizationUri,
                'SamlGroupName': group.name,
                'description': 'desc',
                'AwsAccountId': '123456789012',
                'region': 'eu-west-1',
                'cdk_role_name': 'cdkrole',
            },
        )

        data = dict(
            label='label',
            owner='foo',
            SamlAdminGroupName=group.name,
            businessOwnerDelegationEmails=['foo@amazon.com'],
            businessOwnerEmail=['bar@amazon.com'],
            name='name',
            S3BucketName='S3BucketName',
            GlueDatabaseName='GlueDatabaseName',
            KmsAlias='kmsalias',
            AwsAccountId='123456789012',
            region='eu-west-1',
            IAMDatasetAdminUserArn=f'arn:aws:iam::123456789012:user/dataset',
            IAMDatasetAdminRoleArn=f'arn:aws:iam::123456789012:role/dataset',
        )

        dataset = DatasetService.create_dataset(
            uri=env_with_perm.environmentUri,
            admin_group=group.name,
            data=data,
        )
        assert dataset
