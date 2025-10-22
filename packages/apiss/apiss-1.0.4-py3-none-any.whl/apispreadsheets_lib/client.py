import requests
import json


class APIError(Exception):
    pass


class APISpreadsheets:
    def __init__(self, base_url=None, access_key=None, secret_key=None, bearer_token=None, default_headers=None,
                 timeout=45):
        self.base_url = (base_url or "https://api.apispreadsheets.com").rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key
        self.bearer_token = bearer_token
        self.timeout = timeout
        self.session = requests.Session()
        self.default_headers = default_headers or {}

    def _build_headers(self, extra=None):
        h = {"content-type": "application/json"}
        h.update(self.default_headers)
        if self.access_key is not None:
            h.setdefault("accessKey", self.access_key)
        if self.secret_key is not None:
            h.setdefault("secretKey", self.secret_key)
        if self.bearer_token:
            h["Authorization"] = "Bearer " + self.bearer_token
        if extra:
            h.update(extra)
        return h

    def _request(self, method, path, path_params=None, query=None, headers=None, body=None):
        url_path = path
        if path_params:
            for k, v in path_params.items():
                url_path = url_path.replace("{" + str(k) + "}", str(v))
        url = self.base_url + url_path
        res = self.session.request(
            method=method.upper(),
            url=url,
            params=(query or {}),
            headers=self._build_headers(headers),
            json=body,
            timeout=self.timeout,
        )
        ct = res.headers.get("content-type", "")
        content = res.json() if "application/json" in ct else res.text
        if not res.ok:
            raise APIError("%s %s -> HTTP %s: %s" % (method.upper(), url_path, res.status_code, content))
        return content

    # --------- Generated endpoints ---------

    def run_agent(self, agent_hash=None, temperature=None, top_p=None, file_ids=None, file_descriptions=None, body=None,
                  access_key=None, secret_key=None):
        """
        POST /agents/{agent_hash}

        Convenience params (optional):
        - temperature: float
        - top_p: float
        - file_ids: list[str]
        - file_descriptions: dict[str, str]

        If `body` is provided, it will be sent as-is; otherwise we build it
        from the convenience params above.
        """
        if agent_hash is None:
            raise APIError("Missing required path param: agent_hash")

        pparams = {"agent_hash": agent_hash}
        qparams = {}
        hdrs = {}

        # headers (from args or client defaults)
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # body assembly
        if body is None:
            body = {}
            if temperature is not None:
                body["temperature"] = temperature
            if top_p is not None:
                body["top_p"] = top_p
            if file_ids is not None:
                body["file_ids"] = file_ids
            if file_descriptions is not None:
                body["file_descriptions"] = file_descriptions

        return self._request(
            "post",
            "/agents/{agent_hash}",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body or {}
        )

    def agent_job_status(self, job_hash=None, access_key=None, secret_key=None, method="get"):
        """
        GET /agents/jobs/{job_hash}/
        or POST /agents/jobs/{job_hash}/

        Retrieves job status and (if completed) download URLs.

        Query params:
        - access_key: required
        - secret_key: required
        """
        if job_hash is None:
            raise APIError("Missing required path param: job_hash")

        pparams = {"job_hash": job_hash}
        hdrs = {}
        qparams = {}

        # Use explicit keys or fallback to client defaults
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak or not sk:
            raise APIError("Missing required query params: access_key and secret_key")

        qparams["accessKey"] = ak
        qparams["secretKey"] = sk

        # Backend supports both GET and POST — default to GET unless overridden
        method = method.lower()
        if method not in ("get", "post"):
            raise APIError("method must be 'get' or 'post'")

        return self._request(
            method,
            "/agents/jobs/{job_hash}",
            path_params=pparams,
            query=qparams,
            headers=hdrs
        )

    def ai(self, file_id=None, method="post", prompt=None, body=None, access_key=None, secret_key=None):
        """
        GET|POST /ai/{file_id}/

        Auth: access_key + secret_key (headers)

        Args:
        file_id: required
        method: "get" or "post" (default "post")
        prompt: string or dict, always sent in body
        body: full JSON body (optional, overrides prompt if provided)
        access_key, secret_key: required API headers
        """

        if file_id is None:
            raise APIError("Missing required path param: file_id")

        method = method.lower()
        if method not in ("get", "post"):
            raise APIError("method must be 'get' or 'post'")

        # Headers
        ak = access_key or getattr(self, "access_key", None)
        sk = secret_key or getattr(self, "secret_key", None)

        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")

        hdrs = {
            "accessKey": ak,
            "secretKey": sk
        }

        # Always send prompt in body
        if body is None:
            if prompt is None:
                raise APIError("Missing required request body or prompt")
            body = {"prompt": prompt}

        return self._request(
            method,
            "/ai/{file_id}/",
            path_params={"file_id": file_id},
            headers=hdrs,
            body=body
        )

    def calculate(self, file_id=None, sheet_name=None, input_cells=None, output_cells=None,
                  save_file_post_call=None, body=None, access_key=None, secret_key=None):
        # --- required path param ---
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        pparams = {"file_id": file_id}
        qparams = {}
        hdrs = {}

        # --- headers (use per-call keys or client defaults) ---
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # --- body assembly ---
        if body is None:
            # Build from convenience params
            payload = {"input_cells": {}, "output_cells": {}}

            # input_cells: allow single-sheet shorthand OR full multi-sheet dict
            if input_cells is not None:
                if isinstance(input_cells, dict):
                    # If value is not a dict of sheets, assume single-sheet shorthand
                    # Example shorthand: {"A2": "x", "A3": "y"} + sheet_name="Sheet1"
                    is_single_sheet = all(
                        isinstance(v, (str, int, float, bool, type(None))) for v in input_cells.values())
                    if is_single_sheet:
                        if not sheet_name:
                            raise APIError("sheet_name is required when using shorthand input_cells")
                        payload["input_cells"][sheet_name] = input_cells
                    else:
                        # Assume already shaped like {"Sheet1": {"A2":"x", ...}, "Sheet2": {...}}
                        payload["input_cells"] = input_cells
                else:
                    raise APIError("input_cells must be a dict")

            # output_cells: allow single-sheet shorthand (list) OR full multi-sheet dict
            if output_cells is not None:
                if isinstance(output_cells, dict):
                    # Already like {"Sheet1":["A2","A3"], "Sheet2":[...]}
                    payload["output_cells"] = output_cells
                elif isinstance(output_cells, list):
                    if not sheet_name:
                        raise APIError("sheet_name is required when using shorthand output_cells list")
                    payload["output_cells"][sheet_name] = output_cells
                else:
                    raise APIError("output_cells must be a list or a dict")

            # save_file_post_call
            if save_file_post_call is not None:
                if not isinstance(save_file_post_call, bool):
                    raise APIError("save_file_post_call must be a boolean")
                payload["save_file_post_call"] = save_file_post_call

            body = payload

        # Final validation: body must contain at least input/output keys (can be empty dicts)
        if not isinstance(body, dict):
            raise APIError("body must be a dict")
        if "input_cells" not in body or "output_cells" not in body:
            # If user supplied raw body missing keys, we still try to coerce from convenience values above.
            # Otherwise, enforce presence.
            raise APIError('body must include "input_cells" and "output_cells" keys')

        return self._request(
            "post",
            "/calculate/{file_id}/",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body
        )

    def get_custom_api(self, customapi_hash=None, body=None, access_key=None, secret_key=None):
        """
        POST /custom/details/{customapi_hash}
        Retrieves details of a custom API by its hash.
        Requires access_key and secret_key in headers.
        """
        if customapi_hash is None:
            raise APIError("Missing required path param: customapi_hash")

        pparams = {"customapi_hash": customapi_hash}
        qparams = {}
        hdrs = {}

        # Access credentials (from args or default client)
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key

        if not ak or not sk:
            raise APIError("Missing required headers: access_key and secret_key")

        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # Body is optional
        if body is None:
            body = {}

        return self._request(
            "post",
            "/custom/details/{customapi_hash}",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body
        )

    def run_custom_api(self, customapi_id=None, body=None, headers=None):
        """
        POST /custom/{customapi_id}
        Allows caller-defined headers (e.g., ACCESSKEY) for custom code.
        """
        if customapi_id is None:
            raise APIError("Missing required path param: customapi_id")

        pparams = {"customapi_id": customapi_id}
        qparams = {}
        hdrs = {}

        # Merge caller-provided headers as-is (case-insensitive over the wire)
        if headers is not None:
            if not isinstance(headers, dict):
                raise APIError("headers must be a dict of {str: str}")
            for k, v in headers.items():
                hdrs[str(k)] = v

        # Body can be anything; default to {}
        if body is None:
            body = {}

        return self._request(
            "post",
            "/custom/{customapi_id}",
            path_params=pparams,
            query=qparams,
            headers=hdrs,  # will be merged with _build_headers defaults
            body=body
        )

    def read_data(self, file_id=None, query=None, limit=None, count=None, data_format=None, access_key=None,
                  secret_key=None):
        """
        GET /data/{file_id}/
        Auth for this endpoint is via QUERY PARAMS: ?accessKey=...&secretKey=...
        Optional query params: query, limit, count, data_format
        """
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        pparams = {"file_id": file_id}
        qparams = {}
        hdrs = {}  # no auth headers for this endpoint

        # --- optional filters ---
        if query is not None:
            qparams["query"] = query
        if limit is not None:
            qparams["limit"] = limit
        if count is not None:
            # requests will serialize True/False as 'True'/'False'. If your API needs lowercase:
            qparams["count"] = str(count).lower()
        if data_format is not None:
            qparams["data_format"] = data_format

        # --- auth: QUERY PARAMS (not headers) ---
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required query param: access_key")
        if not sk:
            raise APIError("Missing required query param: secret_key")
        qparams["accessKey"] = ak
        qparams["secretKey"] = sk

        return self._request(
            "get",
            "/data/{file_id}/",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=None
        )

    def update_data(self, file_id=None, body=None, access_key=None, secret_key=None):
        """
        POST /data/{file_id}/
        Update existing row(s). A "query" is REQUIRED to select what to update.

        Body shape:
        {
            "data": {...fields to set...},
            "query": "select * from <file_id> where <condition>"
        }
        """
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        pparams = {"file_id": file_id}
        qparams = {}
        hdrs = {}

        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        if body is None or "data" not in body:
            raise APIError('Update body must include "data" and "query" keys.')
        if "query" not in body or not body["query"]:
            raise APIError('Update requires a "query" string to match rows.')

        return self._request(
            "post",
            "/data/{file_id}/",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body
        )

    def create_data(self, file_id=None, body=None, access_key=None, secret_key=None):
        """
        POST /data/{file_id}/
        Adds a new row (record) to the spreadsheet file.

        Body Example:
        {
            "data": {
                "Name": "Miles Morales",
                "Location": "Metropolis",
                "Fictional": true,
                "Occupation": "Reporter"
            }
        }
        """
        # --- required path param ---
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        pparams = {"file_id": file_id}
        qparams = {}
        hdrs = {}

        # --- headers (access keys) ---
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # --- request body ---
        if body is None or "data" not in body:
            raise APIError('Request body must include "data" key, e.g. {"data": {...}}')

        return self._request(
            "post",
            "/data/{file_id}/",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body
        )

    def import_files(self, files=None, meta=None, access_key=None, secret_key=None):
        """
        POST /import  (multipart/form-data)

        Args:
        files: list of file paths or file-like objects. Examples:
                ["./data/a.csv", "./data/b.xlsx"]
                or [("files", ("a.csv", open("a.csv","rb"), "text/csv")), ...]  # advanced
        meta:  dict, optional. Will be JSON-encoded into a "meta" form field.
                e.g. {"teamHash": "abc123"} or {"teamHash": "abc123", "access_level": ["read"]}
        accesskey, secretkey: override client defaults (optional).

        Returns: parsed JSON (if response is JSON) or raw text.
        """
        if not files:
            raise APIError("No files provided. Pass a list of file paths or file-like objects.")

        # ---- auth headers (lowercase is fine; headers are case-insensitive) ----
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak or not sk:
            raise APIError("Missing required headers: access_key and secret_key")

        headers = {
            "accesskey": ak,
            "secretkey": sk,
            # DO NOT set Content-Type; requests will add the correct multipart boundary.
        }

        # ---- build multipart ----
        multipart_files = []
        opened_handles = []

        try:
            for item in files:
                if isinstance(item, tuple) and len(item) in (2, 3):
                    # Advanced: user supplied ("files", (filename, fileobj[, mimetype]))
                    if item[0] != "files":
                        # normalize to correct field name expected by backend
                        multipart_files.append(("files", item[1]))
                    else:
                        multipart_files.append(item)
                elif isinstance(item, str):
                    # path on disk
                    fh = open(item, "rb")
                    opened_handles.append(fh)
                    filename = item.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                    multipart_files.append(("files", (filename, fh)))
                else:
                    # file-like object (must have .read() and .name ideally)
                    fh = item
                    filename = getattr(fh, "name", "uploaded")
                    multipart_files.append(("files", (filename, fh)))

            # form fields
            form_data = {}
            if meta is not None:
                if not isinstance(meta, dict):
                    raise APIError("meta must be a dict if provided")
                form_data["meta"] = json.dumps(meta)

            # ---- perform request (bypass _request to avoid JSON content-type) ----
            url = self.base_url.rstrip("/") + "/import"
            res = self.session.post(
                url,
                headers=headers,
                files=multipart_files,
                data=form_data,
                timeout=self.timeout,
            )

            ct = res.headers.get("content-type", "")
            content = res.json() if "application/json" in ct else res.text
            if not res.ok:
                raise APIError("POST /import -> HTTP %s: %s" % (res.status_code, content))
            return content

        finally:
            # close any file handles we opened from paths
            for fh in opened_handles:
                try:
                    fh.close()
                except Exception:
                    pass

    def macros(self, file_id=None, macros=None, macro_parameters=None, input_cells=None, output_cells=None,
               save_file_post_call=None, post_formula_actions=None, body=None, access_key=None, secret_key=None):
        """
        POST /macro/{file_id}/

        Either pass a full `body` dict or use the convenience params above.
        """
        # ---- path ----
        if file_id is None:
            raise APIError("Missing required path param: file_id")
        pparams = {"file_id": file_id}

        # ---- headers (use per-call or client defaults) ----
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs = {"accessKey": ak, "secretKey": sk}

        # ---- body assembly ----
        if body is None:
            if not macros:
                raise APIError("`macros` (macro name) is required when no raw `body` is provided")
            payload = {"macros": macros}

            if isinstance(macro_parameters, (list, tuple)):
                payload["macro_parameters"] = list(macro_parameters)

            if isinstance(input_cells, dict):
                payload["input_cells"] = input_cells

            if isinstance(output_cells, dict):
                payload["output_cells"] = output_cells

            if save_file_post_call is not None:
                if not isinstance(save_file_post_call, bool):
                    raise APIError("save_file_post_call must be a boolean")
                payload["save_file_post_call"] = save_file_post_call

            # Optional: include post_formula_actions if caller provided it
            if post_formula_actions is not None:
                payload["post_formula_actions"] = post_formula_actions

            body = payload

        # ---- request ----
        return self._request(
            "post",
            "/macro/{file_id}/",
            path_params=pparams,
            query={},
            headers=hdrs,
            body=body
        )

    def create_file(self, data=None, file_name=None, body=None, access_key=None, secret_key=None):
        """
        POST /utilities/create
        Creates a new file from provided tabular data.

        Pass either a full `body` dict or convenience args `data` and `file_name`.
        """
        pparams = {}
        qparams = {}
        hdrs = {}

        # headers (use per-call or client defaults)
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # body assembly
        if body is None:
            if data is None:
                raise APIError("Missing required body field: data")
            if file_name is None:
                raise APIError("Missing required body field: file_name")
            body = {"data": data, "fileName": file_name}

        return self._request(
            "post",
            "/utilities/create",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body
        )

    def download_file(self, data=None, file_name=None, body=None, access_key=None, secret_key=None):
        """
        POST /utilities/download
        Generates a downloadable spreadsheet for the authenticated user.

        Pass either a full `body` dict or the convenience args `data` and `fileName`.
        """
        pparams = {}
        qparams = {}
        hdrs = {}

        # headers (from args or client defaults)
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # body assembly
        if body is None:
            if data is None:
                raise APIError("Missing required body field: data")
            if file_name is None:
                raise APIError("Missing required body field: file_name")
            body = {"data": data, "file_name": file_name}

        return self._request(
            "post",
            "/utilities/download",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body
        )

    def list_files(self, page=None, page_size=None, q=None, sort_by=None, sort_order=None, created_after=None,
                   created_before=None, access_key=None, secret_key=None):
        """
        GET /utilities/files
        Security: none/handled by base headers

        Path params: []
        Query params: [{'name': 'page', 'required': False}, {'name': 'pageSize', 'required': False}, {'name': 'q', 'required': False}, {'name': 'sortBy', 'required': False}, {'name': 'sortOrder', 'required': False}, {'name': 'createdAfter', 'required': False}, {'name': 'createdBefore', 'required': False}]
        Headers (explicit): [{'name': 'access_key', 'required': True}, {'name': 'secretKey', 'required': True}]
        Body required: False
        """
        pparams = {}
        qparams = {}
        hdrs = {}

        if page is not None:
            qparams["page"] = page
        if page_size is not None:
            qparams["pageSize"] = page_size
        if q is not None:
            qparams["q"] = q
        if sort_by is not None:
            qparams["sortBy"] = sort_by
        if sort_order is not None:
            qparams["sortOrder"] = sort_order
        if created_after is not None:
            qparams["createdAfter"] = created_after
        if created_before is not None:
            qparams["createdBefore"] = created_before
        if access_key is None:
            raise APIError("Missing required header param: access_key")
        if access_key is not None:
            hdrs["accessKey"] = access_key
        if secret_key is None:
            raise APIError("Missing required header param: secret_key")
        if secret_key is not None:
            hdrs["secretKey"] = secret_key

        return self._request(
            "get",
            "/utilities/files",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=None
        )

    def get_file(self, file_id=None, include_samples=None, sample_rows=None, access_key=None, secret_key=None):
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        pparams = {"file_id": file_id}
        qparams = {}
        hdrs = {}

        # --- optional query params ---
        if include_samples is not None:
            qparams["includeSamples"] = str(include_samples).lower()  # true/false as string
        if sample_rows is not None:
            qparams["sampleRows"] = sample_rows

        # --- headers (access keys) ---
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # --- perform request ---
        return self._request(
            "get",
            "/utilities/files/{file_id}",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=None
        )

    def update_file(self, file_id=None, name=None, description=None, sheet_read=None, body=None, access_key=None,
                    secret_key=None):
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        pparams = {"file_id": file_id}
        qparams = {"update": "true"}  # required query flag
        hdrs = {}

        # --- headers (use per-call or client defaults) ---
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")
        hdrs["accessKey"] = ak
        hdrs["secretKey"] = sk

        # --- body: allow either explicit dict or individual fields ---
        if body is None:
            body = {}
            if name is not None:
                body["name"] = name
            if description is not None:
                body["description"] = description
            if sheet_read is not None:
                body["sheetRead"] = sheet_read

        return self._request(
            "post",
            "/utilities/files/{file_id}/",  # matches your screenshot (note trailing slash)
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=body or {}
        )

    def delete_file(self, file_id=None, access_key=None, secret_key=None):
        pparams = {}
        qparams = {"delete": "true"}
        hdrs = {}

        if file_id is None:
            raise APIError("Missing required path param: file_id")
        pparams["file_id"] = file_id

        if access_key is None and self.access_key is None:
            raise APIError("Missing required header param: access_key")
        hdrs["accessKey"] = access_key or self.access_key

        if secret_key is None and self.secret_key is None:
            raise APIError("Missing required header param: secret_key")
        hdrs["secretKey"] = secret_key or self.secret_key

        return self._request(
            "get",
            "/utilities/files/{file_id}",
            path_params=pparams,
            query=qparams,
            headers=hdrs,
            body=None
        )

    def run_macros(self, file_id=None, input_cells=None, output_cells=None, sheet_name=None, save_file_post_call=None,
                   access_key=None, secret_key=None, body=None):
        """
        POST /run-macros/{file_id}/

        This endpoint expects credentials in the **JSON body** (not query),
        alongside:
        - input_cells (dict)  [required]
        - sheet_name (str)    [optional]
        - output_cells (list) [optional]
        - save_file_post_call (bool) [optional]

        NOTE: If you instantiate the client with access_key/secret_key, those may
        still be added as headers by _build_headers(). If you want ONLY body auth,
        construct the client without defaults and pass accessKey/secret_key here.
        """
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        # Build body from convenience args if not provided
        if body is None:
            if not isinstance(input_cells, dict) or input_cells is None:
                raise APIError("input_cells (dict) is required in body for run_macros")
            if save_file_post_call is not None and not isinstance(save_file_post_call, bool):
                raise APIError("save_file_post_call must be a boolean")
            if not access_key:
                raise APIError("Missing required body param: access_key")
            if not secret_key:
                raise APIError("Missing required body param: secret_key")

            body = {
                "accessKey": access_key,
                "secretKey": secret_key,
                "input_cells": input_cells
            }
            if sheet_name is not None:
                body["sheet_name"] = sheet_name
            if isinstance(output_cells, list):
                body["output_cells"] = output_cells
            if save_file_post_call is not None:
                body["save_file_post_call"] = save_file_post_call
        else:
            # minimal validation if caller supplies raw body
            if "accessKey" not in body or not body["accessKey"]:
                raise APIError("Missing required body param: accessKey")
            if "secretKey" not in body or not body["secretKey"]:
                raise APIError("Missing required body param: secretKey")
            if "input_cells" not in body or not isinstance(body["input_cells"], dict):
                raise APIError("body.input_cells must be an object (dict)")

        # Path params
        pparams = {"file_id": file_id}

        # Send as JSON; no special headers required (keys live in body)
        return self._request(
            "post",
            "/run-macros/{file_id}/",
            path_params=pparams,
            headers={},  # (If your client has default keys, they may still be added as headers.)
            body=body
        )

    def get_api_spec(self, file_id=None, is_test=False, access_key=None, secret_key=None, headers=None):
        """
        POST /spec/{file_id}

        Auth: accessKey/secretKey in HEADERS (unless is_test=True, which bypasses)
        Body: { "is_test": bool }
        """
        if file_id is None:
            raise APIError("Missing required path param: file_id")

        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key

        if not is_test:
            if not ak:
                raise APIError("Missing required header param: access_key")
            if not sk:
                raise APIError("Missing required header param: secret_key")

        hdrs = {}
        if headers:
            hdrs.update(headers)
        if ak:
            hdrs["accessKey"] = ak
        if sk:
            hdrs["secretKey"] = sk

        body = {"is_test": bool(is_test)}

        return self._request(
            "post",
            "/spec/{file_id}",
            path_params={"file_id": file_id},
            headers=hdrs,
            body=body
        )

    def build_agent(self, access_key=None, secret_key=None, agent_name=None, agent_description=None, selected_files=None,
                    file_descriptions=None, selected_output_formats=None, agent_instructions=None, body=None):
        """
        POST /build-agent/

        Headers: accessKey/secretKey (required)
        Body fields:
        agent_name (str, required)
        selected_files (list[str], required)
        file_descriptions (dict[str,str], optional)
        selected_output_formats (list[str], optional: .xlsx .pdf .html .docx .csv)
        agent_description (str, optional)
        agent_instructions (str, optional)
        """
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")

        allowed = {".xlsx", ".pdf", ".html", ".docx", ".csv"}

        if body is None:
            if not agent_name or not str(agent_name).strip():
                raise APIError("agent_name is required")
            if not isinstance(selected_files, list) or not selected_files:
                raise APIError("selected_files must be a non-empty list of file ids")
            if selected_output_formats is not None:
                if not isinstance(selected_output_formats, list):
                    raise APIError("selected_output_formats must be a list")
                bad = [f for f in selected_output_formats if f not in allowed]
                if bad:
                    raise APIError("Invalid output format(s): " + ", ".join(bad))

            body = {
                "agentName": agent_name,
                "agentDescription": agent_description or "",
                "selectedFiles": selected_files,
                "fileDescriptions": file_descriptions or {},
                "selectedOutputFormats": selected_output_formats or [],
                "agentInstructions": agent_instructions or ""
            }
        else:
            # minimal validation if raw body supplied
            if "agentName" not in body or not body["agentName"]:
                raise APIError("agent_name is required")
            if "selectedFiles" not in body or not isinstance(body["selectedFiles"], list) or not body["selectedFiles"]:
                raise APIError("selected_files must be a non-empty list of file ids")
            if "selectedOutputFormats" in body and isinstance(body["selectedOutputFormats"], list):
                bad = [f for f in body["selectedOutputFormats"] if f not in allowed]
                if bad:
                    raise APIError("Invalid output format(s): " + ", ".join(bad))

        return self._request(
            "post",
            "/build-agent/",
            headers={"accessKey": ak, "secretKey": sk},
            body=body
        )

    def delete_custom_api(self, customapi_hash=None, access_key=None, secret_key=None, body=None):
        """
        POST /custom/delete/{customapi_hash}

        Headers: accessKey, secretKey (required)
        Body: optional (server doesn't require fields)
        """
        if customapi_hash is None:
            raise APIError("Missing required path param: customapi_hash")

        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")

        return self._request(
            "post",
            "/custom/delete/{customapi_hash}",
            path_params={"customapi_hash": customapi_hash},
            headers={"accessKey": ak, "secretKey": sk},
            body=(body or {})
        )

    def get_custom_apis(self, access_key=None, secret_key=None, body=None):
        """
        POST /custom/list
        Headers: access_key, secretKey (required)
        Body: optional/ignored (send {} by default)
        Returns: { success: bool, custom_apis: [...], count: int }
        """
        ak = access_key if access_key is not None else self.access_key
        sk = secret_key if secret_key is not None else self.secret_key
        if not ak:
            raise APIError("Missing required header param: access_key")
        if not sk:
            raise APIError("Missing required header param: secret_key")

        return self._request(
            "post",
            "/custom/list",
            headers={"accessKey": ak, "secretKey": sk},
            body=(body or {})
        )






