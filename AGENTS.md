# Working with the student

This is a school project for learning infrastructure. Use `roadmap.md` as the
current project goal.

Before changing any file, explain the proposed change and ask the student
for permission. Reading files and running read-only inspection commands are
allowed without permission.

Teach while working: explain the relevant concept, why each change is needed,
and how to verify it. Prefer small steps the student can inspect and repeat.
Do not mark a roadmap item complete until its stated checks pass.

Keep Prometheus, Pushgateway, and `/metrics` internal. Use bounded metric
labels and avoid request-specific or sensitive values. Never commit secrets.

Respect the file ownership split in `roadmap.md` when coordinating work.
