import argparse
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs


def _get_content_type(body: str) -> str:
    """Determines the Content-Type based on the response body content."""
    body_lines = body.strip().split("\n")

    # Check first 3 lines for <MPD
    for line in body_lines[:3]:
        if "<MPD" in line:
            return "application/dash+xml"

    if "#EXTM3U" in body:
        return "application/x-mpegURL"

    # Use regex for more flexible matching of VAST and VMAP
    if re.search(r"<(\w*:)?VAST", body, re.IGNORECASE):
        return "application/vnd.vast+xml"

    if re.search(r"<(\w*:)?VMAP", body, re.IGNORECASE):
        return "application/vnd.vmap+xml"

    if body_lines and body_lines[0].strip().startswith("<?xml"):
        return "application/xml"

    return "text/plain"


class BodyLoggerRecord:
    """
    Represents a single log entry.
    """

    def __init__(
        self,
        timestamp: datetime,
        request_line: str,
        correlation_id: int,
        request_time: float,
        query_params: str,
        headers: Dict[str, str],
        body: str,
        log_type: str,
        service_id: str,
        session_id: Optional[str],
        content_type: str,
    ):
        self.timestamp = timestamp
        self.request_line = request_line
        self.correlation_id = correlation_id
        self.request_time = request_time
        self.query_params = query_params
        self.headers = headers
        self.body = body
        self.log_type = log_type
        self.service_id = service_id
        self.session_id = session_id
        self.content_type = content_type

    def __repr__(self):
        return (
            f"BodyLoggerRecord(timestamp={self.timestamp}, type='{self.log_type}', "
            f"service_id='{self.service_id}', session_id='{self.session_id}')"
        )


class LogCollection:
    """
    A collection of LogRecord objects that can be queried.
    """

    def __init__(self, records: List[BodyLoggerRecord]):
        self.records = records

    def query(
        self,
        log_type: Optional[str] = None,
        service_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> "LogCollection":
        """
        Filters log records based on the provided criteria.
        """
        filtered_records = self.records

        if log_type:
            filtered_records = [
                r for r in filtered_records if r.log_type.lower() == log_type.lower()
            ]

        if service_id:
            filtered_records = [
                r for r in filtered_records if r.service_id == service_id
            ]

        if session_id:
            filtered_records = [
                r for r in filtered_records if r.session_id == session_id
            ]

        if start_time:
            filtered_records = [
                r for r in filtered_records if r.timestamp >= start_time
            ]

        if end_time:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_time]

        return LogCollection(filtered_records)

    def __iter__(self):
        return iter(self.records)

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        return self.records[index]

    def to_har(self) -> Dict[str, Any]:
        """Converts the log collection to a HAR-formatted dictionary."""
        har_log = {
            "log": {
                "version": "1.2",
                "creator": {"name": "bodylogger_parser", "version": "1.0"},
                "entries": [],
            }
        }

        for record in self.records:
            url = f"http://{record.log_type.lower()}/{record.request_line}"

            query_string = []
            if record.query_params:
                parsed_qs = parse_qs(record.query_params)
                for name, values in parsed_qs.items():
                    for value in values:
                        query_string.append({"name": name, "value": value})

            request_headers = record.headers.copy()
            request_headers["correlation-id"] = str(record.correlation_id)
            if "x-sessionid" in request_headers:
                request_headers["BPK-Session"] = request_headers["x-sessionid"]
            if "x-serviceid" in request_headers:
                request_headers["BPK-Service"] = request_headers["x-serviceid"]

            content_type = record.content_type

            response_headers = [{"name": "Content-Type", "value": content_type}]

            # Add HLS-specific headers if applicable
            if content_type == "application/x-mpegURL":
                # Extract HLS-MediaSeq
                media_seq_match = re.search(r"#EXT-X-MEDIA-SEQUENCE:(\d+)", record.body)
                if media_seq_match:
                    response_headers.append(
                        {"name": "HLS-MediaSeq", "value": media_seq_match.group(1)}
                    )

                # Extract HLS-PDT
                pdt_match = re.search(
                    r"#EXT-X-PROGRAM-DATE-TIME:([^,\n]+)", record.body
                )
                if pdt_match:
                    response_headers.append(
                        {"name": "HLS-PDT", "value": pdt_match.group(1)}
                    )

            entry = {
                "_id": str(record.correlation_id),
                "_name": record.request_line,
                "startedDateTime": record.timestamp.isoformat() + "Z",
                "time": int(record.request_time * 1000),
                "request": {
                    "method": "GET",
                    "url": url,
                    "httpVersion": "HTTP/1.1",
                    "cookies": [],
                    "headers": [
                        {"name": name, "value": value}
                        for name, value in request_headers.items()
                    ],
                    "queryString": query_string,
                    "headersSize": -1,
                    "bodySize": -1,
                },
                "response": {
                    "status": 200,
                    "statusText": "OK",
                    "httpVersion": "HTTP/1.1",
                    "cookies": [],
                    "headers": response_headers,
                    "content": {
                        "size": len(record.body.encode("utf-8")),
                        "mimeType": content_type,
                        "text": record.body,
                    },
                    "redirectURL": "",
                    "headersSize": -1,
                    "bodySize": len(record.body.encode("utf-8")),
                },
                "cache": {},
                "timings": {
                    "send": 0,
                    "wait": int(record.request_time * 1000),
                    "receive": 0,
                },
            }
            har_log["log"]["entries"].append(entry)

        return har_log

    def save_har(self, filepath: str):
        """Saves the log collection to a HAR file."""
        har_data = self.to_har()
        with open(filepath, "w") as f:
            json.dump(har_data, f, indent=2)


def parse_bodylogger_file(file_path: str) -> LogCollection:
    """
    Parses a log file and returns a LogCollection.
    """
    records = []
    with open(file_path, "r") as f:
        content = f.read()

    log_entries = re.split(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,:]\d{3})", content)

    for i in range(1, len(log_entries), 2):
        timestamp_str = log_entries[i]
        entry_content = log_entries[i + 1]

        lines = entry_content.strip().split("\n")

        try:
            # --- Timestamp ---
            if timestamp_str[19] == ":":
                timestamp_str = f"{timestamp_str[:19]},{timestamp_str[20:]}"
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")

            # --- Initialize fields ---
            request_line = ""
            correlation_id = 0
            request_time = 0.0
            query_params = ""
            headers = {}
            body_content = []
            log_type, service_id, session_id = None, None, None

            # --- State-machine-like parsing ---
            in_headers = False
            in_body = False

            time_match = re.search(r"request_time=([\d.]+)", lines[0])
            if time_match:
                request_time = float(time_match.group(1))

            for line in lines:
                stripped_line = line.strip()

                if "REQUEST:" in line:
                    full_request_line = line.split("REQUEST:")[1].strip()
                    try:
                        path, req_id = full_request_line.rsplit("_", 1)
                        correlation_id = int(req_id)
                        request_line = path
                    except (ValueError, IndexError):
                        request_line = full_request_line
                        correlation_id = 0  # Default if not found
                    continue

                if "-- Query params:" in line:
                    query_params = (
                        line.split("<<none>>")[0].split("-- Query params:")[1].strip()
                    )
                    continue

                if stripped_line == "-- Headers:":
                    in_headers = True
                    continue

                if stripped_line.startswith("[") and "_START" in stripped_line:
                    in_headers = False
                    in_body = True
                    start_tag_match = re.match(
                        r"\[(\w+)_START ([\w-]+)(?: ([\w.-]+))?\]", stripped_line
                    )
                    if start_tag_match:
                        log_type = start_tag_match.group(1)
                        service_id = start_tag_match.group(2)
                        session_id = start_tag_match.group(3)
                    continue

                if stripped_line.startswith("[") and "_END" in stripped_line:
                    in_body = False
                    break  # End of this log record

                if in_headers:
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        headers[key.strip()] = value.strip()

                if in_body:
                    body_content.append(line)

            # --- Record Creation ---
            if log_type and service_id:
                body = "\n".join(body_content)
                content_type = _get_content_type(body)
                records.append(
                    BodyLoggerRecord(
                        timestamp=timestamp,
                        request_line=request_line,
                        correlation_id=correlation_id,
                        request_time=request_time,
                        query_params=query_params,
                        headers=headers,
                        body=body,
                        log_type=log_type,
                        service_id=service_id,
                        session_id=session_id,
                        content_type=content_type,
                    )
                )

        except (IndexError, ValueError) as e:
            # print(f"Skipping malformed log entry: {e}")
            pass

    return LogCollection(records)


if __name__ == "__main__":
    # This assumes a log file named '2024-04-18_10-15-29.log' exists in the same directory.
    # You might need to adjust the path.
    import os

    parser = argparse.ArgumentParser(
        description="Parse and query lightly structured log files."
    )
    parser.add_argument("logfile", help="Path to the log file to be parsed.")
    args = parser.parse_args()

    log_file_path = args.logfile

    if not os.path.exists(log_file_path):
        print(f"Log file not found at: {log_file_path}")
    else:
        logs = parse_bodylogger_file(log_file_path)
        print(f"Parsed {len(logs)} log records.")

        # Example queries
        print("\n--- Querying for ADORIGIN logs ---")
        adorigin_logs = logs.query(log_type="ADORIGIN")
        for log in adorigin_logs:
            print(log)

        print("\n--- Querying for a specific session ID ---")
        session_id_to_find = "10a0c11b219-b323dfde-dff3-4d94-b749-e03cd077d787"
        session_logs = logs.query(session_id=session_id_to_find)
        if session_logs:
            print(f"Found {len(session_logs)} logs for session_id {session_id_to_find}")
            for log in session_logs:
                print(log)
        else:
            print(f"No logs found for session_id {session_id_to_find}")

        print("\n--- Querying for a specific service ID and log type ---")
        service_id_to_find = "10d0d10e202-486566e5-43b6-4b26-bffa-6a9d17affb80"
        filtered_logs = logs.query(log_type="ORIGIN", service_id=service_id_to_find)
        for log in filtered_logs:
            print(log)

        print("\n--- Querying for a time range ---")
        start = datetime(2024, 4, 18, 10, 15, 29, 200000)
        end = datetime(2024, 4, 18, 10, 15, 29, 205000)
        time_range_logs = logs.query(start_time=start, end_time=end)
        print(f"Found {len(time_range_logs)} logs between {start} and {end}")
        for log in time_range_logs:
            print(log)

        # Example HAR export
        if len(logs) > 0:
            har_filepath = "output.har"
            print(f"\n--- Saving parsed logs to {har_filepath} ---")
            logs.save_har(har_filepath)
            print(f"Successfully saved HAR file to {har_filepath}")
