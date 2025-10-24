import datetime as dt
from uuid import uuid4
from typing import Iterable, Optional
from asyncio import TaskGroup
import asyncio
from debby.collector import Collector
from debby.artifacts import Manifest
from debby.core import CheckInstance, CheckResult, CheckResultStatus


class RunStatus:
    def __init__(self):
        self.unique_id = uuid4()
        self.started_at: Optional[dt.datetime] = None
        self.ended_at: Optional[dt.datetime] = None
        self.check_instance_count = 0
        self.passing = 0
        self.failing = 0
        self.warnings = 0
        self.errors = 0

    def completed_count(self):
        return self.passing + self.failing + self.warnings + self.errors


class Runner:
    def __init__(self, collector: Collector, manifest: Manifest):
        self.collector = collector
        self.manifest = manifest
        self.status = RunStatus()

    def iter_check_instances(self) -> Iterable[CheckInstance]:
        for check in self.collector.iter_checks():
            for node in self.manifest.iter_nodes():
                if check.is_enabled_for(node):
                    yield CheckInstance(check=check, node=node, manifest=self.manifest)

    def collect_check_instances(self) -> list[CheckInstance]:
        check_instances = list(self.iter_check_instances())
        return check_instances

    async def run(self) -> list[CheckResult]:
        self.status.started_at = dt.datetime.now(dt.UTC)
        check_instances = self.collect_check_instances()
        self.status.check_instance_count = len(check_instances)
        checks_collected_duration = dt.datetime.now(dt.UTC) - self.status.started_at

        print(
            f"Collected {self.status.check_instance_count} checks in {checks_collected_duration}"
        )

        tasks = [
            asyncio.get_event_loop().run_in_executor(None, ci.run, self.status)
            for ci in check_instances
        ]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result.status == CheckResultStatus.failing:
                print(
                    result.status.value,
                    result.check_instance.check.name,
                    result.check_instance.node["name"],
                    f"({result.check_instance.node['original_file_path']})",
                )

        self.status.ended_at = dt.datetime.now(dt.UTC)
        run_duration = self.status.ended_at - self.status.started_at
        print(
            f"Finished running {self.status.completed_count()} checks in {run_duration}"
        )
        return results
