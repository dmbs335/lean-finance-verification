from __future__ import annotations

from pathlib import Path


def patch_proof() -> None:
    path = Path("LeanFinance/Control/SafeTreeSearch.lean")
    text = path.read_text(encoding="utf-8")
    old = '''theorem admitted_action_is_safe
    (certificate : TreeActionCertificate)
    (accepted : certificate.admissible = true) :
    certificate.safe = true := by
  simpa [admissible] using accepted |>.1
'''
    new = '''theorem admitted_action_is_safe
    (certificate : TreeActionCertificate)
    (accepted : certificate.admissible = true) :
    certificate.safe = true := by
  have facts :
      certificate.safe = true ∧
        (certificate.minimumSupport ≤ certificate.supportCount ∨
          certificate.isBaseline = true) := by
    simpa [admissible] using accepted
  exact facts.1
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("safe-tree proof anchor missing")
    path.write_text(text, encoding="utf-8")


def patch_aggregate() -> None:
    path = Path("LeanFinance/Control.lean")
    text = path.read_text(encoding="utf-8")
    imports = [
        "import LeanFinance.Control.SafeTreeSearch\n",
        "import LeanFinance.Control.SafeTreeSearchExample\n",
    ]
    anchor = "import LeanFinance.Control.Example\n"
    if anchor not in text:
        raise SystemExit("Control aggregate import anchor missing")
    for line in imports:
        if line not in text:
            text = text.replace(anchor, line + anchor, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_proof()
    patch_aggregate()
    print("integrated safe support-constrained tree search")


if __name__ == "__main__":
    main()
