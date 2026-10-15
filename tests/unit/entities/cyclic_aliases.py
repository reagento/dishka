# Cyclic PEP 695 aliases used to exercise unwrap_type_alias's cycle guard.
# Kept in a py312 helper module so the test package still parses on
# Python 3.10/3.11, where the importing test module is skipped.
type SelfCycle = SelfCycle
type MutualA = MutualB
type MutualB = MutualA
