#!/usr/bin/env python3

from io import BufferedReader
import json
import requests as req
from . import utils


class Axios:
    """It's not axios, it's just a custom extensible wrapper for requests"""

    def __init__(self, url: str):
        self.url = url

    def parse_url_query(self, query):
        try:
            if query is not None and isinstance(query, dict):
                for key, value in query.items():
                    self.url += f"&{key}={value}"
        except Exception as e:
            raise e

    def get(self, headers = None, **kwargs) :
        try:
            self.parse_url_query(kwargs.get("query", None))
            r = req.get(self.url, headers=headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise e

    def post(
        self, body=None, headers= None, **kwargs
    ):
        try:
            self.parse_url_query(kwargs.get("query", None))
            r = req.post(self.url, data=body, headers=headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise e

    def post_files(
        self, file, headers = None, **kwargs
    ) :
        try:
            self.parse_url_query(kwargs.get("query", None))
            files = utils.read_files_for_upload(file)
            r = req.post(self.url, headers=headers, files=files)
            r.raise_for_status()
            utils.close_files_after_upload(files)
            try:
                return r.json()
            except Exception:
                temp = r.text.split("\n")
                return json.loads(temp[len(temp) - 2])
        except Exception as e:
            utils.close_files_after_upload(files)
            raise e

    def post_blob(
        self, file: BufferedReader, filename: str, headers = None, **kwargs
    ) :
        try:
            self.parse_url_query(kwargs.get("query", None))
            files = [(
                "file",
                (
                    utils.extract_file_name(filename),
                    file.read(),
                    "application/octet-stream",
                ),
            ),]
            r = req.post(self.url, headers=headers, files=files)
            r.raise_for_status()
            file.close()
            try:
                return r.json()
            except Exception:
                temp = r.text.split("\n")
                return json.loads(temp[len(temp) - 2])
        except Exception as e:
            file.close()
            raise e
