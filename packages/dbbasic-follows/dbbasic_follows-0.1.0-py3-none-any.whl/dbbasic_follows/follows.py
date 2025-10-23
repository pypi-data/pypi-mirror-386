"""Core API for dbbasic-follows - Social Graph Management"""

from pathlib import Path
from dbbasic_tsv import TSV
from datetime import datetime
from typing import Optional, List, Dict, Set


class Follows:
    """
    Main API class for managing social graph relationships (follows & friends).

    A follow is a one-directional relationship: user A follows user B.
    A friend relationship exists when both users follow each other.

    Example usage:
        follows = Follows()

        # Follow operations
        follows.follow(user_id=1, followee_id=2)
        follows.unfollow(user_id=1, followee_id=2)

        # Check relationships
        is_following = follows.is_following(1, 2)
        are_friends = follows.are_friends(1, 2)

        # Get lists
        followers = follows.get_followers(user_id=2)
        following = follows.get_following(user_id=1)
        friends = follows.get_friends(user_id=1)

        # Suggestions
        suggestions = follows.suggest_follows(user_id=1, limit=10)
        friend_suggestions = follows.suggest_friends(user_id=1, limit=10)
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize Follows API.

        Args:
            data_dir: Directory for data storage (default: "data" in current directory)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize TSV table for follows
        self.table = TSV(self.data_dir / "follows.tsv")

        # Create indexes for fast lookups
        self.table.create_index('follower_id')
        self.table.create_index('followee_id')

    def follow(self, follower_id: int, followee_id: int) -> bool:
        """
        Create a follow relationship.

        Args:
            follower_id: ID of the user who is following
            followee_id: ID of the user being followed

        Returns:
            bool: True if created, False if already exists or invalid

        Example:
            follows.follow(follower_id=1, followee_id=2)
        """
        # Validate: can't follow yourself
        if follower_id == followee_id:
            raise ValueError("Cannot follow yourself")

        # Check if already following
        if self.is_following(follower_id, followee_id):
            return False

        # Create follow relationship
        self.table.insert({
            'follower_id': follower_id,
            'followee_id': followee_id,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        })

        return True

    def unfollow(self, follower_id: int, followee_id: int) -> bool:
        """
        Remove a follow relationship.

        Args:
            follower_id: ID of the user who is unfollowing
            followee_id: ID of the user being unfollowed

        Returns:
            bool: True if deleted, False if didn't exist

        Example:
            follows.unfollow(follower_id=1, followee_id=2)
        """
        # Check if exists
        if not self.is_following(follower_id, followee_id):
            return False

        # Delete the relationship
        self.table.delete(where={
            'follower_id': follower_id,
            'followee_id': followee_id
        })

        return True

    def is_following(self, follower_id: int, followee_id: int) -> bool:
        """
        Check if user A follows user B.

        Args:
            follower_id: ID of potential follower
            followee_id: ID of potential followee

        Returns:
            bool: True if following relationship exists

        Example:
            if follows.is_following(1, 2):
                print("User 1 follows user 2")
        """
        results = self.table.select(where={
            'follower_id': follower_id,
            'followee_id': followee_id,
            'status': 'active'
        })
        return len(results) > 0

    def are_friends(self, user_id_a: int, user_id_b: int) -> bool:
        """
        Check if two users are friends (mutual follow).

        Args:
            user_id_a: First user ID
            user_id_b: Second user ID

        Returns:
            bool: True if both users follow each other

        Example:
            if follows.are_friends(1, 2):
                print("Users are friends")
        """
        return (self.is_following(user_id_a, user_id_b) and
                self.is_following(user_id_b, user_id_a))

    def get_followers(self, user_id: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Get list of users who follow the specified user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results (None = all)

        Returns:
            list: List of follower records

        Example:
            followers = follows.get_followers(user_id=2, limit=50)
        """
        results = self.table.select(where={
            'followee_id': user_id,
            'status': 'active'
        })

        if limit:
            results = results[:limit]

        return results

    def get_following(self, user_id: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Get list of users that the specified user follows.

        Args:
            user_id: ID of the user
            limit: Maximum number of results (None = all)

        Returns:
            list: List of following records

        Example:
            following = follows.get_following(user_id=1, limit=50)
        """
        results = self.table.select(where={
            'follower_id': user_id,
            'status': 'active'
        })

        if limit:
            results = results[:limit]

        return results

    def get_friends(self, user_id: int, limit: Optional[int] = None) -> List[int]:
        """
        Get list of friends (mutual follows) for a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results (None = all)

        Returns:
            list: List of friend user IDs

        Example:
            friends = follows.get_friends(user_id=1)
        """
        # Get users this person follows
        following = self.get_following(user_id)
        following_ids = {row['followee_id'] for row in following}

        # Get users who follow this person
        followers = self.get_followers(user_id)
        follower_ids = {row['follower_id'] for row in followers}

        # Friends are the intersection (mutual follows)
        friend_ids = list(following_ids & follower_ids)

        if limit:
            friend_ids = friend_ids[:limit]

        return friend_ids

    def get_follower_count(self, user_id: int) -> int:
        """Get count of followers for a user."""
        return len(self.get_followers(user_id))

    def get_following_count(self, user_id: int) -> int:
        """Get count of users being followed."""
        return len(self.get_following(user_id))

    def get_friend_count(self, user_id: int) -> int:
        """Get count of friends (mutual follows)."""
        return len(self.get_friends(user_id))

    def suggest_follows(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Suggest users to follow based on social graph.

        Algorithm:
        1. Find users followed by people you follow (2nd degree connections)
        2. Rank by number of mutual connections
        3. Exclude users already followed
        4. Exclude self

        Args:
            user_id: ID of the user to generate suggestions for
            limit: Maximum number of suggestions

        Returns:
            list: Suggested users with scores

        Example:
            suggestions = follows.suggest_follows(user_id=1, limit=10)
            # [{'user_id': 5, 'score': 3, 'mutual_connections': [2, 3, 4]}, ...]
        """
        # Get users this person follows
        following = self.get_following(user_id)
        following_ids = {row['followee_id'] for row in following}

        # Track potential suggestions and their scores
        suggestions: Dict[int, Set[int]] = {}  # user_id -> set of mutual connections

        # For each person we follow, get who they follow
        for follow_record in following:
            followee_id = follow_record['followee_id']
            second_degree = self.get_following(followee_id)

            for second_follow in second_degree:
                candidate_id = second_follow['followee_id']

                # Skip if it's the user themselves or already following
                if candidate_id == user_id or candidate_id in following_ids:
                    continue

                # Track the mutual connection
                if candidate_id not in suggestions:
                    suggestions[candidate_id] = set()
                suggestions[candidate_id].add(followee_id)

        # Convert to list with scores
        suggestion_list = [
            {
                'user_id': uid,
                'score': len(mutual),
                'mutual_connections': list(mutual)
            }
            for uid, mutual in suggestions.items()
        ]

        # Sort by score (descending)
        suggestion_list.sort(key=lambda x: x['score'], reverse=True)

        return suggestion_list[:limit]

    def suggest_friends(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Suggest potential friends (users who follow you but you don't follow back).

        Args:
            user_id: ID of the user to generate suggestions for
            limit: Maximum number of suggestions

        Returns:
            list: Suggested users to follow back

        Example:
            suggestions = follows.suggest_friends(user_id=1, limit=10)
        """
        # Get followers
        followers = self.get_followers(user_id)
        follower_ids = {row['follower_id'] for row in followers}

        # Get following
        following = self.get_following(user_id)
        following_ids = {row['followee_id'] for row in following}

        # Potential friends are followers we don't follow back
        potential_friends = follower_ids - following_ids

        # Get mutual connection counts for ranking
        suggestions = []
        for potential_friend_id in potential_friends:
            # Count mutual connections (people both users follow)
            their_following = self.get_following(potential_friend_id)
            their_following_ids = {row['followee_id'] for row in their_following}
            mutual_count = len(following_ids & their_following_ids)

            suggestions.append({
                'user_id': potential_friend_id,
                'score': mutual_count,
                'follows_you': True
            })

        # Sort by mutual connections
        suggestions.sort(key=lambda x: x['score'], reverse=True)

        return suggestions[:limit]

    def get_stats(self, user_id: int) -> Dict:
        """
        Get social graph statistics for a user.

        Returns:
            dict: Stats including follower/following/friend counts

        Example:
            stats = follows.get_stats(user_id=1)
            # {'followers': 100, 'following': 50, 'friends': 30}
        """
        return {
            'followers': self.get_follower_count(user_id),
            'following': self.get_following_count(user_id),
            'friends': self.get_friend_count(user_id)
        }
