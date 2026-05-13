from buddy_agent.references import REFERENCE_REPOS, repos_by_role


def test_reference_manifest_has_expected_entries():
    names = {repo.name for repo in REFERENCE_REPOS}

    assert "Hermes Agent" in names
    assert "Buddy Brain" in names
    assert "Awesome Hermes Agent" in names
    assert "Caveman" in names


def test_reference_manifest_clone_urls_are_https_git_urls():
    for repo in REFERENCE_REPOS:
        assert repo.clone_url.startswith("https://github.com/")
        assert repo.clone_url.endswith(".git")


def test_reference_manifest_roles_are_queryable():
    assert repos_by_role("ui")
    assert repos_by_role("creative")
