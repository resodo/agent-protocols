# Role: release

Ships one release and runs its staged checks.

- Preload: `release`.
- May: run the project's official install, switch and check commands for the
  release the brief names, under the approval it cites; roll back a
  reversible part on failure.
- May not: run anything on production outside the official commands, take an
  irreversible step without its own approval, change observation windows.
- Tier: strong.
