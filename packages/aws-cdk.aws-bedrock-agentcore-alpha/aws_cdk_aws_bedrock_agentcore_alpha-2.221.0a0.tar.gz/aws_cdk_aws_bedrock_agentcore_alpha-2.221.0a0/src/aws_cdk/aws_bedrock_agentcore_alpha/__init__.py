r'''
# Amazon Bedrock AgentCore Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

| **Language**                                                                                   | **Package**                             |
| :--------------------------------------------------------------------------------------------- | --------------------------------------- |
| ![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) TypeScript | `@aws-cdk/aws-bedrock-agentcore-alpha` |

[Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) enables you to deploy and operate highly capable AI agents securely, at scale. It offers infrastructure purpose-built for dynamic agent workloads, powerful tools to enhance agents, and essential controls for real-world deployment. AgentCore services can be used together or independently and work with any framework including CrewAI, LangGraph, LlamaIndex, and Strands Agents, as well as any foundation model in or outside of Amazon Bedrock, giving you ultimate flexibility. AgentCore eliminates the undifferentiated heavy lifting of building specialized agent infrastructure, so you can accelerate agents to production.

This construct library facilitates the deployment of Bedrock AgentCore primitives, enabling you to create sophisticated AI applications that can interact with your systems and data sources.

## Table of contents

* [AgentCore Runtime](#agentcore-runtime)

  * [Runtime Versioning](#runtime-versioning)
  * [Runtime Endpoints](#runtime-endpoints)
  * [AgentCore Runtime Properties](#agentcore-runtime-properties)
  * [Runtime Endpoint Properties](#runtime-endpoint-properties)
  * [Creating a Runtime](#creating-a-runtime)

    * [Option 1: Use an existing image in ECR](#option-1-use-an-existing-image-in-ecr)
    * [Managing Endpoints and Versions](#managing-endpoints-and-versions)
    * [Option 2: Use a local asset](#option-2-use-a-local-asset)
* [Browser Custom tool](#browser)

  * [Browser properties](#browser-properties)
  * [Browser Network modes](#browser-network-modes)
  * [Basic Browser Creation](#basic-browser-creation)
  * [Browser IAM permissions](#browser-iam-permissions)
* [Code Interpreter Custom tool](#code-interpreter)

  * [Code Interpreter properties](#code-interpreter-properties)
  * [Code Interpreter Network Modes](#code-interpreter-network-modes)
  * [Basic Code Interpreter Creation](#basic-code-interpreter-creation)
  * [Code Interpreter IAM permissions](#code-interpreter-iam-permissions)

## AgentCore Runtime

The AgentCore Runtime construct enables you to deploy containerized agents on Amazon Bedrock AgentCore.
This L2 construct simplifies runtime creation just pass your ECR repository name
and the construct handles all the configuration with sensible defaults.

### Runtime Endpoints

Endpoints provide a stable way to invoke specific versions of your agent runtime, enabling controlled deployments across different environments.
When you create an agent runtime, Amazon Bedrock AgentCore automatically creates a "DEFAULT" endpoint which always points to the latest version
of runtime.

You can create additional endpoints in two ways:

1. **Using Runtime.addEndpoint()** - Convenient method when creating endpoints alongside the runtime.
2. **Using RuntimeEndpoint** - Flexible approach for existing runtimes.

For example, you might keep a "production" endpoint on a stable version while testing newer versions
through a "staging" endpoint. This separation allows you to test changes thoroughly before promoting them
to production by simply updating the endpoint to point to the newer version.

### AgentCore Runtime Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `runtimeName` | `string` | Yes | The name of the agent runtime. Valid characters are a-z, A-Z, 0-9, _ (underscore). Must start with a letter and can be up to 48 characters long |
| `agentRuntimeArtifact` | `AgentRuntimeArtifact` | Yes | The artifact configuration for the agent runtime containing the container configuration with ECR URI |
| `executionRole` | `iam.IRole` | No | The IAM role that provides permissions for the agent runtime. If not provided, a role will be created automatically |
| `networkConfiguration` | `NetworkConfiguration` | No | Network configuration for the agent runtime. Defaults to `RuntimeNetworkConfiguration.usingPublicNetwork()` |
| `description` | `string` | No | Optional description for the agent runtime |
| `protocolConfiguration` | `ProtocolType` | No | Protocol configuration for the agent runtime. Defaults to `ProtocolType.HTTP` |
| `authorizerConfiguration` | `RuntimeAuthorizerConfiguration` | No | Authorizer configuration for the agent runtime. Use `RuntimeAuthorizerConfiguration` static methods to create configurations for IAM, Cognito, JWT, or OAuth authentication |
| `environmentVariables` | `{ [key: string]: string }` | No | Environment variables for the agent runtime. Maximum 50 environment variables |
| `tags` | `{ [key: string]: string }` | No | Tags for the agent runtime. A list of key:value pairs of tags to apply to this Runtime resource |

### Runtime Endpoint Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `endpointName` | `string` | Yes | The name of the runtime endpoint. Valid characters are a-z, A-Z, 0-9, _ (underscore). Must start with a letter and can be up to 48 characters long |
| `agentRuntimeId` | `string` | Yes | The Agent Runtime ID for this endpoint |
| `agentRuntimeVersion` | `string` | Yes | The Agent Runtime version for this endpoint. Must be between 1 and 5 characters long.|
| `description` | `string` | No | Optional description for the runtime endpoint |
| `tags` | `{ [key: string]: string }` | No | Tags for the runtime endpoint |

### Creating a Runtime

#### Option 1: Use an existing image in ECR

Reference an image available within ECR.

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)

# The runtime by default create ECR permission only for the repository available in the account the stack is being deployed
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")

# Create runtime using the built image
runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact
)
```

To grant the runtime permission to invoke a Bedrock model or inference profile:

```text
// Note: This example uses @aws-cdk/aws-bedrock-alpha which must be installed separately
import * as bedrock from '@aws-cdk/aws-bedrock-alpha';

// Create a cross-region inference profile for Claude 3.7 Sonnet
const inferenceProfile = bedrock.CrossRegionInferenceProfile.fromConfig({
  geoRegion: bedrock.CrossRegionInferenceProfileRegion.US,
  model: bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_7_SONNET_V1_0
});

// Grant the runtime permission to invoke the inference profile
inferenceProfile.grantInvoke(runtime);
```

#### Option 2: Use a local asset

Reference a local directory containing a Dockerfile.
Images are built from a local Docker context directory (with a Dockerfile), uploaded to Amazon Elastic Container Registry (ECR)
by the CDK toolkit,and can be naturally referenced in your CDK app .

```python
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_asset(
    path.join(__dirname, "path to agent dockerfile directory"))

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact
)
```

### Runtime Versioning

Amazon Bedrock AgentCore automatically manages runtime versioning to ensure safe deployments and rollback capabilities.
When you create an agent runtime, AgentCore automatically creates version 1 (V1). Each subsequent update to the
runtime configuration (such as updating the container image, modifying network settings, or changing protocol configurations)
creates a new immutable version. These versions contain complete, self-contained configurations that can be referenced by endpoints,
allowing you to maintain different versions for different environments or gradually roll out updates.

#### Managing Endpoints and Versions

Amazon Bedrock AgentCore automatically manages runtime versioning to provide safe deployments and rollback capabilities. You can follow
the steps below to understand how to use versioning with runtime for controlled deployments across different environments.

##### Step 1: Initial Deployment

When you first create an agent runtime, AgentCore automatically creates Version 1 of your runtime. At this point, a DEFAULT endpoint is
automatically created that points to Version 1. This DEFAULT endpoint serves as the main access point for your runtime.

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
)
```

##### Step 2: Creating Custom Endpoints

After the initial deployment, you can create additional endpoints for different environments. For example, you might create a "production"
endpoint that explicitly points to Version 1. This allows you to maintain stable access points for specific environments while keeping the
flexibility to test newer versions elsewhere.

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
)

prod_endpoint = runtime.add_endpoint("production",
    version="1",
    description="Stable production endpoint - pinned to v1"
)
```

##### Step 3: Runtime Update Deployment

When you update the runtime configuration (such as updating the container image, modifying network settings, or changing protocol
configurations), AgentCore automatically creates a new version (Version 2). Upon this update:

* Version 2 is created automatically with the new configuration
* The DEFAULT endpoint automatically updates to point to Version 2
* Any explicitly pinned endpoints (like the production endpoint) remain on their specified versions

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)

agent_runtime_artifact_new = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v2.0.0")

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact_new
)
```

##### Step 4: Testing with Staging Endpoints

Once Version 2 exists, you can create a staging endpoint that points to the new version. This staging endpoint allows you to test the
new version in a controlled environment before promoting it to production. This separation ensures that production traffic continues
to use the stable version while you validate the new version.

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)

agent_runtime_artifact_new = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v2.0.0")

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact_new
)

staging_endpoint = runtime.add_endpoint("staging",
    version="2",
    description="Staging environment for testing new version"
)
```

##### Step 5: Promoting to Production

After thoroughly testing the new version through the staging endpoint, you can update the production endpoint to point to Version 2.
This controlled promotion process ensures that you can validate changes before they affect production traffic.

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)

agent_runtime_artifact_new = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v2.0.0")

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact_new
)

prod_endpoint = runtime.add_endpoint("production",
    version="2",  # New version added here
    description="Stable production endpoint"
)
```

### Creating Standalone Runtime Endpoints

RuntimeEndpoint can also be created as a standalone resource.

#### Example: Creating an endpoint for an existing runtime

```python
# Reference an existing runtime by its ID
existing_runtime_id = "abc123-runtime-id" # The ID of an existing runtime

# Create a standalone endpoint
endpoint = agentcore.RuntimeEndpoint(self, "MyEndpoint",
    endpoint_name="production",
    agent_runtime_id=existing_runtime_id,
    agent_runtime_version="1",  # Specify which version to use
    description="Production endpoint for existing runtime"
)
```

### Runtime Authentication Configuration

The AgentCore Runtime supports multiple authentication modes to secure access to your agent endpoints. Authentication is configured during runtime creation using the `RuntimeAuthorizerConfiguration` class's static factory methods.

#### IAM Authentication (Default)

IAM authentication is the default mode, when no authorizerConfiguration is set then the underlying service use IAM.

#### Cognito Authentication

To configure AWS Cognito User Pool authentication:

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact,
    authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_cognito("us-west-2_ABC123", "client123", "us-west-2")
)
```

#### JWT Authentication

To configure custom JWT authentication with your own OpenID Connect (OIDC) provider:

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact,
    authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_jWT("https://example.com/.well-known/openid-configuration", ["client1", "client2"], ["audience1"])
)
```

**Note**: The discovery URL must end with `/.well-known/openid-configuration`.

#### OAuth Authentication

To configure OAuth 2.0 authentication:

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")

runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact,
    authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_oAuth("https://github.com/.well-known/openid-configuration", "oauth_client_123")
)
```

#### Using a Custom IAM Role

Instead of using the auto-created execution role, you can provide your own IAM role with specific permissions:
The auto-created role includes all necessary baseline permissions for ECR access, CloudWatch logging, and X-Ray tracing. When providing a custom role, ensure these permissions are included.

### Runtime Network Configuration

The AgentCore Runtime supports two network modes for deployment:

#### Public Network Mode (Default)

By default, runtimes are deployed in PUBLIC network mode, which provides internet access suitable for less sensitive or open-use scenarios:

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")

# Explicitly using public network (this is the default)
runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact,
    network_configuration=agentcore.RuntimeNetworkConfiguration.using_public_network()
)
```

#### VPC Network Mode

For enhanced security and network isolation, you can deploy your runtime within a VPC:

```python
repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")

# Create or use an existing VPC
vpc = ec2.Vpc(self, "MyVpc",
    max_azs=2
)

# Configure runtime with VPC
runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact,
    network_configuration=agentcore.RuntimeNetworkConfiguration.using_vpc(self,
        vpc=vpc,
        vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
    )
)
```

#### Managing Security Groups with VPC Configuration

When using VPC mode, the Runtime implements `ec2.IConnectable`, allowing you to manage network access using the `connections` property:

```python
vpc = ec2.Vpc(self, "MyVpc",
    max_azs=2
)

repository = ecr.Repository(self, "TestRepository",
    repository_name="test-agent-runtime"
)
agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")

# Create runtime with VPC configuration
runtime = agentcore.Runtime(self, "MyAgentRuntime",
    runtime_name="myAgent",
    agent_runtime_artifact=agent_runtime_artifact,
    network_configuration=agentcore.RuntimeNetworkConfiguration.using_vpc(self,
        vpc=vpc,
        vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
    )
)

# Now you can manage network access using the connections property
# Allow inbound HTTPS traffic from a specific security group
web_server_security_group = ec2.SecurityGroup(self, "WebServerSG", vpc=vpc)
runtime.connections.allow_from(web_server_security_group, ec2.Port.tcp(443), "Allow HTTPS from web servers")

# Allow outbound connections to a database
database_security_group = ec2.SecurityGroup(self, "DatabaseSG", vpc=vpc)
runtime.connections.allow_to(database_security_group, ec2.Port.tcp(5432), "Allow PostgreSQL connection")

# Allow outbound HTTPS to anywhere (for external API calls)
runtime.connections.allow_to_any_ipv4(ec2.Port.tcp(443), "Allow HTTPS outbound")
```

## Browser

The Amazon Bedrock AgentCore Browser provides a secure, cloud-based browser that enables AI agents to interact with websites. It includes security features such as session isolation, built-in observability through live viewing, CloudTrail logging, and session replay capabilities.

Additional information about the browser tool can be found in the [official documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser-tool.html)

### Browser Network modes

The Browser construct supports the following network modes:

1. **Public Network Mode** (`BrowserNetworkMode.usingPublicNetwork()`) - Default

   * Allows internet access for web browsing and external API calls
   * Suitable for scenarios where agents need to interact with publicly available websites
   * Enables full web browsing capabilities
   * VPC mode is not supported with this option
2. **VPC (Virtual Private Cloud)** (`BrowserNetworkMode.usingVpc()`)

   * Select whether to run the browser in a virtual private cloud (VPC).
   * By configuring VPC connectivity, you enable secure access to private resources such as databases, internal APIs, and services within your VPC.

   While the VPC itself is mandatory, these are optional:

   * Subnets - if not provided, CDK will select appropriate subnets from the VPC
   * Security Groups - if not provided, CDK will create a default security group
   * Specific subnet selection criteria - you can let CDK choose automatically

For more information on VPC connectivity for Amazon Bedrock AgentCore Browser, please refer to the [official documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html).

### Browser Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `browserCustomName` | `string` | Yes | The name of the browser. Must start with a letter and can be up to 48 characters long. Pattern: `[a-zA-Z][a-zA-Z0-9_]{0,47}` |
| `description` | `string` | No | Optional description for the browser. Can have up to 200 characters |
| `networkConfiguration` | `BrowserNetworkConfiguration` | No | Network configuration for browser. Defaults to PUBLIC network mode |
| `recordingConfig` | `RecordingConfig` | No | Recording configuration for browser. Defaults to no recording |
| `executionRole` | `iam.IRole` | No | The IAM role that provides permissions for the browser to access AWS services. A new role will be created if not provided |
| `tags` | `{ [key: string]: string }` | No | Tags to apply to the browser resource |

### Basic Browser Creation

```python
# Create a basic browser with public network access
browser = agentcore.BrowserCustom(self, "MyBrowser",
    browser_custom_name="my_browser",
    description="A browser for web automation"
)
```

### Browser with Tags

```python
# Create a browser with custom tags
browser = agentcore.BrowserCustom(self, "MyBrowser",
    browser_custom_name="my_browser",
    description="A browser for web automation with tags",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network(),
    tags={
        "Environment": "Production",
        "Team": "AI/ML",
        "Project": "AgentCore"
    }
)
```

### Browser with VPC

```python
browser = agentcore.BrowserCustom(self, "BrowserVpcWithRecording",
    browser_custom_name="browser_recording",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_vpc(self,
        vpc=ec2.Vpc(self, "VPC", restrict_default_security_group=False)
    )
)
```

Browser exposes a [connections](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ec2.Connections.html) property. This property returns a connections object, which simplifies the process of defining and managing ingress and egress rules for security groups in your AWS CDK applications. Instead of directly manipulating security group rules, you interact with the Connections object of a construct, which then translates your connectivity requirements into the appropriate security group rules. For instance:

```python
vpc = ec2.Vpc(self, "testVPC")

browser = agentcore.BrowserCustom(self, "test-browser",
    browser_custom_name="test_browser",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_vpc(self,
        vpc=vpc
    )
)

browser.connections.add_security_group(ec2.SecurityGroup(self, "AdditionalGroup", vpc=vpc))
```

So security groups can be added after the browser construct creation. You can use methods like allowFrom() and allowTo() to grant ingress access to/egress access from a specified peer over a given portRange. The Connections object automatically adds the necessary ingress or egress rules to the security group(s) associated with the calling construct.

### Browser with Recording Configuration

```python
# Create an S3 bucket for recordings
recording_bucket = s3.Bucket(self, "RecordingBucket",
    bucket_name="my-browser-recordings",
    removal_policy=RemovalPolicy.DESTROY
)

# Create browser with recording enabled
browser = agentcore.BrowserCustom(self, "MyBrowser",
    browser_custom_name="my_browser",
    description="Browser with recording enabled",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network(),
    recording_config=agentcore.RecordingConfig(
        enabled=True,
        s3_location=s3.Location(
            bucket_name=recording_bucket.bucket_name,
            object_key="browser-recordings/"
        )
    )
)
```

### Browser with Custom Execution Role

```python
# Create a custom execution role
execution_role = iam.Role(self, "BrowserExecutionRole",
    assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
    managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockAgentCoreBrowserExecutionRolePolicy")
    ]
)

# Create browser with custom execution role
browser = agentcore.BrowserCustom(self, "MyBrowser",
    browser_custom_name="my_browser",
    description="Browser with custom execution role",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network(),
    execution_role=execution_role
)
```

### Browser with S3 Recording and Permissions

```python
# Create an S3 bucket for recordings
recording_bucket = s3.Bucket(self, "RecordingBucket",
    bucket_name="my-browser-recordings",
    removal_policy=RemovalPolicy.DESTROY
)

# Create browser with recording enabled
browser = agentcore.BrowserCustom(self, "MyBrowser",
    browser_custom_name="my_browser",
    description="Browser with recording enabled",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network(),
    recording_config=agentcore.RecordingConfig(
        enabled=True,
        s3_location=s3.Location(
            bucket_name=recording_bucket.bucket_name,
            object_key="browser-recordings/"
        )
    )
)
```

### Browser IAM Permissions

The Browser construct provides convenient methods for granting IAM permissions:

```python
# Create a browser
browser = agentcore.BrowserCustom(self, "MyBrowser",
    browser_custom_name="my_browser",
    description="Browser for web automation",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network()
)

# Create a role that needs access to the browser
user_role = iam.Role(self, "UserRole",
    assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
)

# Grant read permissions (Get and List actions)
browser.grant_read(user_role)

# Grant use permissions (Start, Update, Stop actions)
browser.grant_use(user_role)

# Grant specific custom permissions
browser.grant(user_role, "bedrock-agentcore:GetBrowserSession")
```

## Code Interpreter

The Amazon Bedrock AgentCore Code Interpreter enables AI agents to write and execute code securely in sandbox environments, enhancing their accuracy and expanding their ability to solve complex end-to-end tasks. This is critical in Agentic AI applications where the agents may execute arbitrary code that can lead to data compromise or security risks. The AgentCore Code Interpreter tool provides secure code execution, which helps you avoid running into these issues.

For more information about code interpreter, please refer to the [official documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html)

### Code Interpreter Network Modes

The Code Interpreter construct supports the following network modes:

1. **Public Network Mode** (`CodeInterpreterNetworkMode.usingPublicNetwork()`) - Default

   * Allows internet access for package installation and external API calls
   * Suitable for development and testing environments
   * Enables downloading Python packages from PyPI
2. **Sandbox Network Mode** (`CodeInterpreterNetworkMode.usingSandboxNetwork()`)

   * Isolated network environment with no internet access
   * Suitable for production environments with strict security requirements
   * Only allows access to pre-installed packages and local resources
3. **VPC (Virtual Private Cloud)** (`CodeInterpreterNetworkMode.usingVpc()`)

   * Select whether to run the browser in a virtual private cloud (VPC).
   * By configuring VPC connectivity, you enable secure access to private resources such as databases, internal APIs, and services within your VPC.

   While the VPC itself is mandatory, these are optional:

   * Subnets - if not provided, CDK will select appropriate subnets from the VPC
   * Security Groups - if not provided, CDK will create a default security group
   * Specific subnet selection criteria - you can let CDK choose automatically

For more information on VPC connectivity for Amazon Bedrock AgentCore Browser, please refer to the [official documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html).

### Code Interpreter Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codeInterpreterCustomName` | `string` | Yes | The name of the code interpreter. Must start with a letter and can be up to 48 characters long. Pattern: `[a-zA-Z][a-zA-Z0-9_]{0,47}` |
| `description` | `string` | No | Optional description for the code interpreter. Can have up to 200 characters |
| `executionRole` | `iam.IRole` | No | The IAM role that provides permissions for the code interpreter to access AWS services. A new role will be created if not provided |
| `networkConfiguration` | `CodeInterpreterNetworkConfiguration` | No | Network configuration for code interpreter. Defaults to PUBLIC network mode |
| `tags` | `{ [key: string]: string }` | No | Tags to apply to the code interpreter resource |

### Basic Code Interpreter Creation

```python
# Create a basic code interpreter with public network access
code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
    code_interpreter_custom_name="my_code_interpreter",
    description="A code interpreter for Python execution"
)
```

### Code Interpreter with VPC

```python
code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
    code_interpreter_custom_name="my_sandbox_interpreter",
    description="Code interpreter with isolated network access",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_vpc(self,
        vpc=ec2.Vpc(self, "VPC", restrict_default_security_group=False)
    )
)
```

Code Interpreter exposes a [connections](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ec2.Connections.html) property. This property returns a connections object, which simplifies the process of defining and managing ingress and egress rules for security groups in your AWS CDK applications. Instead of directly manipulating security group rules, you interact with the Connections object of a construct, which then translates your connectivity requirements into the appropriate security group rules. For instance:

```python
vpc = ec2.Vpc(self, "testVPC")

code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
    code_interpreter_custom_name="my_sandbox_interpreter",
    description="Code interpreter with isolated network access",
    network_configuration=agentcore.BrowserNetworkConfiguration.using_vpc(self,
        vpc=vpc
    )
)

code_interpreter.connections.add_security_group(ec2.SecurityGroup(self, "AdditionalGroup", vpc=vpc))
```

So security groups can be added after the browser construct creation. You can use methods like allowFrom() and allowTo() to grant ingress access to/egress access from a specified peer over a given portRange. The Connections object automatically adds the necessary ingress or egress rules to the security group(s) associated with the calling construct.

### Code Interpreter with Sandbox Network Mode

```python
# Create code interpreter with sandbox network mode (isolated)
code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
    code_interpreter_custom_name="my_sandbox_interpreter",
    description="Code interpreter with isolated network access",
    network_configuration=agentcore.CodeInterpreterNetworkConfiguration.using_sandbox_network()
)
```

### Code Interpreter with Custom Execution Role

```python
# Create a custom execution role
execution_role = iam.Role(self, "CodeInterpreterExecutionRole",
    assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com")
)

# Create code interpreter with custom execution role
code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
    code_interpreter_custom_name="my_code_interpreter",
    description="Code interpreter with custom execution role",
    network_configuration=agentcore.CodeInterpreterNetworkConfiguration.using_public_network(),
    execution_role=execution_role
)
```

### Code Interpreter IAM Permissions

The Code Interpreter construct provides convenient methods for granting IAM permissions:

```python
# Create a code interpreter
code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
    code_interpreter_custom_name="my_code_interpreter",
    description="Code interpreter for Python execution",
    network_configuration=agentcore.CodeInterpreterNetworkConfiguration.using_public_network()
)

# Create a role that needs access to the code interpreter
user_role = iam.Role(self, "UserRole",
    assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
)

# Grant read permissions (Get and List actions)
code_interpreter.grant_read(user_role)

# Grant use permissions (Start, Invoke, Stop actions)
code_interpreter.grant_use(user_role)

# Grant specific custom permissions
code_interpreter.grant(user_role, "bedrock-agentcore:GetCodeInterpreterSession")
```

### Code interpreter with tags

```python
# Create code interpreter with sandbox network mode (isolated)
code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
    code_interpreter_custom_name="my_sandbox_interpreter",
    description="Code interpreter with isolated network access",
    network_configuration=agentcore.CodeInterpreterNetworkConfiguration.using_public_network(),
    tags={
        "Environment": "Production",
        "Team": "AI/ML",
        "Project": "AgentCore"
    }
)
```
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_cloudwatch as _aws_cdk_aws_cloudwatch_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_ecr as _aws_cdk_aws_ecr_ceddda9d
import aws_cdk.aws_ecr_assets as _aws_cdk_aws_ecr_assets_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.AddEndpointOptions",
    jsii_struct_bases=[],
    name_mapping={"description": "description", "version": "version"},
)
class AddEndpointOptions:
    def __init__(
        self,
        *,
        description: typing.Optional[builtins.str] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Options for adding an endpoint to the runtime.

        :param description: (experimental) Description for the endpoint, Must be between 1 and 1200 characters. Default: - No description
        :param version: (experimental) Override the runtime version for this endpoint. Default: 1

        :stability: experimental
        :exampleMetadata: infused

        Example::

            repository = ecr.Repository(self, "TestRepository",
                repository_name="test-agent-runtime"
            )
            
            agent_runtime_artifact_new = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v2.0.0")
            
            runtime = agentcore.Runtime(self, "MyAgentRuntime",
                runtime_name="myAgent",
                agent_runtime_artifact=agent_runtime_artifact_new
            )
            
            staging_endpoint = runtime.add_endpoint("staging",
                version="2",
                description="Staging environment for testing new version"
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__175b1aee490f549cb19d8945b728786765752ce863f0a55d8732e6f777128e9b)
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if description is not None:
            self._values["description"] = description
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) Description for the endpoint, Must be between 1 and 1200 characters.

        :default: - No description

        :stability: experimental
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''(experimental) Override the runtime version for this endpoint.

        :default: 1

        :stability: experimental
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AddEndpointOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AgentRuntimeArtifact(
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.AgentRuntimeArtifact",
):
    '''(experimental) Abstract base class for agent runtime artifacts.

    Provides methods to reference container images from ECR repositories or local assets.

    :stability: experimental
    :exampleMetadata: infused

    Example::

        repository = ecr.Repository(self, "TestRepository",
            repository_name="test-agent-runtime"
        )
        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
        
        runtime = agentcore.Runtime(self, "MyAgentRuntime",
            runtime_name="myAgent",
            agent_runtime_artifact=agent_runtime_artifact,
            authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_oAuth("https://github.com/.well-known/openid-configuration", "oauth_client_123")
        )
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="fromAsset")
    @builtins.classmethod
    def from_asset(
        cls,
        directory: builtins.str,
        *,
        asset_name: typing.Optional[builtins.str] = None,
        build_args: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        build_secrets: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        build_ssh: typing.Optional[builtins.str] = None,
        cache_disabled: typing.Optional[builtins.bool] = None,
        cache_from: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]]] = None,
        cache_to: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]] = None,
        display_name: typing.Optional[builtins.str] = None,
        file: typing.Optional[builtins.str] = None,
        invalidation: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        network_mode: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode] = None,
        outputs: typing.Optional[typing.Sequence[builtins.str]] = None,
        platform: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform] = None,
        target: typing.Optional[builtins.str] = None,
        extra_hash: typing.Optional[builtins.str] = None,
        exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
        follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
        ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
    ) -> "AgentRuntimeArtifact":
        '''(experimental) Reference an agent runtime artifact that's constructed directly from sources on disk.

        :param directory: The directory where the Dockerfile is stored.
        :param asset_name: Unique identifier of the docker image asset and its potential revisions. Required if using AppScopedStagingSynthesizer. Default: - no asset name
        :param build_args: Build args to pass to the ``docker build`` command. Since Docker build arguments are resolved before deployment, keys and values cannot refer to unresolved tokens (such as ``lambda.functionArn`` or ``queue.queueUrl``). Default: - no build args are passed
        :param build_secrets: Build secrets. Docker BuildKit must be enabled to use build secrets. Default: - no build secrets
        :param build_ssh: SSH agent socket or keys to pass to the ``docker build`` command. Docker BuildKit must be enabled to use the ssh flag Default: - no --ssh flag
        :param cache_disabled: Disable the cache and pass ``--no-cache`` to the ``docker build`` command. Default: - cache is used
        :param cache_from: Cache from options to pass to the ``docker build`` command. Default: - no cache from options are passed to the build command
        :param cache_to: Cache to options to pass to the ``docker build`` command. Default: - no cache to options are passed to the build command
        :param display_name: A display name for this asset. If supplied, the display name will be used in locations where the asset identifier is printed, like in the CLI progress information. If the same asset is added multiple times, the display name of the first occurrence is used. If ``assetName`` is given, it will also be used as the default ``displayName``. Otherwise, the default is the construct path of the ImageAsset construct, with respect to the enclosing stack. If the asset is produced by a construct helper function (such as ``lambda.Code.fromAssetImage()``), this will look like ``MyFunction/AssetImage``. We use the stack-relative construct path so that in the common case where you have multiple stacks with the same asset, we won't show something like ``/MyBetaStack/MyFunction/Code`` when you are actually deploying to production. Default: - Stack-relative construct path
        :param file: Path to the Dockerfile (relative to the directory). Default: 'Dockerfile'
        :param invalidation: Options to control which parameters are used to invalidate the asset hash. Default: - hash all parameters
        :param network_mode: Networking mode for the RUN commands during build. Support docker API 1.25+. Default: - no networking mode specified (the default networking mode ``NetworkMode.DEFAULT`` will be used)
        :param outputs: Outputs to pass to the ``docker build`` command. Default: - no outputs are passed to the build command (default outputs are used)
        :param platform: Platform to build for. *Requires Docker Buildx*. Default: - no platform specified (the current machine architecture will be used)
        :param target: Docker target to build to. Default: - no target
        :param extra_hash: Extra information to encode into the fingerprint (e.g. build instructions and other inputs). Default: - hash is only based on source content
        :param exclude: File paths matching the patterns will be excluded. See ``ignoreMode`` to set the matching behavior. Has no effect on Assets bundled using the ``bundling`` property. Default: - nothing is excluded
        :param follow_symlinks: A strategy for how to handle symlinks. Default: SymlinkFollowMode.NEVER
        :param ignore_mode: The ignore behavior to use for ``exclude`` patterns. Default: IgnoreMode.GLOB

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__604d365a86a290247af7992e6be98b47b27307a51f5ffdb436c6c1ea4019453a)
            check_type(argname="argument directory", value=directory, expected_type=type_hints["directory"])
        options = _aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetOptions(
            asset_name=asset_name,
            build_args=build_args,
            build_secrets=build_secrets,
            build_ssh=build_ssh,
            cache_disabled=cache_disabled,
            cache_from=cache_from,
            cache_to=cache_to,
            display_name=display_name,
            file=file,
            invalidation=invalidation,
            network_mode=network_mode,
            outputs=outputs,
            platform=platform,
            target=target,
            extra_hash=extra_hash,
            exclude=exclude,
            follow_symlinks=follow_symlinks,
            ignore_mode=ignore_mode,
        )

        return typing.cast("AgentRuntimeArtifact", jsii.sinvoke(cls, "fromAsset", [directory, options]))

    @jsii.member(jsii_name="fromEcrRepository")
    @builtins.classmethod
    def from_ecr_repository(
        cls,
        repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
        tag: typing.Optional[builtins.str] = None,
    ) -> "AgentRuntimeArtifact":
        '''(experimental) Reference an image in an ECR repository.

        :param repository: -
        :param tag: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5378ad450d2e50130983bd4e4c0d41f7ddc7b25ef75b63e107cdace81383db49)
            check_type(argname="argument repository", value=repository, expected_type=type_hints["repository"])
            check_type(argname="argument tag", value=tag, expected_type=type_hints["tag"])
        return typing.cast("AgentRuntimeArtifact", jsii.sinvoke(cls, "fromEcrRepository", [repository, tag]))

    @jsii.member(jsii_name="bind")
    @abc.abstractmethod
    def bind(self, scope: _constructs_77d1e7e8.Construct, runtime: "Runtime") -> None:
        '''(experimental) Called when the image is used by a Runtime to handle side effects like permissions.

        :param scope: -
        :param runtime: -

        :stability: experimental
        '''
        ...


class _AgentRuntimeArtifactProxy(AgentRuntimeArtifact):
    @jsii.member(jsii_name="bind")
    def bind(self, scope: _constructs_77d1e7e8.Construct, runtime: "Runtime") -> None:
        '''(experimental) Called when the image is used by a Runtime to handle side effects like permissions.

        :param scope: -
        :param runtime: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bedccb351eb2d100e954ac8354c709d22031237b55a8c9439b4fa56a9c488298)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument runtime", value=runtime, expected_type=type_hints["runtime"])
        return typing.cast(None, jsii.invoke(self, "bind", [scope, runtime]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, AgentRuntimeArtifact).__jsii_proxy_class__ = lambda : _AgentRuntimeArtifactProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.AgentRuntimeAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "agent_runtime_arn": "agentRuntimeArn",
        "agent_runtime_id": "agentRuntimeId",
        "agent_runtime_name": "agentRuntimeName",
        "role_arn": "roleArn",
        "agent_runtime_version": "agentRuntimeVersion",
        "agent_status": "agentStatus",
        "created_at": "createdAt",
        "description": "description",
        "last_updated_at": "lastUpdatedAt",
        "security_groups": "securityGroups",
    },
)
class AgentRuntimeAttributes:
    def __init__(
        self,
        *,
        agent_runtime_arn: builtins.str,
        agent_runtime_id: builtins.str,
        agent_runtime_name: builtins.str,
        role_arn: builtins.str,
        agent_runtime_version: typing.Optional[builtins.str] = None,
        agent_status: typing.Optional[builtins.str] = None,
        created_at: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    ) -> None:
        '''(experimental) Attributes for importing an existing Agent Runtime.

        :param agent_runtime_arn: (experimental) The ARN of the agent runtime.
        :param agent_runtime_id: (experimental) The ID of the agent runtime.
        :param agent_runtime_name: (experimental) The name of the agent runtime.
        :param role_arn: (experimental) The IAM role ARN.
        :param agent_runtime_version: (experimental) The version of the agent runtime When importing a runtime and this is not specified or undefined, endpoints created on this runtime will point to version "1" unless explicitly overridden. Default: - undefined
        :param agent_status: (experimental) The current status of the agent runtime. Default: - Status not available
        :param created_at: (experimental) The time at which the runtime was created. Default: - Creation time not available
        :param description: (experimental) The description of the agent runtime. Default: - No description
        :param last_updated_at: (experimental) The time at which the runtime was last updated. Default: - Last update time not available
        :param security_groups: (experimental) The security groups for this runtime, if in a VPC. Default: - By default, the runtime is not in a VPC.

        :stability: experimental
        :exampleMetadata: fixture=_generated

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_bedrock_agentcore_alpha as bedrock_agentcore_alpha
            from aws_cdk import aws_ec2 as ec2
            
            # security_group: ec2.SecurityGroup
            
            agent_runtime_attributes = bedrock_agentcore_alpha.AgentRuntimeAttributes(
                agent_runtime_arn="agentRuntimeArn",
                agent_runtime_id="agentRuntimeId",
                agent_runtime_name="agentRuntimeName",
                role_arn="roleArn",
            
                # the properties below are optional
                agent_runtime_version="agentRuntimeVersion",
                agent_status="agentStatus",
                created_at="createdAt",
                description="description",
                last_updated_at="lastUpdatedAt",
                security_groups=[security_group]
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__521eb5a43c1809da91e6b913f83fa6446f5b8ac2c440a565fa2764b3cd9f4ad8)
            check_type(argname="argument agent_runtime_arn", value=agent_runtime_arn, expected_type=type_hints["agent_runtime_arn"])
            check_type(argname="argument agent_runtime_id", value=agent_runtime_id, expected_type=type_hints["agent_runtime_id"])
            check_type(argname="argument agent_runtime_name", value=agent_runtime_name, expected_type=type_hints["agent_runtime_name"])
            check_type(argname="argument role_arn", value=role_arn, expected_type=type_hints["role_arn"])
            check_type(argname="argument agent_runtime_version", value=agent_runtime_version, expected_type=type_hints["agent_runtime_version"])
            check_type(argname="argument agent_status", value=agent_status, expected_type=type_hints["agent_status"])
            check_type(argname="argument created_at", value=created_at, expected_type=type_hints["created_at"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument last_updated_at", value=last_updated_at, expected_type=type_hints["last_updated_at"])
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "agent_runtime_arn": agent_runtime_arn,
            "agent_runtime_id": agent_runtime_id,
            "agent_runtime_name": agent_runtime_name,
            "role_arn": role_arn,
        }
        if agent_runtime_version is not None:
            self._values["agent_runtime_version"] = agent_runtime_version
        if agent_status is not None:
            self._values["agent_status"] = agent_status
        if created_at is not None:
            self._values["created_at"] = created_at
        if description is not None:
            self._values["description"] = description
        if last_updated_at is not None:
            self._values["last_updated_at"] = last_updated_at
        if security_groups is not None:
            self._values["security_groups"] = security_groups

    @builtins.property
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime.

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_arn")
        assert result is not None, "Required property 'agent_runtime_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The ID of the agent runtime.

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_id")
        assert result is not None, "Required property 'agent_runtime_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def agent_runtime_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime.

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_name")
        assert result is not None, "Required property 'agent_runtime_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role_arn(self) -> builtins.str:
        '''(experimental) The IAM role ARN.

        :stability: experimental
        '''
        result = self._values.get("role_arn")
        assert result is not None, "Required property 'role_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def agent_runtime_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of the agent runtime When importing a runtime and this is not specified or undefined, endpoints created on this runtime will point to version "1" unless explicitly overridden.

        :default: - undefined

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def agent_status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the agent runtime.

        :default: - Status not available

        :stability: experimental
        '''
        result = self._values.get("agent_status")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was created.

        :default: - Creation time not available

        :stability: experimental
        '''
        result = self._values.get("created_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the agent runtime.

        :default: - No description

        :stability: experimental
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was last updated.

        :default: - Last update time not available

        :stability: experimental
        '''
        result = self._values.get("last_updated_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups for this runtime, if in a VPC.

        :default: - By default, the runtime is not in a VPC.

        :stability: experimental
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AgentRuntimeAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.BrowserCustomAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "browser_arn": "browserArn",
        "role_arn": "roleArn",
        "created_at": "createdAt",
        "last_updated_at": "lastUpdatedAt",
        "security_groups": "securityGroups",
        "status": "status",
    },
)
class BrowserCustomAttributes:
    def __init__(
        self,
        *,
        browser_arn: builtins.str,
        role_arn: builtins.str,
        created_at: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        status: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Attributes for specifying an imported Browser Custom.

        :param browser_arn: (experimental) The ARN of the agent.
        :param role_arn: (experimental) The ARN of the IAM role associated to the browser.
        :param created_at: (experimental) The created timestamp of the browser. Default: undefined - No created timestamp is provided
        :param last_updated_at: (experimental) When this browser was last updated. Default: undefined - No last updated timestamp is provided
        :param security_groups: (experimental) The security groups for this browser, if in a VPC. Default: - By default, the browser is not in a VPC.
        :param status: (experimental) The status of the browser. Default: undefined - No status is provided

        :stability: experimental
        :exampleMetadata: fixture=_generated

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_bedrock_agentcore_alpha as bedrock_agentcore_alpha
            from aws_cdk import aws_ec2 as ec2
            
            # security_group: ec2.SecurityGroup
            
            browser_custom_attributes = bedrock_agentcore_alpha.BrowserCustomAttributes(
                browser_arn="browserArn",
                role_arn="roleArn",
            
                # the properties below are optional
                created_at="createdAt",
                last_updated_at="lastUpdatedAt",
                security_groups=[security_group],
                status="status"
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__14ea7632e5df00d60970b59a9a4cb5f38d208fd7a26740e3444fd2b1e4b432ba)
            check_type(argname="argument browser_arn", value=browser_arn, expected_type=type_hints["browser_arn"])
            check_type(argname="argument role_arn", value=role_arn, expected_type=type_hints["role_arn"])
            check_type(argname="argument created_at", value=created_at, expected_type=type_hints["created_at"])
            check_type(argname="argument last_updated_at", value=last_updated_at, expected_type=type_hints["last_updated_at"])
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
            check_type(argname="argument status", value=status, expected_type=type_hints["status"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "browser_arn": browser_arn,
            "role_arn": role_arn,
        }
        if created_at is not None:
            self._values["created_at"] = created_at
        if last_updated_at is not None:
            self._values["last_updated_at"] = last_updated_at
        if security_groups is not None:
            self._values["security_groups"] = security_groups
        if status is not None:
            self._values["status"] = status

    @builtins.property
    def browser_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent.

        :stability: experimental
        :attribute: true
        '''
        result = self._values.get("browser_arn")
        assert result is not None, "Required property 'browser_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role_arn(self) -> builtins.str:
        '''(experimental) The ARN of the IAM role associated to the browser.

        :stability: experimental
        :attribute: true
        '''
        result = self._values.get("role_arn")
        assert result is not None, "Required property 'role_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The created timestamp of the browser.

        :default: undefined - No created timestamp is provided

        :stability: experimental
        '''
        result = self._values.get("created_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When this browser was last updated.

        :default: undefined - No last updated timestamp is provided

        :stability: experimental
        '''
        result = self._values.get("last_updated_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups for this browser, if in a VPC.

        :default: - By default, the browser is not in a VPC.

        :stability: experimental
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], result)

    @builtins.property
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the browser.

        :default: undefined - No status is provided

        :stability: experimental
        '''
        result = self._values.get("status")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BrowserCustomAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.BrowserCustomProps",
    jsii_struct_bases=[],
    name_mapping={
        "browser_custom_name": "browserCustomName",
        "description": "description",
        "execution_role": "executionRole",
        "network_configuration": "networkConfiguration",
        "recording_config": "recordingConfig",
        "tags": "tags",
    },
)
class BrowserCustomProps:
    def __init__(
        self,
        *,
        browser_custom_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        network_configuration: typing.Optional["BrowserNetworkConfiguration"] = None,
        recording_config: typing.Optional[typing.Union["RecordingConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''(experimental) Properties for creating a Browser resource.

        :param browser_custom_name: (experimental) The name of the browser Valid characters are a-z, A-Z, 0-9, _ (underscore) The name must start with a letter and can be up to 48 characters long Pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}.
        :param description: (experimental) Optional description for the browser Valid characters are a-z, A-Z, 0-9, _ (underscore), - (hyphen) and spaces The description can have up to 200 characters. Default: - No description
        :param execution_role: (experimental) The IAM role that provides permissions for the browser to access AWS services. Default: - A new role will be created
        :param network_configuration: (experimental) Network configuration for browser. Default: - PUBLIC network mode
        :param recording_config: (experimental) Recording configuration for browser. Default: - No recording configuration
        :param tags: (experimental) Tags (optional) A list of key:value pairs of tags to apply to this Browser resource. Default: {} - no tags

        :stability: experimental
        :exampleMetadata: fixture=default infused

        Example::

            # Create a custom execution role
            execution_role = iam.Role(self, "BrowserExecutionRole",
                assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockAgentCoreBrowserExecutionRolePolicy")
                ]
            )
            
            # Create browser with custom execution role
            browser = agentcore.BrowserCustom(self, "MyBrowser",
                browser_custom_name="my_browser",
                description="Browser with custom execution role",
                network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network(),
                execution_role=execution_role
            )
        '''
        if isinstance(recording_config, dict):
            recording_config = RecordingConfig(**recording_config)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c723ceb06d7434df1c72a1865f418037daeeda29f30194820f0872da7d50bbe8)
            check_type(argname="argument browser_custom_name", value=browser_custom_name, expected_type=type_hints["browser_custom_name"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument execution_role", value=execution_role, expected_type=type_hints["execution_role"])
            check_type(argname="argument network_configuration", value=network_configuration, expected_type=type_hints["network_configuration"])
            check_type(argname="argument recording_config", value=recording_config, expected_type=type_hints["recording_config"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "browser_custom_name": browser_custom_name,
        }
        if description is not None:
            self._values["description"] = description
        if execution_role is not None:
            self._values["execution_role"] = execution_role
        if network_configuration is not None:
            self._values["network_configuration"] = network_configuration
        if recording_config is not None:
            self._values["recording_config"] = recording_config
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def browser_custom_name(self) -> builtins.str:
        '''(experimental) The name of the browser Valid characters are a-z, A-Z, 0-9, _ (underscore) The name must start with a letter and can be up to 48 characters long Pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}.

        :stability: experimental
        :required: - Yes
        '''
        result = self._values.get("browser_custom_name")
        assert result is not None, "Required property 'browser_custom_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) Optional description for the browser Valid characters are a-z, A-Z, 0-9, _ (underscore), - (hyphen) and spaces The description can have up to 200 characters.

        :default: - No description

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def execution_role(self) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole]:
        '''(experimental) The IAM role that provides permissions for the browser to access AWS services.

        :default: - A new role will be created

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("execution_role")
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole], result)

    @builtins.property
    def network_configuration(self) -> typing.Optional["BrowserNetworkConfiguration"]:
        '''(experimental) Network configuration for browser.

        :default: - PUBLIC network mode

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("network_configuration")
        return typing.cast(typing.Optional["BrowserNetworkConfiguration"], result)

    @builtins.property
    def recording_config(self) -> typing.Optional["RecordingConfig"]:
        '''(experimental) Recording configuration for browser.

        :default: - No recording configuration

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("recording_config")
        return typing.cast(typing.Optional["RecordingConfig"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags (optional) A list of key:value pairs of tags to apply to this Browser resource.

        :default: {} - no tags

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BrowserCustomProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.CodeInterpreterCustomAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "code_interpreter_arn": "codeInterpreterArn",
        "role_arn": "roleArn",
        "created_at": "createdAt",
        "last_updated_at": "lastUpdatedAt",
        "security_groups": "securityGroups",
        "status": "status",
    },
)
class CodeInterpreterCustomAttributes:
    def __init__(
        self,
        *,
        code_interpreter_arn: builtins.str,
        role_arn: builtins.str,
        created_at: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        status: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Attributes for specifying an imported Code Interpreter Custom.

        :param code_interpreter_arn: (experimental) The ARN of the agent.
        :param role_arn: (experimental) The ARN of the IAM role associated to the code interpreter.
        :param created_at: (experimental) The created timestamp of the code interpreter. Default: undefined - No created timestamp is provided
        :param last_updated_at: (experimental) When this code interpreter was last updated. Default: undefined - No last updated timestamp is provided
        :param security_groups: (experimental) The security groups for this code interpreter, if in a VPC. Default: - By default, the code interpreter is not in a VPC.
        :param status: (experimental) The status of the code interpreter. Default: undefined - No status is provided

        :stability: experimental
        :exampleMetadata: fixture=_generated

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_bedrock_agentcore_alpha as bedrock_agentcore_alpha
            from aws_cdk import aws_ec2 as ec2
            
            # security_group: ec2.SecurityGroup
            
            code_interpreter_custom_attributes = bedrock_agentcore_alpha.CodeInterpreterCustomAttributes(
                code_interpreter_arn="codeInterpreterArn",
                role_arn="roleArn",
            
                # the properties below are optional
                created_at="createdAt",
                last_updated_at="lastUpdatedAt",
                security_groups=[security_group],
                status="status"
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f96ed57c1afc648e15cebfa320e03f93dc4c161c09d253072930e4b7d4e4ed24)
            check_type(argname="argument code_interpreter_arn", value=code_interpreter_arn, expected_type=type_hints["code_interpreter_arn"])
            check_type(argname="argument role_arn", value=role_arn, expected_type=type_hints["role_arn"])
            check_type(argname="argument created_at", value=created_at, expected_type=type_hints["created_at"])
            check_type(argname="argument last_updated_at", value=last_updated_at, expected_type=type_hints["last_updated_at"])
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
            check_type(argname="argument status", value=status, expected_type=type_hints["status"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "code_interpreter_arn": code_interpreter_arn,
            "role_arn": role_arn,
        }
        if created_at is not None:
            self._values["created_at"] = created_at
        if last_updated_at is not None:
            self._values["last_updated_at"] = last_updated_at
        if security_groups is not None:
            self._values["security_groups"] = security_groups
        if status is not None:
            self._values["status"] = status

    @builtins.property
    def code_interpreter_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent.

        :stability: experimental
        :attribute: true
        '''
        result = self._values.get("code_interpreter_arn")
        assert result is not None, "Required property 'code_interpreter_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role_arn(self) -> builtins.str:
        '''(experimental) The ARN of the IAM role associated to the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        result = self._values.get("role_arn")
        assert result is not None, "Required property 'role_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The created timestamp of the code interpreter.

        :default: undefined - No created timestamp is provided

        :stability: experimental
        '''
        result = self._values.get("created_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When this code interpreter was last updated.

        :default: undefined - No last updated timestamp is provided

        :stability: experimental
        '''
        result = self._values.get("last_updated_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups for this code interpreter, if in a VPC.

        :default: - By default, the code interpreter is not in a VPC.

        :stability: experimental
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], result)

    @builtins.property
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the code interpreter.

        :default: undefined - No status is provided

        :stability: experimental
        '''
        result = self._values.get("status")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CodeInterpreterCustomAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.CodeInterpreterCustomProps",
    jsii_struct_bases=[],
    name_mapping={
        "code_interpreter_custom_name": "codeInterpreterCustomName",
        "description": "description",
        "execution_role": "executionRole",
        "network_configuration": "networkConfiguration",
        "tags": "tags",
    },
)
class CodeInterpreterCustomProps:
    def __init__(
        self,
        *,
        code_interpreter_custom_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        network_configuration: typing.Optional["CodeInterpreterNetworkConfiguration"] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''(experimental) Properties for creating a CodeInterpreter resource.

        :param code_interpreter_custom_name: (experimental) The name of the code interpreter Valid characters are a-z, A-Z, 0-9, _ (underscore) The name must start with a letter and can be up to 48 characters long Pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}.
        :param description: (experimental) Optional description for the code interpreter Valid characters are a-z, A-Z, 0-9, _ (underscore), - (hyphen) and spaces The description can have up to 200 characters. Default: - No description
        :param execution_role: (experimental) The IAM role that provides permissions for the code interpreter to access AWS services. Default: - A new role will be created.
        :param network_configuration: (experimental) Network configuration for code interpreter. Default: - PUBLIC network mode
        :param tags: (experimental) Tags (optional) A list of key:value pairs of tags to apply to this Code Interpreter resource. Default: {} - no tags

        :stability: experimental
        :exampleMetadata: fixture=default infused

        Example::

            # Create a custom execution role
            execution_role = iam.Role(self, "CodeInterpreterExecutionRole",
                assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com")
            )
            
            # Create code interpreter with custom execution role
            code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
                code_interpreter_custom_name="my_code_interpreter",
                description="Code interpreter with custom execution role",
                network_configuration=agentcore.CodeInterpreterNetworkConfiguration.using_public_network(),
                execution_role=execution_role
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e75974384deaaee0d0812c3570b15b1adf0a19fbd67095aea1229a4d3d5c5c05)
            check_type(argname="argument code_interpreter_custom_name", value=code_interpreter_custom_name, expected_type=type_hints["code_interpreter_custom_name"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument execution_role", value=execution_role, expected_type=type_hints["execution_role"])
            check_type(argname="argument network_configuration", value=network_configuration, expected_type=type_hints["network_configuration"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "code_interpreter_custom_name": code_interpreter_custom_name,
        }
        if description is not None:
            self._values["description"] = description
        if execution_role is not None:
            self._values["execution_role"] = execution_role
        if network_configuration is not None:
            self._values["network_configuration"] = network_configuration
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def code_interpreter_custom_name(self) -> builtins.str:
        '''(experimental) The name of the code interpreter Valid characters are a-z, A-Z, 0-9, _ (underscore) The name must start with a letter and can be up to 48 characters long Pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}.

        :stability: experimental
        :required: - Yes
        '''
        result = self._values.get("code_interpreter_custom_name")
        assert result is not None, "Required property 'code_interpreter_custom_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) Optional description for the code interpreter Valid characters are a-z, A-Z, 0-9, _ (underscore), - (hyphen) and spaces The description can have up to 200 characters.

        :default: - No description

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def execution_role(self) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole]:
        '''(experimental) The IAM role that provides permissions for the code interpreter to access AWS services.

        :default: - A new role will be created.

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("execution_role")
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole], result)

    @builtins.property
    def network_configuration(
        self,
    ) -> typing.Optional["CodeInterpreterNetworkConfiguration"]:
        '''(experimental) Network configuration for code interpreter.

        :default: - PUBLIC network mode

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("network_configuration")
        return typing.cast(typing.Optional["CodeInterpreterNetworkConfiguration"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags (optional) A list of key:value pairs of tags to apply to this Code Interpreter resource.

        :default: {} - no tags

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CodeInterpreterCustomProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.IBedrockAgentRuntime")
class IBedrockAgentRuntime(
    _aws_cdk_ceddda9d.IResource,
    _aws_cdk_aws_iam_ceddda9d.IGrantable,
    _aws_cdk_aws_ec2_ceddda9d.IConnectable,
    typing_extensions.Protocol,
):
    '''(experimental) Interface for Agent Runtime resources.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime resource - Format ``arn:${Partition}:bedrock-agentcore:${Region}:${Account}:runtime/${RuntimeId}``.

        :stability: experimental
        :attribute: true

        Example::

            "arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/runtime-abc123"
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeId")
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The ID of the agent runtime.

        :stability: experimental
        :attribute: true

        Example::

            "runtime-abc123"
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeName")
    def agent_runtime_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeVersion")
    def agent_runtime_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of the agent runtime.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentStatus")
    def agent_status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was created.

        :stability: experimental
        :attribute: true

        Example::

            "2024-01-15T10:30:00Z"
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was last updated.

        :stability: experimental
        :attribute: true

        Example::

            "2024-01-15T14:45:00Z"
        '''
        ...

    @jsii.member(jsii_name="addToRolePolicy")
    def add_to_role_policy(
        self,
        statement: _aws_cdk_aws_iam_ceddda9d.PolicyStatement,
    ) -> "IBedrockAgentRuntime":
        '''(experimental) Adds a policy statement to the runtime's execution role.

        :param statement: The IAM policy statement to add.

        :return: The runtime instance for chaining

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        actions: typing.Sequence[builtins.str],
        resources: typing.Sequence[builtins.str],
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant the runtime specific actions on AWS resources.

        :param actions: The actions to grant.
        :param resources: The resource ARNs to grant access to.

        :return: The Grant object for chaining

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantInvoke")
    def grant_invoke(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime both directly and on behalf of users Grants both bedrock-agentcore:InvokeAgentRuntime and bedrock-agentcore:InvokeAgentRuntimeForUser permissions.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantInvokeRuntime")
    def grant_invoke_runtime(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime Grants the bedrock-agentcore:InvokeAgentRuntime permission.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantInvokeRuntimeForUser")
    def grant_invoke_runtime_for_user(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime on behalf of a user Grants the bedrock-agentcore:InvokeAgentRuntimeForUser permission Required when using the X-Amzn-Bedrock-AgentCore-Runtime-User-Id header.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this agent runtime.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricInvocations")
    def metric_invocations(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of invocations for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricInvocationsAggregated")
    def metric_invocations_aggregated(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of invocations across all resources.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricLatency")
    def metric_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the latency of requests for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricSessionCount")
    def metric_session_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of agent sessions for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricSessionsAggregated")
    def metric_sessions_aggregated(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of sessions across all resources.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricSystemErrors")
    def metric_system_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of system errors for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricThrottles")
    def metric_throttles(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of throttled requests for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricTotalErrors")
    def metric_total_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of errors (system + user) for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricUserErrors")
    def metric_user_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user errors for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...


class _IBedrockAgentRuntimeProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
    jsii.proxy_for(_aws_cdk_aws_iam_ceddda9d.IGrantable), # type: ignore[misc]
    jsii.proxy_for(_aws_cdk_aws_ec2_ceddda9d.IConnectable), # type: ignore[misc]
):
    '''(experimental) Interface for Agent Runtime resources.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-bedrock-agentcore-alpha.IBedrockAgentRuntime"

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime resource - Format ``arn:${Partition}:bedrock-agentcore:${Region}:${Account}:runtime/${RuntimeId}``.

        :stability: experimental
        :attribute: true

        Example::

            "arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/runtime-abc123"
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeArn"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeId")
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The ID of the agent runtime.

        :stability: experimental
        :attribute: true

        Example::

            "runtime-abc123"
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeId"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeName")
    def agent_runtime_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeName"))

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the agent runtime.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "role"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeVersion")
    def agent_runtime_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of the agent runtime.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "agentRuntimeVersion"))

    @builtins.property
    @jsii.member(jsii_name="agentStatus")
    def agent_status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the agent runtime.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "agentStatus"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was created.

        :stability: experimental
        :attribute: true

        Example::

            "2024-01-15T10:30:00Z"
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was last updated.

        :stability: experimental
        :attribute: true

        Example::

            "2024-01-15T14:45:00Z"
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @jsii.member(jsii_name="addToRolePolicy")
    def add_to_role_policy(
        self,
        statement: _aws_cdk_aws_iam_ceddda9d.PolicyStatement,
    ) -> IBedrockAgentRuntime:
        '''(experimental) Adds a policy statement to the runtime's execution role.

        :param statement: The IAM policy statement to add.

        :return: The runtime instance for chaining

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3b1a5766ae93ba39d5e7df12bdfc35c2a7d298375e7689fbc39a3c76d50d2639)
            check_type(argname="argument statement", value=statement, expected_type=type_hints["statement"])
        return typing.cast(IBedrockAgentRuntime, jsii.invoke(self, "addToRolePolicy", [statement]))

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        actions: typing.Sequence[builtins.str],
        resources: typing.Sequence[builtins.str],
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant the runtime specific actions on AWS resources.

        :param actions: The actions to grant.
        :param resources: The resource ARNs to grant access to.

        :return: The Grant object for chaining

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3208bdcc07b3a3b3b7ac0ed80c7b033074eab2659722a2dec0d8400cf5da5af8)
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
            check_type(argname="argument resources", value=resources, expected_type=type_hints["resources"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [actions, resources]))

    @jsii.member(jsii_name="grantInvoke")
    def grant_invoke(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime both directly and on behalf of users Grants both bedrock-agentcore:InvokeAgentRuntime and bedrock-agentcore:InvokeAgentRuntimeForUser permissions.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e4ed0dc7cd812fb1d50239f33a79cd0a5de1be6488c8ee24a3b016a546ef94b)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantInvoke", [grantee]))

    @jsii.member(jsii_name="grantInvokeRuntime")
    def grant_invoke_runtime(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime Grants the bedrock-agentcore:InvokeAgentRuntime permission.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4e37d3744eaf4f98404f5daccedff6e7a637774c39193ceadfd0f88c7aa16d50)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantInvokeRuntime", [grantee]))

    @jsii.member(jsii_name="grantInvokeRuntimeForUser")
    def grant_invoke_runtime_for_user(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime on behalf of a user Grants the bedrock-agentcore:InvokeAgentRuntimeForUser permission Required when using the X-Amzn-Bedrock-AgentCore-Runtime-User-Id header.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b28241dea68e79093525ede5e9deed8adeda944e89126bbcebe733fd16561495)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantInvokeRuntimeForUser", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this agent runtime.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3beecc1a8cde07edfff6ed6fa9c6deb0e5c35524c1b4ca5bc87c39f95ca1f565)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, dimensions, props]))

    @jsii.member(jsii_name="metricInvocations")
    def metric_invocations(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of invocations for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocations", [props]))

    @jsii.member(jsii_name="metricInvocationsAggregated")
    def metric_invocations_aggregated(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of invocations across all resources.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocationsAggregated", [props]))

    @jsii.member(jsii_name="metricLatency")
    def metric_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the latency of requests for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricLatency", [props]))

    @jsii.member(jsii_name="metricSessionCount")
    def metric_session_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of agent sessions for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionCount", [props]))

    @jsii.member(jsii_name="metricSessionsAggregated")
    def metric_sessions_aggregated(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of sessions across all resources.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionsAggregated", [props]))

    @jsii.member(jsii_name="metricSystemErrors")
    def metric_system_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of system errors for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSystemErrors", [props]))

    @jsii.member(jsii_name="metricThrottles")
    def metric_throttles(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of throttled requests for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricThrottles", [props]))

    @jsii.member(jsii_name="metricTotalErrors")
    def metric_total_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of errors (system + user) for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTotalErrors", [props]))

    @jsii.member(jsii_name="metricUserErrors")
    def metric_user_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user errors for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricUserErrors", [props]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IBedrockAgentRuntime).__jsii_proxy_class__ = lambda : _IBedrockAgentRuntimeProxy


@jsii.interface(jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.IBrowserCustom")
class IBrowserCustom(
    _aws_cdk_ceddda9d.IResource,
    _aws_cdk_aws_iam_ceddda9d.IGrantable,
    _aws_cdk_aws_ec2_ceddda9d.IConnectable,
    typing_extensions.Protocol,
):
    '''(experimental) Interface for Browser resources.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="browserArn")
    def browser_arn(self) -> builtins.str:
        '''(experimental) The ARN of the browser resource.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="browserId")
    def browser_id(self) -> builtins.str:
        '''(experimental) The id of the browser.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the browser to access AWS services.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was created.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was last updated.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the browser.

        :stability: experimental
        :attribute: true
        '''
        ...

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: -
        :param actions: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantRead")
    def grant_read(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Get`` and ``List`` actions on the Browser.

        :param grantee: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantUse")
    def grant_use(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Invoke``, ``Start``, and ``Update`` actions on the Browser.

        :param grantee: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this browser.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricErrorsForApiOperation")
    def metric_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of errors for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricForApiOperation")
    def metric_for_api_operation(
        self,
        metric_name: builtins.str,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric related to the API operation performed on this browser.

        :param metric_name: -
        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricInvocationsForApiOperation")
    def metric_invocations_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of API requests made for a specific browser operation.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricLatencyForApiOperation")
    def metric_latency_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the latency of a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricSessionDuration")
    def metric_session_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the duration of browser sessions.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricSystemErrorsForApiOperation")
    def metric_system_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of system errors for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricTakeOverCount")
    def metric_take_over_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user takeovers.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricTakeOverDuration")
    def metric_take_over_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the duration of user takeovers.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricTakeOverReleaseCount")
    def metric_take_over_release_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user takeovers released.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricThrottlesForApiOperation")
    def metric_throttles_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of throttled requests for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricUserErrorsForApiOperation")
    def metric_user_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user errors for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...


class _IBrowserCustomProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
    jsii.proxy_for(_aws_cdk_aws_iam_ceddda9d.IGrantable), # type: ignore[misc]
    jsii.proxy_for(_aws_cdk_aws_ec2_ceddda9d.IConnectable), # type: ignore[misc]
):
    '''(experimental) Interface for Browser resources.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-bedrock-agentcore-alpha.IBrowserCustom"

    @builtins.property
    @jsii.member(jsii_name="browserArn")
    def browser_arn(self) -> builtins.str:
        '''(experimental) The ARN of the browser resource.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "browserArn"))

    @builtins.property
    @jsii.member(jsii_name="browserId")
    def browser_id(self) -> builtins.str:
        '''(experimental) The id of the browser.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "browserId"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the browser to access AWS services.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was created.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was last updated.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the browser.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: -
        :param actions: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4826f7478acda3a04d53cc2e00e999d28d4b6af89d40b4863b0007b08c0b26bf)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantRead")
    def grant_read(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Get`` and ``List`` actions on the Browser.

        :param grantee: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da9382b030a7d475c5afa4286f7e177b609a5f61d4d9d40b1767f5c1e99b8815)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantRead", [grantee]))

    @jsii.member(jsii_name="grantUse")
    def grant_use(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Invoke``, ``Start``, and ``Update`` actions on the Browser.

        :param grantee: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dd8850bcf1d06baf4b66c051e33ef652a6c75bc169744326c9d541535c3f3ca7)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantUse", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this browser.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__efd83ae8402a4ac91c4d9cee61087a64dc24f53da2f48b59aa2cc85cde883b29)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, dimensions, props]))

    @jsii.member(jsii_name="metricErrorsForApiOperation")
    def metric_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of errors for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9182d2fd8511b983f694d71df771315bd2911e5e5d9482b933161a628210ec54)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricForApiOperation")
    def metric_for_api_operation(
        self,
        metric_name: builtins.str,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric related to the API operation performed on this browser.

        :param metric_name: -
        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e825fd71c16a04ffa07fa3e9ff9d61d6e478bdf2f90788eba67bba76e9f38ccb)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricForApiOperation", [metric_name, operation, props]))

    @jsii.member(jsii_name="metricInvocationsForApiOperation")
    def metric_invocations_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of API requests made for a specific browser operation.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8cf7f7691dff5fcb719882b3a76ff7b4a55b686f01244cf9ab3c1ee39a4dd4fc)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocationsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricLatencyForApiOperation")
    def metric_latency_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the latency of a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f6be7d90ffdb2f66b76b997f0926ae3ff14c53cc65c008f5a0591e3f4676265a)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricLatencyForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricSessionDuration")
    def metric_session_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the duration of browser sessions.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionDuration", [props]))

    @jsii.member(jsii_name="metricSystemErrorsForApiOperation")
    def metric_system_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of system errors for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cfb1295c98675d8b1f487abc85bf1d69ec7ac709035de1d15c83e328863a23ec)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSystemErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricTakeOverCount")
    def metric_take_over_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user takeovers.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTakeOverCount", [props]))

    @jsii.member(jsii_name="metricTakeOverDuration")
    def metric_take_over_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the duration of user takeovers.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTakeOverDuration", [props]))

    @jsii.member(jsii_name="metricTakeOverReleaseCount")
    def metric_take_over_release_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user takeovers released.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTakeOverReleaseCount", [props]))

    @jsii.member(jsii_name="metricThrottlesForApiOperation")
    def metric_throttles_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of throttled requests for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ea0c6d4b07cd9212bb39f789638d8a9a6af30cbc0157a19bcd58f6b94d852755)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricThrottlesForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricUserErrorsForApiOperation")
    def metric_user_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user errors for a specific API operation performed on this browser.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c1768ca682c2fd421a544ff8111e6e6985b07e3d62cdc62c35ef9cee5896ce2e)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricUserErrorsForApiOperation", [operation, props]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IBrowserCustom).__jsii_proxy_class__ = lambda : _IBrowserCustomProxy


@jsii.interface(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.ICodeInterpreterCustom"
)
class ICodeInterpreterCustom(
    _aws_cdk_ceddda9d.IResource,
    _aws_cdk_aws_iam_ceddda9d.IGrantable,
    _aws_cdk_aws_ec2_ceddda9d.IConnectable,
    typing_extensions.Protocol,
):
    '''(experimental) Interface for CodeInterpreterCustom resources.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterArn")
    def code_interpreter_arn(self) -> builtins.str:
        '''(experimental) The ARN of the code interpreter resource.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterId")
    def code_interpreter_id(self) -> builtins.str:
        '''(experimental) The id of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the code interpreter to access AWS services.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was created.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was last updated.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        ...

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: -
        :param actions: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantRead")
    def grant_read(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Get`` and ``List`` actions on the Code Interpreter.

        :param grantee: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantUse")
    def grant_use(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Invoke``, ``Start``, and ``Stop`` actions on the Code Interpreter.

        :param grantee: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this code interpreter.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricErrorsForApiOperation")
    def metric_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of errors for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricForApiOperation")
    def metric_for_api_operation(
        self,
        metric_name: builtins.str,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric related to the API operation performed on this code interpreter.

        :param metric_name: -
        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricInvocationsForApiOperation")
    def metric_invocations_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of API requests made for a specific code interpreter operation.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricLatencyForApiOperation")
    def metric_latency_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the latency of a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricSessionDuration")
    def metric_session_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the duration of code interpreter sessions.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricSystemErrorsForApiOperation")
    def metric_system_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of system errors for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricThrottlesForApiOperation")
    def metric_throttles_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of throttled requests for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricUserErrorsForApiOperation")
    def metric_user_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user errors for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...


class _ICodeInterpreterCustomProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
    jsii.proxy_for(_aws_cdk_aws_iam_ceddda9d.IGrantable), # type: ignore[misc]
    jsii.proxy_for(_aws_cdk_aws_ec2_ceddda9d.IConnectable), # type: ignore[misc]
):
    '''(experimental) Interface for CodeInterpreterCustom resources.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-bedrock-agentcore-alpha.ICodeInterpreterCustom"

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterArn")
    def code_interpreter_arn(self) -> builtins.str:
        '''(experimental) The ARN of the code interpreter resource.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "codeInterpreterArn"))

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterId")
    def code_interpreter_id(self) -> builtins.str:
        '''(experimental) The id of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "codeInterpreterId"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the code interpreter to access AWS services.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was created.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was last updated.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: -
        :param actions: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04274b315577b6819dda4346fc076850f28656449a559f5561ca7d53df97f5e3)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantRead")
    def grant_read(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Get`` and ``List`` actions on the Code Interpreter.

        :param grantee: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0ec65ea8e752705bafc58f0d6cacd39d556973c472ffb0789fa4af3ebcce4bcc)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantRead", [grantee]))

    @jsii.member(jsii_name="grantUse")
    def grant_use(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants ``Invoke``, ``Start``, and ``Stop`` actions on the Code Interpreter.

        :param grantee: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d24a36658edbfd7ecf76e5be971a6012fc93c641f1a510d1ddfd95730be1d7db)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantUse", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this code interpreter.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e4df790d3e336e48159d1eef607374eaf8f903928d69bd2620e375c4794e4fb3)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, dimensions, props]))

    @jsii.member(jsii_name="metricErrorsForApiOperation")
    def metric_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of errors for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eedad4c7938113f5f34f301a9b648ae40f5400a9e4de351b0186137052a65fab)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricForApiOperation")
    def metric_for_api_operation(
        self,
        metric_name: builtins.str,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric related to the API operation performed on this code interpreter.

        :param metric_name: -
        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__669e8f3a0db7a0b0e3787f22af4e559b8709590c28a9b79f240d11855cd87a11)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricForApiOperation", [metric_name, operation, props]))

    @jsii.member(jsii_name="metricInvocationsForApiOperation")
    def metric_invocations_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of API requests made for a specific code interpreter operation.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d5ade6561c63063084b2bd832a2df3362c624482ddaf7b7207ebec55d3e5431b)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocationsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricLatencyForApiOperation")
    def metric_latency_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the latency of a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__79fd1126b940aa58648080ebef78a6ecac9291a3f4e257a9e9b8a3b62fb84e5a)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricLatencyForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricSessionDuration")
    def metric_session_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the duration of code interpreter sessions.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionDuration", [props]))

    @jsii.member(jsii_name="metricSystemErrorsForApiOperation")
    def metric_system_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of system errors for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b950226f77f1b8ff84aba977a1f05f62ed459462976db6648d94a67e1e1ef8cf)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSystemErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricThrottlesForApiOperation")
    def metric_throttles_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of throttled requests for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e4e3175daf088ea941aee60546645fc39148e3a11ab2b2e5d897a48eff09f4e0)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricThrottlesForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricUserErrorsForApiOperation")
    def metric_user_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user errors for a specific API operation performed on this code interpreter.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4e9e3e47628eaf2b6a4ffa31b2d7904f6d5438386a823eeca9d34b97f6f484df)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricUserErrorsForApiOperation", [operation, props]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, ICodeInterpreterCustom).__jsii_proxy_class__ = lambda : _ICodeInterpreterCustomProxy


@jsii.interface(jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.IRuntimeEndpoint")
class IRuntimeEndpoint(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    '''(experimental) Interface for Runtime Endpoint resources.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the parent agent runtime.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeEndpointArn")
    def agent_runtime_endpoint_arn(self) -> builtins.str:
        '''(experimental) The ARN of the runtime endpoint resource.

        :stability: experimental
        :attribute: true

        Example::

            "arn:aws:bedrock-agentcore:us-west-2:123456789012:agent-runtime-endpoint/endpoint-abc123"
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="endpointName")
    def endpoint_name(self) -> builtins.str:
        '''(experimental) The name of the runtime endpoint.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When the endpoint was created.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the runtime endpoint.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="liveVersion")
    def live_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The live version of the agent runtime that is currently serving requests.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the runtime endpoint.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="targetVersion")
    def target_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The target version the endpoint is transitioning to (during updates).

        :stability: experimental
        :attribute: true
        '''
        ...


class _IRuntimeEndpointProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    '''(experimental) Interface for Runtime Endpoint resources.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-bedrock-agentcore-alpha.IRuntimeEndpoint"

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the parent agent runtime.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeArn"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeEndpointArn")
    def agent_runtime_endpoint_arn(self) -> builtins.str:
        '''(experimental) The ARN of the runtime endpoint resource.

        :stability: experimental
        :attribute: true

        Example::

            "arn:aws:bedrock-agentcore:us-west-2:123456789012:agent-runtime-endpoint/endpoint-abc123"
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeEndpointArn"))

    @builtins.property
    @jsii.member(jsii_name="endpointName")
    def endpoint_name(self) -> builtins.str:
        '''(experimental) The name of the runtime endpoint.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "endpointName"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When the endpoint was created.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the runtime endpoint.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "description"))

    @builtins.property
    @jsii.member(jsii_name="liveVersion")
    def live_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The live version of the agent runtime that is currently serving requests.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "liveVersion"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the runtime endpoint.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="targetVersion")
    def target_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The target version the endpoint is transitioning to (during updates).

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "targetVersion"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IRuntimeEndpoint).__jsii_proxy_class__ = lambda : _IRuntimeEndpointProxy


class NetworkConfiguration(
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.NetworkConfiguration",
):
    '''(experimental) Abstract base class for network configuration.

    :stability: experimental
    '''

    def __init__(
        self,
        mode: builtins.str,
        scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) Creates a new network configuration.

        :param mode: - the network mode to use for the tool.
        :param scope: -
        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b1156fe37fe7149a4f863e83246fb36b82ce35366fd78287a7abd74852fa9ecd)
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        vpc_config = VpcConfigProps(
            vpc=vpc,
            allow_all_outbound=allow_all_outbound,
            security_groups=security_groups,
            vpc_subnets=vpc_subnets,
        )

        jsii.create(self.__class__, self, [mode, scope, vpc_config])

    @builtins.property
    @jsii.member(jsii_name="networkMode")
    def network_mode(self) -> builtins.str:
        '''(experimental) The network mode to use.

        Configure the security level for agent
        execution to control access, isolate resources, and protect sensitive data.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "networkMode"))

    @builtins.property
    @jsii.member(jsii_name="connections")
    def connections(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.Connections]:
        '''(experimental) The connections object to the network.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.Connections], jsii.get(self, "connections"))

    @builtins.property
    @jsii.member(jsii_name="scope")
    def scope(self) -> typing.Optional[_constructs_77d1e7e8.Construct]:
        '''(experimental) The scope to create the resource in.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_constructs_77d1e7e8.Construct], jsii.get(self, "scope"))

    @builtins.property
    @jsii.member(jsii_name="vpcSubnets")
    def vpc_subnets(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection]:
        '''(experimental) The VPC subnets to use.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection], jsii.get(self, "vpcSubnets"))


class _NetworkConfigurationProxy(NetworkConfiguration):
    pass

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, NetworkConfiguration).__jsii_proxy_class__ = lambda : _NetworkConfigurationProxy


@jsii.enum(jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.ProtocolType")
class ProtocolType(enum.Enum):
    '''(experimental) Protocol configuration for Agent Runtime.

    :stability: experimental
    '''

    MCP = "MCP"
    '''(experimental) Model Context Protocol.

    :stability: experimental
    '''
    HTTP = "HTTP"
    '''(experimental) HTTP protocol.

    :stability: experimental
    '''


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RecordingConfig",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled", "s3_location": "s3Location"},
)
class RecordingConfig:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        s3_location: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.Location, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) Recording configuration for browser.

        :param enabled: (experimental) Whether recording is enabled. Default: - false
        :param s3_location: (experimental) S3 Location Configuration. Default: - undefined

        :stability: experimental
        :exampleMetadata: fixture=default infused

        Example::

            # Create an S3 bucket for recordings
            recording_bucket = s3.Bucket(self, "RecordingBucket",
                bucket_name="my-browser-recordings",
                removal_policy=RemovalPolicy.DESTROY
            )
            
            # Create browser with recording enabled
            browser = agentcore.BrowserCustom(self, "MyBrowser",
                browser_custom_name="my_browser",
                description="Browser with recording enabled",
                network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network(),
                recording_config=agentcore.RecordingConfig(
                    enabled=True,
                    s3_location=s3.Location(
                        bucket_name=recording_bucket.bucket_name,
                        object_key="browser-recordings/"
                    )
                )
            )
        '''
        if isinstance(s3_location, dict):
            s3_location = _aws_cdk_aws_s3_ceddda9d.Location(**s3_location)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__847016f3fc41e4cdc9b08f4aeed6b6521f23c2c1ef8b55de56db5d14f7dbdc82)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument s3_location", value=s3_location, expected_type=type_hints["s3_location"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if s3_location is not None:
            self._values["s3_location"] = s3_location

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Whether recording is enabled.

        :default: - false

        :stability: experimental
        '''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def s3_location(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Location]:
        '''(experimental) S3 Location Configuration.

        :default: - undefined

        :stability: experimental
        '''
        result = self._values.get("s3_location")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Location], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RecordingConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class RuntimeAuthorizerConfiguration(
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeAuthorizerConfiguration",
):
    '''(experimental) Abstract base class for runtime authorizer configurations.

    Provides static factory methods to create different authentication types.

    :stability: experimental
    :exampleMetadata: infused

    Example::

        repository = ecr.Repository(self, "TestRepository",
            repository_name="test-agent-runtime"
        )
        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
        
        runtime = agentcore.Runtime(self, "MyAgentRuntime",
            runtime_name="myAgent",
            agent_runtime_artifact=agent_runtime_artifact,
            authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_cognito("us-west-2_ABC123", "client123", "us-west-2")
        )
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="usingCognito")
    @builtins.classmethod
    def using_cognito(
        cls,
        user_pool_id: builtins.str,
        client_id: builtins.str,
        region: typing.Optional[builtins.str] = None,
        allowed_audience: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> "RuntimeAuthorizerConfiguration":
        '''(experimental) Use AWS Cognito User Pool authentication.

        Validates Cognito-issued JWT tokens.

        :param user_pool_id: The Cognito User Pool ID (e.g., 'us-west-2_ABC123').
        :param client_id: The Cognito App Client ID.
        :param region: Optional AWS region where the User Pool is located (defaults to stack region).
        :param allowed_audience: Optional array of allowed audiences.

        :return: RuntimeAuthorizerConfiguration for Cognito authentication

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b924023484b6dec8c84698f52f4e325bbda80efa65704ec656d07d774f0f360a)
            check_type(argname="argument user_pool_id", value=user_pool_id, expected_type=type_hints["user_pool_id"])
            check_type(argname="argument client_id", value=client_id, expected_type=type_hints["client_id"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument allowed_audience", value=allowed_audience, expected_type=type_hints["allowed_audience"])
        return typing.cast("RuntimeAuthorizerConfiguration", jsii.sinvoke(cls, "usingCognito", [user_pool_id, client_id, region, allowed_audience]))

    @jsii.member(jsii_name="usingIAM")
    @builtins.classmethod
    def using_iam(cls) -> "RuntimeAuthorizerConfiguration":
        '''(experimental) Use IAM authentication (default).

        Requires AWS credentials to sign requests using SigV4.

        :return: RuntimeAuthorizerConfiguration for IAM authentication

        :stability: experimental
        '''
        return typing.cast("RuntimeAuthorizerConfiguration", jsii.sinvoke(cls, "usingIAM", []))

    @jsii.member(jsii_name="usingJWT")
    @builtins.classmethod
    def using_jwt(
        cls,
        discovery_url: builtins.str,
        allowed_clients: typing.Optional[typing.Sequence[builtins.str]] = None,
        allowed_audience: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> "RuntimeAuthorizerConfiguration":
        '''(experimental) Use custom JWT authentication.

        Validates JWT tokens against the specified OIDC provider.

        :param discovery_url: The OIDC discovery URL (must end with /.well-known/openid-configuration).
        :param allowed_clients: Optional array of allowed client IDs.
        :param allowed_audience: Optional array of allowed audiences.

        :return: RuntimeAuthorizerConfiguration for JWT authentication

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9ac01ece0cc4140cb0b2a31ed95c6b9e03284a2363131d8f59958f4506fdec5f)
            check_type(argname="argument discovery_url", value=discovery_url, expected_type=type_hints["discovery_url"])
            check_type(argname="argument allowed_clients", value=allowed_clients, expected_type=type_hints["allowed_clients"])
            check_type(argname="argument allowed_audience", value=allowed_audience, expected_type=type_hints["allowed_audience"])
        return typing.cast("RuntimeAuthorizerConfiguration", jsii.sinvoke(cls, "usingJWT", [discovery_url, allowed_clients, allowed_audience]))

    @jsii.member(jsii_name="usingOAuth")
    @builtins.classmethod
    def using_o_auth(
        cls,
        discovery_url: builtins.str,
        client_id: builtins.str,
        allowed_audience: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> "RuntimeAuthorizerConfiguration":
        '''(experimental) Use OAuth 2.0 authentication. Supports various OAuth providers.

        :param discovery_url: The OIDC discovery URL (must end with /.well-known/openid-configuration).
        :param client_id: OAuth client ID.
        :param allowed_audience: Optional array of allowed audiences.

        :return: RuntimeAuthorizerConfiguration for OAuth authentication

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0b8de9eb8f6b27c5ad0708ddadcf0e5e78987856a5b94b421cb1abbcc761229)
            check_type(argname="argument discovery_url", value=discovery_url, expected_type=type_hints["discovery_url"])
            check_type(argname="argument client_id", value=client_id, expected_type=type_hints["client_id"])
            check_type(argname="argument allowed_audience", value=allowed_audience, expected_type=type_hints["allowed_audience"])
        return typing.cast("RuntimeAuthorizerConfiguration", jsii.sinvoke(cls, "usingOAuth", [discovery_url, client_id, allowed_audience]))


class _RuntimeAuthorizerConfigurationProxy(RuntimeAuthorizerConfiguration):
    pass

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, RuntimeAuthorizerConfiguration).__jsii_proxy_class__ = lambda : _RuntimeAuthorizerConfigurationProxy


@jsii.implements(IBedrockAgentRuntime)
class RuntimeBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeBase",
):
    '''(experimental) Base class for Agent Runtime.

    :stability: experimental
    '''

    def __init__(self, scope: _constructs_77d1e7e8.Construct, id: builtins.str) -> None:
        '''
        :param scope: -
        :param id: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__16350f8e803148ae58824c157d92d6b5b360c3802a4018cc1e88f99466e7fa95)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        jsii.create(self.__class__, self, [scope, id])

    @jsii.member(jsii_name="addToRolePolicy")
    def add_to_role_policy(
        self,
        statement: _aws_cdk_aws_iam_ceddda9d.PolicyStatement,
    ) -> IBedrockAgentRuntime:
        '''(experimental) Adds a policy statement to the runtime's execution role.

        :param statement: The IAM policy statement to add.

        :return: The runtime instance for chaining

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7231f6dcdd2551159f4e644a7b39271f091fade67469f9bf285044a8c4c90b60)
            check_type(argname="argument statement", value=statement, expected_type=type_hints["statement"])
        return typing.cast(IBedrockAgentRuntime, jsii.invoke(self, "addToRolePolicy", [statement]))

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        actions: typing.Sequence[builtins.str],
        resources: typing.Sequence[builtins.str],
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant the runtime specific actions on AWS resources.

        :param actions: The actions to grant.
        :param resources: The resource ARNs to grant access to.

        :return: The Grant object for chaining

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__87eb6e84d44b507957213f90c634b593ff68893ef29137a6154e73fa53e18e18)
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
            check_type(argname="argument resources", value=resources, expected_type=type_hints["resources"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [actions, resources]))

    @jsii.member(jsii_name="grantInvoke")
    def grant_invoke(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime both directly and on behalf of users Grants both bedrock-agentcore:InvokeAgentRuntime and bedrock-agentcore:InvokeAgentRuntimeForUser permissions.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f464dbb8ec8dc44c2f152bffa0fe6b7e25a72226db47d4575639ab76a3ee504b)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantInvoke", [grantee]))

    @jsii.member(jsii_name="grantInvokeRuntime")
    def grant_invoke_runtime(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime Grants the bedrock-agentcore:InvokeAgentRuntime permission.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__23262a416c2bde8ca6024d06971509afa97486440111e79dfae8c143d05ed9be)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantInvokeRuntime", [grantee]))

    @jsii.member(jsii_name="grantInvokeRuntimeForUser")
    def grant_invoke_runtime_for_user(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Permits an IAM principal to invoke this runtime on behalf of a user Grants the bedrock-agentcore:InvokeAgentRuntimeForUser permission Required when using the X-Amzn-Bedrock-AgentCore-Runtime-User-Id header.

        :param grantee: The principal to grant access to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__894ad60671ea950414fd0416fead36cee5e0bc1348fcb31b422ba8e37ea00c08)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantInvokeRuntimeForUser", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this agent runtime.

        By default, the metric will be calculated as a sum over a period of 5 minutes.
        You can customize this by using the ``statistic`` and ``period`` properties.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f6a2aba3c163e6d2d8cfa3127ef4170f55abf85a15cea83297552f1fe625776d)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, dimensions, props]))

    @jsii.member(jsii_name="metricInvocations")
    def metric_invocations(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of invocations for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocations", [props]))

    @jsii.member(jsii_name="metricInvocationsAggregated")
    def metric_invocations_aggregated(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of invocations across all resources.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocationsAggregated", [props]))

    @jsii.member(jsii_name="metricLatency")
    def metric_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric measuring the latency of requests for this agent runtime.

        The latency metric represents the total time elapsed between receiving the request
        and sending the final response token, representing complete end-to-end processing time.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricLatency", [props]))

    @jsii.member(jsii_name="metricSessionCount")
    def metric_session_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of agent sessions for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionCount", [props]))

    @jsii.member(jsii_name="metricSessionsAggregated")
    def metric_sessions_aggregated(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of sessions across all resources.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionsAggregated", [props]))

    @jsii.member(jsii_name="metricSystemErrors")
    def metric_system_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of system errors for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSystemErrors", [props]))

    @jsii.member(jsii_name="metricThrottles")
    def metric_throttles(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of throttled requests for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricThrottles", [props]))

    @jsii.member(jsii_name="metricTotalErrors")
    def metric_total_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the total number of errors (system + user) for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTotalErrors", [props]))

    @jsii.member(jsii_name="metricUserErrors")
    def metric_user_errors(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return a metric containing the number of user errors for this agent runtime.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricUserErrors", [props]))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    @abc.abstractmethod
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime resource - Format ``arn:${Partition}:bedrock-agentcore:${Region}:${Account}:runtime/${RuntimeId}``.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeId")
    @abc.abstractmethod
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The ID of the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeName")
    @abc.abstractmethod
    def agent_runtime_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="connections")
    def connections(self) -> _aws_cdk_aws_ec2_ceddda9d.Connections:
        '''(experimental) An accessor for the Connections object that will fail if this Runtime does not have a VPC configured.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.Connections, jsii.get(self, "connections"))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    @abc.abstractmethod
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="role")
    @abc.abstractmethod
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeVersion")
    @abc.abstractmethod
    def agent_runtime_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentStatus")
    @abc.abstractmethod
    def agent_status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    @abc.abstractmethod
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was created.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    @abc.abstractmethod
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was last updated.

        :stability: experimental
        '''
        ...


class _RuntimeBaseProxy(
    RuntimeBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime resource - Format ``arn:${Partition}:bedrock-agentcore:${Region}:${Account}:runtime/${RuntimeId}``.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeArn"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeId")
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The ID of the agent runtime.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeId"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeName")
    def agent_runtime_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeName"))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the agent runtime.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "role"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeVersion")
    def agent_runtime_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of the agent runtime.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "agentRuntimeVersion"))

    @builtins.property
    @jsii.member(jsii_name="agentStatus")
    def agent_status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the agent runtime.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "agentStatus"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was created.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The time at which the runtime was last updated.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, RuntimeBase).__jsii_proxy_class__ = lambda : _RuntimeBaseProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeEndpointAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "agent_runtime_arn": "agentRuntimeArn",
        "agent_runtime_endpoint_arn": "agentRuntimeEndpointArn",
        "endpoint_name": "endpointName",
        "created_at": "createdAt",
        "description": "description",
        "endpoint_id": "endpointId",
        "last_updated_at": "lastUpdatedAt",
        "live_version": "liveVersion",
        "status": "status",
        "target_version": "targetVersion",
    },
)
class RuntimeEndpointAttributes:
    def __init__(
        self,
        *,
        agent_runtime_arn: builtins.str,
        agent_runtime_endpoint_arn: builtins.str,
        endpoint_name: builtins.str,
        created_at: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        endpoint_id: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        live_version: typing.Optional[builtins.str] = None,
        status: typing.Optional[builtins.str] = None,
        target_version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Attributes for importing an existing Runtime Endpoint.

        :param agent_runtime_arn: (experimental) The ARN of the parent agent runtime.
        :param agent_runtime_endpoint_arn: (experimental) The ARN of the runtime endpoint.
        :param endpoint_name: (experimental) The name of the runtime endpoint.
        :param created_at: (experimental) When the endpoint was created. Default: - Creation time not available
        :param description: (experimental) The description of the runtime endpoint. Default: - No description
        :param endpoint_id: (experimental) The unique identifier of the runtime endpoint. Default: - Endpoint ID not available
        :param last_updated_at: (experimental) When the endpoint was last updated. Default: - Last update time not available
        :param live_version: (experimental) The live version of the agent runtime that is currently serving requests. Default: - Live version not available
        :param status: (experimental) The current status of the runtime endpoint. Default: - Status not available
        :param target_version: (experimental) The target version the endpoint is transitioning to (during updates). Default: - Target version not available

        :stability: experimental
        :exampleMetadata: fixture=_generated

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_bedrock_agentcore_alpha as bedrock_agentcore_alpha
            
            runtime_endpoint_attributes = bedrock_agentcore_alpha.RuntimeEndpointAttributes(
                agent_runtime_arn="agentRuntimeArn",
                agent_runtime_endpoint_arn="agentRuntimeEndpointArn",
                endpoint_name="endpointName",
            
                # the properties below are optional
                created_at="createdAt",
                description="description",
                endpoint_id="endpointId",
                last_updated_at="lastUpdatedAt",
                live_version="liveVersion",
                status="status",
                target_version="targetVersion"
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d8f995850b550d0ef0b0c5967813f910df0c54b53b6273e50eef58f9c9a599ff)
            check_type(argname="argument agent_runtime_arn", value=agent_runtime_arn, expected_type=type_hints["agent_runtime_arn"])
            check_type(argname="argument agent_runtime_endpoint_arn", value=agent_runtime_endpoint_arn, expected_type=type_hints["agent_runtime_endpoint_arn"])
            check_type(argname="argument endpoint_name", value=endpoint_name, expected_type=type_hints["endpoint_name"])
            check_type(argname="argument created_at", value=created_at, expected_type=type_hints["created_at"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument endpoint_id", value=endpoint_id, expected_type=type_hints["endpoint_id"])
            check_type(argname="argument last_updated_at", value=last_updated_at, expected_type=type_hints["last_updated_at"])
            check_type(argname="argument live_version", value=live_version, expected_type=type_hints["live_version"])
            check_type(argname="argument status", value=status, expected_type=type_hints["status"])
            check_type(argname="argument target_version", value=target_version, expected_type=type_hints["target_version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "agent_runtime_arn": agent_runtime_arn,
            "agent_runtime_endpoint_arn": agent_runtime_endpoint_arn,
            "endpoint_name": endpoint_name,
        }
        if created_at is not None:
            self._values["created_at"] = created_at
        if description is not None:
            self._values["description"] = description
        if endpoint_id is not None:
            self._values["endpoint_id"] = endpoint_id
        if last_updated_at is not None:
            self._values["last_updated_at"] = last_updated_at
        if live_version is not None:
            self._values["live_version"] = live_version
        if status is not None:
            self._values["status"] = status
        if target_version is not None:
            self._values["target_version"] = target_version

    @builtins.property
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the parent agent runtime.

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_arn")
        assert result is not None, "Required property 'agent_runtime_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def agent_runtime_endpoint_arn(self) -> builtins.str:
        '''(experimental) The ARN of the runtime endpoint.

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_endpoint_arn")
        assert result is not None, "Required property 'agent_runtime_endpoint_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def endpoint_name(self) -> builtins.str:
        '''(experimental) The name of the runtime endpoint.

        :stability: experimental
        '''
        result = self._values.get("endpoint_name")
        assert result is not None, "Required property 'endpoint_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When the endpoint was created.

        :default: - Creation time not available

        :stability: experimental
        '''
        result = self._values.get("created_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the runtime endpoint.

        :default: - No description

        :stability: experimental
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def endpoint_id(self) -> typing.Optional[builtins.str]:
        '''(experimental) The unique identifier of the runtime endpoint.

        :default: - Endpoint ID not available

        :stability: experimental
        '''
        result = self._values.get("endpoint_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When the endpoint was last updated.

        :default: - Last update time not available

        :stability: experimental
        '''
        result = self._values.get("last_updated_at")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def live_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The live version of the agent runtime that is currently serving requests.

        :default: - Live version not available

        :stability: experimental
        '''
        result = self._values.get("live_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the runtime endpoint.

        :default: - Status not available

        :stability: experimental
        '''
        result = self._values.get("status")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The target version the endpoint is transitioning to (during updates).

        :default: - Target version not available

        :stability: experimental
        '''
        result = self._values.get("target_version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RuntimeEndpointAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IRuntimeEndpoint)
class RuntimeEndpointBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeEndpointBase",
):
    '''(experimental) Base class for Runtime Endpoint.

    :stability: experimental
    '''

    def __init__(self, scope: _constructs_77d1e7e8.Construct, id: builtins.str) -> None:
        '''
        :param scope: -
        :param id: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__07caa672d91c2d444bbd6350d0c5232e8b425f0f99ff16fa910ac554ef216410)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        jsii.create(self.__class__, self, [scope, id])

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    @abc.abstractmethod
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the parent agent runtime.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeEndpointArn")
    @abc.abstractmethod
    def agent_runtime_endpoint_arn(self) -> builtins.str:
        '''(experimental) The ARN of the runtime endpoint resource.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="endpointName")
    @abc.abstractmethod
    def endpoint_name(self) -> builtins.str:
        '''(experimental) The name of the runtime endpoint.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    @abc.abstractmethod
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When the endpoint was created.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="description")
    @abc.abstractmethod
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the runtime endpoint.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="liveVersion")
    @abc.abstractmethod
    def live_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The live version of the agent runtime that is currently serving requests.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    @abc.abstractmethod
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the runtime endpoint.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="targetVersion")
    @abc.abstractmethod
    def target_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The target version the endpoint is transitioning to (during updates).

        :stability: experimental
        '''
        ...


class _RuntimeEndpointBaseProxy(
    RuntimeEndpointBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the parent agent runtime.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeArn"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeEndpointArn")
    def agent_runtime_endpoint_arn(self) -> builtins.str:
        '''(experimental) The ARN of the runtime endpoint resource.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeEndpointArn"))

    @builtins.property
    @jsii.member(jsii_name="endpointName")
    def endpoint_name(self) -> builtins.str:
        '''(experimental) The name of the runtime endpoint.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "endpointName"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When the endpoint was created.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the runtime endpoint.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "description"))

    @builtins.property
    @jsii.member(jsii_name="liveVersion")
    def live_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The live version of the agent runtime that is currently serving requests.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "liveVersion"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The current status of the runtime endpoint.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="targetVersion")
    def target_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The target version the endpoint is transitioning to (during updates).

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "targetVersion"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, RuntimeEndpointBase).__jsii_proxy_class__ = lambda : _RuntimeEndpointBaseProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeEndpointProps",
    jsii_struct_bases=[],
    name_mapping={
        "agent_runtime_id": "agentRuntimeId",
        "endpoint_name": "endpointName",
        "agent_runtime_version": "agentRuntimeVersion",
        "description": "description",
        "tags": "tags",
    },
)
class RuntimeEndpointProps:
    def __init__(
        self,
        *,
        agent_runtime_id: builtins.str,
        endpoint_name: builtins.str,
        agent_runtime_version: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''(experimental) Properties for creating a Bedrock Agent Core Runtime Endpoint resource.

        :param agent_runtime_id: (experimental) The ID of the agent runtime to associate with this endpoint This is the unique identifier of the runtime resource Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,99}-[a-zA-Z0-9]{10}$.
        :param endpoint_name: (experimental) The name of the agent runtime endpoint Valid characters are a-z, A-Z, 0-9, _ (underscore) Must start with a letter and can be up to 48 characters long Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$.
        :param agent_runtime_version: (experimental) The version of the agent runtime to use for this endpoint If not specified, the endpoint will point to version "1" of the runtime. Pattern: ^([1-9][0-9]{0,4})$ Default: "1"
        :param description: (experimental) Optional description for the agent runtime endpoint Length Minimum: 1 , Maximum: 256. Default: - No description
        :param tags: (experimental) Tags for the agent runtime endpoint A list of key:value pairs of tags to apply to this RuntimeEndpoint resource Pattern: ^[a-zA-Z0-9\\s._:/=+@-]*$. Default: {} - no tags

        :stability: experimental
        :exampleMetadata: infused

        Example::

            # Reference an existing runtime by its ID
            existing_runtime_id = "abc123-runtime-id" # The ID of an existing runtime
            
            # Create a standalone endpoint
            endpoint = agentcore.RuntimeEndpoint(self, "MyEndpoint",
                endpoint_name="production",
                agent_runtime_id=existing_runtime_id,
                agent_runtime_version="1",  # Specify which version to use
                description="Production endpoint for existing runtime"
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7edf14b5674c2c3647a66c54aa24ffa82abf23b571539cd8f02aa354e64da16a)
            check_type(argname="argument agent_runtime_id", value=agent_runtime_id, expected_type=type_hints["agent_runtime_id"])
            check_type(argname="argument endpoint_name", value=endpoint_name, expected_type=type_hints["endpoint_name"])
            check_type(argname="argument agent_runtime_version", value=agent_runtime_version, expected_type=type_hints["agent_runtime_version"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "agent_runtime_id": agent_runtime_id,
            "endpoint_name": endpoint_name,
        }
        if agent_runtime_version is not None:
            self._values["agent_runtime_version"] = agent_runtime_version
        if description is not None:
            self._values["description"] = description
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The ID of the agent runtime to associate with this endpoint This is the unique identifier of the runtime resource Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,99}-[a-zA-Z0-9]{10}$.

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_id")
        assert result is not None, "Required property 'agent_runtime_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def endpoint_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime endpoint Valid characters are a-z, A-Z, 0-9, _ (underscore) Must start with a letter and can be up to 48 characters long Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$.

        :stability: experimental
        '''
        result = self._values.get("endpoint_name")
        assert result is not None, "Required property 'endpoint_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def agent_runtime_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of the agent runtime to use for this endpoint If not specified, the endpoint will point to version "1" of the runtime.

        Pattern: ^([1-9][0-9]{0,4})$

        :default: "1"

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) Optional description for the agent runtime endpoint Length Minimum: 1 ,  Maximum: 256.

        :default: - No description

        :stability: experimental
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags for the agent runtime endpoint A list of key:value pairs of tags to apply to this RuntimeEndpoint resource Pattern: ^[a-zA-Z0-9\\s._:/=+@-]*$.

        :default: {} - no tags

        :stability: experimental
        '''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RuntimeEndpointProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class RuntimeNetworkConfiguration(
    NetworkConfiguration,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeNetworkConfiguration",
):
    '''(experimental) Network configuration for the Runtime.

    :stability: experimental
    :exampleMetadata: infused

    Example::

        repository = ecr.Repository(self, "TestRepository",
            repository_name="test-agent-runtime"
        )
        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
        
        # Create or use an existing VPC
        vpc = ec2.Vpc(self, "MyVpc",
            max_azs=2
        )
        
        # Configure runtime with VPC
        runtime = agentcore.Runtime(self, "MyAgentRuntime",
            runtime_name="myAgent",
            agent_runtime_artifact=agent_runtime_artifact,
            network_configuration=agentcore.RuntimeNetworkConfiguration.using_vpc(self,
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            )
        )
    '''

    def __init__(
        self,
        mode: builtins.str,
        scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) Creates a new network configuration.

        :param mode: - the network mode to use for the tool.
        :param scope: -
        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f3fca872b84d08855284949a94ef7ceab6679568661613e4224125dbf7add5d5)
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        vpc_config = VpcConfigProps(
            vpc=vpc,
            allow_all_outbound=allow_all_outbound,
            security_groups=security_groups,
            vpc_subnets=vpc_subnets,
        )

        jsii.create(self.__class__, self, [mode, scope, vpc_config])

    @jsii.member(jsii_name="usingPublicNetwork")
    @builtins.classmethod
    def using_public_network(cls) -> "RuntimeNetworkConfiguration":
        '''(experimental) Creates a public network configuration.

        PUBLIC is the default network mode.

        :return:

        A RuntimeNetworkConfiguration.
        Run the runtime in a public environment with internet access, suitable for less sensitive or open-use scenarios.

        :stability: experimental
        '''
        return typing.cast("RuntimeNetworkConfiguration", jsii.sinvoke(cls, "usingPublicNetwork", []))

    @jsii.member(jsii_name="usingVpc")
    @builtins.classmethod
    def using_vpc(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> "RuntimeNetworkConfiguration":
        '''(experimental) Creates a network configuration from a VPC configuration.

        :param scope: - The construct scope for creating resources.
        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :return: A RuntimeNetworkConfiguration.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5b65f23ce4df9170ab1ea5e330f24e42113b36afa69e504b887bda27e2e0919b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        vpc_config = VpcConfigProps(
            vpc=vpc,
            allow_all_outbound=allow_all_outbound,
            security_groups=security_groups,
            vpc_subnets=vpc_subnets,
        )

        return typing.cast("RuntimeNetworkConfiguration", jsii.sinvoke(cls, "usingVpc", [scope, vpc_config]))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeProps",
    jsii_struct_bases=[],
    name_mapping={
        "agent_runtime_artifact": "agentRuntimeArtifact",
        "runtime_name": "runtimeName",
        "authorizer_configuration": "authorizerConfiguration",
        "description": "description",
        "environment_variables": "environmentVariables",
        "execution_role": "executionRole",
        "network_configuration": "networkConfiguration",
        "protocol_configuration": "protocolConfiguration",
        "tags": "tags",
    },
)
class RuntimeProps:
    def __init__(
        self,
        *,
        agent_runtime_artifact: AgentRuntimeArtifact,
        runtime_name: builtins.str,
        authorizer_configuration: typing.Optional[RuntimeAuthorizerConfiguration] = None,
        description: typing.Optional[builtins.str] = None,
        environment_variables: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        network_configuration: typing.Optional[RuntimeNetworkConfiguration] = None,
        protocol_configuration: typing.Optional[ProtocolType] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''(experimental) Properties for creating a Bedrock Agent Core Runtime resource.

        :param agent_runtime_artifact: (experimental) The artifact configuration for the agent runtime Contains the container configuration with ECR URI.
        :param runtime_name: (experimental) The name of the agent runtime Valid characters are a-z, A-Z, 0-9, _ (underscore) Must start with a letter and can be up to 48 characters long Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$.
        :param authorizer_configuration: (experimental) Authorizer configuration for the agent runtime Use RuntimeAuthorizerConfiguration static methods to create the configuration. Default: - RuntimeAuthorizerConfiguration.iam() (IAM authentication)
        :param description: (experimental) Optional description for the agent runtime. Default: - No description Length Minimum: 1 , Maximum: 1200
        :param environment_variables: (experimental) Environment variables for the agent runtime - Maximum 50 environment variables - Key: Must be 1-100 characters, start with letter or underscore, contain only letters, numbers, and underscores - Value: Must be 0-2048 characters (per CloudFormation specification). Default: - No environment variables
        :param execution_role: (experimental) The IAM role that provides permissions for the agent runtime If not provided, a role will be created automatically. Default: - A new role will be created
        :param network_configuration: (experimental) Network configuration for the agent runtime. Default: - RuntimeNetworkConfiguration.usingPublicNetwork()
        :param protocol_configuration: (experimental) Protocol configuration for the agent runtime. Default: - ProtocolType.HTTP
        :param tags: (experimental) Tags for the agent runtime A list of key:value pairs of tags to apply to this Runtime resource. Default: {} - no tags

        :stability: experimental
        :exampleMetadata: infused

        Example::

            repository = ecr.Repository(self, "TestRepository",
                repository_name="test-agent-runtime"
            )
            agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
            
            runtime = agentcore.Runtime(self, "MyAgentRuntime",
                runtime_name="myAgent",
                agent_runtime_artifact=agent_runtime_artifact,
                authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_oAuth("https://github.com/.well-known/openid-configuration", "oauth_client_123")
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e60d912f60dcec4a97a088e67e9b6da136fd8fbd51038c0380995a1946e1724f)
            check_type(argname="argument agent_runtime_artifact", value=agent_runtime_artifact, expected_type=type_hints["agent_runtime_artifact"])
            check_type(argname="argument runtime_name", value=runtime_name, expected_type=type_hints["runtime_name"])
            check_type(argname="argument authorizer_configuration", value=authorizer_configuration, expected_type=type_hints["authorizer_configuration"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument environment_variables", value=environment_variables, expected_type=type_hints["environment_variables"])
            check_type(argname="argument execution_role", value=execution_role, expected_type=type_hints["execution_role"])
            check_type(argname="argument network_configuration", value=network_configuration, expected_type=type_hints["network_configuration"])
            check_type(argname="argument protocol_configuration", value=protocol_configuration, expected_type=type_hints["protocol_configuration"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "agent_runtime_artifact": agent_runtime_artifact,
            "runtime_name": runtime_name,
        }
        if authorizer_configuration is not None:
            self._values["authorizer_configuration"] = authorizer_configuration
        if description is not None:
            self._values["description"] = description
        if environment_variables is not None:
            self._values["environment_variables"] = environment_variables
        if execution_role is not None:
            self._values["execution_role"] = execution_role
        if network_configuration is not None:
            self._values["network_configuration"] = network_configuration
        if protocol_configuration is not None:
            self._values["protocol_configuration"] = protocol_configuration
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def agent_runtime_artifact(self) -> AgentRuntimeArtifact:
        '''(experimental) The artifact configuration for the agent runtime Contains the container configuration with ECR URI.

        :stability: experimental
        '''
        result = self._values.get("agent_runtime_artifact")
        assert result is not None, "Required property 'agent_runtime_artifact' is missing"
        return typing.cast(AgentRuntimeArtifact, result)

    @builtins.property
    def runtime_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime Valid characters are a-z, A-Z, 0-9, _ (underscore) Must start with a letter and can be up to 48 characters long Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$.

        :stability: experimental
        '''
        result = self._values.get("runtime_name")
        assert result is not None, "Required property 'runtime_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def authorizer_configuration(
        self,
    ) -> typing.Optional[RuntimeAuthorizerConfiguration]:
        '''(experimental) Authorizer configuration for the agent runtime Use RuntimeAuthorizerConfiguration static methods to create the configuration.

        :default: - RuntimeAuthorizerConfiguration.iam() (IAM authentication)

        :stability: experimental
        '''
        result = self._values.get("authorizer_configuration")
        return typing.cast(typing.Optional[RuntimeAuthorizerConfiguration], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) Optional description for the agent runtime.

        :default:

        - No description
        Length Minimum: 1 , Maximum: 1200

        :stability: experimental
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def environment_variables(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Environment variables for the agent runtime - Maximum 50 environment variables - Key: Must be 1-100 characters, start with letter or underscore, contain only letters, numbers, and underscores - Value: Must be 0-2048 characters (per CloudFormation specification).

        :default: - No environment variables

        :stability: experimental
        '''
        result = self._values.get("environment_variables")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def execution_role(self) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole]:
        '''(experimental) The IAM role that provides permissions for the agent runtime If not provided, a role will be created automatically.

        :default: - A new role will be created

        :stability: experimental
        '''
        result = self._values.get("execution_role")
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole], result)

    @builtins.property
    def network_configuration(self) -> typing.Optional[RuntimeNetworkConfiguration]:
        '''(experimental) Network configuration for the agent runtime.

        :default: - RuntimeNetworkConfiguration.usingPublicNetwork()

        :stability: experimental
        '''
        result = self._values.get("network_configuration")
        return typing.cast(typing.Optional[RuntimeNetworkConfiguration], result)

    @builtins.property
    def protocol_configuration(self) -> typing.Optional[ProtocolType]:
        '''(experimental) Protocol configuration for the agent runtime.

        :default: - ProtocolType.HTTP

        :stability: experimental
        '''
        result = self._values.get("protocol_configuration")
        return typing.cast(typing.Optional[ProtocolType], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags for the agent runtime A list of key:value pairs of tags to apply to this Runtime resource.

        :default: {} - no tags

        :stability: experimental
        '''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RuntimeProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.VpcConfigProps",
    jsii_struct_bases=[],
    name_mapping={
        "vpc": "vpc",
        "allow_all_outbound": "allowAllOutbound",
        "security_groups": "securityGroups",
        "vpc_subnets": "vpcSubnets",
    },
)
class VpcConfigProps:
    def __init__(
        self,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) VPC configuration properties.

        Only used when network mode is VPC.

        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :stability: experimental
        :exampleMetadata: fixture=default infused

        Example::

            vpc = ec2.Vpc(self, "testVPC")
            
            code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
                code_interpreter_custom_name="my_sandbox_interpreter",
                description="Code interpreter with isolated network access",
                network_configuration=agentcore.BrowserNetworkConfiguration.using_vpc(self,
                    vpc=vpc
                )
            )
            
            code_interpreter.connections.add_security_group(ec2.SecurityGroup(self, "AdditionalGroup", vpc=vpc))
        '''
        if isinstance(vpc_subnets, dict):
            vpc_subnets = _aws_cdk_aws_ec2_ceddda9d.SubnetSelection(**vpc_subnets)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2116ad0a264d69770800f27d273a661a955fcb5c6c066f36456e9178f63d742d)
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
            check_type(argname="argument allow_all_outbound", value=allow_all_outbound, expected_type=type_hints["allow_all_outbound"])
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
            check_type(argname="argument vpc_subnets", value=vpc_subnets, expected_type=type_hints["vpc_subnets"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "vpc": vpc,
        }
        if allow_all_outbound is not None:
            self._values["allow_all_outbound"] = allow_all_outbound
        if security_groups is not None:
            self._values["security_groups"] = security_groups
        if vpc_subnets is not None:
            self._values["vpc_subnets"] = vpc_subnets

    @builtins.property
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC to deploy the resource to.

        :stability: experimental
        '''
        result = self._values.get("vpc")
        assert result is not None, "Required property 'vpc' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, result)

    @builtins.property
    def allow_all_outbound(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Whether to allow the resource to send all network traffic (except ipv6).

        If set to false, you must individually add traffic rules to allow the
        resource to connect to network targets.

        Do not specify this property if the ``securityGroups`` property is set.
        Instead, configure ``allowAllOutbound`` directly on the security group.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("allow_all_outbound")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The list of security groups to associate with the resource's network interfaces.

        Only used if 'vpc' is supplied.

        :default:

        - If the resource is placed within a VPC and a security group is
        not specified by this prop, a dedicated security
        group will be created for this resource.

        :stability: experimental
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], result)

    @builtins.property
    def vpc_subnets(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection]:
        '''(experimental) Where to place the network interfaces within the VPC.

        This requires ``vpc`` to be specified in order for interfaces to actually be
        placed in the subnets. If ``vpc`` is not specify, this will raise an error.

        :default: - the Vpc default strategy if not specified

        :stability: experimental
        '''
        result = self._values.get("vpc_subnets")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VpcConfigProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IBrowserCustom)
class BrowserCustomBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.BrowserCustomBase",
):
    '''(experimental) Abstract base class for a Browser.

    Contains methods and attributes valid for Browsers either created with CDK or imported.

    :stability: experimental
    '''

    def __init__(self, scope: _constructs_77d1e7e8.Construct, id: builtins.str) -> None:
        '''
        :param scope: -
        :param id: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c77d9cceeabf2dd05d534145778ab3e1e597cf25fdabc7bdbdbc642c412f2435)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        jsii.create(self.__class__, self, [scope, id])

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: - The IAM principal to grant permissions to.
        :param actions: - The actions to grant.

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d6facf14dce62b7f6f12e4abaf4eb022dff3a45f4068e5f45350aab6e10355a0)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantRead")
    def grant_read(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant read permissions on this browser to an IAM principal.

        This includes both read permissions on the specific browser and list permissions on all browsers.

        :param grantee: - The IAM principal to grant read permissions to.

        :default:

        - Default grant configuration:
        - actions: ['bedrock-agentcore:GetBrowser', 'bedrock-agentcore:GetBrowserSession'] on this.browserArn
        - actions: ['bedrock-agentcore:ListBrowsers', 'bedrock-agentcore:ListBrowserSessions'] on all resources (*)

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2d32eecca999e221fe7baaea3ba395ddee5578ec83675efa9efdbea664213da2)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantRead", [grantee]))

    @jsii.member(jsii_name="grantUse")
    def grant_use(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant invoke permissions on this browser to an IAM principal.

        :param grantee: - The IAM principal to grant invoke permissions to.

        :default:

        - Default grant configuration:
        - actions: ['bedrock-agentcore:StartBrowserSession', 'bedrock-agentcore:UpdateBrowserStream', 'bedrock-agentcore:StopBrowserSession']
        - resourceArns: [this.browserArn]

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9186b5df0e333eb3469e897ab73dc50dee27c22f707afd8f3645295ca9d00d55)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantUse", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this browser.

        By default, the metric will be calculated as a sum over a period of 5 minutes.
        You can customize this by using the ``statistic`` and ``period`` properties.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f8d3ed248b0e1fbb8321d56521a7d7da90f0d2609d7149da6e1d786cbb7e8af8)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, dimensions, props]))

    @jsii.member(jsii_name="metricErrorsForApiOperation")
    def metric_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser errors.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Errors

        :return: A CloudWatch Metric configured for browser errors

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__78f3dfb28f4dc0851b8a333b577550c3ed04b83619039f5923124cdcbed267cd)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricForApiOperation")
    def metric_for_api_operation(
        self,
        metric_name: builtins.str,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser api operations..

        :param metric_name: -
        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: metricName
        - dimensionsMap: { BrowserId: this.browserId }

        :return: A CloudWatch Metric configured for browser api operations

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__44ddd5de65d8344be82e751ad250cc43e9faa11ea964e6b229c0a4d1ec72d5f7)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricForApiOperation", [metric_name, operation, props]))

    @jsii.member(jsii_name="metricInvocationsForApiOperation")
    def metric_invocations_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser invocations.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Invocations

        :return: A CloudWatch Metric configured for browser latencies

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad4dce28a348ae0a4ea1f8be12576c56d15cb4cfabe63fa3ad38edc91bd2674d)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocationsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricLatencyForApiOperation")
    def metric_latency_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser latencies.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Latency

        :return: A CloudWatch Metric configured for browser latencies

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__def70821036fc28a14280760ae0b74a0fece9251b8de279a7787b620952b96f2)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricLatencyForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricSessionDuration")
    def metric_session_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser session duration.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Duration

        :return: A CloudWatch Metric configured for browser session duration

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionDuration", [props]))

    @jsii.member(jsii_name="metricSystemErrorsForApiOperation")
    def metric_system_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser system errors.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: SystemErrors

        :return: A CloudWatch Metric configured for browser system errors

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__35a69ebb2bb4842640813061b2ac17af0959c464410a959b014b4c88834032a5)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSystemErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricTakeOverCount")
    def metric_take_over_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser user takeovers.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: TakeOverCount

        :return: A CloudWatch Metric configured for browser user takeovers

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTakeOverCount", [props]))

    @jsii.member(jsii_name="metricTakeOverDuration")
    def metric_take_over_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser user takeovers duration.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: TakeOverDuration

        :return: A CloudWatch Metric configured for browser user takeovers duration

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTakeOverDuration", [props]))

    @jsii.member(jsii_name="metricTakeOverReleaseCount")
    def metric_take_over_release_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser user takeovers released.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: TakeOverReleaseCount

        :return: A CloudWatch Metric configured for browser user takeovers released

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricTakeOverReleaseCount", [props]))

    @jsii.member(jsii_name="metricThrottlesForApiOperation")
    def metric_throttles_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser throttles.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Throttles

        :return: A CloudWatch Metric configured for browser throttles

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__945c10dd6a920f679edb8ab070a635638c847e8d49d196a218ff5b77cdf8d742)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricThrottlesForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricUserErrorsForApiOperation")
    def metric_user_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking browser user errors.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: UserErrors

        :return: A CloudWatch Metric configured for browser user errors

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6a2ee85b94b08620ec9b5951320326c2a5e06e58d8c74143b59faaa569c5db5a)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricUserErrorsForApiOperation", [operation, props]))

    @builtins.property
    @jsii.member(jsii_name="browserArn")
    @abc.abstractmethod
    def browser_arn(self) -> builtins.str:
        '''(experimental) The ARN of the browser resource.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="browserId")
    @abc.abstractmethod
    def browser_id(self) -> builtins.str:
        '''(experimental) The id of the browser.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="connections")
    def connections(self) -> _aws_cdk_aws_ec2_ceddda9d.Connections:
        '''(experimental) An accessor for the Connections object that will fail if this Browser does not have a VPC configured.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.Connections, jsii.get(self, "connections"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    @abc.abstractmethod
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the browser to access AWS services.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    @abc.abstractmethod
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    @abc.abstractmethod
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was created.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    @abc.abstractmethod
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was last updated.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    @abc.abstractmethod
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the browser.

        :stability: experimental
        '''
        ...


class _BrowserCustomBaseProxy(
    BrowserCustomBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="browserArn")
    def browser_arn(self) -> builtins.str:
        '''(experimental) The ARN of the browser resource.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "browserArn"))

    @builtins.property
    @jsii.member(jsii_name="browserId")
    def browser_id(self) -> builtins.str:
        '''(experimental) The id of the browser.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "browserId"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the browser to access AWS services.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was created.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the browser was last updated.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the browser.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, BrowserCustomBase).__jsii_proxy_class__ = lambda : _BrowserCustomBaseProxy


class BrowserNetworkConfiguration(
    NetworkConfiguration,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.BrowserNetworkConfiguration",
):
    '''(experimental) Network configuration for the Browser tool.

    :stability: experimental
    :exampleMetadata: fixture=default infused

    Example::

        vpc = ec2.Vpc(self, "testVPC")
        
        code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
            code_interpreter_custom_name="my_sandbox_interpreter",
            description="Code interpreter with isolated network access",
            network_configuration=agentcore.BrowserNetworkConfiguration.using_vpc(self,
                vpc=vpc
            )
        )
        
        code_interpreter.connections.add_security_group(ec2.SecurityGroup(self, "AdditionalGroup", vpc=vpc))
    '''

    def __init__(
        self,
        mode: builtins.str,
        scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) Creates a new network configuration.

        :param mode: - the network mode to use for the tool.
        :param scope: -
        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a61932e41a10c1b55eb12421708f57f6f8fa7f51c4a52602ae921332f603e4bc)
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        vpc_config = VpcConfigProps(
            vpc=vpc,
            allow_all_outbound=allow_all_outbound,
            security_groups=security_groups,
            vpc_subnets=vpc_subnets,
        )

        jsii.create(self.__class__, self, [mode, scope, vpc_config])

    @jsii.member(jsii_name="usingPublicNetwork")
    @builtins.classmethod
    def using_public_network(cls) -> "BrowserNetworkConfiguration":
        '''(experimental) Creates a public network configuration.

        PUBLIC is the default network mode.

        :return:

        A BrowserNetworkConfiguration.
        Run this tool to operate in a public environment with internet access, suitable for less sensitive or open-use scenarios.

        :stability: experimental
        '''
        return typing.cast("BrowserNetworkConfiguration", jsii.sinvoke(cls, "usingPublicNetwork", []))

    @jsii.member(jsii_name="usingVpc")
    @builtins.classmethod
    def using_vpc(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> "BrowserNetworkConfiguration":
        '''(experimental) Creates a network configuration from a VPC configuration.

        :param scope: -
        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :return: A BrowserNetworkConfiguration.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ffadf1618c1ccf9e7f800598ace60f876ef2c866dfa2193de733904aef830531)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        vpc_config = VpcConfigProps(
            vpc=vpc,
            allow_all_outbound=allow_all_outbound,
            security_groups=security_groups,
            vpc_subnets=vpc_subnets,
        )

        return typing.cast("BrowserNetworkConfiguration", jsii.sinvoke(cls, "usingVpc", [scope, vpc_config]))


@jsii.implements(ICodeInterpreterCustom)
class CodeInterpreterCustomBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.CodeInterpreterCustomBase",
):
    '''(experimental) Abstract base class for a Code Interpreter.

    Contains methods and attributes valid for Code Interpreters either created with CDK or imported.

    :stability: experimental
    '''

    def __init__(self, scope: _constructs_77d1e7e8.Construct, id: builtins.str) -> None:
        '''
        :param scope: -
        :param id: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c3ba04960e2402fcf93e24376e08d3027678d856540da250157c6e19f1dc1862)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        jsii.create(self.__class__, self, [scope, id])

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: - The IAM principal to grant permissions to.
        :param actions: - The actions to grant.

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1788c6502070824895d3503d450005bb1c205c4d74bb8738add0bf26f3de4904)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantInvoke")
    def grant_invoke(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant invoke permissions on this code interpreter to an IAM principal.

        :param grantee: - The IAM principal to grant invoke permissions to.

        :default:

        - Default grant configuration:
        - actions: ['bedrock-agentcore:InvokeCodeInterpreter']
        - resourceArns: [this.codeInterpreterArn]

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b2db493ce830ccc0f4897a55b53f8cb527c29ca1faf55e5ef17c8df1975c84db)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantInvoke", [grantee]))

    @jsii.member(jsii_name="grantRead")
    def grant_read(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant read permissions on this code interpreter to an IAM principal.

        This includes both read permissions on the specific code interpreter and list permissions on all code interpreters.

        :param grantee: - The IAM principal to grant read permissions to.

        :default:

        - Default grant configuration:
        - actions: ['bedrock-agentcore:GetCodeInterpreter', 'bedrock-agentcore:GetCodeInterpreterSession'] on this.codeInterpreterArn
        - actions: ['bedrock-agentcore:ListCodeInterpreters', 'bedrock-agentcore:ListCodeInterpreterSessions'] on all resources (*)

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__49cb39b73910ca0e9b10fd69d88ba3c962540e3ffe52e4af83aa081763523e1e)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantRead", [grantee]))

    @jsii.member(jsii_name="grantUse")
    def grant_use(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant invoke permissions on this code interpreter to an IAM principal.

        :param grantee: - The IAM principal to grant invoke permissions to.

        :default:

        - Default grant configuration:
        - actions: ['bedrock-agentcore:StartCodeInterpreterSession', 'bedrock-agentcore:InvokeCodeInterpreter', 'bedrock-agentcore:StopCodeInterpreterSession']
        - resourceArns: [this.codeInterpreterArn]

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b4d919318556058b051ce30963bb88b3ea857942f805b6da65b497596bc8e39b)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantUse", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        dimensions: typing.Mapping[builtins.str, builtins.str],
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this code interpreter.

        By default, the metric will be calculated as a sum over a period of 5 minutes.
        You can customize this by using the ``statistic`` and ``period`` properties.

        :param metric_name: -
        :param dimensions: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e89914064bfd399d5233c80170ff40fe971de7b840aeca4ac822fd1fcaf4c53)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, dimensions, props]))

    @jsii.member(jsii_name="metricErrorsForApiOperation")
    def metric_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter errors.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Errors

        :return: A CloudWatch Metric configured for code interpreter errors

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a96b5df243162f6e4ccc604d71ceff9d4907e1fb21c4bdc077b17e437bad6d1e)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricForApiOperation")
    def metric_for_api_operation(
        self,
        metric_name: builtins.str,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter api operations..

        :param metric_name: -
        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: metricName
        - dimensionsMap: { CodeInterpreterId: this.codeInterpreterId }

        :return: A CloudWatch Metric configured for code interpreter api operations

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__601c512b2394720d7f44430e54e52ac9b991b7aa673c58633b67406ae999ec8a)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricForApiOperation", [metric_name, operation, props]))

    @jsii.member(jsii_name="metricInvocationsForApiOperation")
    def metric_invocations_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter invocations.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Invocations

        :return: A CloudWatch Metric configured for code interpreter invocations

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da0ad6292c612c8f34d7b641b68c10de89777fe2d41763b66d9ea6f7c878c4a6)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricInvocationsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricLatencyForApiOperation")
    def metric_latency_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter latencies.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Latency

        :return: A CloudWatch Metric configured for code interpreter latencies

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__72deaefdc0ab67927aa48a7e5dbfb70a9004b85dab32f68b95be249b26066bd0)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricLatencyForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricSessionDuration")
    def metric_session_duration(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter session duration.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Duration

        :return: A CloudWatch Metric configured for code interpreter session duration

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSessionDuration", [props]))

    @jsii.member(jsii_name="metricSystemErrorsForApiOperation")
    def metric_system_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter system errors.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: SystemErrors

        :return: A CloudWatch Metric configured for code interpreter system errors

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__65d0b839015fe6a1c368d562bdee51b93c69cb5b759c1f1173dc2758a1413968)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricSystemErrorsForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricThrottlesForApiOperation")
    def metric_throttles_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter throttles.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: Throttles

        :return: A CloudWatch Metric configured for code interpreter throttles

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a56c641c8e2af33eb396292b7658955fbae3d77a1c0a87985f4020dfe2e45f2)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricThrottlesForApiOperation", [operation, props]))

    @jsii.member(jsii_name="metricUserErrorsForApiOperation")
    def metric_user_errors_for_api_operation(
        self,
        operation: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Creates a CloudWatch metric for tracking code interpreter user errors.

        :param operation: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default:

        - Default metric configuration:
        - namespace: 'AWS/Bedrock-AgentCore'
        - metricName: UserErrors

        :return: A CloudWatch Metric configured for code interpreter user errors

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9be097202746caca62d9d0d7831461e673cceaf8e528a88286bd03a9c0c5b694)
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricUserErrorsForApiOperation", [operation, props]))

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterArn")
    @abc.abstractmethod
    def code_interpreter_arn(self) -> builtins.str:
        '''(experimental) The ARN of the code interpreter resource.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterId")
    @abc.abstractmethod
    def code_interpreter_id(self) -> builtins.str:
        '''(experimental) The id of the code interpreter.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="connections")
    def connections(self) -> _aws_cdk_aws_ec2_ceddda9d.Connections:
        '''(experimental) An accessor for the Connections object that will fail if this Browser does not have a VPC configured.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.Connections, jsii.get(self, "connections"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    @abc.abstractmethod
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the code interpreter to access AWS services.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    @abc.abstractmethod
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    @abc.abstractmethod
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was created.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    @abc.abstractmethod
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was last updated.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    @abc.abstractmethod
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the code interpreter.

        :stability: experimental
        '''
        ...


class _CodeInterpreterCustomBaseProxy(
    CodeInterpreterCustomBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="codeInterpreterArn")
    def code_interpreter_arn(self) -> builtins.str:
        '''(experimental) The ARN of the code interpreter resource.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "codeInterpreterArn"))

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterId")
    def code_interpreter_id(self) -> builtins.str:
        '''(experimental) The id of the code interpreter.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "codeInterpreterId"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the code interpreter to access AWS services.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was created.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) Timestamp when the code interpreter was last updated.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the code interpreter.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, CodeInterpreterCustomBase).__jsii_proxy_class__ = lambda : _CodeInterpreterCustomBaseProxy


class CodeInterpreterNetworkConfiguration(
    NetworkConfiguration,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.CodeInterpreterNetworkConfiguration",
):
    '''(experimental) Network configuration for the Code Interpreter tool.

    :stability: experimental
    :exampleMetadata: fixture=default infused

    Example::

        # Create a custom execution role
        execution_role = iam.Role(self, "CodeInterpreterExecutionRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com")
        )
        
        # Create code interpreter with custom execution role
        code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
            code_interpreter_custom_name="my_code_interpreter",
            description="Code interpreter with custom execution role",
            network_configuration=agentcore.CodeInterpreterNetworkConfiguration.using_public_network(),
            execution_role=execution_role
        )
    '''

    def __init__(
        self,
        mode: builtins.str,
        scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) Creates a new network configuration.

        :param mode: - the network mode to use for the tool.
        :param scope: -
        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5abf274e5386aff6188eb410a31a1f9a74e1ef0c691c2c7886dd26347a9bbcc6)
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        vpc_config = VpcConfigProps(
            vpc=vpc,
            allow_all_outbound=allow_all_outbound,
            security_groups=security_groups,
            vpc_subnets=vpc_subnets,
        )

        jsii.create(self.__class__, self, [mode, scope, vpc_config])

    @jsii.member(jsii_name="usingPublicNetwork")
    @builtins.classmethod
    def using_public_network(cls) -> "CodeInterpreterNetworkConfiguration":
        '''(experimental) Creates a public network configuration.

        :return:

        A CodeInterpreterNetworkConfiguration.
        Run this tool to operate in a public environment with internet access, suitable for less sensitive or open-use scenarios.

        :stability: experimental
        '''
        return typing.cast("CodeInterpreterNetworkConfiguration", jsii.sinvoke(cls, "usingPublicNetwork", []))

    @jsii.member(jsii_name="usingSandboxNetwork")
    @builtins.classmethod
    def using_sandbox_network(cls) -> "CodeInterpreterNetworkConfiguration":
        '''(experimental) Creates a sandbox network configuration.

        :return:

        A CodeInterpreterNetworkConfiguration.
        Run this tool in a restricted environment with limited Permissions and Encryption to enhance safety and reduce potential risks.

        :stability: experimental
        '''
        return typing.cast("CodeInterpreterNetworkConfiguration", jsii.sinvoke(cls, "usingSandboxNetwork", []))

    @jsii.member(jsii_name="usingVpc")
    @builtins.classmethod
    def using_vpc(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        allow_all_outbound: typing.Optional[builtins.bool] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> "CodeInterpreterNetworkConfiguration":
        '''(experimental) Creates a network configuration from a VPC configuration.

        :param scope: -
        :param vpc: (experimental) The VPC to deploy the resource to.
        :param allow_all_outbound: (experimental) Whether to allow the resource to send all network traffic (except ipv6). If set to false, you must individually add traffic rules to allow the resource to connect to network targets. Do not specify this property if the ``securityGroups`` property is set. Instead, configure ``allowAllOutbound`` directly on the security group. Default: true
        :param security_groups: (experimental) The list of security groups to associate with the resource's network interfaces. Only used if 'vpc' is supplied. Default: - If the resource is placed within a VPC and a security group is not specified by this prop, a dedicated security group will be created for this resource.
        :param vpc_subnets: (experimental) Where to place the network interfaces within the VPC. This requires ``vpc`` to be specified in order for interfaces to actually be placed in the subnets. If ``vpc`` is not specify, this will raise an error. Default: - the Vpc default strategy if not specified

        :return: A CodeInterpreterNetworkConfiguration.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__38e59bc603de9e405a37067fca444858724ba4a5692828408586100c7172d14d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        vpc_config = VpcConfigProps(
            vpc=vpc,
            allow_all_outbound=allow_all_outbound,
            security_groups=security_groups,
            vpc_subnets=vpc_subnets,
        )

        return typing.cast("CodeInterpreterNetworkConfiguration", jsii.sinvoke(cls, "usingVpc", [scope, vpc_config]))


class Runtime(
    RuntimeBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.Runtime",
):
    '''(experimental) Bedrock Agent Core Runtime Enables running containerized agents with specific network configurations, security settings, and runtime artifacts.

    :see: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime.html
    :stability: experimental
    :resource: AWS::BedrockAgentCore::Runtime
    :exampleMetadata: infused

    Example::

        repository = ecr.Repository(self, "TestRepository",
            repository_name="test-agent-runtime"
        )
        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
        
        runtime = agentcore.Runtime(self, "MyAgentRuntime",
            runtime_name="myAgent",
            agent_runtime_artifact=agent_runtime_artifact,
            authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_oAuth("https://github.com/.well-known/openid-configuration", "oauth_client_123")
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        agent_runtime_artifact: AgentRuntimeArtifact,
        runtime_name: builtins.str,
        authorizer_configuration: typing.Optional[RuntimeAuthorizerConfiguration] = None,
        description: typing.Optional[builtins.str] = None,
        environment_variables: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        network_configuration: typing.Optional[RuntimeNetworkConfiguration] = None,
        protocol_configuration: typing.Optional[ProtocolType] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param agent_runtime_artifact: (experimental) The artifact configuration for the agent runtime Contains the container configuration with ECR URI.
        :param runtime_name: (experimental) The name of the agent runtime Valid characters are a-z, A-Z, 0-9, _ (underscore) Must start with a letter and can be up to 48 characters long Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$.
        :param authorizer_configuration: (experimental) Authorizer configuration for the agent runtime Use RuntimeAuthorizerConfiguration static methods to create the configuration. Default: - RuntimeAuthorizerConfiguration.iam() (IAM authentication)
        :param description: (experimental) Optional description for the agent runtime. Default: - No description Length Minimum: 1 , Maximum: 1200
        :param environment_variables: (experimental) Environment variables for the agent runtime - Maximum 50 environment variables - Key: Must be 1-100 characters, start with letter or underscore, contain only letters, numbers, and underscores - Value: Must be 0-2048 characters (per CloudFormation specification). Default: - No environment variables
        :param execution_role: (experimental) The IAM role that provides permissions for the agent runtime If not provided, a role will be created automatically. Default: - A new role will be created
        :param network_configuration: (experimental) Network configuration for the agent runtime. Default: - RuntimeNetworkConfiguration.usingPublicNetwork()
        :param protocol_configuration: (experimental) Protocol configuration for the agent runtime. Default: - ProtocolType.HTTP
        :param tags: (experimental) Tags for the agent runtime A list of key:value pairs of tags to apply to this Runtime resource. Default: {} - no tags

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d3c75c162a496b2457c5b16d4ab318237dd0f6028aaaa787f5968728ad5bea40)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = RuntimeProps(
            agent_runtime_artifact=agent_runtime_artifact,
            runtime_name=runtime_name,
            authorizer_configuration=authorizer_configuration,
            description=description,
            environment_variables=environment_variables,
            execution_role=execution_role,
            network_configuration=network_configuration,
            protocol_configuration=protocol_configuration,
            tags=tags,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromAgentRuntimeAttributes")
    @builtins.classmethod
    def from_agent_runtime_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        agent_runtime_arn: builtins.str,
        agent_runtime_id: builtins.str,
        agent_runtime_name: builtins.str,
        role_arn: builtins.str,
        agent_runtime_version: typing.Optional[builtins.str] = None,
        agent_status: typing.Optional[builtins.str] = None,
        created_at: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    ) -> IBedrockAgentRuntime:
        '''(experimental) Import an existing Agent Runtime using attributes This allows you to reference an Agent Runtime that was created outside of CDK.

        :param scope: The construct scope.
        :param id: The construct id.
        :param agent_runtime_arn: (experimental) The ARN of the agent runtime.
        :param agent_runtime_id: (experimental) The ID of the agent runtime.
        :param agent_runtime_name: (experimental) The name of the agent runtime.
        :param role_arn: (experimental) The IAM role ARN.
        :param agent_runtime_version: (experimental) The version of the agent runtime When importing a runtime and this is not specified or undefined, endpoints created on this runtime will point to version "1" unless explicitly overridden. Default: - undefined
        :param agent_status: (experimental) The current status of the agent runtime. Default: - Status not available
        :param created_at: (experimental) The time at which the runtime was created. Default: - Creation time not available
        :param description: (experimental) The description of the agent runtime. Default: - No description
        :param last_updated_at: (experimental) The time at which the runtime was last updated. Default: - Last update time not available
        :param security_groups: (experimental) The security groups for this runtime, if in a VPC. Default: - By default, the runtime is not in a VPC.

        :return: An IBedrockAgentRuntime instance representing the imported runtime

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__05959bcf4b4bc641f8cd5e6663c98667c22ec794751ac633e033ccabebf69312)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = AgentRuntimeAttributes(
            agent_runtime_arn=agent_runtime_arn,
            agent_runtime_id=agent_runtime_id,
            agent_runtime_name=agent_runtime_name,
            role_arn=role_arn,
            agent_runtime_version=agent_runtime_version,
            agent_status=agent_status,
            created_at=created_at,
            description=description,
            last_updated_at=last_updated_at,
            security_groups=security_groups,
        )

        return typing.cast(IBedrockAgentRuntime, jsii.sinvoke(cls, "fromAgentRuntimeAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="addEndpoint")
    def add_endpoint(
        self,
        endpoint_name: builtins.str,
        *,
        description: typing.Optional[builtins.str] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> "RuntimeEndpoint":
        '''(experimental) Add an endpoint to this runtime This is a convenience method that creates a RuntimeEndpoint associated with this runtime.

        :param endpoint_name: The name of the endpoint.
        :param description: (experimental) Description for the endpoint, Must be between 1 and 1200 characters. Default: - No description
        :param version: (experimental) Override the runtime version for this endpoint. Default: 1

        :return: The created RuntimeEndpoint

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9c9f210c62e6b8a9cc9f91d2223cadcf66989308f610a152e24937c2e6f75fea)
            check_type(argname="argument endpoint_name", value=endpoint_name, expected_type=type_hints["endpoint_name"])
        options = AddEndpointOptions(description=description, version=version)

        return typing.cast("RuntimeEndpoint", jsii.invoke(self, "addEndpoint", [endpoint_name, options]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime.

        :return: a token representing the ARN of this agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeArn"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArtifact")
    def agent_runtime_artifact(self) -> AgentRuntimeArtifact:
        '''(experimental) The artifact configuration for the agent runtime.

        :stability: experimental
        '''
        return typing.cast(AgentRuntimeArtifact, jsii.get(self, "agentRuntimeArtifact"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeId")
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The unique identifier of the agent runtime.

        :return: a token representing the ID of this agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeId"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeName")
    def agent_runtime_name(self) -> builtins.str:
        '''(experimental) The name of the agent runtime.

        :return: a token representing the name of this agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeName"))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the agent runtime.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "role"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeVersion")
    def agent_runtime_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of the agent runtime.

        :return: a token representing the version of this agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "agentRuntimeVersion"))

    @builtins.property
    @jsii.member(jsii_name="agentStatus")
    def agent_status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the agent runtime.

        :return: a token representing the status of this agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "agentStatus"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the agent runtime was created.

        :return: a token representing the creation timestamp of this agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) Optional description for the agent runtime.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "description"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the agent runtime was last updated.

        :return: a token representing the last update timestamp of this agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))


class RuntimeEndpoint(
    RuntimeEndpointBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.RuntimeEndpoint",
):
    '''(experimental) Bedrock Agent Core Runtime Endpoint Provides a stable endpoint for invoking agent runtimes with versioning support.

    :see: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-endpoint.html
    :stability: experimental
    :resource: AWS::BedrockAgentCore::RuntimeEndpoint
    :exampleMetadata: infused

    Example::

        repository = ecr.Repository(self, "TestRepository",
            repository_name="test-agent-runtime"
        )
        
        runtime = agentcore.Runtime(self, "MyAgentRuntime",
            runtime_name="myAgent",
            agent_runtime_artifact=agentcore.AgentRuntimeArtifact.from_ecr_repository(repository, "v1.0.0")
        )
        
        prod_endpoint = runtime.add_endpoint("production",
            version="1",
            description="Stable production endpoint - pinned to v1"
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        agent_runtime_id: builtins.str,
        endpoint_name: builtins.str,
        agent_runtime_version: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param agent_runtime_id: (experimental) The ID of the agent runtime to associate with this endpoint This is the unique identifier of the runtime resource Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,99}-[a-zA-Z0-9]{10}$.
        :param endpoint_name: (experimental) The name of the agent runtime endpoint Valid characters are a-z, A-Z, 0-9, _ (underscore) Must start with a letter and can be up to 48 characters long Pattern: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$.
        :param agent_runtime_version: (experimental) The version of the agent runtime to use for this endpoint If not specified, the endpoint will point to version "1" of the runtime. Pattern: ^([1-9][0-9]{0,4})$ Default: "1"
        :param description: (experimental) Optional description for the agent runtime endpoint Length Minimum: 1 , Maximum: 256. Default: - No description
        :param tags: (experimental) Tags for the agent runtime endpoint A list of key:value pairs of tags to apply to this RuntimeEndpoint resource Pattern: ^[a-zA-Z0-9\\s._:/=+@-]*$. Default: {} - no tags

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c08f9203e17afcdac6a5a193e263989301ad529a8b9defc871c88e757bc1f18a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = RuntimeEndpointProps(
            agent_runtime_id=agent_runtime_id,
            endpoint_name=endpoint_name,
            agent_runtime_version=agent_runtime_version,
            description=description,
            tags=tags,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromRuntimeEndpointAttributes")
    @builtins.classmethod
    def from_runtime_endpoint_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        agent_runtime_arn: builtins.str,
        agent_runtime_endpoint_arn: builtins.str,
        endpoint_name: builtins.str,
        created_at: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        endpoint_id: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        live_version: typing.Optional[builtins.str] = None,
        status: typing.Optional[builtins.str] = None,
        target_version: typing.Optional[builtins.str] = None,
    ) -> IRuntimeEndpoint:
        '''(experimental) Import an existing Agent Runtime Endpoint using attributes This allows you to reference an Agent Runtime Endpoint that was created outside of CDK.

        :param scope: The construct scope.
        :param id: The construct id.
        :param agent_runtime_arn: (experimental) The ARN of the parent agent runtime.
        :param agent_runtime_endpoint_arn: (experimental) The ARN of the runtime endpoint.
        :param endpoint_name: (experimental) The name of the runtime endpoint.
        :param created_at: (experimental) When the endpoint was created. Default: - Creation time not available
        :param description: (experimental) The description of the runtime endpoint. Default: - No description
        :param endpoint_id: (experimental) The unique identifier of the runtime endpoint. Default: - Endpoint ID not available
        :param last_updated_at: (experimental) When the endpoint was last updated. Default: - Last update time not available
        :param live_version: (experimental) The live version of the agent runtime that is currently serving requests. Default: - Live version not available
        :param status: (experimental) The current status of the runtime endpoint. Default: - Status not available
        :param target_version: (experimental) The target version the endpoint is transitioning to (during updates). Default: - Target version not available

        :return: An IRuntimeEndpoint instance representing the imported endpoint

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7aac4684398202199ff45b016211ef025a54472a69d037cfafe89eaa76bac9ac)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = RuntimeEndpointAttributes(
            agent_runtime_arn=agent_runtime_arn,
            agent_runtime_endpoint_arn=agent_runtime_endpoint_arn,
            endpoint_name=endpoint_name,
            created_at=created_at,
            description=description,
            endpoint_id=endpoint_id,
            last_updated_at=last_updated_at,
            live_version=live_version,
            status=status,
            target_version=target_version,
        )

        return typing.cast(IRuntimeEndpoint, jsii.sinvoke(cls, "fromRuntimeEndpointAttributes", [scope, id, attrs]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeArn")
    def agent_runtime_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime associated with this endpoint.

        :return: a token representing the ARN of the agent runtime

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeArn"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeEndpointArn")
    def agent_runtime_endpoint_arn(self) -> builtins.str:
        '''(experimental) The ARN of the agent runtime endpoint.

        :return: a token representing the ARN of this agent runtime endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeEndpointArn"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeId")
    def agent_runtime_id(self) -> builtins.str:
        '''(experimental) The ID of the agent runtime associated with this endpoint.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeId"))

    @builtins.property
    @jsii.member(jsii_name="agentRuntimeVersion")
    def agent_runtime_version(self) -> builtins.str:
        '''(experimental) The version of the agent runtime used by this endpoint.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "agentRuntimeVersion"))

    @builtins.property
    @jsii.member(jsii_name="endpointId")
    def endpoint_id(self) -> builtins.str:
        '''(experimental) The unique identifier of the runtime endpoint.

        :return: a token representing the ID of this endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "endpointId"))

    @builtins.property
    @jsii.member(jsii_name="endpointName")
    def endpoint_name(self) -> builtins.str:
        '''(experimental) The name of the endpoint.

        :return: a token representing the name of this endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "endpointName"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the endpoint was created.

        :return: a token representing the creation timestamp of this endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) Optional description for the endpoint.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "description"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) When this endpoint was last updated.

        :return: a token representing the last update timestamp of this endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @builtins.property
    @jsii.member(jsii_name="liveVersion")
    def live_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The live version of the endpoint.

        :return: a token representing the live version of this endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "liveVersion"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the endpoint.

        :return: a token representing the status of this endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="targetVersion")
    def target_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The target version of the endpoint.

        :return: a token representing the target version of this endpoint

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "targetVersion"))


class BrowserCustom(
    BrowserCustomBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.BrowserCustom",
):
    '''(experimental) Browser resource for AWS Bedrock Agent Core.

    Provides a browser environment for web automation and interaction.

    :see: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser.html
    :stability: experimental
    :resource: AWS::BedrockAgentCore::BrowserCustom
    :exampleMetadata: fixture=default infused

    Example::

        # Create a custom execution role
        execution_role = iam.Role(self, "BrowserExecutionRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockAgentCoreBrowserExecutionRolePolicy")
            ]
        )
        
        # Create browser with custom execution role
        browser = agentcore.BrowserCustom(self, "MyBrowser",
            browser_custom_name="my_browser",
            description="Browser with custom execution role",
            network_configuration=agentcore.BrowserNetworkConfiguration.using_public_network(),
            execution_role=execution_role
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        browser_custom_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        network_configuration: typing.Optional[BrowserNetworkConfiguration] = None,
        recording_config: typing.Optional[typing.Union[RecordingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param browser_custom_name: (experimental) The name of the browser Valid characters are a-z, A-Z, 0-9, _ (underscore) The name must start with a letter and can be up to 48 characters long Pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}.
        :param description: (experimental) Optional description for the browser Valid characters are a-z, A-Z, 0-9, _ (underscore), - (hyphen) and spaces The description can have up to 200 characters. Default: - No description
        :param execution_role: (experimental) The IAM role that provides permissions for the browser to access AWS services. Default: - A new role will be created
        :param network_configuration: (experimental) Network configuration for browser. Default: - PUBLIC network mode
        :param recording_config: (experimental) Recording configuration for browser. Default: - No recording configuration
        :param tags: (experimental) Tags (optional) A list of key:value pairs of tags to apply to this Browser resource. Default: {} - no tags

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1158b103a85cbce3d28e980992f8b82595d918f92538cc576de16ed55fbc4071)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = BrowserCustomProps(
            browser_custom_name=browser_custom_name,
            description=description,
            execution_role=execution_role,
            network_configuration=network_configuration,
            recording_config=recording_config,
            tags=tags,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromBrowserCustomAttributes")
    @builtins.classmethod
    def from_browser_custom_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        browser_arn: builtins.str,
        role_arn: builtins.str,
        created_at: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        status: typing.Optional[builtins.str] = None,
    ) -> IBrowserCustom:
        '''(experimental) Creates an Browser Custom reference from an existing browser's attributes.

        :param scope: - The construct scope.
        :param id: - Identifier of the construct.
        :param browser_arn: (experimental) The ARN of the agent.
        :param role_arn: (experimental) The ARN of the IAM role associated to the browser.
        :param created_at: (experimental) The created timestamp of the browser. Default: undefined - No created timestamp is provided
        :param last_updated_at: (experimental) When this browser was last updated. Default: undefined - No last updated timestamp is provided
        :param security_groups: (experimental) The security groups for this browser, if in a VPC. Default: - By default, the browser is not in a VPC.
        :param status: (experimental) The status of the browser. Default: undefined - No status is provided

        :return: An IBrowserCustom reference to the existing browser

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3e143bea37e02f65f29c3f3dfd523e8452322bb7ee9d57f98ab6bd947e40e261)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = BrowserCustomAttributes(
            browser_arn=browser_arn,
            role_arn=role_arn,
            created_at=created_at,
            last_updated_at=last_updated_at,
            security_groups=security_groups,
            status=status,
        )

        return typing.cast(IBrowserCustom, jsii.sinvoke(cls, "fromBrowserCustomAttributes", [scope, id, attrs]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="browserArn")
    def browser_arn(self) -> builtins.str:
        '''(experimental) The ARN of the browser resource.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "browserArn"))

    @builtins.property
    @jsii.member(jsii_name="browserId")
    def browser_id(self) -> builtins.str:
        '''(experimental) The id of the browser.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "browserId"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role associated to the browser.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''(experimental) The name of the browser.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="networkConfiguration")
    def network_configuration(self) -> BrowserNetworkConfiguration:
        '''(experimental) The network configuration of the browser.

        :stability: experimental
        '''
        return typing.cast(BrowserNetworkConfiguration, jsii.get(self, "networkConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The created timestamp of the browser.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the browser.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "description"))

    @builtins.property
    @jsii.member(jsii_name="failureReason")
    def failure_reason(self) -> typing.Optional[builtins.str]:
        '''(experimental) The failure reason of the browser.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "failureReason"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The last updated timestamp of the browser.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @builtins.property
    @jsii.member(jsii_name="recordingConfig")
    def recording_config(self) -> typing.Optional[RecordingConfig]:
        '''(experimental) The recording configuration of the browser.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[RecordingConfig], jsii.get(self, "recordingConfig"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the browser.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags applied to this browser resource A map of key-value pairs for resource tagging.

        :default: - No tags applied

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "tags"))


class CodeInterpreterCustom(
    CodeInterpreterCustomBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-bedrock-agentcore-alpha.CodeInterpreterCustom",
):
    '''(experimental) Custom code interpreter resource for AWS Bedrock Agent Core.

    Provides a sandboxed environment for code execution with configurable network access.

    :see: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter.html
    :stability: experimental
    :resource: AWS::BedrockAgentCore::CodeInterpreterCustom
    :exampleMetadata: fixture=default infused

    Example::

        # Create a custom execution role
        execution_role = iam.Role(self, "CodeInterpreterExecutionRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com")
        )
        
        # Create code interpreter with custom execution role
        code_interpreter = agentcore.CodeInterpreterCustom(self, "MyCodeInterpreter",
            code_interpreter_custom_name="my_code_interpreter",
            description="Code interpreter with custom execution role",
            network_configuration=agentcore.CodeInterpreterNetworkConfiguration.using_public_network(),
            execution_role=execution_role
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        code_interpreter_custom_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        network_configuration: typing.Optional[CodeInterpreterNetworkConfiguration] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param code_interpreter_custom_name: (experimental) The name of the code interpreter Valid characters are a-z, A-Z, 0-9, _ (underscore) The name must start with a letter and can be up to 48 characters long Pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}.
        :param description: (experimental) Optional description for the code interpreter Valid characters are a-z, A-Z, 0-9, _ (underscore), - (hyphen) and spaces The description can have up to 200 characters. Default: - No description
        :param execution_role: (experimental) The IAM role that provides permissions for the code interpreter to access AWS services. Default: - A new role will be created.
        :param network_configuration: (experimental) Network configuration for code interpreter. Default: - PUBLIC network mode
        :param tags: (experimental) Tags (optional) A list of key:value pairs of tags to apply to this Code Interpreter resource. Default: {} - no tags

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__97059670dcd4750424fbb12f68be0e5fc4005cf0b64c6621aff517561009ef5a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = CodeInterpreterCustomProps(
            code_interpreter_custom_name=code_interpreter_custom_name,
            description=description,
            execution_role=execution_role,
            network_configuration=network_configuration,
            tags=tags,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromCodeInterpreterCustomAttributes")
    @builtins.classmethod
    def from_code_interpreter_custom_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        code_interpreter_arn: builtins.str,
        role_arn: builtins.str,
        created_at: typing.Optional[builtins.str] = None,
        last_updated_at: typing.Optional[builtins.str] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        status: typing.Optional[builtins.str] = None,
    ) -> ICodeInterpreterCustom:
        '''(experimental) Creates an Code Interpreter Custom reference from an existing code interpreter's attributes.

        :param scope: - The construct scope.
        :param id: - Identifier of the construct.
        :param code_interpreter_arn: (experimental) The ARN of the agent.
        :param role_arn: (experimental) The ARN of the IAM role associated to the code interpreter.
        :param created_at: (experimental) The created timestamp of the code interpreter. Default: undefined - No created timestamp is provided
        :param last_updated_at: (experimental) When this code interpreter was last updated. Default: undefined - No last updated timestamp is provided
        :param security_groups: (experimental) The security groups for this code interpreter, if in a VPC. Default: - By default, the code interpreter is not in a VPC.
        :param status: (experimental) The status of the code interpreter. Default: undefined - No status is provided

        :return: An ICodeInterpreterCustom reference to the existing code interpreter

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da00b980caf9bfd0b84d4f7c4ec856774682fff062a743c88616a5a9368f2a09)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = CodeInterpreterCustomAttributes(
            code_interpreter_arn=code_interpreter_arn,
            role_arn=role_arn,
            created_at=created_at,
            last_updated_at=last_updated_at,
            security_groups=security_groups,
            status=status,
        )

        return typing.cast(ICodeInterpreterCustom, jsii.sinvoke(cls, "fromCodeInterpreterCustomAttributes", [scope, id, attrs]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterArn")
    def code_interpreter_arn(self) -> builtins.str:
        '''(experimental) The ARN of the code interpreter resource.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "codeInterpreterArn"))

    @builtins.property
    @jsii.member(jsii_name="codeInterpreterId")
    def code_interpreter_id(self) -> builtins.str:
        '''(experimental) The id of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "codeInterpreterId"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) The IAM role that provides permissions for the code interpreter to access AWS services.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''(experimental) The principal to grant permissions to.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''(experimental) The name of the code interpreter.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="networkConfiguration")
    def network_configuration(self) -> CodeInterpreterNetworkConfiguration:
        '''(experimental) The network configuration of the code interpreter.

        :stability: experimental
        '''
        return typing.cast(CodeInterpreterNetworkConfiguration, jsii.get(self, "networkConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The created timestamp of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description of the code interpreter.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "description"))

    @builtins.property
    @jsii.member(jsii_name="failureReason")
    def failure_reason(self) -> typing.Optional[builtins.str]:
        '''(experimental) The failure reason of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "failureReason"))

    @builtins.property
    @jsii.member(jsii_name="lastUpdatedAt")
    def last_updated_at(self) -> typing.Optional[builtins.str]:
        '''(experimental) The last updated timestamp of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lastUpdatedAt"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the code interpreter.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags applied to this code interpreter resource A map of key-value pairs for resource tagging.

        :default: - No tags applied

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "tags"))


__all__ = [
    "AddEndpointOptions",
    "AgentRuntimeArtifact",
    "AgentRuntimeAttributes",
    "BrowserCustom",
    "BrowserCustomAttributes",
    "BrowserCustomBase",
    "BrowserCustomProps",
    "BrowserNetworkConfiguration",
    "CodeInterpreterCustom",
    "CodeInterpreterCustomAttributes",
    "CodeInterpreterCustomBase",
    "CodeInterpreterCustomProps",
    "CodeInterpreterNetworkConfiguration",
    "IBedrockAgentRuntime",
    "IBrowserCustom",
    "ICodeInterpreterCustom",
    "IRuntimeEndpoint",
    "NetworkConfiguration",
    "ProtocolType",
    "RecordingConfig",
    "Runtime",
    "RuntimeAuthorizerConfiguration",
    "RuntimeBase",
    "RuntimeEndpoint",
    "RuntimeEndpointAttributes",
    "RuntimeEndpointBase",
    "RuntimeEndpointProps",
    "RuntimeNetworkConfiguration",
    "RuntimeProps",
    "VpcConfigProps",
]

publication.publish()

def _typecheckingstub__175b1aee490f549cb19d8945b728786765752ce863f0a55d8732e6f777128e9b(
    *,
    description: typing.Optional[builtins.str] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__604d365a86a290247af7992e6be98b47b27307a51f5ffdb436c6c1ea4019453a(
    directory: builtins.str,
    *,
    asset_name: typing.Optional[builtins.str] = None,
    build_args: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    build_secrets: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    build_ssh: typing.Optional[builtins.str] = None,
    cache_disabled: typing.Optional[builtins.bool] = None,
    cache_from: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]]] = None,
    cache_to: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]] = None,
    display_name: typing.Optional[builtins.str] = None,
    file: typing.Optional[builtins.str] = None,
    invalidation: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    network_mode: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode] = None,
    outputs: typing.Optional[typing.Sequence[builtins.str]] = None,
    platform: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform] = None,
    target: typing.Optional[builtins.str] = None,
    extra_hash: typing.Optional[builtins.str] = None,
    exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
    follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
    ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5378ad450d2e50130983bd4e4c0d41f7ddc7b25ef75b63e107cdace81383db49(
    repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
    tag: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bedccb351eb2d100e954ac8354c709d22031237b55a8c9439b4fa56a9c488298(
    scope: _constructs_77d1e7e8.Construct,
    runtime: Runtime,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__521eb5a43c1809da91e6b913f83fa6446f5b8ac2c440a565fa2764b3cd9f4ad8(
    *,
    agent_runtime_arn: builtins.str,
    agent_runtime_id: builtins.str,
    agent_runtime_name: builtins.str,
    role_arn: builtins.str,
    agent_runtime_version: typing.Optional[builtins.str] = None,
    agent_status: typing.Optional[builtins.str] = None,
    created_at: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__14ea7632e5df00d60970b59a9a4cb5f38d208fd7a26740e3444fd2b1e4b432ba(
    *,
    browser_arn: builtins.str,
    role_arn: builtins.str,
    created_at: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    status: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c723ceb06d7434df1c72a1865f418037daeeda29f30194820f0872da7d50bbe8(
    *,
    browser_custom_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    network_configuration: typing.Optional[BrowserNetworkConfiguration] = None,
    recording_config: typing.Optional[typing.Union[RecordingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f96ed57c1afc648e15cebfa320e03f93dc4c161c09d253072930e4b7d4e4ed24(
    *,
    code_interpreter_arn: builtins.str,
    role_arn: builtins.str,
    created_at: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    status: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e75974384deaaee0d0812c3570b15b1adf0a19fbd67095aea1229a4d3d5c5c05(
    *,
    code_interpreter_custom_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    network_configuration: typing.Optional[CodeInterpreterNetworkConfiguration] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3b1a5766ae93ba39d5e7df12bdfc35c2a7d298375e7689fbc39a3c76d50d2639(
    statement: _aws_cdk_aws_iam_ceddda9d.PolicyStatement,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3208bdcc07b3a3b3b7ac0ed80c7b033074eab2659722a2dec0d8400cf5da5af8(
    actions: typing.Sequence[builtins.str],
    resources: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6e4ed0dc7cd812fb1d50239f33a79cd0a5de1be6488c8ee24a3b016a546ef94b(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4e37d3744eaf4f98404f5daccedff6e7a637774c39193ceadfd0f88c7aa16d50(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b28241dea68e79093525ede5e9deed8adeda944e89126bbcebe733fd16561495(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3beecc1a8cde07edfff6ed6fa9c6deb0e5c35524c1b4ca5bc87c39f95ca1f565(
    metric_name: builtins.str,
    dimensions: typing.Mapping[builtins.str, builtins.str],
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4826f7478acda3a04d53cc2e00e999d28d4b6af89d40b4863b0007b08c0b26bf(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da9382b030a7d475c5afa4286f7e177b609a5f61d4d9d40b1767f5c1e99b8815(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dd8850bcf1d06baf4b66c051e33ef652a6c75bc169744326c9d541535c3f3ca7(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__efd83ae8402a4ac91c4d9cee61087a64dc24f53da2f48b59aa2cc85cde883b29(
    metric_name: builtins.str,
    dimensions: typing.Mapping[builtins.str, builtins.str],
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9182d2fd8511b983f694d71df771315bd2911e5e5d9482b933161a628210ec54(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e825fd71c16a04ffa07fa3e9ff9d61d6e478bdf2f90788eba67bba76e9f38ccb(
    metric_name: builtins.str,
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8cf7f7691dff5fcb719882b3a76ff7b4a55b686f01244cf9ab3c1ee39a4dd4fc(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f6be7d90ffdb2f66b76b997f0926ae3ff14c53cc65c008f5a0591e3f4676265a(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cfb1295c98675d8b1f487abc85bf1d69ec7ac709035de1d15c83e328863a23ec(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ea0c6d4b07cd9212bb39f789638d8a9a6af30cbc0157a19bcd58f6b94d852755(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c1768ca682c2fd421a544ff8111e6e6985b07e3d62cdc62c35ef9cee5896ce2e(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04274b315577b6819dda4346fc076850f28656449a559f5561ca7d53df97f5e3(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0ec65ea8e752705bafc58f0d6cacd39d556973c472ffb0789fa4af3ebcce4bcc(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d24a36658edbfd7ecf76e5be971a6012fc93c641f1a510d1ddfd95730be1d7db(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e4df790d3e336e48159d1eef607374eaf8f903928d69bd2620e375c4794e4fb3(
    metric_name: builtins.str,
    dimensions: typing.Mapping[builtins.str, builtins.str],
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eedad4c7938113f5f34f301a9b648ae40f5400a9e4de351b0186137052a65fab(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__669e8f3a0db7a0b0e3787f22af4e559b8709590c28a9b79f240d11855cd87a11(
    metric_name: builtins.str,
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d5ade6561c63063084b2bd832a2df3362c624482ddaf7b7207ebec55d3e5431b(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__79fd1126b940aa58648080ebef78a6ecac9291a3f4e257a9e9b8a3b62fb84e5a(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b950226f77f1b8ff84aba977a1f05f62ed459462976db6648d94a67e1e1ef8cf(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e4e3175daf088ea941aee60546645fc39148e3a11ab2b2e5d897a48eff09f4e0(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4e9e3e47628eaf2b6a4ffa31b2d7904f6d5438386a823eeca9d34b97f6f484df(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b1156fe37fe7149a4f863e83246fb36b82ce35366fd78287a7abd74852fa9ecd(
    mode: builtins.str,
    scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__847016f3fc41e4cdc9b08f4aeed6b6521f23c2c1ef8b55de56db5d14f7dbdc82(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    s3_location: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.Location, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b924023484b6dec8c84698f52f4e325bbda80efa65704ec656d07d774f0f360a(
    user_pool_id: builtins.str,
    client_id: builtins.str,
    region: typing.Optional[builtins.str] = None,
    allowed_audience: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9ac01ece0cc4140cb0b2a31ed95c6b9e03284a2363131d8f59958f4506fdec5f(
    discovery_url: builtins.str,
    allowed_clients: typing.Optional[typing.Sequence[builtins.str]] = None,
    allowed_audience: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0b8de9eb8f6b27c5ad0708ddadcf0e5e78987856a5b94b421cb1abbcc761229(
    discovery_url: builtins.str,
    client_id: builtins.str,
    allowed_audience: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__16350f8e803148ae58824c157d92d6b5b360c3802a4018cc1e88f99466e7fa95(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7231f6dcdd2551159f4e644a7b39271f091fade67469f9bf285044a8c4c90b60(
    statement: _aws_cdk_aws_iam_ceddda9d.PolicyStatement,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__87eb6e84d44b507957213f90c634b593ff68893ef29137a6154e73fa53e18e18(
    actions: typing.Sequence[builtins.str],
    resources: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f464dbb8ec8dc44c2f152bffa0fe6b7e25a72226db47d4575639ab76a3ee504b(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__23262a416c2bde8ca6024d06971509afa97486440111e79dfae8c143d05ed9be(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__894ad60671ea950414fd0416fead36cee5e0bc1348fcb31b422ba8e37ea00c08(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f6a2aba3c163e6d2d8cfa3127ef4170f55abf85a15cea83297552f1fe625776d(
    metric_name: builtins.str,
    dimensions: typing.Mapping[builtins.str, builtins.str],
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d8f995850b550d0ef0b0c5967813f910df0c54b53b6273e50eef58f9c9a599ff(
    *,
    agent_runtime_arn: builtins.str,
    agent_runtime_endpoint_arn: builtins.str,
    endpoint_name: builtins.str,
    created_at: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    endpoint_id: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    live_version: typing.Optional[builtins.str] = None,
    status: typing.Optional[builtins.str] = None,
    target_version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__07caa672d91c2d444bbd6350d0c5232e8b425f0f99ff16fa910ac554ef216410(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7edf14b5674c2c3647a66c54aa24ffa82abf23b571539cd8f02aa354e64da16a(
    *,
    agent_runtime_id: builtins.str,
    endpoint_name: builtins.str,
    agent_runtime_version: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f3fca872b84d08855284949a94ef7ceab6679568661613e4224125dbf7add5d5(
    mode: builtins.str,
    scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5b65f23ce4df9170ab1ea5e330f24e42113b36afa69e504b887bda27e2e0919b(
    scope: _constructs_77d1e7e8.Construct,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e60d912f60dcec4a97a088e67e9b6da136fd8fbd51038c0380995a1946e1724f(
    *,
    agent_runtime_artifact: AgentRuntimeArtifact,
    runtime_name: builtins.str,
    authorizer_configuration: typing.Optional[RuntimeAuthorizerConfiguration] = None,
    description: typing.Optional[builtins.str] = None,
    environment_variables: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    network_configuration: typing.Optional[RuntimeNetworkConfiguration] = None,
    protocol_configuration: typing.Optional[ProtocolType] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2116ad0a264d69770800f27d273a661a955fcb5c6c066f36456e9178f63d742d(
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c77d9cceeabf2dd05d534145778ab3e1e597cf25fdabc7bdbdbc642c412f2435(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d6facf14dce62b7f6f12e4abaf4eb022dff3a45f4068e5f45350aab6e10355a0(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2d32eecca999e221fe7baaea3ba395ddee5578ec83675efa9efdbea664213da2(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9186b5df0e333eb3469e897ab73dc50dee27c22f707afd8f3645295ca9d00d55(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f8d3ed248b0e1fbb8321d56521a7d7da90f0d2609d7149da6e1d786cbb7e8af8(
    metric_name: builtins.str,
    dimensions: typing.Mapping[builtins.str, builtins.str],
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__78f3dfb28f4dc0851b8a333b577550c3ed04b83619039f5923124cdcbed267cd(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__44ddd5de65d8344be82e751ad250cc43e9faa11ea964e6b229c0a4d1ec72d5f7(
    metric_name: builtins.str,
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad4dce28a348ae0a4ea1f8be12576c56d15cb4cfabe63fa3ad38edc91bd2674d(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__def70821036fc28a14280760ae0b74a0fece9251b8de279a7787b620952b96f2(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__35a69ebb2bb4842640813061b2ac17af0959c464410a959b014b4c88834032a5(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__945c10dd6a920f679edb8ab070a635638c847e8d49d196a218ff5b77cdf8d742(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6a2ee85b94b08620ec9b5951320326c2a5e06e58d8c74143b59faaa569c5db5a(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a61932e41a10c1b55eb12421708f57f6f8fa7f51c4a52602ae921332f603e4bc(
    mode: builtins.str,
    scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ffadf1618c1ccf9e7f800598ace60f876ef2c866dfa2193de733904aef830531(
    scope: _constructs_77d1e7e8.Construct,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c3ba04960e2402fcf93e24376e08d3027678d856540da250157c6e19f1dc1862(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1788c6502070824895d3503d450005bb1c205c4d74bb8738add0bf26f3de4904(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b2db493ce830ccc0f4897a55b53f8cb527c29ca1faf55e5ef17c8df1975c84db(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__49cb39b73910ca0e9b10fd69d88ba3c962540e3ffe52e4af83aa081763523e1e(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b4d919318556058b051ce30963bb88b3ea857942f805b6da65b497596bc8e39b(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e89914064bfd399d5233c80170ff40fe971de7b840aeca4ac822fd1fcaf4c53(
    metric_name: builtins.str,
    dimensions: typing.Mapping[builtins.str, builtins.str],
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a96b5df243162f6e4ccc604d71ceff9d4907e1fb21c4bdc077b17e437bad6d1e(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__601c512b2394720d7f44430e54e52ac9b991b7aa673c58633b67406ae999ec8a(
    metric_name: builtins.str,
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da0ad6292c612c8f34d7b641b68c10de89777fe2d41763b66d9ea6f7c878c4a6(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__72deaefdc0ab67927aa48a7e5dbfb70a9004b85dab32f68b95be249b26066bd0(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__65d0b839015fe6a1c368d562bdee51b93c69cb5b759c1f1173dc2758a1413968(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a56c641c8e2af33eb396292b7658955fbae3d77a1c0a87985f4020dfe2e45f2(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9be097202746caca62d9d0d7831461e673cceaf8e528a88286bd03a9c0c5b694(
    operation: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5abf274e5386aff6188eb410a31a1f9a74e1ef0c691c2c7886dd26347a9bbcc6(
    mode: builtins.str,
    scope: typing.Optional[_constructs_77d1e7e8.Construct] = None,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__38e59bc603de9e405a37067fca444858724ba4a5692828408586100c7172d14d(
    scope: _constructs_77d1e7e8.Construct,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    allow_all_outbound: typing.Optional[builtins.bool] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d3c75c162a496b2457c5b16d4ab318237dd0f6028aaaa787f5968728ad5bea40(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    agent_runtime_artifact: AgentRuntimeArtifact,
    runtime_name: builtins.str,
    authorizer_configuration: typing.Optional[RuntimeAuthorizerConfiguration] = None,
    description: typing.Optional[builtins.str] = None,
    environment_variables: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    network_configuration: typing.Optional[RuntimeNetworkConfiguration] = None,
    protocol_configuration: typing.Optional[ProtocolType] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__05959bcf4b4bc641f8cd5e6663c98667c22ec794751ac633e033ccabebf69312(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    agent_runtime_arn: builtins.str,
    agent_runtime_id: builtins.str,
    agent_runtime_name: builtins.str,
    role_arn: builtins.str,
    agent_runtime_version: typing.Optional[builtins.str] = None,
    agent_status: typing.Optional[builtins.str] = None,
    created_at: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9c9f210c62e6b8a9cc9f91d2223cadcf66989308f610a152e24937c2e6f75fea(
    endpoint_name: builtins.str,
    *,
    description: typing.Optional[builtins.str] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c08f9203e17afcdac6a5a193e263989301ad529a8b9defc871c88e757bc1f18a(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    agent_runtime_id: builtins.str,
    endpoint_name: builtins.str,
    agent_runtime_version: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7aac4684398202199ff45b016211ef025a54472a69d037cfafe89eaa76bac9ac(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    agent_runtime_arn: builtins.str,
    agent_runtime_endpoint_arn: builtins.str,
    endpoint_name: builtins.str,
    created_at: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    endpoint_id: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    live_version: typing.Optional[builtins.str] = None,
    status: typing.Optional[builtins.str] = None,
    target_version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1158b103a85cbce3d28e980992f8b82595d918f92538cc576de16ed55fbc4071(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    browser_custom_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    network_configuration: typing.Optional[BrowserNetworkConfiguration] = None,
    recording_config: typing.Optional[typing.Union[RecordingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3e143bea37e02f65f29c3f3dfd523e8452322bb7ee9d57f98ab6bd947e40e261(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    browser_arn: builtins.str,
    role_arn: builtins.str,
    created_at: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    status: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__97059670dcd4750424fbb12f68be0e5fc4005cf0b64c6621aff517561009ef5a(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    code_interpreter_custom_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    network_configuration: typing.Optional[CodeInterpreterNetworkConfiguration] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da00b980caf9bfd0b84d4f7c4ec856774682fff062a743c88616a5a9368f2a09(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    code_interpreter_arn: builtins.str,
    role_arn: builtins.str,
    created_at: typing.Optional[builtins.str] = None,
    last_updated_at: typing.Optional[builtins.str] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    status: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

for cls in [IBedrockAgentRuntime, IBrowserCustom, ICodeInterpreterCustom, IRuntimeEndpoint]:
    typing.cast(typing.Any, cls).__protocol_attrs__ = typing.cast(typing.Any, cls).__protocol_attrs__ - set(['__jsii_proxy_class__', '__jsii_type__'])
