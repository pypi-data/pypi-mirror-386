import pytest

parametrize = pytest.mark.parametrize("param1, param2", [("A", "A"), (2, 2), (3, 3), (4, 5)])


@pytest.fixture(scope="session")
def print_x():
    """Fixture that runs before any tests in the session."""
    print("Running setup for the test session.")
    yield
    print("Running teardown for the test session.")


@pytest.mark.xfail(reason="This feature is not implemented yet")
def test_expected_to_fail():
    # This will FAIL → pytest marks it as XFAIL
    assert 2 + 2 == 5


@pytest.mark.xfail(reason="Known bug, not fixed yet")
def test_unexpected_pass():
    # This actually passes, even though we marked it xfail
    assert 2 + 2 == 4


@pytest.mark.abc
def test_abc():
    """A dummy test to ensure pytest is working."""
    assert False, "This is a dummy test to ensure pytest is working."


class TestDummy:
    @pytest.mark.test_pass
    def test_pass(self, print_x):  # pylint: disable=R6301, W0613,  W0621
        assert True

    @pytest.mark.test_fail
    def test_false(self):  # pylint: disable=R6301, W0613,  W0621
        assert False, {"message": "This test is expected to fail."}  # noqa: B011

    @pytest.mark.fail2skip(reason="This test is expected to fail and be skipped.")
    def test_fail2skip(self):  # pylint: disable=R6301, W0613,  W0621
        assert False, {"message": "This test is expected to fail."}  # noqa: B011

    @parametrize
    def test_with_parameters_1(self, param1, param2):  # pylint: disable=R6301, W0613,  W0621
        assert param1 != param2, {
            "expected_value": param1,
            "actual_value": param2,
            "diagnostic_info": {"param1": param1, "param2": param2},
        }

    @pytest.mark.parametrize("param1, param2", [(1, 1), (2, 2), (3, 3), (4, 5)])
    def test_with_parameters_2(self, param1, param2):  # pylint: disable=R6301, W0613,  W0621
        assert param1 != param2


def test_dummy_1():
    """A dummy test to ensure pytest is working."""
    assert True, "This is a dummy test 1 to ensure pytest is working."


@pytest.mark.skip
def test_dummy_2():
    """A dummy test to ensure pytest is working."""
    assert True, "This is a dummy test 2 to ensure pytest is working."


@pytest.mark.skip
class TestDummy2:
    def test_pass(self, print_x):  # pylint: disable=R6301, W0613,  W0621
        assert True

    def test_pass2(self, print_x):  # pylint: disable=R6301, W0613,  W0621
        assert True
