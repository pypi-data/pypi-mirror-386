"""Unit tests for Repository and RepositoryManager."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from taskrepo.core.repository import Repository, RepositoryManager
from taskrepo.core.task import Task


def test_repository_creation():
    """Test creating a repository."""
    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "tasks-test"
        repo_path.mkdir()

        repo = Repository(repo_path)

        assert repo.name == "test"
        assert repo.path == repo_path
        assert repo.tasks_dir.exists()


def test_repository_invalid_name():
    """Test that invalid repository name raises ValueError."""
    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "invalid-name"
        repo_path.mkdir()

        with pytest.raises(ValueError, match="Must start with 'tasks-'"):
            Repository(repo_path)


def test_repository_save_and_load_task():
    """Test saving and loading tasks in a repository."""
    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "tasks-test"
        repo_path.mkdir()

        repo = Repository(repo_path)

        # Create and save task
        task = Task(id="001", title="Test task", status="pending", priority="M")
        repo.save_task(task)

        # Load task
        loaded_task = repo.get_task("001")
        assert loaded_task is not None
        assert loaded_task.id == "001"
        assert loaded_task.title == "Test task"
        assert loaded_task.repo == "test"


def test_repository_list_tasks():
    """Test listing tasks in a repository."""
    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "tasks-test"
        repo_path.mkdir()

        repo = Repository(repo_path)

        # Create multiple tasks
        for i in range(1, 4):
            task = Task(id=f"{i:03d}", title=f"Task {i}", status="pending", priority="M")
            repo.save_task(task)

        # List tasks
        tasks = repo.list_tasks()
        assert len(tasks) == 3
        assert all(task.repo == "test" for task in tasks)


def test_repository_next_task_id():
    """Test generating next task ID."""
    import uuid

    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "tasks-test"
        repo_path.mkdir()

        repo = Repository(repo_path)

        # First task ID should be a valid UUID
        task_id_1 = repo.next_task_id()
        assert isinstance(task_id_1, str)
        # Verify it's a valid UUID by trying to parse it
        uuid.UUID(task_id_1)

        # Create a task
        task = Task(id=task_id_1, title="Task 1", status="pending", priority="M")
        repo.save_task(task)

        # Next task ID should also be a UUID and different from the first
        task_id_2 = repo.next_task_id()
        assert isinstance(task_id_2, str)
        uuid.UUID(task_id_2)
        assert task_id_1 != task_id_2


def test_repository_get_projects():
    """Test getting unique projects."""
    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "tasks-test"
        repo_path.mkdir()

        repo = Repository(repo_path)

        # Create tasks with projects
        Task(id="001", title="Task 1", project="project-a").save(repo_path)
        Task(id="002", title="Task 2", project="project-b").save(repo_path)
        Task(id="003", title="Task 3", project="project-a").save(repo_path)

        projects = repo.get_projects()
        assert len(projects) == 2
        assert "project-a" in projects
        assert "project-b" in projects


def test_repository_manager_discover():
    """Test discovering repositories."""
    with TemporaryDirectory() as tmpdir:
        parent_dir = Path(tmpdir)

        # Create multiple repositories
        (parent_dir / "tasks-repo1").mkdir()
        (parent_dir / "tasks-repo2").mkdir()
        (parent_dir / "not-a-repo").mkdir()  # Should be ignored

        manager = RepositoryManager(parent_dir)
        repos = manager.discover_repositories()

        assert len(repos) == 2
        assert {repo.name for repo in repos} == {"repo1", "repo2"}


def test_repository_manager_create():
    """Test creating a new repository."""
    with TemporaryDirectory() as tmpdir:
        parent_dir = Path(tmpdir)
        manager = RepositoryManager(parent_dir)

        repo = manager.create_repository("new-repo")

        assert repo.name == "new-repo"
        assert repo.path.exists()
        assert repo.tasks_dir.exists()
        # Check initial commit was created
        assert not repo.git_repo.head.is_detached
        # Check README was created
        readme_path = repo.path / "README.md"
        assert readme_path.exists()
        # Check .gitkeep was created
        gitkeep_path = repo.tasks_dir / ".gitkeep"
        assert gitkeep_path.exists()


def test_repository_manager_list_all_tasks():
    """Test listing tasks across all repositories."""
    with TemporaryDirectory() as tmpdir:
        parent_dir = Path(tmpdir)

        # Create repositories with tasks
        repo1_path = parent_dir / "tasks-repo1"
        repo1_path.mkdir()
        repo1 = Repository(repo1_path)
        Task(id="001", title="Task 1").save(repo1.path)

        repo2_path = parent_dir / "tasks-repo2"
        repo2_path.mkdir()
        repo2 = Repository(repo2_path)
        Task(id="001", title="Task 2").save(repo2.path)

        manager = RepositoryManager(parent_dir)
        all_tasks = manager.list_all_tasks()

        assert len(all_tasks) == 2
        assert {task.repo for task in all_tasks} == {"repo1", "repo2"}


def test_repository_generate_readme():
    """Test generating README with active tasks table."""
    from datetime import datetime, timedelta

    from taskrepo.core.config import Config

    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "tasks-test"
        repo_path.mkdir()

        repo = Repository(repo_path)

        # Create config with default sorting
        config_path = Path(tmpdir) / ".taskreporc"
        config = Config(config_path)

        # Create tasks with different statuses and due dates
        Task(
            id="001",
            title="Pending task",
            status="pending",
            priority="H",
            project="backend",
            assignees=["@alice"],
            tags=["bug"],
            due=datetime.now() + timedelta(days=2),
        ).save(repo_path)

        Task(
            id="002",
            title="In progress task",
            status="in-progress",
            priority="M",
            assignees=["@bob", "@charlie"],
            due=datetime.now() + timedelta(days=60),
        ).save(repo_path)

        Task(
            id="003",
            title="Completed task",
            status="completed",
            priority="L",
        ).save(repo_path)

        # Generate README
        readme_path = repo.generate_readme(config)

        assert readme_path.exists()
        readme_content = readme_path.read_text()

        # Check header
        assert "# Tasks - test" in readme_content
        assert "## Active Tasks" in readme_content

        # Check that active tasks are included
        assert "Pending task" in readme_content
        assert "In progress task" in readme_content

        # Check that completed task is NOT included
        assert "Completed task" not in readme_content

        # Check table structure with Countdown and Links columns
        assert (
            "| ID | Title | Status | Priority | Assignees | Project | Tags | Links | Due | Countdown |"
            in readme_content
        )

        # Check task details
        assert "@alice" in readme_content
        assert "@bob, @charlie" in readme_content
        assert "backend" in readme_content
        assert "bug" in readme_content

        # Check emoji indicators
        assert "🔴" in readme_content  # High priority emoji
        assert "🟡" in readme_content  # Medium priority emoji
        assert "⏳" in readme_content  # Pending status emoji
        assert "🔄" in readme_content  # In progress status emoji

        # Check countdown (could be "tomorrow" or "2 days" depending on exact time)
        assert "⏰" in readme_content  # Urgent countdown emoji
        assert "📅 1 month" in readme_content  # Future countdown

        # Check footer
        assert "_Last updated:" in readme_content


def test_repository_generate_readme_no_active_tasks():
    """Test generating README when there are no active tasks."""
    from taskrepo.core.config import Config

    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "tasks-test"
        repo_path.mkdir()

        repo = Repository(repo_path)

        # Create config
        config_path = Path(tmpdir) / ".taskreporc"
        config = Config(config_path)

        # Create only completed tasks
        Task(id="001", title="Completed task", status="completed").save(repo_path)

        # Generate README
        readme_path = repo.generate_readme(config)

        assert readme_path.exists()
        readme_content = readme_path.read_text()

        # Check that it shows no active tasks message
        assert "No active tasks." in readme_content
        assert "# Tasks - test" in readme_content


def test_repository_manager_create_github_validation():
    """Test that GitHub parameters are validated properly."""
    with TemporaryDirectory() as tmpdir:
        parent_dir = Path(tmpdir)
        manager = RepositoryManager(parent_dir)

        # Test missing org parameter
        with pytest.raises(ValueError, match="GitHub organization/owner is required"):
            manager.create_repository("test-repo", github_enabled=True, visibility="private")

        # Test missing visibility parameter
        with pytest.raises(ValueError, match="Repository visibility is required"):
            manager.create_repository("test-repo", github_enabled=True, github_org="testorg")

        # Test invalid visibility
        with pytest.raises(ValueError, match="Visibility must be"):
            manager.create_repository("test-repo", github_enabled=True, github_org="testorg", visibility="invalid")


def test_repository_manager_create_github_integration(monkeypatch):
    """Test GitHub repository creation with mocked gh CLI."""
    from unittest.mock import MagicMock

    with TemporaryDirectory() as tmpdir:
        parent_dir = Path(tmpdir)
        manager = RepositoryManager(parent_dir)

        # Mock GitHub utilities
        mock_create_github_repo = MagicMock(return_value="https://github.com/testorg/tasks-test-repo")
        mock_setup_git_remote = MagicMock()
        mock_push_to_remote = MagicMock()

        # Patch the functions in the utils.github module
        monkeypatch.setattr("taskrepo.utils.github.create_github_repo", mock_create_github_repo)
        monkeypatch.setattr("taskrepo.utils.github.setup_git_remote", mock_setup_git_remote)
        monkeypatch.setattr("taskrepo.utils.github.push_to_remote", mock_push_to_remote)

        # Create repository with GitHub
        repo = manager.create_repository("test-repo", github_enabled=True, github_org="testorg", visibility="private")

        # Verify local repository was created
        assert repo.name == "test-repo"
        assert repo.path.exists()
        assert (repo.path / "README.md").exists()

        # Verify GitHub functions were called
        mock_create_github_repo.assert_called_once_with("testorg", "tasks-test-repo", "private")
        mock_setup_git_remote.assert_called_once()
        mock_push_to_remote.assert_called_once()
