# OpenCode Loading Safety Notes

These notes cover OpenCode-specific discovery and projection behavior. Skill
authority remains defined by the manifest and source skill.

- Use `/skills` to confirm which skills are actually visible.
- Do not use `style-doctor` as a patch applier.
- Do not let `style-doctor` update patch ledgers or mark maintainer decisions.
- Do not add new platform exposures without checking the skill's role, authority, and intended execution modes.
- Do not edit source through platform projection folders.
- ZYC-specific lessons require review before generator generalization.
