# Task: Choose the Best Legal Action in "{game_name}"

You are player-{player_idx} in a game of "{game_name}". This game has {num_players} players: {player_name_list}. You have a list of {num_legal_actions} legal action choices. You must select the top action. Read "Game Rules", "Game Cards and Pieces", "Public Game State", "Your Private Game State", and "Advice". Your legal actions choices are found under "Your Private Game State". The best action should maximize your chances of winning the game. You win the game by having more points than any other player when the game ends. Keep in mind the ways you can gain points and lose points. Also, keep in mind how other players can gain points and lose points. Respond only with the code of the best legal action.

## Game Rules

"{game_name}" is a board game inspired by "{inspiration_game_name}". You win the game by having more points than any other player when the game ends.

### End of Game

- The game ends when the last player has his turn. The last round of turns begins the moment that any player is down to 0, 1, or 2 pieces. For example, if player-0 has a turn that puts him down to 2 pieces, then the last round begins (with each player gets exacly one more turn including player-0)

### How to Gain Victory Points

1. Achieving goals
    - Each goal has a "score". If a player achieves his goal, he gains that many points. If a player does not achieve his goal, he loses that many points.
2. Claiming paths
    - Each path has a "score". When a player claims a path, he gains that many points.
3. Achieving bonuses
    - Each bonus has a "score". If the player achieves the bonus, he gains that many points.

### Definitions

- Goal: a secret objective of a player to build a trail (a sequence of claimed edges) between two specific nodes. A goal is obtained by drawing a goal card. "Deck-0" is the "goal card" deck. Goal cards for a player are not visible other players.
- Trail: a trail is a sequence of claimed edges. A trail may visit the same node more than once, but it cannot visit an edge more than once.
- Edge: similar to a edge in graph theory. An edge connects two nodes. An edge contains paths in parallel. An edge contains at least one path and may contain more than one path. For the conditions under which a player can claim a path, see the "Rules for Claiming an Edge".
- Path: a path belongs to exactly one edge. A path can be claimed by only one player. A path contains a sequence of segments. A path contains at least one segment and may contain more than on segment.
- Segment: a segment belongs to exactly one path. A segment can only be claimed by one player. A player claims a segment by placing a piece on the segment during a turn. A segment may or may not have a "resource".
- Node: similar to a node in graph theory. In "{game_name}" a node represents a specific location.
- Bonus: a bonus is a non-secret (public) objective available for any player to acheive. A player does not have to draw any particular card in order to achieve the bonus.
- Facedown card stack: stack of cards with the information hidden.
- Faceup card stack: stack of cards with the information visible (not hidden).
- Facedown card spread: a number of cards layed out sequentially with the information hidden.
- Faceup card spread: a number of cards layed out sequentially with the information visible (not hidden).
- Pile: a pile contains many pieces and is assigned to a particular player.
- Piece: a piece belongs to only one pile. A piece can either be located in a player's hand or on a segment.
- Decks: a deck contains at least one card.
- Card: a card belongs to only one deck. A card may or may not have a "resource".
- Resources: resources represents the primary currency of the game. Resources can be obtained by cards. Resources can be used to move pieces onto a segment.
- Round: a sequence of player turns, where each player has a turn.
- Turn: a turn requires at least one action by a player. Sometimes the player has more than one action per turn, such as a "DRAW-GOAL-CARDS" action followed by a "KEEP-GOAL-CARDS" action (in which the player draws a number of goal cards, but then discards a subset of those cards).
- Player Hand: this refers to a player's possession of cards and/or pieces. Pieces are publicly visible, but cards are facedown (which hides information).

### Rules for Claiming an Edge

- A player may claim an edge by claiming one path on the edge. A path can be claimed by placing pieces on each segment of the path.
- In 2-player or 3-player games, only one player may claim an edge (by claiming one of the edge's paths). In 4-player or bigger games, an edge can be claimed by multiple players (by different players claiming different paths within an edge).
- A path is claimed by placing pieces on each segment of that path. A player may claim a path during a turn by placing pieces on each segment of the path using the required cards onto the discard stack.
- For any path, each segment of the path has the same "resource" or all have the "resource" set to null.
    - If each segment of the path has the same "resource", then a player may claim the path by discarding cards with the same "resource" (the player may use a "wild" resource card as a substitute for any card). The number of cards must match the number of segments.
    - If each segment of the path has null for the "resource", then a player may claim the path by discarding cards that have any "resource" as long as the "resource" matches for each card (the player may use a "wild" resource card as a substitute for any card). The number of cards must match the number of segments.

### Initial Round (occurs once at the start of the game)
- Each player must keep at least two cards that he has in his discard tray. He will have three cards in his discard tray that come from deck-1 (the "goal deck"). Each card from the "goal deck" is associated with a single "goal".

### Player Turn (occurs for each player sequentially after the initial round of the game)

#### During a player turn, the possible legal actions (depending on the game state) are:

1. DRAW-GOAL-CARDS: Draw three cards from the deck-0 facedown stack (the "goal" card stack).
2. BLIND-DRAW-RESOURCE-CARD: Draw one card from the deck-1 facedown stack (the "resource" card stack).
3. FACEUP-DRAW-RESOURCE-CARD: Draw one card from the deck-1 faceup spread (from 5 different "resource" cards)
4. CLAIM-PATH: Claim a path on the game board.
5. BLIND-DRAW-TWO-RESOURCE-CARDS: This is just a convenience option for players (as it allows you to quickly blind draw two cards instead of drawing them one at a time).

#### Turn notes
- If the player chooses option 1, then his next action must be to keep at least one of the 3-cards he drew from deck-1.
- If the player chooses option 2, then his next action can be either 2 or 3.
- If the player chooses option 4, then his turn is over.
- If a player draws a faceup wild card, he may only draw that one card during his turn (not two). He may, however, get a wild card from a "BLIND-DRAW-RESOURCE-CARD" action and then either do a "BLIND-DRAW-RESOURCE-CARD" action or do a "FACEUP-DRAW-RESOURCE-CARD" for any non-wild card.

### Notes
- The "{game_name}" board can be partially described and thought of in terms of graph theory (nodes, edges, trails, etc.). All edges in "{game_name}" are undirected.

## Game Cards and Pieces

These are all the cards and pieces of the game. Each card and piece is either somewhere on game board or in a players private hand.

```json
{game_config_json}
```

## Public Game State

This game state information is publicly available to all players.

```json
{public_game_state_json}
```

## Your Private Game State

This game state information is only available to you.

```json
{private_game_state_json}
```

## General Advice

These are general guidelines.

Guidelines:
- In general, don't choose "DRAW-GOAL-CARDS" towards the beginning of the game, as it's very risky. It's easy to be overwhelmed with goals. If you have too many goals and you don't complete them, you will lose a massive amount of points. "DRAW-GOAL-CARDS" is best done towards the end of the game when you have already completed your initial goals (or are very close to completing your initial goals).


## Basic Action Analysis

{basic_analysis}