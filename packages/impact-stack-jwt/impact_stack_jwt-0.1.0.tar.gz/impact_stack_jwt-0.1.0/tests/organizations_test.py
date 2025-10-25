"""Test organization utilities."""

from impact_stack import jwt


def test_ancestors():
    """Run a few scenarios for the ancestors calculation."""
    assert jwt.ancestors(["root>parent>org1"]) == {"root", "root>parent"}
    assert jwt.ancestors(["root>parent>org1", "root>parent>org2"]) == {"root", "root>parent"}
    assert jwt.ancestors(["root>parent>org1", "root>other>org"]) == {
        "root",
        "root>parent",
        "root>other",
    }
    assert jwt.ancestors(["root>parent", "root>parent>org"]) == {"root", "root>parent"}
