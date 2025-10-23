"""Interface to Plotly's /v2/external_files endpoints."""

from figlinq.api.v2.utils import build_url, make_params, request

RESOURCE = "external-files"


def create(file, filename, parent_path=None, world_readable="false"):
    """
    Create a new external_file.

    :param file: File-like object (e.g., open(...) or BytesIO).
    :param filename: File name.
    :param parent_path: Parent path for the file.
    :param world_readable: If True, the file is public.
    :return: requests.Response
    """
    url = build_url(RESOURCE, route="upload")

    files = {"files": (filename, file)}
    headers = {
        "X-File-Name": filename,
        "plotly-parent-path": parent_path,
        "plotly-world-readable": world_readable,
    }

    response = request("post", url, files=files, headers=headers)
    return response.json()


def content(fid, share_key=None):
    """
    Retrieve full content for the external_file

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :param (str) share_key: The secret key granting 'read' access if private.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid, route="content")
    params = make_params(share_key=share_key)
    return request("get", url, params=params)


# def retrieve(fid, share_key=None):
#     """
#     Retrieve an external_file object.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :param (str) share_key: The secret key granting 'read' access if private.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid)
#     params = make_params(share_key=share_key)
#     return request("get", url, params=params)


# Not implemented yet
# def update(fid, body):
#     """
#     Update an external_file.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :param (dict) body: A mapping of body param names to values.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid)
#     return request("put", url, json=body)


# def trash(fid):
#     """
#     Soft-delete an external_file. (Can be undone with 'restore').

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="trash")
#     return request("post", url)


# def restore(fid):
#     """
#     Restore a trashed external_file. See 'trash'.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="restore")
#     return request("post", url)


# def permanent_delete(fid):
#     """
#     Permanently delete a trashed external_file. See 'trash'.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="permanent_delete")
#     return request("delete", url)


# def destroy(fid):
#     """
#     Permanently delete a file.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid)
#     return request("delete", url)


# def lookup(path, parent=None, user=None, exists=None):
#     """
#     Retrieve a file by path.

#     :param (str) path: The '/'-delimited path specifying the file location.
#     :param (int) parent: Parent id, an integer, which the path is relative to.
#     :param (str) user: The username to target files for. Defaults to requestor.
#     :param (bool) exists: If True, don't return the full file, just a flag.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, route="lookup")
#     params = make_params(path=path, parent=parent, user=user, exists=exists)
#     return request("get", url, params=params)
