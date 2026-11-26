"""Recommendation service.

Evaluates every active scheme for a user with the transparent rules engine
and (optionally) stores the results as Recommendation rows so the dashboard
and recommendations page can read them back quickly.
"""
from extensions import db
from models import Scheme, Recommendation
from services import rules_engine


def evaluate_all(user):
    """Return a list of (scheme, result_dict) for every active scheme."""
    profile = user.profile_dict()
    results = []
    schemes = Scheme.query.filter_by(is_active=True).all()
    for scheme in schemes:
        outcome = rules_engine.evaluate(profile, scheme.rules)
        results.append((scheme, outcome))
    # best matches first
    results.sort(key=lambda t: t[1]["score"], reverse=True)
    return results


def refresh_for_user(user):
    """Recompute and persist recommendations for the user. Returns the count."""
    Recommendation.query.filter_by(user_id=user.id).delete()
    results = evaluate_all(user)
    for scheme, outcome in results:
        rec = Recommendation(
            user_id=user.id,
            scheme_id=scheme.id,
            result=outcome["result"],
            score=outcome["score"],
            reasons="\n".join(outcome["reasons"]),
        )
        db.session.add(rec)
    db.session.commit()
    return len(results)


def top_recommendations(user, limit=3):
    """Eligible / likely schemes with the highest score, for the dashboard."""
    recs = (
        Recommendation.query.filter_by(user_id=user.id)
        .order_by(Recommendation.score.desc())
        .all()
    )
    good = [r for r in recs if r.result in ("Eligible", "Likely Eligible")]
    return good[:limit] if good else recs[:limit]
