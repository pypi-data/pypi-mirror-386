from pco_calendar.api import api
from axis_vapix.device import a1001
import yaml
import os
import dotenv
import schedule
import logging
import time


data = {}


def init():

    global data

    logging.basicConfig()
    data["logger"] = logging.getLogger("groundsman")
    data["logger"].setLevel(level=logging.DEBUG)

    data["logger"].info("Loading Config...")
    dotenv.load_dotenv()

    config = os.environ.get("GROUNDSMAN_CONFIG")

    if not config:
        config = "/etc/groundsman/grounds.yml"

    config = yaml.safe_load(open(config))

    for key in config.keys():
        data[key] = config[key]

    data["logger"].info("Initializing Planning Center API...")

    data["pco"]["api"] = api(
        user=data["pco"]["user"],
        password=data["pco"]["password"],
    )

    for tag in data["pco"]["tags"]:

        data["pco"]["api"].calendar.tags[tag].enabled = True
        data["pco"]["tags_lower"] = tag.lower()

    data["logger"].info("Initializing Axis Controller...")

    data["controller"]["api"] = a1001(
        host=data["controller"]["host"],
        user=data["controller"]["user"],
        password=data["controller"]["password"],
        removal_limit=data["controller"]["removal_limit"],
    )

    if (
        "postfix_pattern" not in data["controller"].keys()
        or data["controller"]["postfix_pattern"] != ""
    ):
        data["controller"]["postfix_pattern"] = " %Y %m"

    data["logger"].info("...Initialization Completed")


def pull():

    global data
    data["logger"].info("Starting Poll...")

    data["pco"]["events"] = {}

    data["logger"].info("Pulling New Events from Planning Center...")
    for tag in data["pco"]["tags"]:

        data["pco"]["api"].calendar.tags[tag].limit = data["pco"]["day_limit"]

        data["pco"]["events"][tag] = (
            data["pco"]["api"].calendar.tags[tag].get_newevents()
        )

    data["logger"].info("Pulling Schedules from Axis Controller...")
    for token in data["controller"]["api"].schedule.schedules.keys():

        if token.split("_")[0].lower() in data["pco"]["tags_lower"]:

            data["controller"]["api"].schedule.schedules[token].enabled = True

            data["controller"]["api"].schedule.schedules[token].get_schedule()

    data["logger"].info("Pulling Lock Schedules from Axis Controller...")
    for door in data["controller"]["doors"]:

        data["controller"]["api"].doorcontrol.doors[door["name"]].get_unlockschedules()

    data["logger"].info("...Pulling Completed")


def push():

    global data
    pull()

    data["logger"].info("Pushing New Events to Schedules on Axis Controller...")
    for door in data["controller"]["doors"]:

        data["logger"].debug("Updating Door " + door["name"] + "...")

        for tag in door["tags"]:

            data["logger"].debug("Processing Tag " + tag + "...")

            for event in data["pco"]["events"][tag]:

                postfix = event.starts_at.strftime(
                    data["controller"]["postfix_pattern"]
                )

                schedule_name = tag + postfix
                schedule_token = schedule_name.lower().replace(" ", "_")

                if (
                    schedule_token
                    not in data["controller"]["api"].schedule.schedules.keys()
                ):
                    data["logger"].debug("Creating Schedule " + schedule_name + "...")

                    data["controller"]["api"].schedule.create_schedule(
                        name=schedule_name, token=schedule_token
                    )

                status = (
                    data["controller"]["api"]
                    .schedule.schedules[schedule_token]
                    .add_event(
                        name=event.name, start=event.starts_at, end=event.ends_at
                    )
                )

                if status == 0:

                    data["logger"].debug(
                        "Created Event "
                        + event.name
                        + " starting at "
                        + event.starts_at.strftime("%m-%d-%Y, %H:%M:%S")
                        + " and ending at "
                        + event.ends_at.strftime("%m-%d-%Y, %H:%M:%S")
                    )

                status = (
                    data["controller"]["api"]
                    .doorcontrol.doors[door["name"]]
                    .set_unlockschedules(token=schedule_token, reset=False)
                )

                if status == 0:

                    data["logger"].debug(
                        "Updated Unlock Schedules for Door " + door["name"]
                    )

    data["logger"].info("...Finished Updating Events on Axis Controller")


def purge():

    global data
    pull()

    data["logger"].debug("Removing Old Events from Schedule on Axis Controller...")

    data["controller"]["api"].schedule.remove_pastschedules()

    data["logger"].debug("...Finished removing Events from Axis Controller")


def app():

    global data

    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s", datefmt="%m/%d/%Y %H:%M:%S"
    )

    init()

    schedule_logger = logging.getLogger("schedule")
    schedule_logger.setLevel(
        level=logging.getLevelName(data["groundsman"]["logs"]["level"])
    )

    for t in data["groundsman"]["init"]:
        schedule.every().day.at(t).do(init)

    for t in data["groundsman"]["purge"]:
        schedule.every().day.at(t).do(purge)

    schedule.every(data["groundsman"]["push"]).minutes.do(push)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    app()
