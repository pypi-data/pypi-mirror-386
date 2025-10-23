from typing import Any, List, Callable
from dataclasses import dataclass, field, InitVar

# Default policy point constants
POINTS_LOW = 1
POINTS_MEDIUM = 3
POINTS_HIGH = 9


def _evaluate_checks(obj: Any, checks: list[Callable[[Any], bool]]) -> tuple[bool, dict[str, bool]]:
    success = True
    results = {}
    for check in checks:
        result = check(obj)
        success = success and result
        results[getattr(check, "__name__", str(check))] = result
    return success, results


def _calculate_score(points_sum: int, points_max: int, calculation_factor: float = 100) -> float:
    """Calculate percentage score, handling edge cases."""
    return (points_sum / points_max) * calculation_factor if points_max > 0 else 0


@dataclass
class EvaluatedPolicy:
    """Detailed information about a policy evaluation."""

    name: str
    points: int
    failed: bool
    qualified: bool
    check_results: dict[str, bool] = field(default_factory=dict)
    qualifier_results: dict[str, bool] = field(default_factory=dict)


@dataclass
class Policy:
    """A policy with qualifiers and checks for evaluation."""

    name: str
    points: int
    checks: list[Callable[[Any], bool]]
    qualifiers: list[Callable[[Any], bool]] = field(default_factory=list)

    def __post_init__(self):
        if not self.checks:
            raise ValueError("Policy must have at least one check")
        if self.points <= 0:
            raise ValueError("Points must be positive")

    def get_points(self, obj: Any) -> int:
        """Get points if all checks pass, 0 otherwise."""
        return self.points if all(check(obj) for check in self.checks) else 0

    def evaluate(self, obj_to_evaluate: Any) -> EvaluatedPolicy:
        # Check if policy qualifies
        qualified, qualifier_results = _evaluate_checks(obj_to_evaluate, self.qualifiers)

        all_checks_pass, check_results = _evaluate_checks(obj_to_evaluate, self.checks)

        # Determine if policy failed (qualified but checks didn't all pass)
        failed = qualified and not all_checks_pass

        return EvaluatedPolicy(
            name=self.name,
            points=self.points,
            failed=failed,
            qualified=qualified,
            check_results=check_results,
            qualifier_results=qualifier_results,
        )


@dataclass
class GroupResult:
    name: str
    qualified: bool


@dataclass
class PolicyGroupResult(GroupResult):
    """Results of evaluating a PolicyGroup."""

    points_max: int
    points_sum: int
    evaluated_policies: List[EvaluatedPolicy] = field(default_factory=list)


@dataclass
class PolicyGroup:
    policies: list[Policy]
    name: str
    description: str = ""
    qualifiers: list[Callable[[Any], bool]] = field(default_factory=list)

    def evaluate(self, obj_to_evaluate: Any) -> PolicyGroupResult:
        evaluated_policies = []
        points_max = 0
        points_sum = 0

        qualified, _ = _evaluate_checks(obj_to_evaluate, self.qualifiers)

        if qualified:
            for policy in self.policies:
                evaluated_policy = policy.evaluate(obj_to_evaluate)

                if evaluated_policy.qualified:  # Add to totals if qualified
                    points_max += policy.points
                    points_sum += evaluated_policy.points if not evaluated_policy.failed else 0

                evaluated_policies.append(evaluated_policy)

        return PolicyGroupResult(
            points_max=points_max,
            points_sum=points_sum,
            evaluated_policies=evaluated_policies,
            name=self.name,
            qualified=qualified,
        )


@dataclass
class TierResult:
    """Holds the evaluation result for a single tier."""

    tier: int
    points_max: int
    points_sum: int
    evaluated_policies: List[EvaluatedPolicy] = field(default_factory=list)


@dataclass
class TieredPolicyGroupResult(GroupResult):
    """Results of evaluating a TieredPolicyGroup."""

    tier_results: dict[int, TierResult] = field(default_factory=dict)

    def points_max(self) -> int:
        return sum(r.points_max for r in self.tier_results.values())

    def points_sum(self) -> int:
        return sum(r.points_sum for r in self.tier_results.values())


@dataclass
class TieredPolicyGroup:
    """Evaluates policies in tiers where failure in one tier affects subsequent tiers."""

    name: str
    description: str = ""
    _tiered_policies: dict[int, list[Policy]] = field(default_factory=dict)
    tiered_policies: InitVar[dict[int, list[Policy]] | None] = None
    qualifiers: list[Callable[[Any], bool]] = field(default_factory=list)

    def __post_init__(self, tiered_policies):
        if tiered_policies:
            self.add_tiers(tiered_policies)

    def add_tier(self, tier: int, policies: list[Policy]):
        if tier < 1:
            raise ValueError("Tier must be 1 or higher")
        if tier in self._tiered_policies:
            raise ValueError(f"Tier {tier} already exists")
        if self._tiered_policies and tier != max(self._tiered_policies.keys()) + 1:
            raise ValueError("Tier must increment by one from the previous highest tier")
        self._tiered_policies[tier] = policies

    def add_tiers(self, tiered_policies: dict[int, list[Policy]]):
        """Add multiple tiers at once."""
        if not tiered_policies:
            raise ValueError("Tiered policies cannot be empty")

        sorted_tiers = sorted(tiered_policies.keys())
        if sorted_tiers != list(range(1, len(sorted_tiers) + 1)):
            raise ValueError("Tier keys must form a complete sequence starting from 1 (e.g., 1, 2, 3)")

        for tier, policies in tiered_policies.items():
            self.add_tier(tier, policies)

    def evaluate(self, obj_to_evaluate: Any) -> TieredPolicyGroupResult:
        """Evaluate tiers, where failure in one tier affects subsequent tiers."""
        results = {}
        tier_failed = False

        policy_group_qualified, _ = _evaluate_checks(obj_to_evaluate, self.qualifiers)

        if not policy_group_qualified:
            return TieredPolicyGroupResult(
                name=self.name,
                tier_results=results,
                qualified=policy_group_qualified,
            )

        for tier_num in sorted(self._tiered_policies.keys()):
            policy_group = PolicyGroup(name="temp", policies=self._tiered_policies[tier_num])
            policy_group_result = policy_group.evaluate(obj_to_evaluate)

            if tier_failed or policy_group_result.points_max == 0:
                points_sum = 0
            else:
                points_sum = policy_group_result.points_sum
                # Mark subsequent tiers as failed if this tier didn't achieve max points
                if policy_group_result.points_sum < policy_group_result.points_max:
                    tier_failed = True

            results[tier_num] = TierResult(
                tier=tier_num,
                points_max=policy_group_result.points_max,
                points_sum=points_sum,
                evaluated_policies=policy_group_result.evaluated_policies,
            )

        return TieredPolicyGroupResult(
            name=self.name,
            tier_results=results,
            qualified=policy_group_qualified,
        )
