from pathlib import Path

from agent.profile import load_profile


def test_profile__reads_fresher_sources(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
candidate:
  skills:
    - Python
    - Java
  locations:
    - Remote
    - Delhi
  experience_years: 1
  resume_path: JobBot/resume.txt

search:
  max_age_hours: 8
  match_threshold: 35
  email_min_score: 45
  exclude_terms:
    - C2C

sources:
  greenhouse:
    - google
  lever:
    - thoughtworks
  workday: []
  naukri:
    - naukri.com
  freshers:
    - internshala.com
  generic_web:
    - https://jobs.github.com/positions.json
""".strip(),
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.sources.greenhouse == ["google"]
    assert profile.sources.lever == ["thoughtworks"]
    assert profile.sources.naukri == ["naukri.com"]
    assert profile.sources.freshers == ["internshala.com"]
    assert profile.sources.generic_web == ["https://jobs.github.com/positions.json"]
