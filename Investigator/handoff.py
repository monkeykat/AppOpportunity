"""Import an explicit JSON export of Phase 1 opportunities into Phase 2."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from database import get_connection, init_database


OPPORTUNITY_FIELDS = (
    "app_id",
    "app_name",
    "developer",
    "url",
    "description",
    "category",
    "rating",
    "review_count",
    "install_count",
    "score",
    "reason",
)


def import_opportunities(records: Iterable[Dict[str, Any]], database_path: Path = None) -> int:
    """Copy opportunity records from an export without touching Scout."""
    init_database(database_path)
    imported = 0
    with get_connection(database_path) as connection:
        for record in records:
            missing = [field for field in ("app_id", "score") if field not in record]
            if missing:
                raise ValueError("Opportunity is missing required field(s): " + ", ".join(missing))
            values = [record.get(field) for field in OPPORTUNITY_FIELDS]
            connection.execute(
                """
                INSERT INTO opportunities ({}) VALUES ({})
                ON CONFLICT(app_id) DO UPDATE SET
                    app_name = excluded.app_name,
                    developer = excluded.developer,
                    url = excluded.url,
                    description = excluded.description,
                    category = excluded.category,
                    rating = excluded.rating,
                    review_count = excluded.review_count,
                    install_count = excluded.install_count,
                    score = excluded.score,
                    reason = excluded.reason
                """.format(", ".join(OPPORTUNITY_FIELDS), ", ".join("?" for _ in OPPORTUNITY_FIELDS)),
                values,
            )
            imported += 1
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a Phase 1 opportunity JSON export into Phase 2.")
    parser.add_argument("export", type=Path, help="JSON file containing an array of opportunity records")
    parser.add_argument("--database", type=Path, help="Optional Phase 2 database path")
    args = parser.parse_args()
    records = json.loads(args.export.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("The export must contain a JSON array")
    print("Imported {} opportunities.".format(import_opportunities(records, args.database)))


if __name__ == "__main__":
    main()