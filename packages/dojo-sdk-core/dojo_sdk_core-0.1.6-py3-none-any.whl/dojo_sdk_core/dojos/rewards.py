"""
Centralized reward functions for all dojos.

This module contains all reward validation functions used across different dojos.
Each function takes (initial_state, final_state) and returns (score, reason).
"""

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


def _validate_get_2048(initial_state: Dict[str, Any], final_state: Dict[str, Any]) -> Tuple[float, str]:
    """Validate that a 2048 tile is present on the board."""
    if "board" not in final_state:
        return 0.0, "No board in final state"

    logger.debug(f"running reward function on state: {final_state}")
    if 2048 in final_state["board"]:
        return 1.0, "A 2048 tile is present."
    return 0.0, "No 2048 tile is present."


def _validate_search_for_dzaka(initial_state: Dict[str, Any], final_state: Dict[str, Any]) -> Tuple[float, str]:
    """Validate that the user successfully searched for Dzaka Athif."""
    logger.debug(f"Running reward function on state: {final_state}")
    
    # Check 1: currentView is "search"
    if final_state.get("currentView") != "search":
        return 0.0, f"Not on search page, current view: {final_state.get('currentView')}"
    
    # Check 2: searchQuery contains "dzaka" (case insensitive)
    query = final_state.get("searchQuery", "").lower()
    if "dzaka" not in query:
        return 0.0, f"Search query doesn't contain 'dzaka': {final_state.get('searchQuery')}"
    
    # Check 3: Dzaka Athif in search results
    search_results = final_state.get("searchResults", {})
    people = search_results.get("allPeople", [])
    
    dzaka_found = any(
        user.get("name") == "Dzaka Athif" 
        for user in people
    )
    
    if dzaka_found:
        return 1.0, "Successfully searched for Dzaka Athif"
    
    return 0.0, f"Dzaka Athif not found in search results. Found {len(people)} people."


def _validate_drag_to_different_column(initial_state: Dict[str, Any], final_state: Dict[str, Any]) -> Tuple[float, str]:
    """Validate that an issue was moved to a different column."""
    if "issues" not in final_state:
        return 0.0, "No issues in final state"

    logger.debug(f"Running reward function on state: {final_state}")
    
    # Find the issue we're tracking (VSS-101)
    target_issue = next(
        (issue for issue in final_state["issues"] if issue.get("identifier") == "VSS-101"),
        None
    )
    
    if not target_issue:
        return 0.0, "Target issue VSS-101 not found in final state"
    
    # Check if it moved to in_progress status
    if target_issue.get("status") == "in_progress" and target_issue.get("assigneeId") == "1":
        return 1.0, "Issue VSS-101 successfully moved to In Progress column for user 1"
    
    return 0.0, f"Issue VSS-101 has status={target_issue.get('status')}, assigneeId={target_issue.get('assigneeId')}, expected status=in_progress, assigneeId=1"


def _validate_drag_two_issues_same_user(initial_state: Dict[str, Any], final_state: Dict[str, Any]) -> Tuple[float, str]:
    """Validate that two issues were moved within the same user's board."""
    if "issues" not in final_state:
        return 0.0, "No issues in final state"

    logger.debug(f"Running reward function on state: {final_state}")
    
    # Find both target issues
    issue_101 = next(
        (issue for issue in final_state["issues"] if issue.get("identifier") == "VSS-101"),
        None
    )
    issue_106 = next(
        (issue for issue in final_state["issues"] if issue.get("identifier") == "VSS-106"),
        None
    )
    
    if not issue_101:
        return 0.0, "Target issue VSS-101 not found in final state"
    if not issue_106:
        return 0.0, "Target issue VSS-106 not found in final state"
    
    # Check both issues
    issue_101_correct = (
        issue_101.get("status") == "in_progress" and 
        issue_101.get("assigneeId") == "1"
    )
    issue_106_correct = (
        issue_106.get("status") == "queued" and 
        issue_106.get("assigneeId") == "1"
    )
    
    if issue_101_correct and issue_106_correct:
        return 1.0, "Both issues successfully moved to target columns for user 1"
    
    errors = []
    if not issue_101_correct:
        errors.append(f"VSS-101: status={issue_101.get('status')}, assigneeId={issue_101.get('assigneeId')} (expected in_progress, 1)")
    if not issue_106_correct:
        errors.append(f"VSS-106: status={issue_106.get('status')}, assigneeId={issue_106.get('assigneeId')} (expected queued, 1)")
    
    return 0.0, "; ".join(errors)


# Registry of all reward functions for easy lookup
REWARD_FUNCTIONS = {
    "_validate_get_2048": _validate_get_2048,
    "_validate_search_for_dzaka": _validate_search_for_dzaka,
    "_validate_drag_to_different_column": _validate_drag_to_different_column,
    "_validate_drag_two_issues_same_user": _validate_drag_two_issues_same_user,
}


def get_reward_function(name: str):
    """Get a reward function by name."""
    return REWARD_FUNCTIONS.get(name)
