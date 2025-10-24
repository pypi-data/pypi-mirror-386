import argparse
import sys
from .XOX_game import xox
from .pingpong_game import ping_pong
from .snake_game import snake_game
from .flappy_bird import flappy_bird
from .brickbreaker_game import brick_breaker
from .click_a_dot import click_a_dot
from .peg_game import peg_game


def main():
    parser = argparse.ArgumentParser(description='SG Games Collection')
    parser.add_argument('--brick_breaker', action='store_true',
                        help='Launch Brick Breaker game')
    parser.add_argument('--flappy_bird', action='store_true',
                        help='Launch Flappy Bird game')
    parser.add_argument('--ping_pong', action='store_true',
                        help='Launch Ping Pong game')
    parser.add_argument('--snake', action='store_true',
                        help='Launch Snake game')
    parser.add_argument('--xox', action='store_true',
                        help='Launch TicTacToe')
    parser.add_argument('--peg_game', action='store_true',
                        help='Launch PegSolitaire')
    parser.add_argument('--click_a_dot', action='store_true',
                        help='Launch ClickADot')

    args = parser.parse_args()

    # Check which game to launch
    if args.brick_breaker:
        brick_breaker()

    elif args.flappy_bird:
        flappy_bird()

    elif args.ping_pong:
        ping_pong()

    elif args.snake:
        snake_game()

    elif args.xox:
        xox()

    elif args.peg_game:
        peg_game()

    elif args.click_a_dot:
        click_a_dot()

    else:
        print("SG Games Collection")
        print("\nAvailable games:")
        print("  --brick_breaker    Launch Brick Breaker game")
        print("  --flappy_bird      Launch Flappy Bird game")
        print("  --ping_pong        Launch Ping Pong Game")
        print("  --snake            Launch Snake Game")
        print("  --xox              Launch TicTacToe")
        print("  --peg_game         Launch PegSolitaire")
        print("  --click_a_dot      Launch ClickADot")
        print("\n Example Usage:")
        print("  python -m sg_games --flappy_bird")
        sys.exit(0)


if __name__ == "__main__":
    main()
