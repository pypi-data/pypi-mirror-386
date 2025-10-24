import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from jupyter_server.base.handlers import APIHandler
import tornado
from schema_search import SchemaSearch
from sqlalchemy import create_engine


class SchemaSearchHandler(APIHandler):
    CONFIG_PATH = Path(__file__).with_name("schema_search_config.yml")

    def _get_database_url(self, explicit: Optional[str]) -> Optional[str]:
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip()

        for key, value in os.environ.items():
            if key.endswith("_CONNECTION_JSON") and isinstance(value, str) and value.strip().startswith("{"):
                config = json.loads(value)
                url = config.get("connectionUrl")
                if url:
                    return url
        return os.environ.get("DB_URL")

    @tornado.web.authenticated
    async def post(self):
        body = self.get_json_body() or {}
        queries = body.get("queries")
        if isinstance(queries, str):
            queries = [queries]

        if not isinstance(queries, list):
            self.set_status(400)
            self.finish(json.dumps({"error": "queries parameter must be a list of strings"}))
            return

        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]

        if not queries:
            self.set_status(400)
            self.finish(json.dumps({"error": "queries parameter is required"}))
            return

        db_url = self._get_database_url(body.get("dbUrl"))
        if not db_url:
            self.set_status(400)
            self.finish(json.dumps({"error": "Database connection URL is not configured"}))
            return

        db_url = db_url.strip()
        db_url_lower = db_url.lower()

        if db_url_lower.startswith("mysql://"):
            db_url = "mysql+pymysql://" + db_url[len("mysql://"):]
            db_url_lower = db_url.lower()

        if db_url_lower.startswith("snowflake://"):
            self._ensure_snowflake_dependencies()
        elif db_url_lower.startswith("postgresql") or db_url_lower.startswith("postgres") or db_url_lower.startswith("mysql+pymysql"):
            pass
        else:
            self.set_status(400)
            self.finish(json.dumps({"error": "Schema search currently supports PostgreSQL, MySQL, or Snowflake connections"}))
            return

        engine = None
        try:
            engine = create_engine(db_url)
            schema_search = SchemaSearch(engine=engine, config_path=str(self.CONFIG_PATH))
            schema_search.index()

            limit = body.get("limit")
            if limit is not None:
                limit = max(1, min(int(limit), 10))
            else:
                limit = 5

            query_results = []
            for query in queries:
                result = schema_search.search(query, limit=limit)
                query_results.append({
                    "query": query,
                    "results": result
                })

            self.finish(json.dumps({"results": query_results}))
        except Exception as error:
            self.set_status(500)
            self.finish(json.dumps({"error": f"Schema search failed: {error}"}))
        finally:
            if engine is not None:
                try:
                    engine.dispose()
                except Exception:
                    pass

    def _install_package(self, package: str) -> None:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    def _ensure_snowflake_dependencies(self) -> None:
        try:
            import snowflake.sqlalchemy  # type: ignore  # noqa: F401
        except ImportError:
            self._install_package("snowflake-sqlalchemy")
            import snowflake.sqlalchemy  # type: ignore  # noqa: F401
