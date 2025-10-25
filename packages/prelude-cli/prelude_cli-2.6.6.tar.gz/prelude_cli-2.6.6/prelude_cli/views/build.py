import importlib.resources as pkg_resources
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path, PurePath

import click

import prelude_cli.templates as templates
from prelude_cli.views.shared import Spinner, pretty_print
from prelude_sdk.controllers.build_controller import BuildController
from prelude_sdk.models.codes import Control, EDRResponse


UUID = re.compile(
    "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"
)


@click.group()
@click.pass_context
def build(ctx):
    """Custom security tests"""
    ctx.obj = BuildController(account=ctx.obj)


@build.command("clone-test")
@click.argument("source-test-id")
@click.pass_obj
@pretty_print
def clone_test(controller, source_test_id):
    """Clone a security test"""

    with Spinner(description="Creating new test"):
        return controller.clone_test(
            source_test_id=source_test_id,
        )


@build.command("create-test")
@click.argument("name")
@click.option("-u", "--unit", required=True, help="unit identifier", type=str)
@click.option("-t", "--test", help="test identifier", default=None, type=str)
@click.option(
    "-q", "--technique", help="MITRE ATT&CK code [e.g. T1557]", default=None, type=str
)
@click.pass_obj
@pretty_print
def create_test(controller, name, unit, test, technique):
    """Create a security test"""

    def create_template(template, name):
        template_body = pkg_resources.read_text(templates, template)
        template_body = template_body.replace("$ID", res["id"])
        template_body = template_body.replace("$NAME", res["name"])
        template_body = template_body.replace("$UNIT", res["unit"])
        template_body = template_body.replace("$TECHNIQUE", res["technique"] or "")
        template_body = template_body.replace("$TIME", str(datetime.now(timezone.utc)))

        with Spinner(description="Applying default template to new test"):
            controller.upload(
                test_id=res["id"], filename=name, data=template_body.encode("utf-8")
            )
            res["attachments"] += [name]

        dir = PurePath(res["id"], name)

        with open(dir, "w", encoding="utf8") as code:
            code.write(template_body)

    with Spinner(description="Creating new test"):
        res = controller.create_test(
            name=name, unit=unit, test_id=test, technique=technique
        )

    if not test:
        Path(res["id"]).mkdir(parents=True, exist_ok=True)
        create_template(template="README.md", name="README.md")
        create_template(template="template.go", name=f'{res["id"]}.go')
    return res


@build.command("update-test")
@click.argument("test")
@click.option(
    "-c",
    "--crowdstrike_expected",
    help="Crowdstrike expected outcome",
    type=click.Choice(
        [c.name for c in EDRResponse if c != EDRResponse.INVALID], case_sensitive=False
    ),
)
@click.option("-n", "--name", help="test name", default=None, type=str)
@click.option("-u", "--unit", help="unit identifier", default=None, type=str)
@click.option(
    "-q", "--technique", help="MITRE ATT&CK code [e.g. T1557]", default=None, type=str
)
@click.pass_obj
@pretty_print
def update_test(controller, test, crowdstrike_expected, name, unit, technique):
    """Update a security test"""
    with Spinner(description="Updating test"):
        return controller.update_test(
            test_id=test,
            crowdstrike_expected_outcome=(
                EDRResponse[crowdstrike_expected] if crowdstrike_expected else None
            ),
            name=name,
            unit=unit,
            technique=technique,
        )


@build.command("delete-test")
@click.argument("test")
@click.option("-p", "--purge", is_flag=True, help="purge test and associated files")
@click.confirmation_option(prompt="Are you sure?")
@click.pass_obj
@pretty_print
def delete_test(controller, test, purge):
    """Delete a test"""
    with Spinner(description="Removing test"):
        return controller.delete_test(test_id=test, purge=purge)


@build.command("compile-code-file")
@click.argument("path", type=click.Path(exists=True))
@click.option("-s", "--source-test-id", help="Include source test attachments")
@click.pass_obj
@pretty_print
def compile_code_file(controller, path, source_test_id):
    """Test compile a go file, with test attachments if needed."""

    with Spinner(description="Compiling code test") as spinner:
        with open(path, "rb") as data:
            data = controller.compile_code_string(
                code=data.read(),
                source_test_id=source_test_id,
            )
            if compile_job_id := data.get("job_id"):
                spinner.update(spinner.task_ids[-1], description="Compiling")
                while (
                    result := controller.get_compile_status(compile_job_id)
                ) and result["status"] == "RUNNING":
                    time.sleep(2)
                if result["status"] == "FAILED":
                    result["error"] = "Failed to compile"
                data |= result
    return data


@build.command("undelete-test")
@click.argument("test")
@click.pass_obj
@pretty_print
def undelete_test(controller, test):
    """Undelete a test"""
    with Spinner(description="Restoring test"):
        return controller.undelete_test(test_id=test)


@build.command("upload")
@click.argument("path", type=click.Path(exists=True))
@click.option("-t", "--test", help="test identifier", default=None, type=str)
@click.pass_obj
@pretty_print
def upload_attachment(controller, path, test):
    """Upload a test attachment from disk"""

    def test_id():
        match = UUID.search(path)
        if match:
            return match.group(0)
        raise FileNotFoundError("You must supply a test ID or include it in the path")

    def upload(p: Path, skip_compile=False):
        if not p.is_file():
            return

        with open(p, "rb") as data:
            with Spinner(description="Uploading to test") as spinner:
                data = controller.upload(
                    test_id=identifier,
                    filename=p.name,
                    data=data.read(),
                    skip_compile=skip_compile,
                )
                if data.get("compile_job_id"):
                    spinner.update(spinner.task_ids[-1], description="Compiling")
                    while (
                        result := controller.get_compile_status(data["compile_job_id"])
                    ) and result["status"] == "RUNNING":
                        time.sleep(2)
                    if result["status"] == "FAILED":
                        result["error"] = "Failed to compile"
                    data |= result
            res.append(data)

    res = []
    identifier = test or test_id()

    if Path(path).is_file():
        upload(p=Path(path))
    else:
        objs = list(Path(path).glob("*"))
        for ind, obj in enumerate(objs):
            try:
                upload(p=Path(obj), skip_compile=ind != len(objs) - 1)
            except ValueError as e:
                res.append(dict(status="FAILED", reason=e.args[0]))
    return res


@build.command("create-threat")
@click.argument("name")
@click.option(
    "-p", "--published", help="date the threat was published", required=True, type=str
)
@click.option("--id", help="identifier", type=str)
@click.option(
    "-s", "--source", help="source of threat (ex. www.cisa.gov)", default=None, type=str
)
@click.option(
    "-i",
    "--source_id",
    help="ID of the threat, per the source (ex. aa23-075a)",
    default=None,
    type=str,
)
@click.option(
    "-t", "--tests", help="comma-separated list of test IDs", default=None, type=str
)
@click.option(
    "-d",
    "--directory",
    help="directory containing tests, detections, and hunt queries generated from threat_intel",
    default=None,
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.pass_obj
@pretty_print
def create_threat(controller, name, published, id, source_id, source, tests, directory):
    """Create a security threat"""
    with Spinner(description="Creating new threat"):
        try:
            created_tests = []
            test_uploads = []
            created_detections = []
            created_queries = []
            threat = None
            if directory:
                for technique_dir in os.listdir(directory):
                    with open(f"{directory}/{technique_dir}/config.json", "r") as f:
                        config = json.load(f)
                        test = controller.create_test(
                            name=config["name"],
                            unit=config["unit"],
                            technique=config["technique"],
                        )
                        created_tests.append(test)
                    with open(f"{directory}/{technique_dir}/test.go", "r") as f:
                        go_code = f.read()
                        test_uploads.append(
                            controller.upload(
                                test_id=test["id"],
                                filename=f'{test["id"]}.go',
                                data=go_code.encode(),
                            )
                        )
                    for sigma_file in Path(f"{directory}/{technique_dir}").glob(
                        "sigma*"
                    ):
                        with open(sigma_file, "r") as f:
                            rule = f.read()
                            created_detections.append(
                                controller.create_detection(
                                    rule=rule, test_id=test["id"]
                                )
                            )
                    for query_file in Path(f"{directory}/{technique_dir}").glob(
                        "query*"
                    ):
                        with open(query_file, "r") as f:
                            query = json.load(f)
                            created_queries.append(
                                controller.create_threat_hunt(
                                    name=query["name"],
                                    query=query["query"],
                                    test_id=test["id"],
                                )
                            )
                tests = ",".join([t["id"] for t in created_tests])
            threat = controller.create_threat(
                name=name,
                threat_id=id,
                source_id=source_id,
                source=source,
                published=published,
                tests=tests,
            )
        except FileNotFoundError as e:
            raise Exception(e)
        finally:
            return dict(
                threat=threat,
                created_tests=created_tests,
                test_uploads=test_uploads,
                created_detections=created_detections,
                created_threat_hunt_queries=created_queries,
            )


@build.command("update-threat")
@click.argument("threat")
@click.option("-n", "--name", help="test name", default=None, type=str)
@click.option(
    "-s", "--source", help="source of threat (ex. www.cisa.gov)", default=None, type=str
)
@click.option(
    "-i",
    "--source_id",
    help="ID of the threat, per the source (ex. aa23-075a)",
    default=None,
    type=str,
)
@click.option(
    "-p", "--published", help="date the threat was published", default=None, type=str
)
@click.option(
    "-t", "--tests", help="comma-separated list of test IDs", default=None, type=str
)
@click.pass_obj
@pretty_print
def update_threat(controller, threat, name, source_id, source, published, tests):
    """Create or update a security threat"""
    with Spinner(description="Updating threat"):
        return controller.update_threat(
            threat_id=threat,
            source_id=source_id,
            name=name,
            source=source,
            published=published,
            tests=tests,
        )


@build.command("delete-threat")
@click.argument("threat")
@click.option("-p", "--purge", is_flag=True, help="purge threat")
@click.confirmation_option(prompt="Are you sure?")
@click.pass_obj
@pretty_print
def delete_threat(controller, threat, purge):
    """Delete a threat"""
    with Spinner(description="Removing threat"):
        return controller.delete_threat(threat_id=threat, purge=purge)


@build.command("undelete-threat")
@click.argument("threat")
@click.pass_obj
@pretty_print
def undelete_threat(controller, threat):
    """Undelete a threat"""
    with Spinner(description="Restoring threat"):
        return controller.undelete_threat(threat_id=threat)


@build.command("create-detection")
@click.argument("sigma_rule_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-t", "--test", help="ID of the test this detection is for", required=True, type=str
)
@click.option("--detection_id", help="detection ID", default=None, type=str)
@click.option("--rule_id", help="rule ID", default=None, type=str)
@click.pass_obj
@pretty_print
def create_detection(controller, sigma_rule_file, test, detection_id, rule_id):
    """Create a detection rule"""
    with Spinner(description="Creating new detection"):
        with open(sigma_rule_file, "r") as f:
            rule = f.read()
        return controller.create_detection(
            rule=rule, test_id=test, detection_id=detection_id, rule_id=rule_id
        )


@build.command("update-detection")
@click.argument("detection")
@click.option(
    "--sigma_rule_file",
    help="Sigma rule, from a yaml file",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "-t", "--test", help="ID of the test this detection is for", default=None, type=str
)
@click.pass_obj
@pretty_print
def update_detection(controller, detection, sigma_rule_file, test):
    """Update a detection"""
    with Spinner(description="Updating detection"):
        with open(sigma_rule_file, "r") as f:
            rule = f.read()
        return controller.update_detection(
            rule=rule,
            test_id=test,
            detection_id=detection,
        )


@build.command("delete-detection")
@click.argument("detection")
@click.confirmation_option(prompt="Are you sure?")
@click.pass_obj
@pretty_print
def delete_detection(controller, detection):
    """Delete a detection"""
    with Spinner(description="Removing detection"):
        return controller.delete_detection(detection_id=detection)


@build.command("create-threat-hunt")
@click.argument("name")
@click.option(
    "-c",
    "--control",
    help="",
    required=True,
    type=click.Choice(
        [Control.CROWDSTRIKE.name, Control.DEFENDER.name], case_sensitive=False
    ),
)
@click.option("-q", "--query", help="Threat hunt query", required=True, type=str)
@click.option(
    "-t",
    "--test",
    help="ID of the test this threat hunt query is for",
    required=True,
    type=str,
)
@click.option("--id", default=None, type=str)
@click.pass_obj
@pretty_print
def create_threat_hunt(controller, name, control, query, test, id):
    """Create a threat hunt query"""
    with Spinner(description="Creating new threat hunt"):
        return controller.create_threat_hunt(
            control=Control[control],
            name=name,
            query=query,
            test_id=test,
            threat_hunt_id=id,
        )


@build.command("update-threat-hunt")
@click.argument("threat_hunt")
@click.option("-n", "--name", help="Name of this threat hunt query", type=str)
@click.option("-q", "--query", help="Threat hunt query", type=str)
@click.option(
    "-t", "--test", help="ID of the test this threat hunt query is for", type=str
)
@click.pass_obj
@pretty_print
def update_threat_hunt(controller, threat_hunt, name, query, test):
    """Update a threat hunt"""
    with Spinner(description="Updating threat hunt"):
        return controller.update_threat_hunt(
            name=name,
            query=query,
            test_id=test,
            threat_hunt_id=threat_hunt,
        )


@build.command("delete-threat-hunt")
@click.argument("threat_hunt")
@click.confirmation_option(prompt="Are you sure?")
@click.pass_obj
@pretty_print
def delete_threat_hunt(controller, threat_hunt):
    """Delete a threat hunt"""
    with Spinner(description="Removing threat hunt"):
        return controller.delete_threat_hunt(threat_hunt_id=threat_hunt)
