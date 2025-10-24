# Copyright (C) 2018 Bloomberg LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import pytest

from buildgrid._protos.build.bazel.remote.execution.v2 import remote_execution_pb2
from buildgrid.server.decorators.requestid import track_request_id
from buildgrid.server.metadata import ctx_grpc_request_id
from buildgrid.server.utils.digests import create_digest, get_hash_type, parse_digest

BLOBS = (
    b"",
    b"non-empty-blob",
)
BLOB_HASHES = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "89070dfb3175a2c75835d70147b52bd97afd8228819566d84eecd2d20e9b19fc",
)
BLOB_SIZES = (
    0,
    14,
)
BLOB_DATA = zip(BLOBS, BLOB_HASHES, BLOB_SIZES)

STRINGS = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/0",
    "89070dfb3175a2c75835d70147b52bd97afd8228819566d84eecd2d20e9b19fc/14",
    "e1ca41574914ba00e8ed5c8fc78ec8efdfd48941c7e48ad74dad8ada7f2066d/12",
)
BLOB_HASHES = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "89070dfb3175a2c75835d70147b52bd97afd8228819566d84eecd2d20e9b19fc",
    None,
)
BLOB_SIZES = (
    0,
    14,
    None,
)
STRING_VALIDITIES = (
    True,
    True,
    False,
)
STRING_DATA = zip(STRINGS, BLOB_HASHES, BLOB_SIZES, STRING_VALIDITIES)

BASE_URL = "http://localhost:8080"
INSTANCES = (
    None,
    "",
    "instance",
)
URL_HASHES = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "89070dfb3175a2c75835d70147b52bd97afd8228819566d84eecd2d20e9b19fc",
)
URL_SIZES = (
    0,
    14,
)
URL_DATA = zip(URL_HASHES, URL_SIZES)


@pytest.mark.parametrize("blob,digest_hash,digest_size", BLOB_DATA)
def test_create_digest(blob, digest_hash, digest_size):
    # Generate a Digest message from given blob:
    blob_digest = create_digest(blob)

    assert get_hash_type() == remote_execution_pb2.DigestFunction.SHA256

    assert hasattr(blob_digest, "DESCRIPTOR")
    assert blob_digest.DESCRIPTOR == remote_execution_pb2.Digest.DESCRIPTOR
    assert blob_digest.hash == digest_hash
    assert blob_digest.size_bytes == digest_size


@pytest.mark.parametrize("string,digest_hash,digest_size,validity", STRING_DATA)
def test_parse_digest(string, digest_hash, digest_size, validity):
    # Generate a Digest message from given string:
    string_digest = parse_digest(string)

    assert get_hash_type() == remote_execution_pb2.DigestFunction.SHA256

    if validity:
        assert hasattr(string_digest, "DESCRIPTOR")
        assert string_digest.DESCRIPTOR == remote_execution_pb2.Digest.DESCRIPTOR
        assert string_digest.hash == digest_hash
        assert string_digest.size_bytes == digest_size

    else:
        assert string_digest is None


def test_track_request_id():
    @track_request_id
    def _example_request_handler():
        assert ctx_grpc_request_id.get() is not None

    assert ctx_grpc_request_id.get() is None
    _example_request_handler()
    assert ctx_grpc_request_id.get() is None


def test_request_id_unset_on_error():
    @track_request_id
    def _example_request_handler():
        assert ctx_grpc_request_id.get() is not None
        raise RuntimeError("expected")

    assert ctx_grpc_request_id.get() is None
    with pytest.raises(RuntimeError):
        _example_request_handler()
    assert ctx_grpc_request_id.get() is None


def test_track_request_id_generator():
    @track_request_id
    def _example_request_handler():
        assert ctx_grpc_request_id.get() is not None
        yield

    assert ctx_grpc_request_id.get() is None
    for _ in _example_request_handler():
        pass
    assert ctx_grpc_request_id.get() is None


def test_request_id_generator_unset_on_error():
    @track_request_id
    def _example_generator_handler():
        assert ctx_grpc_request_id.get() is not None
        yield
        raise RuntimeError("expected")

    assert ctx_grpc_request_id.get() is None
    with pytest.raises(RuntimeError):
        for _ in _example_generator_handler():
            assert ctx_grpc_request_id.get() is not None
    assert ctx_grpc_request_id.get() is None
