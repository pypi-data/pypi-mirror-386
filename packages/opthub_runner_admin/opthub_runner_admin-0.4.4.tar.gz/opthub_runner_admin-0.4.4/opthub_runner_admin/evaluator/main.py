"""This module is the main module for the evaluator process."""

import json
import logging
import signal
import sys
from time import sleep
from traceback import format_exc

from opthub_runner_admin.args import Args
from opthub_runner_admin.lib.docker_executor import execute_in_docker
from opthub_runner_admin.lib.dynamodb import DynamoDB
from opthub_runner_admin.lib.sqs import EvaluationMessage, EvaluatorSQS
from opthub_runner_admin.models.evaluation import (
    FailedEvaluationCreateParams,
    is_evaluation_exists,
    save_failed_evaluation,
    save_success_evaluation,
)
from opthub_runner_admin.models.exception import ContainerRuntimeError, DockerImageNotFoundError
from opthub_runner_admin.models.match import Match, fetch_match_by_id
from opthub_runner_admin.models.solution import fetch_solution_by_primary_key
from opthub_runner_admin.utils.process import delete_flag_file, is_stop_flag_set
from opthub_runner_admin.utils.time import get_utcnow
from opthub_runner_admin.utils.truncate import truncate_text_center

LOGGER = logging.getLogger(__name__)


def setup_sqs(args: Args) -> EvaluatorSQS:
    """Set up the SQS instance.

    Args:
        args (Args): The arguments for the evaluation process.

    Returns:
        EvaluatorSQS: The SQS instance.
    """
    sqs = EvaluatorSQS(
        {
            "queue_url": args["evaluator_queue_url"],
            "region_name": args["region_name"],
            "aws_access_key_id": args["access_key_id"],
            "aws_secret_access_key": args["secret_access_key"],
        },
    )
    sqs.check_accessible()  # check if the queue is accessible
    sqs.wake_up_visibility_extender()  # wake up the visibility extender
    return sqs


def setup_dynamodb(args: Args) -> DynamoDB:
    """Setup DynamoDB.

    Args:
        args (Args): Args

    Returns:
        DynamoDB: DynamoDB
    """
    # for communication with DynamoDB
    dynamodb = DynamoDB(
        {
            "region_name": args["region_name"],
            "aws_access_key_id": args["access_key_id"],
            "aws_secret_access_key": args["secret_access_key"],
            "table_name": args["table_name"],
        },
    )
    dynamodb.check_accessible()  # check if the table is accessible
    return dynamodb


def get_message_from_queue(sqs: EvaluatorSQS, interval: float, process_name: str) -> EvaluationMessage | None:
    """Get message from the queue.

    Args:
        sqs (ScorerSQS): Scorer SQS
        interval (float): Polling interval.
        process_name (str): The process name.

    Returns:
        EvaluationMessage: Evaluation message
    """
    LOGGER.info("Finding Solution to evaluate...")
    try:
        # Poll the message from the queue
        while True:
            # Check if the stop flag is set while polling the message
            if is_stop_flag_set(process_name):
                msg = f"Stop flag detected. Stop Evaluator on the process {process_name}."
                LOGGER.info(msg)
                LOGGER.info("Deleting the stop flag file...")
                delete_flag_file(process_name)
                LOGGER.info("...Deleted")
                sys.exit(0)

            # Try to get the message from the queue
            message = sqs.get_message_from_queue()

            if message is not None:  # If the message is found, start to evaluate the solution
                break

            sleep(interval)

    except KeyboardInterrupt:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        LOGGER.exception("Error occurred while fetching message from SQS.")
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(1)
    except Exception:
        LOGGER.exception("Error occurred while fetching message from SQS.")
        return None
    else:  # If the message is found, return the message
        LOGGER.debug("Message: %s", message)
        LOGGER.info("...Found")
        return message


def get_match_by_message(process_name: str, message: EvaluationMessage, dev: bool) -> Match | None:
    """Get match from message.

    Args:
        process_name (str): The process name
        message (ScoreMessage): ScoreMessage
        dev (bool): Whether to use the development environment

    Returns:
        Match: Match
    """
    match_id = "Match#" + message["match_id"]
    LOGGER.info("Fetching problem data from GraphQL...")
    try:
        match = fetch_match_by_id(process_name, match_id, dev)
    except KeyboardInterrupt:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        LOGGER.exception("Error occurred while fetching problem data from DB.")
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(1)
    except Exception as error:
        LOGGER.exception("Error occurred while fetching problem data from DB.")
        if isinstance(error, DockerImageNotFoundError):
            sys.exit(1)
        return None
    else:
        LOGGER.debug("Match %s:\n%s", match_id, match)
        LOGGER.info("...Fetched")
        return match


def evaluate(process_name: str, args: Args) -> None:  # noqa: PLR0915, C901, PLR0912
    """The function that controls the evaluation process.

    Args:
        args (Args): The arguments for the evaluation process.
    """
    sqs = setup_sqs(args)
    dynamodb = setup_dynamodb(args)

    n_evaluation = 0

    while True:
        n_evaluation += 1

        if args["num"] > 0 and n_evaluation > args["num"]:
            LOGGER.info("Reached the maximum number of evaluations.")
            break

        LOGGER.info("==================== Evaluation: %d ====================", n_evaluation)

        message = get_message_from_queue(sqs, args["interval"], process_name)

        if message is None:
            continue

        match = get_match_by_message(process_name, message, args["dev"])

        if match is None:
            continue

        if is_evaluation_exists(dynamodb, message["match_id"], message["participant_id"], message["trial_no"]):
            LOGGER.warning("The evaluation already exists.")
            sqs.delete_message_from_queue()
            continue

        try:
            started_at = None
            finished_at = None

            LOGGER.info("Fetching Solution from DB...")
            solution = fetch_solution_by_primary_key(
                dynamodb,
                match["id"],
                message["participant_id"],
                message["trial"],
            )
            LOGGER.debug("Solution: %s", solution)
            LOGGER.info("...Fetched")

            LOGGER.info("Evaluating...")
            started_at = get_utcnow()
            info_msg = "Started at : " + started_at
            LOGGER.info(info_msg)

            evaluation_result = execute_in_docker(
                {
                    "image": match["problem_docker_image"],
                    "environments": match["problem_environments"],
                    "command": args["command"],
                    "timeout": args["timeout"],
                    "rm": args["rm"],
                },
                [json.dumps(solution["variable"]) + "\n"],
            )

            if "error" in evaluation_result:
                msg = "Error occurred while evaluating solution:\n" + evaluation_result["error"]
                raise ContainerRuntimeError(msg)
            if "feasible" not in evaluation_result:
                evaluation_result["feasible"] = None
            if "constraint" not in evaluation_result:
                evaluation_result["constraint"] = None
            if "info" not in evaluation_result:
                evaluation_result["info"] = {}

            LOGGER.debug("Evaluation Result: %s", evaluation_result)

            LOGGER.info("...Evaluated")
            finished_at = get_utcnow()
            info_msg = "Finished at : " + finished_at
            LOGGER.info(info_msg)

            LOGGER.info("Saving Evaluation...")
            save_success_evaluation(
                dynamodb,
                {
                    "match_id": match["id"],
                    "participant_id": message["participant_id"],
                    "trial_no": message["trial_no"],
                    "created_at": get_utcnow(),
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "objective": evaluation_result["objective"],
                    "constraint": evaluation_result["constraint"],
                    "info": evaluation_result["info"],
                    "feasible": evaluation_result["feasible"],
                },
            )
            LOGGER.debug(
                "Evaluation to save: %s",
                {
                    "match_id": match["id"],
                    "participant_id": message["participant_id"],
                    "trial_no": message["trial_no"],
                    "created_at": get_utcnow(),
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "objective": evaluation_result["objective"],
                    "constraint": evaluation_result["constraint"],
                    "info": evaluation_result["info"],
                    "feasible": evaluation_result["feasible"],
                },
            )
            LOGGER.info("...Saved")

            sqs.delete_message_from_queue()

        except (KeyboardInterrupt, Exception) as error:
            if isinstance(error, KeyboardInterrupt):
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                started_at = started_at if started_at is not None else get_utcnow()
                finished_at = finished_at if finished_at is not None else get_utcnow()
                error_msg = format_exc() if isinstance(error, ContainerRuntimeError) else "Internal Server Error"
                admin_error_msg = format_exc()
                LOGGER.exception("Error occurred while evaluating solution.")
                LOGGER.info("Saving Failed Evaluation...")
                failed_evaluation: FailedEvaluationCreateParams = {
                    "match_id": match["id"],
                    "participant_id": message["participant_id"],
                    "trial_no": message["trial_no"],
                    "created_at": get_utcnow(),
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "error_message": truncate_text_center(error_msg, 16384),
                    "admin_error_message": truncate_text_center(admin_error_msg, 16384),
                }
                LOGGER.debug("Evaluation to save: %s", failed_evaluation)
                save_failed_evaluation(dynamodb, failed_evaluation)
                LOGGER.info("...Saved")
                sqs.delete_message_from_queue()
            except Exception:
                LOGGER.exception("Error occurred while handling failed evaluation.")
                LOGGER.exception(format_exc())
            if isinstance(error, KeyboardInterrupt):
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                sys.exit(1)
            continue
