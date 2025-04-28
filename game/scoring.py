# game/scoring.py

class Scoring:
    def __init__(self, player_count=1):
        """
        Initialize the scoring system.
        
        Args:
            player_count: Number of players
        """
        self.player_count = player_count
        self.reset_scores()
    
    def reset_scores(self):
        """Reset all scores to zero."""
        # Dictionary for each player {player_id: {'claps': count, 'on_beat': count}}
        self.scores = {i: {'claps': 0, 'on_beat': 0} for i in range(1, self.player_count + 1)}
        self.total_beats = 0
    
    def register_clap(self, player_id, is_on_beat):
        """
        Register a clap for a player.
        
        Args:
            player_id: ID of the player who clapped
            is_on_beat: Whether the clap was on beat
        """
        if player_id in self.scores:
            self.scores[player_id]['claps'] += 1
            if is_on_beat:
                self.scores[player_id]['on_beat'] += 1
                print(f"Player {player_id}: CORRECT! Good timing!")
            else:
                print(f"Player {player_id}: WRONG! Off beat!")
    
    def register_beat(self):
        """Register a beat."""
        self.total_beats += 1
    
    def get_score(self, player_id):
        """
        Get the score for a specific player.
        
        Args:
            player_id: ID of the player
        
        Returns:
            Dictionary with score information for the player
        """
        if player_id not in self.scores:
            return {'claps': 0, 'on_beat': 0, 'percentage': 0, 'missed_beats': 0}
        
        player_data = self.scores[player_id]
        
        if player_data['claps'] == 0:
            percentage = 0
        else:
            percentage = (player_data['on_beat'] / player_data['claps']) * 100
        
        missed_beats = max(0, self.total_beats - player_data['on_beat'])
        
        return {
            'claps': player_data['claps'],
            'on_beat': player_data['on_beat'],
            'percentage': percentage,
            'missed_beats': missed_beats
        }
    
    def get_all_scores(self):
        """
        Get scores for all players.
        
        Returns:
            Dictionary mapping player IDs to their score information
        """
        result = {}
        for player_id in self.scores:
            result[player_id] = self.get_score(player_id)
        return result
    
    def get_winner(self):
        """
        Get the player with the highest score.
        
        Returns:
            Tuple of (player_id, score) for the winning player, or None if no players
        """
        if not self.scores:
            return None
        
        best_player = None
        best_score = -1
        
        for player_id, data in self.scores.items():
            if data['on_beat'] > best_score:
                best_score = data['on_beat']
                best_player = player_id
        
        if best_player is not None:
            return (best_player, self.get_score(best_player))
        return None


# Test function for the scoring system
def test_scoring():
    """Test function for the scoring system."""
    # Create scoring system for 2 players
    scoring = Scoring(player_count=2)
    
    # Register some beats
    for _ in range(10):
        scoring.register_beat()
    
    # Register some claps for player 1
    for _ in range(8):
        scoring.register_clap(1, True)  # On beat
    
    for _ in range(2):
        scoring.register_clap(1, False)  # Off beat
    
    # Register some claps for player 2
    for _ in range(5):
        scoring.register_clap(2, True)  # On beat
    
    for _ in range(3):
        scoring.register_clap(2, False)  # Off beat
    
    # Print scores
    print("Player 1 score:", scoring.get_score(1))
    print("Player 2 score:", scoring.get_score(2))
    print("All scores:", scoring.get_all_scores())
    
    # Get winner
    winner = scoring.get_winner()
    if winner:
        player_id, score = winner
        print(f"Winner: Player {player_id} with {score['on_beat']} correct claps!")


if __name__ == "__main__":
    test_scoring()