import json
import logging
import os
import tempfile
import zipfile

import boto3

logger = logging.getLogger(__name__)
STACK_PREFIX = "rvm-provisioned"
REGION = os.environ["AWS_REGION"]


def _download_and_extract_zip(bucket, key):
    s3_client = boto3.client("s3")

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "rvm-configuration.zip")

    logger.info(f"Downloading {bucket}/{key} to {zip_path}")
    s3_client.download_file(bucket, key, zip_path)

    logger.info(f"Extracting zip file to {temp_dir}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    return temp_dir


def _read_manifest(manifest_file):
    with open(manifest_file) as file:
        manifest = json.loads(file.read())
        return manifest


def _assume_role(account_id, role_name="RvmWorkflowRole"):
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    sts_client = boto3.client("sts")
    response = sts_client.assume_role(
        RoleArn=role_arn, RoleSessionName=f"rvm-deployment-{account_id}"
    )

    session = boto3.Session(
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
    )

    logger.info(f"Successfully assumed role {role_arn}")
    return session


def _read_template_file(template_file: str) -> str:
    with open(template_file) as file:
        template_content = file.read()
        return template_content


def _get_existing_stacks(session: boto3.Session) -> dict[str, str]:
    cloudformation = session.client("cloudformation", region_name=REGION)
    existing_stacks = {}

    try:
        paginator = cloudformation.get_paginator("list_stacks")
        for page in paginator.paginate(
            StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE"]
        ):
            for stack in page["StackSummaries"]:
                if stack["StackName"].startswith(STACK_PREFIX):
                    existing_stacks[stack["StackName"]] = stack["StackStatus"]
    except Exception as e:
        logger.warning(f"Failed to list existing stacks: {e}")

    return existing_stacks


def _delete_stack(session: boto3.Session, stack_name: str, account_id: str) -> bool:
    cloudformation = session.client("cloudformation", region_name=REGION)

    try:
        cloudformation.delete_stack(StackName=stack_name)
        logger.info(f"Started deletion of stack '{stack_name}' in account {account_id}")

        # Wait for stack deletion to complete
        waiter = cloudformation.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stack_name)

        logger.info(
            f"Successfully deleted stack '{stack_name}' in account {account_id}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to delete stack '{stack_name}' in account {account_id}: {e}"
        )
        return False


def _deploy_stack(
    session: boto3.Session,
    template_content: str,
    stack_name: str,
    account_id: str,
    existing_stacks: dict[str, str],
) -> bool:
    cloudformation = session.client("cloudformation", region_name=REGION)

    if stack_name in existing_stacks:
        logger.info(f"Stack '{stack_name}' exists in account {account_id}, updating...")

        cloudformation.update_stack(
            StackName=stack_name,
            TemplateBody=template_content,
            Capabilities=["CAPABILITY_NAMED_IAM"],
        )

        logger.info(f"Started update of stack '{stack_name}' in account {account_id}")
        return True
    else:
        logger.info(f"Creating new stack '{stack_name}' in account {account_id}")

        cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=template_content,
            Capabilities=["CAPABILITY_NAMED_IAM"],
        )

        logger.info(f"Started creation of stack '{stack_name}' in account {account_id}")
        return True


def _generate_stack_name(template_file: str) -> str:
    base_name = os.path.splitext(os.path.basename(template_file))[0]
    stack_name = f"{STACK_PREFIX}-{base_name}"
    return stack_name


def deploy_all(extracted_dir: str) -> dict[str, list[str]]:
    manifest_path = os.path.join(extracted_dir, "manifest.json")
    results = {"success": [], "failed": [], "deleted": []}

    manifest = _read_manifest(manifest_path)

    if "templates" not in manifest:
        logger.warning("No 'templates' section found in manifest")
        return results

    expected_stacks = set()
    all_accounts = set()
    account_stacks = {}

    for template_config in manifest["templates"]:
        template_file = template_config.get("template_file")
        accounts = template_config.get("accounts", [])

        if not template_file:
            logger.warning("Template configuration missing 'template_file'")
            continue

        if not accounts:
            logger.warning(f"No accounts specified for template {template_file}")
            continue

        template_path = os.path.join(extracted_dir, template_file)

        try:
            template_content = _read_template_file(template_path)
        except FileNotFoundError:
            logger.warning(f"Template file not found: {template_path}")
            results["failed"].extend(accounts)
            continue

        stack_name = _generate_stack_name(template_file)
        all_accounts.update(accounts)

        for account_id in accounts:
            expected_stacks.add(f"{stack_name}-{account_id}")

            if account_id not in account_stacks:
                account_stacks[account_id] = set()
            account_stacks[account_id].add(f"{stack_name}-{account_id}")

    account_existing_stacks = {}
    for account_id in all_accounts:
        try:
            session = _assume_role(account_id)
            existing_stacks = _get_existing_stacks(session)
            account_existing_stacks[account_id] = existing_stacks

            expected_for_account = account_stacks.get(account_id, set())
            orphaned_stacks = set(existing_stacks.keys()) - expected_for_account

            for stack_name in orphaned_stacks:
                if _delete_stack(session, stack_name, account_id):
                    results["deleted"].append(f"{stack_name}:{account_id}")

        except Exception as e:
            logger.error(
                f"Failed to check for orphaned stacks in account {account_id}: {e}"
            )

    for template_config in manifest["templates"]:
        template_file = template_config.get("template_file")
        accounts = template_config.get("accounts", [])

        if not template_file:
            continue

        if not accounts:
            continue

        template_path = os.path.join(extracted_dir, template_file)

        try:
            template_content = _read_template_file(template_path)
        except FileNotFoundError:
            continue

        stack_name = _generate_stack_name(template_file)

        for account_id in accounts:
            try:
                session = _assume_role(account_id)
                existing_stacks = account_existing_stacks.get(account_id, {})

                if _deploy_stack(
                    session, template_content, stack_name, account_id, existing_stacks
                ):
                    results["success"].append(f"{template_file}:{account_id}")
                else:
                    results["failed"].append(f"{template_file}:{account_id}")

            except Exception as e:
                logger.error(
                    f"Failed to deploy {template_file} to account {account_id}: {e}"
                )
                results["failed"].append(f"{template_file}:{account_id}")

    logger.info(
        f"Deployment complete. Successful: {len(results['success'])}, Failed: "
        f"{len(results['failed'])}, Deleted: {len(results['deleted'])}"
    )
    if results["success"]:
        logger.info(f"Successful deployments: {results['success']}")
    if results["failed"]:
        logger.warning(f"Failed deployments: {results['failed']}")
    if results["deleted"]:
        logger.info(f"Deleted stacks: {results['deleted']}")

    return results


def handle(event, _):
    try:
        s3_event = event["Records"][0]["s3"]
        bucket = s3_event["bucket"]["name"]
        key = s3_event["object"]["key"]
        logger.info(f"Processing S3 object: {bucket}/{key}")
        extracted_dir = _download_and_extract_zip(bucket, key)
        results = deploy_all(extracted_dir)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Deployment completed",
                    "success": results["success"],
                    "failed": results["failed"],
                    "deleted": results["deleted"],
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error processing deployment: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
