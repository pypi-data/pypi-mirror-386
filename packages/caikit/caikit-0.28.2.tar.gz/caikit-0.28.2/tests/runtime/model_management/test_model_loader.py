# Copyright The Caikit Authors
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
# Standard
from concurrent.futures import Future
from contextlib import contextmanager
from unittest import mock
import tempfile
import threading

# Third Party
import grpc
import pytest

# Local
from caikit.config import get_config
from caikit.core import ModuleConfig
from caikit.core.module_backends import backend_types
from caikit.core.modules import base, module
from caikit.core.toolkit.factory import FactoryConstructible
from caikit.runtime.model_management.batcher import Batcher
from caikit.runtime.model_management.core_model_loader import CoreModelLoader
from caikit.runtime.model_management.factories import model_loader_factory
from caikit.runtime.types.caikit_runtime_exception import CaikitRuntimeException
from sample_lib.data_model import SampleInputType, SampleOutputType
from sample_lib.modules.sample_task import SampleModule
from tests.conftest import TempFailWrapper, random_test_id, temp_config
from tests.core.helpers import MockBackend
from tests.fixtures import Fixtures
import caikit.core

## Helpers #####################################################################


@contextmanager
def temp_model_loader():
    """Temporarily reset the ModelLoader singleton"""
    yield construct_model_loader()


@pytest.fixture
def model_loader():
    yield construct_model_loader()


def construct_model_loader():
    model_loader: CoreModelLoader = model_loader_factory.construct(
        get_config().model_management.loaders.default, "default"
    )
    return model_loader


def make_model_future(model_instance):
    fake_future = Future()
    fake_future.result = lambda *_, **__: model_instance
    return fake_future


## Tests #######################################################################


def test_load_model_ok_response(model_loader):
    """Test that we can load up a valid model folder"""
    model_id = "happy_load_test"
    loaded_model = model_loader.load_model(
        model_id=model_id,
        local_model_path=Fixtures.get_good_model_path(),
        model_type=Fixtures.get_good_model_type(),
    )
    assert loaded_model.model() is not None
    assert isinstance(loaded_model.model(), base.ModuleBase)
    assert model_id == loaded_model.id()
    assert Fixtures.get_good_model_type() == loaded_model.type()
    assert Fixtures.get_good_model_path() == loaded_model.path()

    # Models are not sized by the loader
    assert loaded_model.size() == 0


def test_load_model_archive(model_loader):
    """Test that we can load up a valid model archive"""
    model_id = "happy_load_test"
    loaded_model = model_loader.load_model(
        model_id=model_id,
        local_model_path=Fixtures.get_good_model_archive_path(),
        model_type=Fixtures.get_good_model_type(),
    )
    assert loaded_model.model() is not None
    assert isinstance(loaded_model.model(), base.ModuleBase)


def test_load_model_error_not_found_response(model_loader):
    """Test load model's model does not exist error response"""
    model_id = random_test_id()
    with pytest.raises(CaikitRuntimeException) as context:
        model_loader.load_model(
            model_id=model_id,
            local_model_path="test/this/does/not/exist.zip",
            model_type="categories_esa",
        ).wait()
    assert context.value.status_code == grpc.StatusCode.NOT_FOUND
    assert model_id in context.value.message


def test_load_invalid_model_error_response(model_loader):
    """Test load invalid model error response"""
    model_id = random_test_id()
    with pytest.raises(CaikitRuntimeException) as context:
        loaded_model = model_loader.load_model(
            model_id=model_id,
            local_model_path=Fixtures.get_bad_model_archive_path(),
            model_type="not_real",
        )
        loaded_model.wait()
    assert context.value.status_code == grpc.StatusCode.NOT_FOUND
    assert model_id in context.value.message
    assert not loaded_model.loaded()


def test_it_can_load_more_than_one_model(model_loader):
    """Make sure we can load multiple models without side effects"""
    # TODO: change test to load multiple models

    model_id = "concurrent_load_test"
    model_1 = model_loader.load_model(
        model_id,
        Fixtures.get_good_model_path(),
        model_type=Fixtures.get_good_model_type(),
    )
    model_id = "concurrent_load_test_2"
    model_2 = model_loader.load_model(
        model_id,
        Fixtures.get_good_model_path(),
        model_type=Fixtures.get_good_model_type(),
    )

    assert model_1 is not None
    assert model_2 is not None
    # Different refs
    assert model_1 != model_2


def test_nonzip_extract_fails(model_loader):
    """Check that we raise an error if we throw in an archive that isn't really an archive"""
    model_id = "will_not_be_created"

    with pytest.raises(CaikitRuntimeException) as context:
        model_loader.load_model(
            model_id,
            Fixtures.get_invalid_model_archive_path(),
            Fixtures.get_good_model_type(),
        ).wait()
    # This ends up returning a FileNotFoundError from caikit core.
    # maybe not the best? But it does include an error message at least
    assert (
        context.value.status_code == grpc.StatusCode.NOT_FOUND
    ), "Non-zip file did not raise an error"
    assert Fixtures.get_invalid_model_archive_path() in context.value.message
    assert "config.yml" in context.value.message


def test_no_double_instantiation_of_thread_pools():
    """Make sure trying to re-instantiate this singleton raises"""
    loader1 = construct_model_loader()
    loader2 = construct_model_loader()
    assert loader1._load_thread_pool is loader2._load_thread_pool


def test_with_batching(model_loader):
    """Make sure that loading with batching configuration correctly wraps a
    Batcher around the model.
    """
    model = model_loader.load_model(
        "load_with_batch",
        Fixtures.get_good_model_path(),
        model_type="fake_batch_module",
    ).model()
    assert isinstance(model, Batcher)
    assert model._batch_size == get_config().runtime.batching.fake_batch_module.size

    # Make sure another model loads without batching
    model = model_loader.load_model(
        "load_without_batch",
        Fixtures.get_good_model_path(),
        model_type=Fixtures.get_good_model_type(),
    ).model()
    assert not isinstance(model, Batcher)


def test_with_batching_by_default(model_loader):
    """Make sure that a model type without specific batching enabled will
    load with a batcher if default is enabled
    """
    with temp_config({"runtime": {"batching": {"default": {"size": 10}}}}) as cfg:
        model = model_loader.load_model(
            "load_with_batch_default",
            Fixtures.get_good_model_path(),
            model_type=Fixtures.get_good_model_type(),
        ).model()
        assert isinstance(model, Batcher)
        assert model._batch_size == cfg.runtime.batching.default.size


def test_with_batching_collect_delay(model_loader):
    """Make sure that a non-zero collect_delay_s is read correctly"""
    model_type = Fixtures.get_good_model_type()
    with temp_config(
        {
            "runtime": {
                "batching": {
                    model_type: {
                        "size": 10,
                        "collect_delay_s": 0.01,
                    },
                }
            }
        }
    ) as cfg:
        model = model_loader.load_model(
            "load_with_batch_default",
            Fixtures.get_good_model_path(),
            model_type=model_type,
        ).model()
        assert isinstance(model, Batcher)
        assert model._batch_size == getattr(cfg.runtime.batching, model_type).size
        assert (
            model._batch_collect_delay_s
            == getattr(cfg.runtime.batching, model_type).collect_delay_s
        )


def test_load_distributed_impl(reset_globals):
    """Make sure that when configured, an alternate distributed
    implementation of a module can be loaded
    """

    @module(
        base_module=SampleModule,
        backend_type=backend_types.MOCK,
        backend_config_override={"bar1": 1},
    )
    class DistributedGadget(caikit.core.ModuleBase):
        """An alternate implementation of a Gadget"""

        SUPPORTED_LOAD_BACKENDS = [
            MockBackend.backend_type,
            backend_types.LOCAL,
        ]

        def __init__(self, bar):
            self.bar = bar

        def run(self, sample_input: SampleInputType) -> SampleOutputType:
            return SampleOutputType(greeting=f"hello distributed {sample_input.name}")

        @classmethod
        def load(cls, model_load_path, **kwargs) -> "DistributedGadget":
            # NOTE: kwargs needed here for load_backend
            config = ModuleConfig.load(model_load_path)
            return cls(bar=config.bar)

    with tempfile.TemporaryDirectory() as model_path:
        # Create and save the model directly with the local impl
        SampleModule().save(model_path)

        model_type = "gadget"

        with temp_model_loader() as model_loader:
            # Load the distributed version
            model = model_loader.load_model(
                random_test_id(),
                model_path,
                model_type=model_type,
            ).model()
            assert isinstance(model, DistributedGadget)


def test_load_model_without_waiting_success(model_loader):
    """Make sure that loading a model can defer the model to a future and access
    the loaded model when complete
    """
    model_id = random_test_id()
    loaded_model = model_loader.load_model(
        model_id=model_id,
        local_model_path=Fixtures.get_good_model_path(),
        model_type=Fixtures.get_good_model_type(),
    )
    # Block to get the model
    assert loaded_model.model() is not None
    assert isinstance(loaded_model.model(), base.ModuleBase)
    assert model_id == loaded_model.id()
    assert Fixtures.get_good_model_type() == loaded_model.type()
    assert Fixtures.get_good_model_path() == loaded_model.path()

    # Models are not sized by the loader
    assert loaded_model.size() == 0


def test_load_model_without_waiting_deferred_error(model_loader):
    """Make sure that loading a model can defer the model to a future and raise
    when the future is used if the loading failed
    """
    model_id = random_test_id()
    loaded_model = model_loader.load_model(
        model_id=model_id,
        local_model_path=Fixtures.get_bad_model_archive_path(),
        model_type="not_real",
    )
    with pytest.raises(CaikitRuntimeException) as context:
        loaded_model.model()
    assert context.value.status_code == grpc.StatusCode.NOT_FOUND
    assert model_id in context.value.message


def test_load_model_succeed_after_retry(model_loader):
    """Make sure that a model which fails to load on the first try can load
    successfully on a retry.
    """
    failures = 2
    fail_wrapper = TempFailWrapper(
        model_loader.load_module_instance,
        num_failures=failures,
        exc=CaikitRuntimeException(grpc.StatusCode.INTERNAL, "Yikes!"),
    )
    with mock.patch.object(model_loader, "load_module_instance", fail_wrapper):
        model_id = random_test_id()
        loaded_model = model_loader.load_model(
            model_id=model_id,
            local_model_path=Fixtures.get_good_model_path(),
            model_type=Fixtures.get_good_model_type(),
            retries=failures + 1,
        )
        assert loaded_model.model() is not None
        assert isinstance(loaded_model.model(), base.ModuleBase)
        assert loaded_model._retries == 1


def test_load_model_fail_callback_once(model_loader):
    """Make sure that a model which fails all of its retries will only call the
    fail callback once
    """
    failures = 3
    fail_wrapper = TempFailWrapper(
        model_loader.load_module_instance,
        num_failures=failures,
        exc=CaikitRuntimeException(grpc.StatusCode.INTERNAL, "Yikes!"),
    )
    with mock.patch.object(model_loader, "load_module_instance", fail_wrapper):
        model_id = random_test_id()
        fail_cb = mock.MagicMock()
        loaded_model = model_loader.load_model(
            model_id=model_id,
            local_model_path=Fixtures.get_good_model_path(),
            model_type=Fixtures.get_good_model_type(),
            fail_callback=fail_cb,
            retries=failures - 1,
        )
        with pytest.raises(CaikitRuntimeException):
            loaded_model.wait()
        fail_cb.assert_called_once()


def test_load_model_loaded_status(model_loader):
    """Test that we can observe the 'loaded' status of a model without waiting"""
    model_id = "loaded_status_test"
    release_event = threading.Event()
    model_mock = mock.MagicMock()

    def _load_module_instance_mock(*_, **__):
        release_event.wait()
        return model_mock

    with mock.patch.object(
        model_loader, "load_module_instance", _load_module_instance_mock
    ):
        loaded_model = model_loader.load_model(
            model_id=model_id,
            local_model_path=Fixtures.get_good_model_path(),
            model_type=Fixtures.get_good_model_type(),
        )
        # While still loading, it's not loaded
        assert not loaded_model.loaded()

        # Unblock loading and wait for the future to complete
        release_event.set()
        loaded_model._caikit_model_future.result()

        # It is done "loading" even if .model() has not been called
        assert not loaded_model.loading()
        assert loaded_model._model is None

        # After calling .model() it's also loaded
        assert loaded_model.model()
        assert loaded_model.loaded()
