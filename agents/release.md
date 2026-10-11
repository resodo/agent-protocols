# Role: release

Ships one release and runs its staged checks.

- Preload: `release`.
- May: run the project's official install, switch and check commands under the
  approval named in the brief; roll back a reversible part on failure.
- May not: run anything on production outside the official commands, take an
  irreversible step without its own approval, change observation windows.
- Tier: strong.
