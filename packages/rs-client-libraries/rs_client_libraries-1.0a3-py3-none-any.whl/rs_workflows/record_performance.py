# Copyright 2025 CS Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module with task used to insert or update flow run table."""

import os
import re
import sys
from datetime import datetime
from importlib.metadata import version

from prefect import get_run_logger, runtime, task
from sqlalchemy import MetaData, Table, create_engine, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker


def get_db_session():
    """Initialize and return a DB session."""
    try:
        db_url = (
            f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
            f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
            f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_PI_DB']}"
        )
    except KeyError as e:
        # Fail fast with a clearer error message
        raise KeyError(f"Missing environment variable for DB connection: {e}") from e

    engine = create_engine(db_url, pool_pre_ping=True)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session(), engine


def resolve_param(param_value, runtime_key, default):
    """Return param_value if set, else runtime parameter, else default."""
    if param_value is not None:
        return param_value
    runtime_val = runtime.flow_run.parameters.get(runtime_key)
    return runtime_val if runtime_val is not None else default


def get_flow_run_id(prefect_flow_id: str) -> int | None:
    """Return id from flow_run table for given prefect_flow_id."""

    logger = get_run_logger()
    db, engine = get_db_session()
    try:
        logger.info(f"Connecting to DB with engine: {engine}")

        metadata = MetaData()
        flow_run = Table("flow_run", metadata, autoload_with=engine)
        logger.info("Loaded flow_run table metadata")

        logger.info(f"Looking up flow_run.id for prefect_flow_id={prefect_flow_id}")
        row = db.execute(select(flow_run.c.id).where(flow_run.c.prefect_flow_id == prefect_flow_id)).fetchone()

        if row:
            logger.info(f"Found flow_run.id={row[0]} for prefect_flow_id={prefect_flow_id}")
            return row[0]
        logger.warning(f"No record found in flow_run for prefect_flow_id={prefect_flow_id}")
        return None

    except Exception as e:
        logger.error(f"Error while fetching flow_run.id for prefect_flow_id={prefect_flow_id}: {e}")
        raise
    finally:
        db.close()
        logger.info("DB session closed")


def get_pi_category_id(eopf_type: str) -> int | None:
    """
    Return id from pi_category table based on eopf_type.

    Mapping rules (example):
        - S01* -> mission='S1', name='L12-NRT'
        - S02* -> mission='S2', name='L1C'
        - S03* -> mission='S3', name='NRT'

        "S01SIWOCN": 5,  # Level-1/2 IW/GRD Sentinel-1
        "S01SIWV": 6,    # Level-2 Wave Sentinel-1
        "S02L1C": 9,     # Level-1C Sentinel-2
        "S02L2A": 10,    # Level-2A Sentinel-2
        "S03NRT": 12     # All NRT Sentinel-3
    """
    logger = get_run_logger()
    db, engine = get_db_session()

    try:
        logger.info(f"Connecting to DB with engine: {engine}")

        metadata = MetaData()
        pi_category = Table("pi_category", metadata, autoload_with=engine)
        logger.info("Loaded pi_category table metadata")

        # Determine mission and name based on eopf_type
        mission = None
        name = None
        if eopf_type.startswith("S01"):
            mission = "S1"
            name = "L12-NRT"  # Level-1/2 EW/IW/SM
        elif eopf_type.startswith("S02"):
            mission = "S2"
            name = "L1C"
        elif eopf_type.startswith("S03"):
            mission = "S3"
            name = "NRT"

        if mission is None or name is None:
            logger.warning(f"No mapping found for eopf_type={eopf_type}")
            return None

        logger.info(f"Looking up pi_category.id for mission={mission}, name={name}")
        row = db.execute(
            select(pi_category.c.id).where((pi_category.c.mission == mission) & (pi_category.c.name == name)),
        ).fetchone()

        if row:
            logger.info(f"Found pi_category.id={row[0]} for eopf_type={eopf_type}")
            return row[0]

        logger.warning(f"No record found in pi_category for eopf_type={eopf_type}")
        return None

    except Exception as e:
        logger.error(f"Error while fetching pi_category.id for eopf_type={eopf_type}: {e}")
        raise
    finally:
        db.close()
        logger.info("DB session closed")


def record_flow_run(
    start_date: datetime | str | None = None,
    stop_date: datetime | str | None = None,
    status: str | None = None,
    flow_run_type: str | None = None,
    mission: str | None = None,
    dpr_processor_name: str | None = None,
    dpr_processor_version: str | None = None,
    dpr_processor_unit: str | None = None,
    dpr_processing_input_stac_items: str | None = None,
):
    """Insert or update a record in flow_run table and return the DB id."""

    logger = get_run_logger()
    metadata = MetaData()
    db, engine = get_db_session()
    flow_run = Table("flow_run", metadata, autoload_with=engine)

    prefect_flow_id = runtime.flow_run.id

    # Check if record exists
    existing = db.execute(select(flow_run.c.id).where(flow_run.c.prefect_flow_id == prefect_flow_id)).fetchone()

    if not existing:
        # Insert new record with RETURNING id
        values = {
            "flow_type": resolve_param(flow_run_type, "flow_run_type", "systematic"),
            "mission": resolve_param(mission, "mission", "sentinel-1"),
            "prefect_flow_id": prefect_flow_id,
            "prefect_flow_parent_id": runtime.flow_run.parent_flow_run_id,
            "dask_version": version("dask"),
            "python_version": sys.version.split()[0],
            "dpr_processor_name": resolve_param(dpr_processor_name, "dpr_processor_name", "dpr_processor"),
            "dpr_processor_version": resolve_param(
                dpr_processor_version,
                "dpr_processor_version",
                "v1.0",
            ),
            "dpr_processor_unit": resolve_param(dpr_processor_unit, "dpr_processor_unit", "DPR_PU"),
            "dpr_processing_input_stac_items": resolve_param(
                dpr_processing_input_stac_items,
                "dpr_processing_input_stac_items",
                "{'dpr_processing_input_stac_items': 'value'}",
            ),
            "dpr_processing_start_datetime": start_date,
            "dpr_processing_stop_datetime": stop_date,
            "dpr_processing_status": status,
            "excluded_from_pi": False,
        }
        stmt = insert(flow_run).values(**values).returning(flow_run.c.id)
        flow_run_id = db.execute(stmt).scalar()
        logger.info(f"Inserted new flow_run record with id={flow_run_id}")

    else:
        flow_run_id = existing[0]
        # Update only selected fields if provided
        update_values = {}
        if start_date is not None:
            update_values["dpr_processing_start_datetime"] = start_date
        if stop_date is not None:
            update_values["dpr_processing_stop_datetime"] = stop_date
        if status is not None:
            update_values["dpr_processing_status"] = status

        if update_values:
            stmt = (
                update(flow_run)
                .where(flow_run.c.prefect_flow_id == prefect_flow_id)
                .values(**update_values)  # type: ignore
            )
            db.execute(stmt)
            logger.info(f"Updated flow_run {prefect_flow_id} with {update_values}")

    db.commit()
    logger.info(f"Successfully inserted / updated flow_run with id={flow_run_id}")
    return flow_run_id


def record_product_realised(flow_run_id, stac_items):
    """Insert records in product_realised table"""
    logger = get_run_logger()
    metadata = MetaData()
    db, engine = get_db_session()
    product_realised = Table("product_realised", metadata, autoload_with=engine)

    if not stac_items:
        logger.info("No STAC items provided — skipping insert into product_realised.")
        return

    try:
        for dpr_product in stac_items:
            stac_discovery = dpr_product["stac_discovery"]
            eopf_type = stac_discovery["properties"]["product:type"]

            values = {
                "flow_run_id": flow_run_id,
                "pi_category_id": get_pi_category_id(eopf_type),
                "eopf_type": eopf_type,
                "stac_item": stac_discovery,
                # get it from properties instead of product name, now() if missing
                "sensing_start_datetime": stac_discovery["properties"].get("start_datetime", datetime.now()),
                "origin_date": stac_discovery["properties"].get("datetime", datetime.now()),
                "catalog_stored_datetime": datetime.now(),
                # default to false, will be updated by validate
                "unexpected": False,
                "on_time_0_day": False,
                "on_time_1_day": False,
                "on_time_2_day": False,
                "on_time_3_day": False,
                "on_time_7_day": False,
            }
            # no upsert, only insert each element from dpr output
            stmt = insert(product_realised).values(**values)
            db.execute(stmt)
            logger.info(f"Inserted product_realised for flow_run_id={flow_run_id}")

        db.commit()

    except KeyError as ker:
        db.rollback()
        logger.error(f"Key error while unpacking DPR product: {ker}")
        raise

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in record_product_realised: {e}")
        raise

    finally:
        db.close()


def extract_min_datetime(list_items):
    """Finds the earliest datetime to insert in column sensing_start_datetime of product_expected."""

    datetime_patterns = [(re.compile(r"\d{8}T\d{6}"), "%Y%m%dT%H%M%S"), (re.compile(r"\d{20}"), "%Y%m%d%H%M%S%f")]
    earliest = None

    for item in list_items:
        for pattern, fmt in datetime_patterns:
            match = pattern.search(item)
            if match:
                try:
                    dt = datetime.strptime(match.group(), fmt)
                    if earliest is None or dt < earliest:
                        earliest = dt
                    break
                except ValueError:
                    continue

    return earliest


def record_product_expected(flow_run_id: str, dpr_processor_name, payload):
    """Insert hardcoded records in product_expected table by flow_run_id."""

    logger = get_run_logger()
    metadata = MetaData()
    db, engine = get_db_session()
    product_expected = Table("product_expected", metadata, autoload_with=engine)

    eopf_type_dict = []
    # products expected for S3 Level 0
    if dpr_processor_name == "s3_l0":
        eopf_type_dict = [
            ("S03DORDOP", 1, 1),
            ("S03DORNAV", 1, 1),
            ("S03GNSL0_", 1, 1),
            ("S03MWRL0_", 3, 3),
            ("S03OLCCR0", 0, 1),
            ("S03OLCCR1", 0, 1),
            ("S03OLCL0_", 23, 23),
            ("S03SLSL0_", 15, 22),
            ("S03ALTL0_", 12, 13),
            ("S03SRCRL0", 0, 1),
            ("S03HKML0_", 2, 2),
            ("S03NATL0_", 2, 2),
        ]
    else:
        return

    eopf_type_lookup = {k: (min_c, max_c) for k, min_c, max_c in eopf_type_dict}

    list_eopf_types = list(payload["workflow"][0]["outputs"].values())
    list_items = list((payload["workflow"][0]["inputs"]).values())
    min_val = extract_min_datetime(list_items)

    try:
        for eopf_type in list_eopf_types:

            try:
                min_c, max_c = eopf_type_lookup[eopf_type]
            except KeyError:
                logger.error(f"EOPF type '{eopf_type}' not found in eopf_type_lookup.")
                raise
            except Exception as e:
                logger.exception(f"Unexpected error accessing eopf_type_lookup with key '{eopf_type}': {e}")
                raise

            values = {
                "flow_run_id": flow_run_id,
                "pi_category_id": get_pi_category_id(eopf_type),
                "eopf_type": eopf_type,
                "sensing_start_datetime": min_val,
                "min_count": min_c,
                "max_count": max_c,
            }

            existing = db.execute(
                select(product_expected.c.id).where(
                    (product_expected.c.flow_run_id == flow_run_id) & (product_expected.c.eopf_type == eopf_type),
                ),
            ).fetchone()

            if not existing:
                stmt = insert(product_expected).values(**values)  # type: ignore
                db.execute(stmt)
                logger.info(f"Inserted product_expected for flow_run_id={flow_run_id} for eopf_type={eopf_type}")

            db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error in record_product_expected: {e}")
        raise
    finally:
        db.close()


def validate_products(flow_run_id: str):
    """Validate realised vs expected products for a given flow_run_id.
    : running multiple times won't duplicate inserts/updates.
    """

    logger = get_run_logger()
    metadata = MetaData()
    db, engine = get_db_session()

    # get all involved tables in rspy 743
    product_expected = Table("product_expected", metadata, autoload_with=engine)
    product_realised = Table("product_realised", metadata, autoload_with=engine)
    product_missing = Table("product_missing", metadata, autoload_with=engine)

    try:
        # get expected products:  type min / max count
        expected_rows = db.execute(
            select(
                product_expected.c.eopf_type,
                product_expected.c.min_count,
                product_expected.c.max_count,
            ).where(product_expected.c.flow_run_id == flow_run_id),
        ).fetchall()

        # step 1: validate each expected type
        for row in expected_rows:
            eopf_type, min_count, max_count = row

            realised_count = db.execute(
                select(func.count())  # pylint: disable = not-callable
                .select_from(product_realised)
                .where(
                    product_realised.c.flow_run_id == flow_run_id,
                    product_realised.c.eopf_type == eopf_type,
                ),
            ).scalar()

            logger.debug(f"eopf_type={eopf_type}, expected {min_count}-{max_count}, realised={realised_count}")

            if realised_count < min_count:
                # case 1 fill product_missing table
                missing_count = min_count - realised_count

                # check if already inserted
                exists_missing = db.execute(
                    select(product_missing.c.id).where(
                        product_missing.c.flow_run_id == flow_run_id,
                        product_missing.c.eopf_type == eopf_type,
                    ),
                ).fetchone()

                if not exists_missing:
                    # try to retrieve pi_category_id and sensing_start_datetime from product_realised
                    realised_info = db.execute(
                        select(
                            product_realised.c.pi_category_id,
                            product_realised.c.sensing_start_datetime,
                        )
                        .where(
                            product_realised.c.flow_run_id == flow_run_id,
                            product_realised.c.eopf_type == eopf_type,
                        )
                        .limit(1),
                    ).fetchone()

                    if realised_info:
                        pi_category_id, sensing_start_datetime = realised_info
                    else:
                        pi_category_id, sensing_start_datetime = None, None
                        logger.warning(
                            f"No realised info found for {eopf_type}, leaving category and start_datetime as NULL",
                        )

                    stmt = insert(product_missing).values(
                        flow_run_id=flow_run_id,
                        eopf_type=eopf_type,
                        count=missing_count,
                        pi_category_id=pi_category_id,
                        sensing_start_datetime=sensing_start_datetime,
                    )
                    db.execute(stmt)
                    logger.warning(
                        f"Missing products for {eopf_type}: inserted {missing_count} into product_missing "
                        f"(pi_category_id={pi_category_id}, sensing_start_datetime={sensing_start_datetime})",
                    )
                else:
                    logger.info(f"Missing products for {eopf_type} already recorded, skipping insert")

            elif realised_count > max_count:
                # case 2: update 'product_realised.unexpected'
                stmt = (
                    update(product_realised)  # type: ignore
                    .where(
                        product_realised.c.flow_run_id == flow_run_id,
                        product_realised.c.eopf_type == eopf_type,
                        product_realised.c.unexpected.is_(False),
                    )
                    .values(unexpected=True)
                )
                result = db.execute(stmt)
                if result.rowcount > 0:
                    logger.error(f"Too many products for {eopf_type}: marked all as unexpected")
                else:
                    logger.info(f"Too many products for {eopf_type} already marked, skipping update")

        # step 2: check realised types without expected
        realised_types = db.execute(
            select(product_realised.c.eopf_type).distinct().where(product_realised.c.flow_run_id == flow_run_id),
        ).fetchall()

        realised_types = [r[0] for r in realised_types]
        expected_types = [r[0] for r in expected_rows]

        extra_types = set(realised_types) - set(expected_types)
        for eopf_type in extra_types:
            stmt = (
                update(product_realised)  # type: ignore
                .where(
                    product_realised.c.flow_run_id == flow_run_id,
                    product_realised.c.eopf_type == eopf_type,
                    product_realised.c.unexpected.is_(False),
                )
                .values(unexpected=True)
            )
            result = db.execute(stmt)
            if result.rowcount > 0:
                logger.error(f"Unexpected product type {eopf_type}: marked all as unexpected")
            else:
                logger.info(f"Unexpected product type {eopf_type} already marked, skipping update")

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error in validate_products: {e}")
        raise
    finally:
        db.close()


@task
def record_performance_indicators(
    # flow_run params
    start_date: datetime | str | None = None,
    stop_date: datetime | str | None = None,
    status: str | None = None,
    flow_run_type: str | None = None,
    mission: str | None = None,
    dpr_processor_name: str | None = None,
    dpr_processor_version: str | None = None,
    dpr_processor_unit: str | None = None,
    dpr_processing_input_stac_items: str | None = None,
    payload: dict | None = None,
    # product_realised params
    stac_items=None,
):
    """Main task that orchestrates DB recording for flow_run and product_realised."""

    logger = get_run_logger()
    logger.info("Starting record_performance_indicators")

    db, _ = get_db_session()

    try:
        flow_run_id = record_flow_run(
            start_date,
            stop_date,
            status,
            flow_run_type,
            mission,
            dpr_processor_name,
            dpr_processor_version,
            dpr_processor_unit,
            dpr_processing_input_stac_items,
        )
        record_product_expected(flow_run_id, dpr_processor_name, payload)

        record_product_realised(flow_run_id, stac_items)

        validate_products(flow_run_id)
        logger.info("Transaction committed successfully!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error in record_performance_indicators: {e}")
        raise
    finally:
        db.close()
