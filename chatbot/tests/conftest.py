import sys
from unittest.mock import MagicMock


class _FakeSessionState(dict):
    """A dict subclass that mimics st.session_state access patterns."""
    pass


_mock_st = MagicMock()
_mock_st.session_state = _FakeSessionState()

sys.modules.setdefault("streamlit", _mock_st)
