# Defense Puzzle Scoring Instructions

## 0. Key Information
The focus of this problem is Sections 1 to 4. Section 5 and onwards merely detail the defenders' movement methods and do not require close reading.

## 1. Game Objective

The attacking team must use dribbling, off-ball movement, and passing to change positions and finally complete a shot to score a goal within the specified number of rounds.

- Goal: Passes the problem immediately.
- Dribbling into a defender's square, tight marking conditions being met at the end of the Movement Phase, a failed pass, or a missed shot: Immediate failure.

## 2. Field and Coordinates

### 2.1 Grid Board

- The field is **7 squares wide × 8 squares deep** (physical grid lines).
- The horizontal coordinate is `x = 0–6`, increasing from left to right.
- The vertical coordinate is `y = 0–7`; the closer to `y = 7`, the closer to the opponent's goal.
- Any player's position is represented by `(x, y)`.

### 2.2 Goal

The goal is located at the deepest row, `y = 7`, and includes three squares:

- Left post: `(2.5,7)`
- Center: `(3,7)`
- Right post: `(3.5,7)`

Shooting targets must correspond to the above goal area. The Goalkeeper's position is also restricted to these three squares.

### 2.3 Movement Distance

"Moving 1 square" is calculated in eight directions:

- Including up, down, left, right, and four diagonal directions.

## 3. Players and Positioning
Violating the following rules will result in a yellow card.

### 3.1 Player in Possession

- Only one attacking player may possess the ball at any given time.
- The starting positions and the initial player in possession are designated by the task.
- After a successful pass, the receiver immediately becomes the new player in possession.

### 3.2 Square Occupation

- Two or more players may not occupy the same square.

### 3.3 Designated Square

- Every player belongs to one designated square at any given time.
- Both feet must stand within that square.
- During non-movement phases, players may not leave their original square without authorization.

## 4. Round Structure

### 4.1 Round Count

Official tasks have a maximum limit of **8 rounds** (unless otherwise explicitly specified by the task). The task steps include the following phases. The next phase begins when the previous phase ends. At the start of each phase, the Task Master will announce it and ask the team members to choose whether to execute or skip it. If they choose to execute, the Task Master will confirm its success or failure.

### 4.2 Shooting Phase

- If a shot is chosen, the round ends immediately.
- A goal is scored if the entire ball enters the goal area.
- The player in possession must be located at **`y ≥ 4`** to shoot.

### 4.3 Movement Phase

During this phase, all team members may move, but each team member can only move once. The movement of the player in possession is defined as dribbling; the movement of non-possessing players is defined as off-ball movement. The legal operations for both are as follows:

- The destination is within the grid board;
- It is exactly 1 square away from the original position;
- Dribbling is not prohibited by the task.

However, when dribbling, the player must perform a cone-dribbling maneuver designated by the Task Master without touching any cones during the process (TBD).

### 4.4 Passing Phase

The Passing Phase is determined by the following pass-related rules:

#### 4.4.1 Passing Procedure

The player in possession declares the receiving teammate.

#### 4.4.2 End of Pass

Must simultaneously meet:

1. The receiver must touch the ball; 
2. The ball stops moving.

After ending:

1. The receiver becomes the player in possession;
2. The round ends.

### 4.5 End of Round

- The defending team moves collectively;
- The round count increases by 1.

## 5. Common Rules for Defenders

### 5.1 Defensive Reactions and Overlap Resolution

During a defensive reaction, resolve according to the following procedure:

1. **Calculate the first choice**: Each defender calculates their preferred target square and the maximum number of steps for this reaction based on their role rules.
2. **Leave squares collectively**: All defenders leave their original squares simultaneously.
3. **Occupy squares by priority**: Goalkeeper → Blocker → Presser → Interceptor → Shadow. For defenders with the same role, occupation follows the dictionary order of their defender IDs; the one earlier in the order occupies first.
4. **Later occupiers may use squares vacated by earlier occupiers**: Since all have left their squares collectively, original squares not chosen by those resolved earlier can be entered by those resolved later.
5. **Cannot enter a square occupied by an attacking player**.
6. **Two defenders are not allowed to overlap**.

#### Maximum Steps for This Reaction

| Role | Max Steps | Role Area |
|------|-----------|-----------|
| Goalkeeper | 1 | Only the three goal squares `(2,7)(3,7)(4,7)` |
| Blocker | 1 | Only their fixed horizontal line `y` |
| Presser | 2 | Entire field (cannot enter goal squares, cannot occupy the player in possession's square) |
| Interceptor | 2 if distance to positioning target is ≥ 2, otherwise 1 | Entire field (cannot enter goal squares) |
| Shadow | 1 | Entire field (cannot enter goal squares; cannot stand on the ball-side of the marked player) |
| Anchored Blocker | 0 | Task-designated square, never leaves the square |

Distance is calculated in eight directions (Chebyshev distance): moving diagonally 1 square also counts as 1 step.

#### Landing Spot Determination

Each defender sequentially determines their landing spot:

1. If the preferred square is available → occupy the preferred square.
2. Otherwise, select an alternative square only from **empty squares** where "distance from original position ≤ maximum steps for this reaction" and that comply with the role area.
3. Alternative square ranking (the earlier, the higher priority; all are hard comparisons with no discretion):
   1. Lies on the role's preferred route (Interceptor: middle square of the passing line; Shadow: a square on the route from the marked player to the goal center; no such item for other roles).
   2. Closer to the preferred target.
   3. Does not move backward to a shallower `y` than the preferred choice.
   4. Closer to the original position (shorter movement).
   5. Larger `y`, then smaller `x`.
4. If there are no empty squares within the legal range → stay in the original position if it is still empty; Anchored Defenders always stay in their original position.  
   (Under the 7×8 grid and the above priority order, a situation where the original position is occupied and there is no alternative square should not occur. If it does, it is an execution error and must not be resolved using teleportation or cross-zone movement.)

**It is prohibited** to avoid overlap by:

- Exceeding the role's maximum steps for this reaction;
- Leaving a Blocker's fixed horizontal line;
- Allowing a non-Goalkeeper to enter the three goal squares;
- Allowing a Goalkeeper to leave the three goal squares;
- Occupying an Anchored Blocker's square.

## 6. Defensive Roles

### 6.1 Presser (Mad Dog Presser)

- Moves up to 2 squares per defensive reaction.
- Can move straight or diagonally.
- Moves towards the player in possession.
- Will not actively stand in the square occupied by the player in possession, but will stop in an adjacent position to apply pressure.
- Will not cross the depth line where the player in possession is located (may not make their own `y` greater than the player in possession's `y`).

Tight marking:

- If the Presser is already adjacent to the player in possession at the start of an action, and the player in possession chooses to end the round or force a dribble under tight marking, and still has not escaped the adjacent range after the action, **it is immediately ruled a steal, resulting in task failure**.
- A timely pass can clear the tight marking judgment on the original player in possession.

During a pass/shot, the Presser can only physically intercept or block within their own square and does not automatically intercept.

![Presser Movement Diagram](../defender_figures/presser.png)

### 6.2 Blocker (Zonal Stopper)

- Each Blocker has a fixed horizontal line `y`.
- Does not move forward or backward.
- Moves horizontally up to 1 square per reaction.
- The target is to stand at the position where the line connecting "the ball's position to the goal center `(3,7)`" crosses their horizontal line.
- If the preferred square is occupied, follow the Section 8 overlap resolution, selecting an alternative square on the same horizontal line and ≤ 1 square away from the original position.

Anchored Blocker:

- Does not move at all, staying in the task-designated square throughout.
- Can still physically intercept or block within that square during a pass/shot.

![Blocker Movement Diagram](../defender_figures/block.png)

### 6.3 Shadow (Shadow Marker)

- Each Shadow is fixed on marking one attacking player.
- If not designated in advance, they choose the nearest attacking player at the start.
- Once the marking relationship is established, it cannot be changed arbitrarily.
- Moves up to 1 square per defensive reaction.
- The target square is the next square from the marked player in the direction of the goal center.
- Does not actively stand in the square occupied by the marked player.
- Does not stand on the ball-side of the marked player, meaning they will not stand at a smaller `y` than the marked player.
- Goes up to `y=6` at most, and does not enter the goal squares.

The Shadow does not move during soft phases like off-ball movement or dribbling, and will only follow up after a pass or the end of the round.

![Shadow Movement Diagram](../defender_figures/shadow.png)

### 6.4 Interceptor (Passing Lane Interceptor)

- Exclude the current player in possession first.
- Among the remaining attacking players, prioritize the one with the largest `y` (closest to the goal).
- If the threat level is identical, prioritize the one closer to the player in possession.
- Set the midpoint of the passing line from the player in possession to that player as the positioning target.
- Moves up to 2 squares when further from the target, and 1 square when closer.
- If the preferred square is occupied, follow the Section 8 overlap resolution, prioritizing alternative empty squares on the same passing line and within the step count for this reaction.

The Interceptor standing on the predicted route does **not** automatically cause the pass to fail; they must physically touch or control the ball on the field.

![Interceptor Movement Diagram](../defender_figures/interceptor.png)

### 6.5 Goalkeeper

- Can only stand in the three goal squares `(2,7)`, `(3,7)`, and `(4,7)`.
- Moves horizontally up to 1 square per defensive reaction.
- Moves towards `(2,7)` when the ball is on the left side.
- Moves towards `(3,7)` when the ball is in the center.
- Moves towards `(4,7)` when the ball is on the right side.
- Follows the ball's horizontal position regardless of how far the ball is from the goal.

The Goalkeeper standing in a certain goal square does **not** automatically make a save; they must physically complete a save or miss during a shot.

![Goalkeeper Movement Diagram](../defender_figures/goalkeeper.png)
