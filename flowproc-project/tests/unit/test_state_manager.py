"""
Unit tests for the StateManager class.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from flowproc.presentation.gui.views.components.state_manager import StateManager, WindowState


class TestStateManager:
    """Test cases for the StateManager class."""

    @pytest.fixture
    def state_manager(self):
        """Create a fresh StateManager instance for each test."""
        return StateManager()

    def test_initialization(self, state_manager):
        """Test that StateManager initializes with default state."""
        assert state_manager is not None
        assert state_manager.preview_paths == []
        assert state_manager.last_csv is None
        assert state_manager.current_group_labels == []
        assert not state_manager.is_processing
        assert state_manager.last_output_dir is None

    def test_preview_paths_property(self, state_manager):
        """Test preview_paths property getter and setter."""
        # Test setting paths
        test_paths = ["/path/to/file1.csv", "/path/to/file2.csv"]
        state_manager.preview_paths = test_paths
        
        # Test getting paths (should return a copy)
        result_paths = state_manager.preview_paths
        assert result_paths == test_paths
        assert result_paths is not test_paths  # Should be a copy
        
        # Test that modifying the returned list doesn't affect the state
        result_paths.append("/path/to/file3.csv")
        assert state_manager.preview_paths == test_paths

    def test_last_csv_property(self, state_manager):
        """Test last_csv property getter and setter."""
        # Test setting a CSV path
        test_path = Path("/path/to/test.csv")
        state_manager.last_csv = test_path
        assert state_manager.last_csv == test_path
        
        # Test setting None
        state_manager.last_csv = None
        assert state_manager.last_csv is None

    def test_current_group_labels_property(self, state_manager):
        """Test current_group_labels property getter and setter."""
        # Test setting labels
        test_labels = ["Group A", "Group B", "Group C"]
        state_manager.current_group_labels = test_labels
        
        # Test getting labels (should return a copy)
        result_labels = state_manager.current_group_labels
        assert result_labels == test_labels
        assert result_labels is not test_labels  # Should be a copy
        
        # Test that modifying the returned list doesn't affect the state
        result_labels.append("Group D")
        assert state_manager.current_group_labels == test_labels

    def test_is_processing_property(self, state_manager):
        """Test is_processing property getter and setter."""
        # Test setting to True
        state_manager.is_processing = True
        assert state_manager.is_processing is True
        
        # Test setting to False
        state_manager.is_processing = False
        assert state_manager.is_processing is False

    def test_last_output_dir_property(self, state_manager):
        """Test last_output_dir property getter and setter."""
        # Test setting output directory
        test_dir = "/path/to/output"
        state_manager.last_output_dir = test_dir
        assert state_manager.last_output_dir == test_dir
        
        # Test setting None
        state_manager.last_output_dir = None
        assert state_manager.last_output_dir is None

    def test_clear_preview_data(self, state_manager):
        """Test clearing preview data."""
        # Set some preview data
        state_manager.preview_paths = ["/path/to/file1.csv"]
        state_manager.last_csv = Path("/path/to/file1.csv")
        
        # Clear preview data
        state_manager.clear_preview_data()
        
        # Check that data is cleared
        assert state_manager.preview_paths == []
        assert state_manager.last_csv is None

    def test_observer_notifications(self, state_manager, mock_observer):
        """Test that observers are notified of state changes."""
        # Add observer
        state_manager.add_observer(mock_observer)
        
        # Make a state change
        state_manager.preview_paths = ["/path/to/file.csv"]
        
        # Check that observer was notified
        mock_observer.assert_called_once()
        # Check that the first argument is the change type
        assert mock_observer.call_args[0][0] == 'preview_paths'

    def test_observer_removal(self, state_manager, mock_observer):
        """Test removing observers."""
        # Add and then remove observer
        state_manager.add_observer(mock_observer)
        state_manager.remove_observer(mock_observer)
        
        # Make a state change
        state_manager.preview_paths = ["/path/to/file.csv"]
        
        # Check that observer was not notified
        mock_observer.assert_not_called()

    def test_multiple_state_changes(self, state_manager, mock_observer):
        """Test multiple state changes trigger appropriate notifications."""
        state_manager.add_observer(mock_observer)
        
        # Make multiple state changes
        state_manager.preview_paths = ["/path/to/file1.csv"]
        state_manager.is_processing = True
        state_manager.current_group_labels = ["Group A"]
        
        # Check that observer was called for each change
        assert mock_observer.call_count == 3
        
        # Check the specific calls
        calls = mock_observer.call_args_list
        assert calls[0][0][0] == 'preview_paths'
        assert calls[1][0][0] == 'is_processing'
        assert calls[2][0][0] == 'current_group_labels'

    def test_clear_preview_data_notification(self, state_manager, mock_observer):
        """Test that clear_preview_data triggers notification."""
        state_manager.add_observer(mock_observer)
        
        # Clear preview data
        state_manager.clear_preview_data()
        
        # Check that observer was notified
        mock_observer.assert_called_once()
        assert mock_observer.call_args[0][0] == 'preview_data_cleared'

    def test_empty_list_handling(self, state_manager):
        """Test handling of empty lists."""
        # Test empty preview paths
        state_manager.preview_paths = []
        assert state_manager.preview_paths == []
        
        # Test empty group labels
        state_manager.current_group_labels = []
        assert state_manager.current_group_labels == []

    def test_none_handling(self, state_manager):
        """Test handling of None values."""
        # Test None for last_csv
        state_manager.last_csv = None
        assert state_manager.last_csv is None
        
        # Test None for last_output_dir
        state_manager.last_output_dir = None
        assert state_manager.last_output_dir is None

    def test_path_object_handling(self, state_manager):
        """Test handling of Path objects."""
        # Test Path object for last_csv
        test_path = Path("/path/to/test.csv")
        state_manager.last_csv = test_path
        assert state_manager.last_csv == test_path
        assert isinstance(state_manager.last_csv, Path)

    def test_observer_list_isolation(self, state_manager):
        """Test that observer list is isolated between instances."""
        manager1 = StateManager()
        manager2 = StateManager()
        
        observer1 = Mock()
        observer2 = Mock()
        
        # Add observers to different managers
        manager1.add_observer(observer1)
        manager2.add_observer(observer2)
        
        # Make changes to manager1
        manager1.preview_paths = ["/path/to/file.csv"]
        
        # Check that only observer1 was notified
        observer1.assert_called_once()
        observer2.assert_not_called()

    def test_state_copy_protection(self, state_manager):
        """Test that state is protected from external modification."""
        # Set some state
        test_paths = ["/path/to/file1.csv", "/path/to/file2.csv"]
        state_manager.preview_paths = test_paths
        
        # Try to modify the original list
        test_paths.append("/path/to/file3.csv")
        
        # State should remain unchanged
        assert state_manager.preview_paths == ["/path/to/file1.csv", "/path/to/file2.csv"]

    def test_multiple_observers(self, state_manager):
        """Test that multiple observers are notified correctly."""
        observer1 = Mock()
        observer2 = Mock()
        observer3 = Mock()
        
        # Add multiple observers
        state_manager.add_observer(observer1)
        state_manager.add_observer(observer2)
        state_manager.add_observer(observer3)
        
        # Make a state change
        state_manager.preview_paths = ["/path/to/file.csv"]
        
        # Check that all observers were notified
        observer1.assert_called_once()
        observer2.assert_called_once()
        observer3.assert_called_once()

    def test_observer_duplicate_removal(self, state_manager, mock_observer):
        """Test that removing a non-existent observer doesn't cause issues."""
        # Try to remove observer that was never added
        state_manager.remove_observer(mock_observer)
        
        # Add observer and make change
        state_manager.add_observer(mock_observer)
        state_manager.preview_paths = ["/path/to/file.csv"]
        
        # Should still be notified
        mock_observer.assert_called_once()

    def test_window_state_dataclass(self):
        """Test the WindowState dataclass."""
        # Test default values
        state = WindowState()
        assert state.preview_paths == []
        assert state.last_csv is None
        assert state.current_group_labels == []
        assert not state.is_processing
        assert state.last_output_dir is None
        
        # Test custom values
        custom_state = WindowState(
            preview_paths=["/path/to/file.csv"],
            last_csv=Path("/path/to/file.csv"),
            current_group_labels=["Group A"],
            is_processing=True,
            last_output_dir="/path/to/output"
        )
        assert custom_state.preview_paths == ["/path/to/file.csv"]
        assert custom_state.last_csv == Path("/path/to/file.csv")
        assert custom_state.current_group_labels == ["Group A"]
        assert custom_state.is_processing is True
        assert custom_state.last_output_dir == "/path/to/output" 