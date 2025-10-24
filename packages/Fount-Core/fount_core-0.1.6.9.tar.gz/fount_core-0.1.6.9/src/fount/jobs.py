from ._exceptions import TrainingError, TuningError, InferenceError, JobError
from typing import Any
from io import StringIO
import pandas as pd
import time
import sys


class Job:
    id: str
    _transport: Any
    payload: dict
    job_type: str

    def run(self, wait=False, poll_interval=30) -> bool:
        transport = self._transport
        try:
            response = transport.start_job(self.job_type, self.payload)
        except TrainingError:
            return False, None
        self.id = response["id"]
        if wait:
            try:
                self._wait_for_completion(poll_interval, transport)
            except KeyboardInterrupt:
                return False, None
        return True, self.id

    def _wait_for_completion(self, poll_interval=20, _transport=None):
        transport = _transport or self._transport
        try:
            dot_count = 0
            while True:
                status = self.status(transport)
                state = status.get("status", "")
                if state in ["Completed", "Failed"]:
                    sys.stdout.write(f"\rJob {self.id} {state}")
                    sys.stdout.flush()
                    return status
                dot_count = (dot_count % 5) + 1
                dots = "." * dot_count
                sys.stdout.write(f"\rJob {self.id} is {state}{dots}")
                sys.stdout.flush()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            sys.stdout.write(f"\nInterrupted! Attempting to stop job {self.id}...")
            try:
                self.stop(transport)
                sys.stdout.write(f"\nJob {self.id} stop requested.\n")
            except Exception as e:
                sys.stdout.write(f"\nFailed to stop job: {e}")
            raise

    def status(self, _transport=None):
        transport = _transport or self._transport
        if self.id == "":
            raise JobError("Job ID is required")
        return transport.get_job_status(self.id)

    def model(self, _transport=None):
        transport = _transport or self._transport
        return transport.get_model("training")

    def metrics(self, _transport=None):
        transport = _transport or self._transport
        if self.id == "":
            raise JobError("Job ID is required")
        _r = transport.get_job_metrics(self.id, self.job_type)
        return pd.read_csv(StringIO(_r))

    def predictions(self, _transport=None):
        transport = _transport or self._transport
        if self.id == "":
            raise JobError("Job ID is required")
        _r = transport.get_predictions(self.id, self.job_type)
        return pd.read_csv(StringIO(_r))

    def stop(self, _transport=None):
        transport = _transport or self._transport
        if self.id == "":
            raise JobError("Job ID is required")
        return transport.stop(self.id)


class TrainingJob(Job):

    def __init__(self, id, _transport, payload, job_type):
        self.id = id
        self._transport = _transport
        self.payload = payload
        self.job_type = job_type

    @classmethod
    def submit(cls, _transport, job_type, payload):
        try:
            return cls(id="", _transport=_transport, payload=payload, job_type=job_type)
        except Exception as e:
            sys.stderr.write(str(e))
            raise TrainingError(str(e))


class TuningJob(Job):

    def __init__(self, id, _transport, payload, job_type):
        self.id = id
        self._transport = _transport
        self.payload = payload
        self.job_type = job_type

    @classmethod
    def submit(cls, _transport, job_type, payload):
        try:
            return cls(id="", _transport=_transport, payload=payload, job_type=job_type)
        except Exception as e:
            sys.stderr.write(str(e))
            raise TuningError(str(e))


class InferenceJob(Job):

    def __init__(self, id, _transport, payload, job_type):
        self.id = id
        self._transport = _transport
        self.payload = payload
        self.job_type = job_type

    @classmethod
    def submit(cls, _transport, job_type, payload):
        try:
            return cls(id="", _transport=_transport, payload=payload, job_type=job_type)
        except Exception as e:
            sys.stderr.write(str(e))
            raise InferenceError(str(e))
