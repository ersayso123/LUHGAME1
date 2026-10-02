# LUHGAME1: Streetball Kingdom

A top-down **3v3 streetball** career game. You start as a nobody at a cracked-up park court and build your kingdom, court by court, until you're the **King of the Courts**.

## How to run

**Best:** play the online version at https://claude.ai/artifact/B4v3SddbEb7wSkMKUkDzTk. It's always the newest version and saves your careers in your browser.

**Offline:** open `web/index.html` in any browser, or double-click **`PLAY.bat`** on Windows (it opens the same file). Pull the latest from GitHub first to get new features.

### Old Python version

`python main.py` (and `python -m pygbag .` for localhost) runs the original Python prototype in `game/`. It is **not updated anymore** and is missing everything added since (archetypes and attributes, the league ladder, card machines, scouts, fatigue, the new moves and animations, and more).

## Controls (in a game)

| Key | On offense | On defense |
| --- | --- | --- |
| WASD / arrows | Move whoever has the ball | Move your player |
| SPACE | Hold, then release in the green zone to shoot. Near the rim with **Dunker**, it dunks | Jump (block or rebound) |
| J | Pass (aims the way you're moving). Control follows the ball | |
| K | Crossover (can break ankles) | Steal |
| Q | | Switch to the defender nearest the ball |
| Esc | Pause (F to forfeit) | |

You are the gold-ringed player. On offense you control whoever has the ball. On defense you control your main guy.

## Rules

- Half court, first to **11**. Shots inside the arc count **1**, outside the arc count **2**.
- **Make it take it**: the team that scores keeps the ball, and the ball is checked at the top.
- After a steal or a defensive rebound, you must **clear it** past the arc before you can shoot.
- There's a 14-second shot clock.

## Career

| Tier | Court | Boss crew |
| --- | --- | --- |
| Nobody | Rusty Rim Park | The Rust Kings |
| Local | Southside Blacktop | Blacktop Bullies |
| Neighborhood Name | Pier Courts | The Tide |
| City Legend | Downtown Cage | Cage Kings |
| City Legend | The Throne | The Last King (beat them to become **King of the Courts**) |

- Wins earn **fame** and **cash**. Enough fame opens a court's boss, and beating the boss moves you up a tier and unlocks the next court.
- **Crew**: after a win, you can recruit one of the players you beat. You can have up to 6 in your crew, and you pick 2 starters.
- **Train Stats**: Shooting, Speed, Handles, Defense and Rebounding.
- **Attribute Shop**:
  - Your **Main** attribute gets the full effect and goes to level 5.
  - At Local fame you unlock a **Secondary**. It gets **50%** of the effect and caps at level 3.
  - The attributes are Sharpshooter, Dunker, Lockdown, Glass Cleaner, Playmaker and Speedster.

## Luck (in-game cash only)

- **Luck Machine**: 3 reels. 3 crowns pays 20x, any 3 of a kind 5x, 2 cash or 2 crowns 2x, and any other pair gives your bet back. The machine wins over time.
- **Mystery Baller**: pay for a random recruit. The odds are 40% Bum, 35% Solid, 20% Baller and 5% Legend.
- **Side bets**: before a game, bet on yourself. The tougher the other crew, the bigger the payout.

## Code layout

| File | What's in it |
| --- | --- |
| `main.py` | Game window and screen switching |
| `game/match.py` | Rules of one game (no drawing, so it's testable) |
| `game/ai.py` | Computer players |
| `game/ball.py` | The ball |
| `game/career.py` | Tiers, courts, crews, cash, saving |
| `game/attributes.py` | Attributes and the Main/Secondary math |
| `game/luck.py` | Luck Machine, Mystery Baller, wagers |
| `game/court.py` | Court drawing (each tier has its own look) |
| `game/screens.py` | All menus and the in-game view |
| `game/settings.py` | All the balance numbers in one place |

Run the tests with `python -m pytest`.
