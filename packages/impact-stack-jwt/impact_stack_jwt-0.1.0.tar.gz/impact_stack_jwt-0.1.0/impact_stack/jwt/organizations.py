"""Utility functions to manipulate organization strings.

Organizations fully-qualified names of an organization using ">" to seperate layers within he
hierarchy. Impact Stack always uses "impact-stack" as the top-level organization. Examples:

    impact-stack
    impact-stack>organisation
    impact-stack>organisation>chapter
"""

import itertools
import typing as t


def iterate_parents(org: str, include_self=False):
    """Iterate over all parent organizations."""
    parts = org.split(">")
    if not include_self:
        parts.pop()
    return itertools.accumulate(parts, lambda a, b: f"{a}>{b}")


def ancestors(orgs: t.Iterable[str]) -> frozenset[str]:
    """Get all the ancestors of all the given organizations.

    Returns:
        A set of all organizations which are ancestors of at least one of the passed organizations.
    """
    return frozenset(itertools.chain.from_iterable(iterate_parents(org) for org in orgs))
