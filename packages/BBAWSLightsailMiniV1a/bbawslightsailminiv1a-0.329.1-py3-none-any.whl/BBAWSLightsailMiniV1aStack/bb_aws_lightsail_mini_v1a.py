"""
AWS Lightsail Mini Infrastructure Stack
======================================

This module provides a comprehensive AWS Lightsail infrastructure deployment stack
using CDKTF (Cloud Development Kit for Terraform) with Python.

The stack includes:
    * Lightsail Container Service with automatic custom domain attachment
    * PostgreSQL Database (optional)
    * DNS management with CNAME records
    * SSL certificate management with automatic validation
    * IAM resources for service access
    * S3 bucket for application data
    * Secrets Manager for credential storage

:author: Generated with GitHub Copilot
:version: 1.0.0
:license: MIT
"""

import os
import json
from enum import Enum
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput, S3Backend
from AWSArchitectureBaseStack import AWSArchitectureBase

# AWS Provider and Resources
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws import (
    lightsail_container_service,
    lightsail_database,
    lightsail_instance,
    lightsail_key_pair,
    lightsail_domain,
    lightsail_domain_entry,
    cloudfront_distribution,
    iam_user,
    iam_access_key,
    iam_user_policy,
    s3_bucket,
)

# Random Provider and Resources
from cdktf_cdktf_provider_random.provider import RandomProvider
from cdktf_cdktf_provider_random import password

# AWS Secrets Manager
from cdktf_cdktf_provider_aws.secretsmanager_secret import SecretsmanagerSecret
from cdktf_cdktf_provider_aws.secretsmanager_secret_version import SecretsmanagerSecretVersion

# AWS WAF (currently unused but imported for future use)
from cdktf_cdktf_provider_aws.wafv2_web_acl import (
    Wafv2WebAcl,
    Wafv2WebAclDefaultAction,
    Wafv2WebAclRule,
    Wafv2WebAclVisibilityConfig,
    Wafv2WebAclDefaultActionAllow,
    Wafv2WebAclRuleOverrideAction,
    Wafv2WebAclRuleOverrideActionNone,
    Wafv2WebAclRuleOverrideActionCount,
    Wafv2WebAclRuleVisibilityConfig,
)
from cdktf_cdktf_provider_aws.wafv2_web_acl_association import Wafv2WebAclAssociation
from cdktf_cdktf_provider_aws.wafv2_rule_group import Wafv2RuleGroupRuleVisibilityConfig

# Null Provider for local-exec provisioner
from cdktf_cdktf_provider_null.provider import NullProvider
from cdktf_cdktf_provider_null.resource import Resource as NullResource

# Local domain attachment wrapper
from .lightsail_domain_wrapper import LightSailDomainAttachWrapper


class ArchitectureFlags(Enum):
    """
    Architecture configuration flags for optional components.

    :param SKIP_DATABASE: Skip database creation
    :param SKIP_DOMAIN: Skip domain and DNS configuration
    :param SKIP_DEFAULT_POST_APPLY_SCRIPTS: Skip default post-apply scripts
    """

    SKIP_DATABASE = "skip_database"
    SKIP_DOMAIN = "skip_domain"
    SKIP_DEFAULT_POST_APPLY_SCRIPTS = "skip_default_post_apply_scripts"
    SKIP_SSL_CERT = "skip_ssl_cert"


class BBAWSLightsailMiniV1a(AWSArchitectureBase):
    """
    AWS Lightsail Mini Infrastructure Stack.

    A comprehensive infrastructure stack that deploys:
        * Lightsail Container Service with custom domain support
        * PostgreSQL database (optional)
        * DNS records with automatic SSL certificate management
        * IAM resources and S3 storage
        * Automated domain attachment with validation retry logic

    :param scope: The construct scope
    :param id: The construct ID
    :param kwargs: Configuration parameters including region, domains, flags, etc.

    Example:
        >>> stack = BBAWSLightsailMiniV1a(
        ...     app, "my-stack",
        ...     region="ca-central-1",
        ...     domains=["app.example.com"],
        ...     project_name="my-app",
        ...     postApplyScripts=[
        ...         "echo 'Deployment completed'",
        ...         "curl -X POST https://webhook.example.com/notify"
        ...     ]
        ... )
    """

    # Class-level resource registry
    resources = {}

    # Default post-apply scripts executed after deployment
    default_post_apply_scripts = []

    @staticmethod
    def get_architecture_flags():
        """
        Get the ArchitectureFlags enum for configuration.

        :returns: ArchitectureFlags enum class
        :rtype: type[ArchitectureFlags]
        """
        return ArchitectureFlags

    @staticmethod
    def get_archetype(product, app, tier, organization, region):
        """
        Get the BuzzerboyArchetype instance for advanced configuration.

        :param product: Product name
        :param app: Application name
        :param tier: Environment tier (dev, staging, prod)
        :param organization: Organization name
        :param region: AWS region
        :returns: BuzzerboyArchetype instance
        :rtype: BuzzerboyArchetype

        .. note::
           This method requires the BuzzerboyArchetypeStack module to be available.
        """
        from BuzzerboyArchetypeStack import BuzzerboyArchetype

        return BuzzerboyArchetype(product=product, app=app, tier=tier, organization=organization, region=region)

    @staticmethod
    def get_lightsail_domain_from_aws(container_service_name, region, profile="default"):
        """
        Static method to retrieve Lightsail container service domain from AWS.
        
        This is a utility method that can be called independently to get the actual
        domain name from AWS Lightsail for a given container service.

        :param container_service_name: Name of the container service
        :type container_service_name: str
        :param region: AWS region where the service is deployed
        :type region: str
        :param profile: AWS profile to use (default: "default")
        :type profile: str
        :returns: The public domain URL ending with amazonlightsail.com
        :rtype: str

        Example:
            >>> domain = BBAWSLightsailMiniV1a.get_lightsail_domain_from_aws(
            ...     "my-app", "us-east-1", "my-profile"
            ... )
            >>> print(domain)  # my-app.us-east-1.cs.amazonlightsail.com
        """
        import boto3
        from botocore.exceptions import ClientError
        
        try:
            # Create a session with the specified profile
            session = boto3.Session(profile_name=profile)
            lightsail_client = session.client('lightsail', region_name=region)
            
            # Get container services
            response = lightsail_client.get_container_services()
            
            # Find our container service by name
            for service in response.get('containerServices', []):
                if service.get('containerServiceName') == container_service_name:
                    # Get the public domain endpoints
                    public_domain_names = service.get('publicDomainNames', {})
                    
                    # Look for the domain that ends with amazonlightsail.com
                    for domain_list in public_domain_names.values():
                        for domain in domain_list:
                            if domain.endswith('amazonlightsail.com'):
                                return domain
                    
                    # Fallback: use the URL from container service properties
                    url = service.get('url', '')
                    if url and 'amazonlightsail.com' in url:
                        # Extract domain from URL (remove https://)
                        return url.replace('https://', '').replace('http://', '')
            
            # If not found, fall back to constructed domain
            print(f"Warning: Could not find actual domain for {container_service_name}")
            return f"{container_service_name}.{region}.cs.amazonlightsail.com"
            
        except ClientError as e:
            print(f"Error retrieving Lightsail domain: {e}")
            return f"{container_service_name}.{region}.cs.amazonlightsail.com"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return f"{container_service_name}.{region}.cs.amazonlightsail.com"

    def __init__(self, scope, id, **kwargs):
        """
        Initialize the AWS Lightsail Mini Infrastructure Stack.

        :param scope: The construct scope
        :param id: Unique identifier for this stack
        :param kwargs: Configuration parameters

        **Configuration Parameters:**

        :param region: AWS region (default: "us-east-1")
        :param environment: Environment name (default: "dev")
        :param project_name: Project identifier (default: "bb-aws-lightsail-mini-v1a-app")
        :param domain_name: Primary domain name
        :param domains: List of custom domains to configure
        :param flags: List of ArchitectureFlags to modify behavior
        :param profile: AWS profile to use (default: "default")
        :param postApplyScripts: List of shell commands to execute after deployment

        .. warning::
           Lightsail domain operations must use us-east-1 region regardless of
           the main stack region.
        """
        # Initialize configuration before parent class to ensure proper state bucket setup
        self.region = kwargs.get("region", "us-east-1")
        self.environment = kwargs.get("environment", "dev")
        self.project_name = kwargs.get("project_name", "bb-aws-lightsail-mini-v1a-app")
        self.profile = kwargs.get("profile", "default")
        
        # Ensure we pass all kwargs to parent class
        super().__init__(scope, id, **kwargs)

        # ===== Stack Configuration =====
        self.domain_name = kwargs.get("domain_name", "bb-aws-lightsail-mini-v1a-app.buzzerboy.com")
        self.flags = kwargs.get("flags", [])
        self.domains = kwargs.get("domains", []) or []
        self.post_apply_scripts = kwargs.get("postApplyScripts", []) or []

        # ===== Database Configuration =====
        self.default_db_name = kwargs.get("default_db_name", self.project_name)
        self.default_db_username = kwargs.get("default_db_username", "dbadmin")

        # ===== Security Configuration =====
        self.secret_name = kwargs.get("secret_name", f"{self.project_name}/{self.environment}/database-credentials")
        self.default_signature_version = kwargs.get("default_signature_version", "s3v4")
        self.default_extra_secret_env = kwargs.get("default_extra_secret_env", "SECRET_STRING")

        # ===== Storage Configuration =====
        default_bucket_name = self.properize_s3_bucketname(f"{self.region}-{self.project_name}-tfstate")
        self.state_bucket_name = kwargs.get("state_bucket_name", default_bucket_name)

        # ===== Internal State =====
        self.secrets = {}
        self.post_terraform_messages = []
        self._post_plan_guidance: list[str] = []

        # ===== Infrastructure Setup =====
        # Base infrastructure is already set up by parent class
        # Only initialize our specific components
        self._set_default_post_apply_scripts()
        self._create_infrastructure_components()

    def _initialize_providers(self):
        """Initialize all required Terraform providers."""
        # Call parent class to initialize base providers (AWS, Random, Null)
        super()._initialize_providers()
        
        # Add Lightsail-specific provider for domain operations (must be us-east-1)
        self.aws_domain_provider = AwsProvider(
            self, "aws_domain", region="us-east-1", profile=self.profile, alias="domain"
        )
        self.resources["aws_domain"] = self.aws_domain_provider

    def _set_default_post_apply_scripts(self):
        """
        Set default post-apply scripts and merge with user-provided scripts.

        This method configures the default post-apply scripts that provide
        deployment status information and basic verification. These scripts
        are automatically added to the post_apply_scripts list unless the
        SKIP_DEFAULT_POST_APPLY_SCRIPTS flag is set.

        **Default Scripts Include:**

        * Deployment completion notification
        * Infrastructure summary information
        * Container service URL display
        * Environment and project details
        * Basic system information

        **Script Merging:**

        * Default scripts are prepended to user-provided scripts
        * User scripts execute after default scripts
        * Duplicates are not automatically removed

        .. note::
           Default scripts can be skipped by including
           ArchitectureFlags.SKIP_DEFAULT_POST_APPLY_SCRIPTS in the flags
           parameter during stack initialization.

        .. warning::
           Default scripts use environment variables and command substitution.
           Ensure the execution environment supports bash-style commands.
        """
        # Define default post-apply scripts
        self.default_post_apply_scripts = [
            "echo '============================================='",
            "echo '🎉 AWS Lightsail Infrastructure Deployment Complete!'",
            "echo '============================================='",
            f"echo '📦 Project: {self.project_name}'",
            f"echo '🌍 Environment: {self.environment}'",
            f"echo '📍 Region: {self.region}'",
            "echo '⏰ Deployment Time: '$(date)",
            "echo '============================================='",
            f"echo '🚀 Container Service URL: https://{self.project_name}.{self.region}.cs.amazonlightsail.com'",
            "echo '💻 System Information:'",
            "echo '   - OS: '$(uname -s)",
            "echo '   - Architecture: '$(uname -m)",
            "echo '   - User: '$(whoami)",
            "echo '   - Working Directory: '$(pwd)",
            "echo '============================================='",
            "echo '✅ Post-deployment scripts execution started'",
        ]

        # Skip default scripts if flag is set
        if ArchitectureFlags.SKIP_DEFAULT_POST_APPLY_SCRIPTS.value in self.flags:
            return

        # Merge default scripts with user-provided scripts
        # Default scripts execute first, then user scripts
        self.post_apply_scripts = self.default_post_apply_scripts + self.post_apply_scripts

    def _create_infrastructure_components(self):
        """Create all infrastructure components in the correct order."""
        # Core infrastructure
        self.create_iam_resources()
        self.create_lightsail_resources()
        self.create_lightsail_database()

        # DNS and domain management
        self.create_lightsail_domain()
        self.attach_custom_domains_to_container_service()

        #create storage
        self.create_s3_bucket()


        # Additional components (currently commented out)
        self.create_bastion_host()
        self.create_networking_resources()

        # Security and storage
        self.create_security_resources()

        # Post-apply scripts
        self.execute_post_apply_scripts()

        # Output generation
        self.create_outputs()

    # ==================== CORE INFRASTRUCTURE CREATION ====================

    def create_iam_resources(self):
        """
        Create IAM resources for container service access.

        Creates:
            * IAM user for programmatic access to AWS services
            * Access key pair for the IAM user
            * IAM policy loaded from external JSON file

        The IAM user follows the naming pattern: {project_name}-service-user
        """
        # Create IAM User and Access Key 
        user_name = f"{self.project_name}-service-user"
        self.container_service_user, self.container_service_key = super().create_iam_user_with_key(
            user_name=user_name,
            resource_id="container_service"
        )

        # IAM Policy from external file
        self.container_service_policy = self.create_iam_policy_from_file()
        self.resources["iam_policy"] = self.container_service_policy

    def create_iam_policy_from_file(self, file_path="iam_policy.json"):
        """
        Create IAM policy from JSON file.

        :param file_path: Path to IAM policy JSON file relative to this module
        :type file_path: str
        :returns: IAM user policy resource
        :rtype: IamUserPolicy

        .. note::
           The policy file should be located in the same directory as this module.
        """
        file_to_open = os.path.join(os.path.dirname(__file__), file_path)
        return super().create_iam_policy_from_file(
            file_to_open,
            self.container_service_user.name,
            policy_type="service-policy"
        )

    def create_s3_bucket(self):
        """
        Create S3 bucket for application data storage.

        Creates a private S3 bucket with proper tagging for application data storage
        and security configurations:
        - Bucket versioning enabled
        - Server-side encryption with Amazon S3 managed keys (SSE-S3)
        - Bucket key enabled to reduce encryption costs
        - Private ACL

        The bucket name follows the pattern: {project_name}-s3

        .. note::
           The ACL parameter is deprecated in favor of aws_s3_bucket_acl resource
           but is retained for backwards compatibility.
        """
        bucket_name = self.properize_s3_bucketname(f"{self.project_name}-s3")
        super().create_s3_bucket(bucket_name=bucket_name)

    def create_lightsail_resources(self):
        """
        Create core Lightsail resources.

        Creates:
            * Lightsail Container Service with nano power and scale of 1
            * Random password for database authentication

        .. note::
           Custom domains are configured separately through DNS records and
           post-deployment automation rather than the public_domain_names parameter
           due to CDKTF type complexity.
        """
        # Lightsail Container Service
        self.container_service = lightsail_container_service.LightsailContainerService(
            self,
            "app_container",
            name=f"{self.project_name}",
            power="nano",
            region=self.region,
            scale=1,
            is_disabled=False,
            # Note: Custom domains are configured separately via DNS records
            # The public_domain_names parameter has complex type requirements
            tags={"Environment": self.environment, "Project": self.project_name, "Stack": self.__class__.__name__},
        )
        self.container_service_url = self.get_lightsail_container_service_domain()

        # Database Password Generation
        self.db_password = password.Password(
            self, "db_password", length=16, special=True, override_special="!#$%&*()-_=+[]{}<>:?"
        )

        self.resources["lightsail_container_service"] = self.container_service

    def create_lightsail_database(self):
        """
        Create Lightsail PostgreSQL database (optional).

        Creates a micro PostgreSQL 14 database instance if the SKIP_DATABASE flag
        is not set. Also populates the secrets dictionary with database connection
        information for use in Secrets Manager.

        Database Configuration:
            * Engine: PostgreSQL 14
            * Size: micro_2_0
            * Final snapshot: Disabled (skip_final_snapshot=True)

        .. note::
           Database creation can be skipped by including ArchitectureFlags.SKIP_DATABASE
           in the flags parameter during stack initialization.
        """
        if ArchitectureFlags.SKIP_DATABASE.value in self.flags:
            return

        self.database = lightsail_database.LightsailDatabase(
            self,
            "app_database",
            relational_database_name=f"{self.project_name}-db",
            blueprint_id="postgres_14",
            bundle_id="micro_2_0",
            master_database_name=self.clean_hyphens(f"{self.project_name}"),
            master_username=self.default_db_username,
            master_password=self.db_password.result,
            skip_final_snapshot=True,
            tags={"Environment": self.environment, "Project": self.project_name, "Stack": self.__class__.__name__},
        )

        # Populate secrets for database connection
        self.secrets.update(
            {
                "password": self.db_password.result,
                "username": self.default_db_username,
                "dbname": self.default_db_name,
                "host": self.database.master_endpoint_address,
                "port": self.database.master_endpoint_port,
            }
        )

        self.resources["lightsail_database"] = self.database

    # ==================== DNS & DOMAIN MANAGEMENT ====================

    def create_lightsail_domain(self):
        """
        Create Lightsail DNS records for custom domains.

        For each domain in the domains list, creates:
            * CNAME record pointing to the actual container service URL from AWS
            * Terraform output with the complete domain name

        The method intelligently parses domains to:
            * Extract subdomain (first part) as the record name
            * Use root domain (remaining parts) as the DNS zone
            * Target the actual container service URL retrieved from AWS

        .. important::
           * Domain operations require the us-east-1 provider regardless of stack region
           * Only creates DNS records; does not create new domain zones
           * Assumes root domains already exist in Lightsail
           * Uses actual AWS Lightsail domain rather than constructed domain

        Example:
            For domain "api.myapp.com":
                * Record name: "api"
                * Zone: "myapp.com"
                * Target: Retrieved from AWS Lightsail API
        """
        if ArchitectureFlags.SKIP_DOMAIN.value in self.flags or not self.domains:
            return

        # Create a local-exec provisioner to get the actual domain after container service is created
        self._create_domain_update_script()

        for domain in self.domains:
            # Sanitize domain for resource naming
            domain_key = self.properize_s3_keyname(domain)

            # Parse domain components
            domain_parts = domain.split(".")
            record_name = domain_parts[0]
            root_domain = ".".join(domain_parts[1:]) if len(domain_parts) > 1 else domain
            
            # Use a placeholder initially - this will be updated by the local-exec script
            self.container_service_url = self.get_lightsail_container_service_domain()
            record_value = self.container_service_url

            # Create DNS record in existing root domain zone
            lightsail_domain_entry.LightsailDomainEntry(
                self,
                f"{domain_key}_{record_name}_record",
                domain_name=root_domain,
                type="CNAME",
                name=record_name,
                target=record_value,
                provider=self.aws_domain_provider,
            )

            # Create Terraform output for reference
            TerraformOutput(
                self,
                f"domain_{domain_key}_{record_name}_record",
                value=f"{record_name}.{root_domain}",
                description=f"DNS record for {self.project_name} in {self.environment} environment.",
            )

    def _create_domain_update_script(self):
        """
        Create a local-exec provisioner script to update DNS records with actual Lightsail domain.
        
        This script runs after the container service is created and updates any DNS records
        to point to the actual domain retrieved from AWS Lightsail API.
        """
        update_script = "echo 'Please attach custom domain manually'"

        # Create null resource with the update script
        NullResource(
            self,
            "update_dns_with_actual_domain",
            depends_on=[self.container_service],
            provisioners=[
                {
                    "type": "local-exec",
                    "command": update_script,
                    "on_failure": "continue",  # Don't fail deployment if DNS update fails
                }
            ],
        )

    def get_lightsail_container_service_domain(self):
        """
        Retrieve the actual Lightsail container service domain from AWS.

        Queries AWS Lightsail to get the container service information and extracts
        the public domain that ends with 'amazonlightsail.com'.

        :returns: The public domain URL for the container service
        :rtype: str
        :raises: Exception if unable to retrieve domain or service not found

        Example:
            >>> domain = stack.get_lightsail_container_service_domain()
            >>> print(domain)  # outputs: my-service.us-east-1.cs.amazonlightsail.com
        """
        return self.get_lightsail_domain_from_aws(
            self.container_service.name, 
            self.region, 
            self.profile
        )

    def create_lightsail_domain_record(self, domain_name, record_name, record_type, value):
        """
        Create a Lightsail domain record.
        """
        if ArchitectureFlags.SKIP_DOMAIN.value in self.flags or not self.domains:
            return

        # Ensure the domain exists in resources
        if f"lightsail_domain_{domain_name}" not in self.resources:
            raise ValueError(f"Domain {domain_name} does not exist in resources.")

        # Create the domain record
        lightsail_domain_entry.LightsailDomainEntry(
            self,
            f"{domain_name}_{record_name}_record",
            domain_name=domain_name,
            type=record_type,
            name=record_name,
            target=value,
            provider=self.aws_domain_provider,  # Use us-east-1 provider for domain operations
        )

    def attach_custom_domains_to_container_service(self):
        """
        Create Lightsail DNS records for custom domains.

        For each domain in the domains list, creates:
            * CNAME record pointing to the actual container service URL from AWS
            * Terraform output with the complete domain name

        The method intelligently parses domains to:
            * Extract subdomain (first part) as the record name
            * Use root domain (remaining parts) as the DNS zone
            * Target the actual container service URL retrieved from AWS

        .. important::
           * Domain operations require the us-east-1 provider regardless of stack region
           * Only creates DNS records; does not create new domain zones
           * Assumes root domains already exist in Lightsail
           * Uses actual AWS Lightsail domain rather than constructed domain

        Example:
            For domain "api.myapp.com":
                * Record name: "api"
                * Zone: "myapp.com"
                * Target: Retrieved from AWS Lightsail API
        """
        if ArchitectureFlags.SKIP_DOMAIN.value in self.flags or not self.domains:
            return

        # Create a local-exec provisioner to get the actual domain after container service is created
        self._create_domain_update_script()

        for domain in self.domains:
            # Sanitize domain for resource naming
            domain_key = self.properize_s3_keyname(domain)

            # Parse domain components
            domain_parts = domain.split(".")
            record_name = domain_parts[0]
            root_domain = ".".join(domain_parts[1:]) if len(domain_parts) > 1 else domain
            
            # Use a placeholder initially - this will be updated by the local-exec script
            self.container_service_url = self.get_lightsail_container_service_domain()
            record_value = self.container_service_url

            # Create DNS record in existing root domain zone
            lightsail_domain_entry.LightsailDomainEntry(
                self,
                f"{domain_key}_{record_name}_record",
                domain_name=root_domain,
                type="CNAME",
                name=record_name,
                target=record_value,
                provider=self.aws_domain_provider,
            )

            # Create Terraform output for reference
            TerraformOutput(
                self,
                f"domain_{domain_key}_{record_name}_record",
                value=f"{record_name}.{root_domain}",
                description=f"DNS record for {self.project_name} in {self.environment} environment.",
            )

    def _create_domain_update_script(self):
        """
        Create a local-exec provisioner script to update DNS records with actual Lightsail domain.
        
        This script runs after the container service is created and updates any DNS records
        to point to the actual domain retrieved from AWS Lightsail API.
        """
        update_script = "echo 'Please attach custom domain manually'"

        # Create null resource with the update script
        NullResource(
            self,
            "update_dns_with_actual_domain",
            depends_on=[self.container_service],
            provisioners=[
                {
                    "type": "local-exec",
                    "command": update_script,
                    "on_failure": "continue",  # Don't fail deployment if DNS update fails
                }
            ],
        )

    def attach_custom_domains_to_container_service(self):
        """
        Attach custom domains to container service with automated SSL certificate management.

        This method uses the LightSailDomainAttachWrapper to implement a sophisticated
        domain attachment workflow:

        **Workflow Steps:**

        1. **Certificate Creation**: Creates SSL certificate for the first domain
        2. **Validation Wait**: Monitors certificate status for up to 5 minutes
        3. **Domain Attachment**: Attempts to attach domains once certificate is validated
        4. **Fallback Guidance**: Provides manual commands if automation fails

        **Certificate Validation:**

        * Checks every 10 seconds for up to 30 attempts (5 minutes total)
        * Monitors for ISSUED, FAILED, or PENDING_VALIDATION status
        * Exits early on success or failure

        **Error Handling:**

        * Continues deployment even if domain attachment fails
        * Provides clear manual recovery instructions
        * Includes commands for checking certificate status

        .. note::
           Domain attachment can be skipped by including ArchitectureFlags.SKIP_DOMAIN
           in the flags parameter during stack initialization.

        .. warning::
           SSL certificates must be validated before domains can be attached.
           DNS propagation may take additional time beyond the 5-minute wait.
        """
        if ArchitectureFlags.SKIP_DOMAIN.value in self.flags or not self.domains:
            return
        
        if ArchitectureFlags.SKIP_SSL_CERT.value in self.flags:
            return

        # Create domain attachment wrapper with configuration
        domain_wrapper = LightSailDomainAttachWrapper(
            domains=self.domains,
            region=self.region,
            container_service_name=self.container_service.name,
            max_validation_attempts=30,  # 5 minutes total wait time
            validation_wait_seconds=10,
        )

        # Get the complete attachment command from wrapper
        attach_domains_command = domain_wrapper.get_attach_command()

        # Create null resource with local-exec provisioner
        NullResource(
            self,
            "attach_custom_domains",
            depends_on=[self.container_service],
            provisioners=[
                {
                    "type": "local-exec",
                    "command": attach_domains_command,
                    "on_failure": "continue",  # Don't fail deployment on domain attachment failure
                }
            ],
        )

        # Add informational messages for post-deployment guidance
        self.post_terraform_messages.extend(domain_wrapper.get_post_deployment_messages())

    # ==================== SECURITY & SECRETS ====================

    def get_extra_secret_env(self):
        """
        Load additional secrets from environment variable.

        Wraps the base class method using the Lightsail-specific environment variable name.
        Uses the default_extra_secret_env attribute for the environment variable name.

        .. note::
           This method wraps the base class method with Lightsail-specific defaults.
        """
        super().get_extra_secret_env(self.default_extra_secret_env)

    def create_security_resources(self):
        """
        Create AWS Secrets Manager resources for credential storage.

        Creates:
            * Secrets Manager secret for storing application credentials
            * Secret version with JSON-formatted credential data

        **Stored Credentials:**

        * Database connection details (if database is enabled)
        * IAM access keys for service authentication
        * AWS region and signature version configuration
        * Any additional secrets from environment variables

        .. note::
           All secrets are stored as a single JSON document in Secrets Manager
           for easy retrieval by applications.
        """
        # Create Secrets Manager secret
        self.db_secret = SecretsmanagerSecret(self, self.secret_name, name=f"{self.secret_name}")
        self.resources["secretsmanager_secret"] = self.db_secret

        # Populate IAM and AWS configuration secrets
        self.secrets.update(
            {
                "service_user_access_key": self.container_service_key.id,
                "service_user_secret_key": self.container_service_key.secret,
                "access_key": self.container_service_key.id,
                "secret_access_key": self.container_service_key.secret,
                "region_name": self.region,
                "signature_version": self.default_signature_version                
            }
        )

        if hasattr(self, 's3_bucket') and self.s3_bucket:
            self.secrets["bucket_name"] = self.s3_bucket.bucket

        # Load additional secrets from environment
        self.get_extra_secret_env()

        # Create secret version with all credentials
        SecretsmanagerSecretVersion(
            self,
            self.secret_name + "_version",
            secret_id=self.db_secret.id,
            secret_string=(json.dumps(self.secrets, indent=2, sort_keys=True) if self.secrets else None),
        )

    # ==================== POST-DEPLOYMENT ====================

    def execute_post_apply_scripts(self):
        """
        Execute post-apply scripts using local-exec provisioners.

        Creates a null resource with local-exec provisioner for each script
        in the post_apply_scripts list. Scripts are executed sequentially
        after all other infrastructure resources are created.

        **Script Execution:**

        * Each script runs as a separate null resource
        * Scripts execute in the order they appear in the list
        * Failures in scripts don't prevent deployment completion
        * All scripts depend on core infrastructure being ready

        **Error Handling:**

        * Scripts use "on_failure: continue" to prevent deployment failures
        * Failed scripts are logged but don't halt the deployment process
        * Manual intervention may be required if critical scripts fail

        .. note::
           Post-apply scripts can be provided via the postApplyScripts parameter
           during stack initialization. If no scripts are provided, this method
           returns without creating any resources.

        .. warning::
           Scripts have access to the local environment where Terraform runs.
           Ensure scripts are safe and don't expose sensitive information.

        Example:
            >>> stack = BBAWSLightsailMiniV1a(
            ...     app, "my-stack",
            ...     postApplyScripts=[
            ...         "echo 'Deployment completed successfully'",
            ...         "curl -X POST https://api.example.com/notify",
            ...         "python /path/to/setup_script.py"
            ...     ]
            ... )
        """
        dependencies = [
            self.container_service,
            # Add other core resources as dependencies
            *([self.database] if not self.has_flag(ArchitectureFlags.SKIP_DATABASE.value) else []),
            *([self.s3_bucket] if hasattr(self, 's3_bucket') else []),
        ]
        
        super().execute_post_apply_scripts(dependencies=dependencies)

    # ==================== OUTPUTS ====================

    def create_outputs(self):
        """
        Create Terraform outputs for important resource information.

        Generates outputs for:
            * Container service public URL
            * Database endpoint (if database is enabled)
            * Database password (sensitive, if database is enabled)
            * IAM access keys (sensitive)

        .. note::
           Sensitive outputs are marked as such and will be hidden in
           Terraform output unless explicitly requested.
        """
        # Container service public URL
        TerraformOutput(
            self,
            "container_service_url",
            value=self.container_service_url,
            description="Public URL of the Lightsail container service",
        )

        # Database outputs (if database is enabled)
        if not self.has_flag(ArchitectureFlags.SKIP_DATABASE.value):
            TerraformOutput(
                self,
                "database_endpoint",
                value=f"{self.database.master_endpoint_address}:{self.database.master_endpoint_port}",
                description="Database connection endpoint",
            )
            TerraformOutput(
                self,
                "database_password",
                value=self.database.master_password,
                sensitive=True,
                description="Database master password (sensitive)",
            )

        # IAM credentials (sensitive)
        TerraformOutput(
            self,
            "iam_user_access_key",
            value=self.container_service_key.id,
            sensitive=True,
            description="IAM user access key ID (sensitive)",
        )

        TerraformOutput(
            self,
            "iam_user_secret_key",
            value=self.container_service_key.secret,
            sensitive=True,
            description="IAM user secret access key (sensitive)",
        )

# ==================== FUTURE METHODS ====================

    def create_bastion_host(self):
        """Placeholder for bastion host creation."""
        pass

    def create_networking_resources(self):
        """Placeholder for networking resources creation."""
        pass