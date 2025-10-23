"""Tests for dbbasic-follows"""

import pytest
from pathlib import Path
import tempfile
import shutil
from dbbasic_follows import Follows


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def follows(temp_data_dir):
    """Create Follows instance with temp data dir"""
    return Follows(data_dir=temp_data_dir)


class TestFollowOperations:
    """Test core follow/unfollow operations"""

    def test_follow(self, follows):
        """Test creating a follow relationship"""
        result = follows.follow(follower_id=1, followee_id=2)
        assert result is True
        assert follows.is_following(1, 2) is True

    def test_follow_duplicate(self, follows):
        """Test that duplicate follows return False"""
        follows.follow(1, 2)
        result = follows.follow(1, 2)
        assert result is False

    def test_follow_self(self, follows):
        """Test that users cannot follow themselves"""
        with pytest.raises(ValueError, match="Cannot follow yourself"):
            follows.follow(1, 1)

    def test_unfollow(self, follows):
        """Test unfollowing a user"""
        follows.follow(1, 2)
        result = follows.unfollow(1, 2)
        assert result is True
        assert follows.is_following(1, 2) is False

    def test_unfollow_nonexistent(self, follows):
        """Test unfollowing when not following returns False"""
        result = follows.unfollow(1, 2)
        assert result is False

    def test_is_following_false(self, follows):
        """Test is_following returns False when not following"""
        assert follows.is_following(1, 2) is False


class TestFriendRelationships:
    """Test friend relationship detection"""

    def test_are_friends_both_follow(self, follows):
        """Test that mutual follows create friendship"""
        follows.follow(1, 2)
        follows.follow(2, 1)
        assert follows.are_friends(1, 2) is True

    def test_are_friends_one_way(self, follows):
        """Test that one-way follow is not friendship"""
        follows.follow(1, 2)
        assert follows.are_friends(1, 2) is False

    def test_are_friends_no_relationship(self, follows):
        """Test that no relationship is not friendship"""
        assert follows.are_friends(1, 2) is False

    def test_are_friends_symmetric(self, follows):
        """Test that friendship is symmetric"""
        follows.follow(1, 2)
        follows.follow(2, 1)
        assert follows.are_friends(1, 2) is True
        assert follows.are_friends(2, 1) is True


class TestGetRelationships:
    """Test retrieving followers, following, friends"""

    def test_get_followers(self, follows):
        """Test getting list of followers"""
        follows.follow(1, 3)
        follows.follow(2, 3)
        follows.follow(4, 3)

        followers = follows.get_followers(user_id=3)
        follower_ids = [f['follower_id'] for f in followers]

        assert len(followers) == 3
        assert set(follower_ids) == {1, 2, 4}

    def test_get_followers_empty(self, follows):
        """Test getting followers when none exist"""
        followers = follows.get_followers(user_id=1)
        assert followers == []

    def test_get_followers_with_limit(self, follows):
        """Test getting followers with limit"""
        for i in range(10):
            follows.follow(i, 100)

        followers = follows.get_followers(user_id=100, limit=5)
        assert len(followers) == 5

    def test_get_following(self, follows):
        """Test getting list of following"""
        follows.follow(1, 2)
        follows.follow(1, 3)
        follows.follow(1, 4)

        following = follows.get_following(user_id=1)
        followee_ids = [f['followee_id'] for f in following]

        assert len(following) == 3
        assert set(followee_ids) == {2, 3, 4}

    def test_get_following_empty(self, follows):
        """Test getting following when none exist"""
        following = follows.get_following(user_id=1)
        assert following == []

    def test_get_following_with_limit(self, follows):
        """Test getting following with limit"""
        for i in range(10):
            follows.follow(1, i + 100)

        following = follows.get_following(user_id=1, limit=5)
        assert len(following) == 5

    def test_get_friends(self, follows):
        """Test getting list of friends"""
        # Create mutual follows (friends)
        follows.follow(1, 2)
        follows.follow(2, 1)
        follows.follow(1, 3)
        follows.follow(3, 1)

        # Create one-way follow (not friend)
        follows.follow(1, 4)

        friends = follows.get_friends(user_id=1)
        assert len(friends) == 2
        assert set(friends) == {2, 3}

    def test_get_friends_empty(self, follows):
        """Test getting friends when none exist"""
        follows.follow(1, 2)  # One-way only
        friends = follows.get_friends(user_id=1)
        assert friends == []

    def test_get_friends_with_limit(self, follows):
        """Test getting friends with limit"""
        for i in range(10):
            follows.follow(1, i + 100)
            follows.follow(i + 100, 1)

        friends = follows.get_friends(user_id=1, limit=5)
        assert len(friends) == 5


class TestCounts:
    """Test count methods"""

    def test_get_follower_count(self, follows):
        """Test counting followers"""
        follows.follow(1, 10)
        follows.follow(2, 10)
        follows.follow(3, 10)

        assert follows.get_follower_count(10) == 3

    def test_get_follower_count_zero(self, follows):
        """Test counting followers when zero"""
        assert follows.get_follower_count(1) == 0

    def test_get_following_count(self, follows):
        """Test counting following"""
        follows.follow(1, 2)
        follows.follow(1, 3)
        follows.follow(1, 4)

        assert follows.get_following_count(1) == 3

    def test_get_following_count_zero(self, follows):
        """Test counting following when zero"""
        assert follows.get_following_count(1) == 0

    def test_get_friend_count(self, follows):
        """Test counting friends"""
        follows.follow(1, 2)
        follows.follow(2, 1)
        follows.follow(1, 3)
        follows.follow(3, 1)
        follows.follow(1, 4)  # One-way, not a friend

        assert follows.get_friend_count(1) == 2

    def test_get_friend_count_zero(self, follows):
        """Test counting friends when zero"""
        assert follows.get_friend_count(1) == 0


class TestSuggestions:
    """Test suggestion algorithms"""

    def test_suggest_follows_second_degree(self, follows):
        """Test follow suggestions from 2nd degree connections"""
        # User 1 follows User 2
        follows.follow(1, 2)

        # User 2 follows Users 3, 4, 5
        follows.follow(2, 3)
        follows.follow(2, 4)
        follows.follow(2, 5)

        # Get suggestions for User 1
        suggestions = follows.suggest_follows(user_id=1, limit=10)

        # Should suggest 3, 4, 5
        suggested_ids = [s['user_id'] for s in suggestions]
        assert set(suggested_ids) == {3, 4, 5}

    def test_suggest_follows_excludes_self(self, follows):
        """Test that suggestions don't include self"""
        follows.follow(1, 2)
        follows.follow(2, 1)  # Creates circular reference

        suggestions = follows.suggest_follows(user_id=1, limit=10)
        suggested_ids = [s['user_id'] for s in suggestions]

        assert 1 not in suggested_ids

    def test_suggest_follows_excludes_already_following(self, follows):
        """Test that suggestions exclude users already followed"""
        follows.follow(1, 2)
        follows.follow(1, 3)  # Already following 3
        follows.follow(2, 3)

        suggestions = follows.suggest_follows(user_id=1, limit=10)
        suggested_ids = [s['user_id'] for s in suggestions]

        assert 3 not in suggested_ids

    def test_suggest_follows_ranking(self, follows):
        """Test that suggestions are ranked by mutual connections"""
        # User 1 follows 2, 3, 4
        follows.follow(1, 2)
        follows.follow(1, 3)
        follows.follow(1, 4)

        # Users 2, 3, 4 all follow User 10 (score: 3)
        follows.follow(2, 10)
        follows.follow(3, 10)
        follows.follow(4, 10)

        # Only User 2 follows User 11 (score: 1)
        follows.follow(2, 11)

        suggestions = follows.suggest_follows(user_id=1, limit=10)

        # User 10 should be ranked higher
        assert suggestions[0]['user_id'] == 10
        assert suggestions[0]['score'] == 3
        assert suggestions[1]['user_id'] == 11
        assert suggestions[1]['score'] == 1

    def test_suggest_follows_with_limit(self, follows):
        """Test that limit parameter works"""
        follows.follow(1, 2)
        for i in range(10):
            follows.follow(2, i + 100)

        suggestions = follows.suggest_follows(user_id=1, limit=5)
        assert len(suggestions) == 5

    def test_suggest_follows_empty(self, follows):
        """Test suggestions when no follows exist"""
        suggestions = follows.suggest_follows(user_id=1, limit=10)
        assert suggestions == []

    def test_suggest_friends(self, follows):
        """Test friend suggestions (users who follow you back)"""
        # Users 2, 3, 4 follow User 1
        follows.follow(2, 1)
        follows.follow(3, 1)
        follows.follow(4, 1)

        # User 1 already follows User 2 back (already friends)
        follows.follow(1, 2)

        # Get friend suggestions for User 1
        suggestions = follows.suggest_friends(user_id=1, limit=10)
        suggested_ids = [s['user_id'] for s in suggestions]

        # Should suggest 3 and 4 (not 2, already friends)
        assert set(suggested_ids) == {3, 4}
        assert all(s['follows_you'] is True for s in suggestions)

    def test_suggest_friends_ranking(self, follows):
        """Test friend suggestions ranked by mutual connections"""
        # Users 2, 3 follow User 1
        follows.follow(2, 1)
        follows.follow(3, 1)

        # User 1 follows some people
        follows.follow(1, 10)
        follows.follow(1, 11)

        # User 2 also follows those same people (more mutual connections)
        follows.follow(2, 10)
        follows.follow(2, 11)

        # User 3 follows only one of them
        follows.follow(3, 10)

        suggestions = follows.suggest_friends(user_id=1, limit=10)

        # User 2 should be ranked higher (more mutual connections)
        assert suggestions[0]['user_id'] == 2
        assert suggestions[0]['score'] >= suggestions[1]['score']

    def test_suggest_friends_empty(self, follows):
        """Test friend suggestions when none exist"""
        suggestions = follows.suggest_friends(user_id=1, limit=10)
        assert suggestions == []


class TestStatistics:
    """Test statistics methods"""

    def test_get_stats(self, follows):
        """Test getting complete stats"""
        # Create relationships for User 1
        follows.follow(1, 2)
        follows.follow(1, 3)
        follows.follow(2, 1)  # Friend
        follows.follow(4, 1)  # Follower only

        stats = follows.get_stats(user_id=1)

        assert stats['followers'] == 2  # Users 2, 4
        assert stats['following'] == 2  # Users 2, 3
        assert stats['friends'] == 1    # User 2 only

    def test_get_stats_empty(self, follows):
        """Test stats for user with no relationships"""
        stats = follows.get_stats(user_id=1)

        assert stats['followers'] == 0
        assert stats['following'] == 0
        assert stats['friends'] == 0


class TestComplexScenarios:
    """Test complex real-world scenarios"""

    def test_complex_social_graph(self, follows):
        """Test a complex social graph with multiple relationships"""
        # Create a small social network
        # User 1: follows 2, 3, 4
        # User 2: follows 1, 3, 5
        # User 3: follows 1, 2
        # User 4: follows 1
        # User 5: follows 2

        follows.follow(1, 2)
        follows.follow(1, 3)
        follows.follow(1, 4)
        follows.follow(2, 1)
        follows.follow(2, 3)
        follows.follow(2, 5)
        follows.follow(3, 1)
        follows.follow(3, 2)
        follows.follow(4, 1)
        follows.follow(5, 2)

        # Verify User 1's stats
        stats = follows.get_stats(1)
        assert stats['followers'] == 3  # 2, 3, 4
        assert stats['following'] == 3  # 2, 3, 4
        assert stats['friends'] == 2    # 2, 3 (mutual)

        # Verify User 1's friends
        friends = follows.get_friends(1)
        assert set(friends) == {2, 3}

        # User 1 should get suggestion for User 5
        # (User 2 follows User 5, and User 1 follows User 2)
        suggestions = follows.suggest_follows(1, limit=10)
        suggested_ids = [s['user_id'] for s in suggestions]
        assert 5 in suggested_ids

    def test_unfollow_breaks_friendship(self, follows):
        """Test that unfollowing breaks a friendship"""
        # Create friendship
        follows.follow(1, 2)
        follows.follow(2, 1)
        assert follows.are_friends(1, 2) is True

        # One person unfollows
        follows.unfollow(1, 2)

        # No longer friends
        assert follows.are_friends(1, 2) is False
        assert follows.is_following(2, 1) is True  # Other direction still exists

    def test_mutual_follow_sequence(self, follows):
        """Test the sequence of creating a mutual follow"""
        # Initially not following
        assert follows.is_following(1, 2) is False
        assert follows.is_following(2, 1) is False
        assert follows.are_friends(1, 2) is False

        # User 1 follows User 2
        follows.follow(1, 2)
        assert follows.is_following(1, 2) is True
        assert follows.is_following(2, 1) is False
        assert follows.are_friends(1, 2) is False

        # User 2 follows User 1 back
        follows.follow(2, 1)
        assert follows.is_following(1, 2) is True
        assert follows.is_following(2, 1) is True
        assert follows.are_friends(1, 2) is True
