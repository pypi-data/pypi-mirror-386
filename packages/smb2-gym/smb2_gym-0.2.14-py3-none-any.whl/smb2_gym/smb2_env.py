"""Super Mario Bros 2 (Europe) Gymnasium Environment."""

import os
from typing import (
    Any,
    Optional,
)

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from tetanes_py import NesEnv

from .actions import (
    COMPLEX_ACTIONS,
    SIMPLE_ACTIONS,
    ActionType,
    action_to_buttons,
    actions_to_buttons,
    get_action_meanings,
)
from .app import InitConfig
from .app.info_display import create_info_panel
from .app.rendering import render_frame
from .constants import (
    GAME_INIT_FRAMES,
    MAX_SAVE_SLOTS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    GlobalCoordinate,
)
from .state.enemies import EnemiesMixin
from .state.player import PlayerStateMixin
from .state.position import PositionMixin
from .state.semantic_map import SemanticMapMixin


class SuperMarioBros2Env(
    gym.Env,
    PositionMixin,
    PlayerStateMixin,
    EnemiesMixin,
    SemanticMapMixin,
):
    """
    Gymnasium environment for Super Mario Bros 2 (Europe).

    This environment provides a minimal interface to the NES emulator,
    returning pixel observations and allowing all 256 button combinations as
    actions.

    Rewards are always 0 - users should implement their own reward functions
    based on the RAM values available in the info dict.
    """

    # Number of frames to wait during area transitions before accepting new coordinates
    AREA_TRANSITION_FRAMES: int = 98  # TODO: Perhaps we can detect this when the sub-space door despawns?

    def __init__(
        self,
        init_config: InitConfig,
        render_mode: Optional[str] = None,
        max_episode_steps: Optional[int] = None,
        action_type: ActionType = "simple",
        reset_on_life_loss: bool = False,
        render_fps: Optional[int] = None,
        frame_method: str = "rgb",
        env_name: Optional[str] = None,
    ):
        """Initialize the SMB2 environment.

        Args:
            init_config: InitConfig object specifying initialisation mode
            render_mode: 'human' or None
            max_episode_steps: Maximum steps per episode (for truncation)
            action_type: Type of action space
            reset_on_life_loss: If True, episode terminates when Mario loses a life
            render_fps: FPS for human rendering (None = no limit, good for training)
            frame_method: Frame rendering method ('rgb', 'grayscale')
                - 'rgb': RGB rendering
                - 'grayscale': Grayscale rendering (faster, 67% less memory)
        """
        super().__init__()

        self.render_mode: Optional[str] = render_mode
        self.max_episode_steps: Optional[int] = max_episode_steps
        self.reset_on_life_loss: bool = reset_on_life_loss
        self.init_config: InitConfig = init_config
        self.render_fps: Optional[int] = render_fps
        self.env_name: Optional[str] = env_name
        if self.env_name:
            print(f'Creating {self.env_name} environment...')

        # Validate and store frame method
        valid_frame_methods = ["rgb", "grayscale"]
        if frame_method not in valid_frame_methods:
            raise ValueError(
                f"Invalid frame_method '{frame_method}'. Must be one of {valid_frame_methods}"
            )
        self.frame_method: str = frame_method

        # Store relevant attributes (only meaningful for built-in ROM mode)
        self.starting_level: Optional[str]
        self.starting_level_id: Optional[int]
        self.starting_character: Optional[int]

        if not self.init_config.rom_path:  # Built-in ROM mode
            self.starting_level = self.init_config.level
            self.starting_level_id = self.init_config.level_id
            self.starting_character = self.init_config.character_id
        else:  # Custom ROM mode
            self.starting_level = None
            self.starting_level_id = None
            self.starting_character = None

        # Validate and store action type
        if action_type not in ["all", "complex", "simple"]:
            raise ValueError(
                f"Invalid action_type '{action_type}'. Must be 'all', 'complex', or 'simple'"
            )
        self.action_type: ActionType = action_type

        self._init_emulator()
        self._init_spaces()
        self._init_state_tracking()

        # Initialize rendering attributes but defer pygame init until needed
        self._screen: Any = None  # pygame.Surface | None - avoid importing pygame
        self._clock: Any = None  # pygame.time.Clock | None - avoid importing pygame
        self._pygame_initialized: bool = False

    def _init_emulator(self) -> None:
        """Initialize the NES emulator and load ROM."""
        rom_path = self.init_config.get_rom_path()
        if not os.path.exists(rom_path):
            raise FileNotFoundError(f"ROM file not found: {rom_path}")

        # Initialize TetaNES with frame rendering method
        self._nes: NesEnv = NesEnv(headless=False, frame_method=self.frame_method)

        # Load ROM
        with open(rom_path, 'rb') as f:
            rom_data = f.read()
        rom_name = os.path.basename(rom_path)
        self._nes.load_rom(rom_name, rom_data)

    def _init_spaces(self) -> None:
        """Initialize observation and action spaces."""
        # Define observation space based on frame method
        if self.frame_method == "grayscale":
            self.observation_space = spaces.Box(
                low=0,
                high=255,
                shape=(SCREEN_HEIGHT, SCREEN_WIDTH),
                dtype=np.uint8,
            )
        else:  # rgb
            self.observation_space = spaces.Box(
                low=0,
                high=255,
                shape=(SCREEN_HEIGHT, SCREEN_WIDTH, 3),
                dtype=np.uint8,
            )

        # Define action space based on action_type
        if self.action_type == "all":
            self.action_space = spaces.Discrete(256)
            self._action_meanings = get_action_meanings()
        elif self.action_type == "complex":
            self.action_space = spaces.Discrete(len(COMPLEX_ACTIONS))
            self._action_meanings = COMPLEX_ACTIONS
        elif self.action_type == "simple":
            self.action_space = spaces.Discrete(len(SIMPLE_ACTIONS))
            self._action_meanings = SIMPLE_ACTIONS

    def _init_state_tracking(self) -> None:
        """Initialize state tracking variables."""
        self._done: bool = False
        self._episode_steps: int = 0
        self._previous_lives: Optional[int] = None  # Track lives to detect life loss
        self._previous_levels_finished: Optional[dict[str, int]] = {}  # Track level completion
        self._previous_sub_area: Optional[int] = None  # Track sub-area for transition detection
        self._previous_x_global: Optional[int] = None  # Track x position for transition detection
        self._previous_y_global: Optional[int] = None  # Track y position for transition detection
        self._transition_frame_count: int = 0  # Count frames since transition detected
        self._last_obs: Optional[np.ndarray] = None  # Track last observation for rendering

    def _init_rendering(self) -> None:
        """Initialize pygame rendering when first needed."""
        if self._pygame_initialized or self.render_mode != 'human':
            return

        # Lazy load this, we don't need for non rendered envs
        import pygame
        pygame.init()

        from .app.info_display import get_required_info_height
        from .constants import (
            DEFAULT_SCALE,
            FONT_SIZE_BASE,
            SCREEN_HEIGHT,
            SCREEN_WIDTH,
        )

        self._scale: int = DEFAULT_SCALE
        self._width: int = SCREEN_WIDTH * self._scale
        self._height: int = SCREEN_HEIGHT * self._scale
        self._info_height: int = get_required_info_height(self._scale)

        self._screen = pygame.display.set_mode((self._width, self._height + self._info_height))
        pygame.display.set_caption("Super Mario Bros 2")
        self._clock = pygame.time.Clock() if self.render_fps is not None else None

        # Setup font for info display
        self._font_size: int = FONT_SIZE_BASE * self._scale // 2
        self._font: Any = pygame.font.Font(None, self._font_size)  # pygame.font.Font
        self._pygame_initialized = True

    # ---- Primary Gym methods ---------------------------------------

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the environment by loading a save state.

        Args:
            seed: Random seed
            options: Additional options

        Returns:
            observation: Initial frame
            info: Initial info dict
        """
        super().reset(seed=seed)

        # Reset NES first
        self._nes.reset()
        self._done = False
        self._episode_steps = 0
        self._transition_frame_count = 0

        save_path = self.init_config.get_save_state_path()

        if save_path and not os.path.exists(save_path):
            raise FileNotFoundError(f"Save state file not found: {save_path}")

        if save_path:
            self.load_state_from_path(save_path)
        else:
            # When no save state, navigate to character selection screen
            # Wait for title screen to appear
            # TODO: Onces we have all the save states perhaps remove this logic
            for _ in range(120):  # 2 seconds
                self._nes.step([False] * 8, render=False)

            # Press START to get past title screen
            start_button = [False, False, False, True, False, False, False, False]  # START button
            for _ in range(10):  # Press START
                self._nes.step(start_button, render=False)
            for _ in range(10):  # Release
                self._nes.step([False] * 8, render=False)

            # Wait for transition to character select screen
            for _ in range(120):  # 2 seconds
                self._nes.step([False] * 8, render=False)

            # Stop here - let the user select their character manually

        # Get one frame after reset/loading save state
        obs, _, _, _, _ = self._nes.step([False] * 8, render=True)
        self._last_obs = obs

        info = self.info

        # Initialize tracking for detecting life loss and level completion
        self._previous_lives = self.lives
        self._previous_levels_finished = self.levels_finished.copy()

        # Initialize tracking with consistent global coordinates
        global_coords = self.global_coordinate_system
        self._previous_sub_area = global_coords.sub_area
        self._previous_x_global = global_coords.global_x
        self._previous_y_global = global_coords.global_y
        if self.render_mode == 'human':
            self.render()

        return np.array(obs), info

    def step(self, action: np.int64) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Step the environment.

        Args:
            action: Discrete action (0-255)

        Returns:
            observation: Current frame
            reward: Always 0.0
            terminated: True if game over
            truncated: True if max steps reached
            info: dict with game state
        """
        if self._done:
            raise RuntimeError("Cannot step after episode is done. Call reset().")

        # Convert and validate action to buttons
        buttons = self._validate_and_convert_action(action)

        # 1. Step emulator
        obs, _, _, _, nes_info = self._nes.step(buttons.tolist(), render=True)
        self._episode_steps += 1
        self._last_obs = obs

        # 2. Get game state
        info = self.info
        info.update(nes_info)  # Include NES emulator info

        # 3. Check for life loss and update tracking
        life_lost = self._detect_life_loss()
        if life_lost:
            info['life_lost'] = True

        # Update tracking for next step
        self._previous_lives = self.lives
        self._previous_levels_finished = self.levels_finished.copy()

        # Track global coords
        global_coords = self.global_coordinate_system
        self._previous_sub_area = global_coords.sub_area
        self._previous_x_global = global_coords.global_x
        self._previous_y_global = global_coords.global_y

        # 4. Check termination
        terminated = self.game.is_game_over or life_lost or self.level_completed
        truncated = (
            self.max_episode_steps is not None and self._episode_steps >= self.max_episode_steps
        )

        self._done = terminated or truncated
        reward = 0.0  # Always return 0 reward

        # Render if in human mode
        if self.render_mode == 'human':
            self.render()

        return np.array(obs), reward, terminated, truncated, info

    def render(self) -> Optional[np.ndarray]:
        """Render the environment.

        Returns:
            RGB array for display, None if no render mode
        """
        if self.render_mode == 'human':
            if not self._pygame_initialized:  # Lazy load
                self._init_rendering()

            if self._screen is not None and self._last_obs is not None:
                import pygame

                # Handle pygame events to prevent window freezing
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return self._last_obs

                # Render
                render_frame(self._screen, self._last_obs, self._width, self._height)
                create_info_panel(self._screen, self.info, self._font, self._height, self._width)

                pygame.display.flip()
                # Only limit FPS if render_fps is specified
                if self._clock is not None and self.render_fps is not None:
                    self._clock.tick(self.render_fps)

            return self._last_obs
        return None

    def _read_ram_safe(self, address: int) -> int:
        """Read from RAM.

        Args:
            address: RAM address to read

        Returns:
            Value at RAM address
        """
        return self._nes.read_ram(address)

    def _read_ppu(self, address: int) -> int:
        """Read from PPU memory.

        Args:
            address: PPU address to read (e.g., 0x2000-0x23FF for nametable)

        Returns:
            Value at PPU address
        """
        return self._nes.read_ppu(address)

    # ---- Properties ------------------------------------------------

    @property
    def pos(self):
        """Position and coordinate properties from PositionMixin."""

        class PositionAccessor:

            def __init__(self, env):
                self._env = env

            @property
            def x_global(self) -> int:
                return self._env.x_position_global

            @property
            def x_local(self) -> int:
                return self._env.x_position

            @property
            def x_page(self) -> int:
                return self._env.x_page

            @property
            def y_global(self) -> int:
                return self._env.y_position_global

            @property
            def y_local(self) -> int:
                return self._env.y_position

            @property
            def y_page(self) -> int:
                return self._env.y_page

            @property
            def area(self) -> int:
                return self._env.area

            @property
            def sub_area(self) -> int:
                return self._env.sub_area

            @property
            def spawn_page(self) -> int:
                return self._env.spawn_page

            @property
            def current_page(self) -> int:
                return self._env.current_page_position

            @property
            def total_pages(self) -> int:
                return self._env.total_pages_in_sub_area

            @property
            def is_vertical(self) -> bool:
                return self._env.is_vertical_area

            @property
            def global_coords(self) -> GlobalCoordinate:
                return self._env.global_coordinate_system

        return PositionAccessor(self)

    @property
    def game(self):
        """World and level state properties from PositionMixin."""

        class GameAccessor:

            def __init__(self, env):
                self._env = env

            @property
            def world(self) -> int:
                return self._env.world

            @property
            def level(self) -> str:
                return self._env.level

            @property
            def is_game_over(self) -> bool:
                if self._env._episode_steps < GAME_INIT_FRAMES:
                    return False
                return self._env.lives == 0

        return GameAccessor(self)

    @property
    def pc(self):
        """Player character state properties from PlayerStateMixin."""

        class PlayerCharacterAccessor:

            def __init__(self, env):
                self._env = env

            @property
            def lives(self) -> int:
                return self._env.lives

            @property
            def character(self) -> int:
                return self._env.character

            @property
            def hearts(self) -> int:
                return self._env.hearts

            @property
            def cherries(self) -> int:
                return self._env.cherries

            @property
            def coins(self) -> int:
                return self._env.coins

            @property
            def continues(self) -> int:
                return self._env.continues

            @property
            def holding_item(self) -> bool:
                return self._env.holding_item

            @property
            def item_pulled(self) -> int:
                return self._env.item_pulled

            @property
            def big_vegetables_pulled(self) -> int:
                return self._env.big_vegetables_pulled

            @property
            def speed(self) -> int:
                return self._env.player_speed

            @property
            def on_vine(self) -> bool:
                return self._env.on_vine

            @property
            def starman_timer(self) -> int:
                return self._env.starman_timer

            @property
            def subspace_timer(self) -> int:
                return self._env.subspace_timer

            @property
            def stopwatch_timer(self) -> int:
                return self._env.stopwatch_timer

            @property
            def invulnerability_timer(self) -> int:
                return self._env.invulnerability_timer

            @property
            def framerule_timer(self) -> int:
                return self._env.framerule_timer

            @property
            def pidget_carpet_timer(self) -> int:
                return self._env.pidget_carpet_timer

            @property
            def float_timer(self) -> int:
                return self._env.float_timer

            @property
            def door_transition_timer(self) -> int:
                return self._env.door_transition_timer

            @property
            def state(self) -> int:
                return self._env.player_state

            @property
            def levels_finished(self) -> dict[str, int]:
                return self._env.levels_finished

            @property
            def level_completed(self) -> bool:
                return self._env.level_completed

            @property
            def subspace_status(self) -> int:
                return self._env.subspace_status

            @property
            def level_transition(self) -> int:
                return self._env.level_transition

            @property
            def stats(self):
                return self._env.character_stats

        return PlayerCharacterAccessor(self)

    @property
    def semantic(self):
        """Semantic tile map from SemanticMapMixin.

        Returns structured numpy array (15 x 16) with fields:
            - tile_id: Raw BackgroundTile ID
            - fine_type: Fine-grained FineTileType (SOLID, ENEMY, etc.)
            - coarse_type: Coarse-grained CoarseTileType (TERRAIN, ENEMY, etc.)
            - color_r, color_g, color_b: RGB visualisation colour
        """
        return self.semantic_map

    @property
    def info(self) -> dict[str, Any]:
        """Get current game info from RAM.

        Returns:
            dict with organized game state using accessor objects
        """
        return {
            'pc': self.pc,
            'pos': self.pos,
            'game': self.game,
            'enemies': self.enemies,
            'semantic': self.semantic,
        }

    def _detect_life_loss(self) -> bool:
        """Detect if Mario lost a life this step.

        Returns:
            True if a life was lost, False otherwise
        """
        if not self.reset_on_life_loss:
            return False

        if self._previous_lives is None:
            return False

        # Don't detect life loss during initialisation
        if self._episode_steps < GAME_INIT_FRAMES:
            return False

        current_lives = self.lives
        return current_lives < self._previous_lives

    # ---- Validators ------------------------------------------------

    def _validate_and_convert_action(self, action: np.int64) -> np.ndarray:
        """Validate and convert action to button array based on action type.

        Args:
            action: Discrete action index

        Returns:
            Button array for NES controller

        Raises:
            ValueError: If action is invalid for the current action type
        """
        if self.action_type == "all":
            if not 0 <= action <= 255:
                raise ValueError(f"Invalid action {action}. Must be 0-255 for 'all' action type")
            return action_to_buttons(int(action))
        elif self.action_type == "complex":
            if action >= len(COMPLEX_ACTIONS):
                raise ValueError(f"Invalid action {action}. Must be 0-{len(COMPLEX_ACTIONS)-1}")
            return actions_to_buttons(COMPLEX_ACTIONS[action])
        elif self.action_type == "simple":
            if action >= len(SIMPLE_ACTIONS):
                raise ValueError(f"Invalid action {action}. Must be 0-{len(SIMPLE_ACTIONS)-1}")
            return actions_to_buttons(SIMPLE_ACTIONS[action])
        else:
            raise ValueError('Action type not supported.')

    # ---- Other bindings --------------------------------------------

    def get_action_meanings(self) -> list[list[str]]:
        """Get the meanings of actions for this environment.

        Returns:
            List of action meanings based on the action_type
        """
        return self._action_meanings

    def save_state(self, slot: int) -> None:
        """Save current emulator state to a slot.

        Args:
            slot: Save state slot (0-9)
        """
        if not 0 <= slot < MAX_SAVE_SLOTS:
            raise ValueError(f"Slot must be between 0-9, got {slot}")
        self._nes.save_state(slot)

    def load_state(self, slot: int) -> None:
        """Load emulator state from a slot.

        Args:
            slot: Save state slot (0-9)
        """
        if not 0 <= slot < MAX_SAVE_SLOTS:
            raise ValueError(f"Slot must be between 0-9, got {slot}")
        self._nes.load_state(slot)

    def save_state_to_path(self, filepath: str) -> None:
        """Save current emulator state to a file.

        Args:
            filepath: Path where to save the state file
        """
        self._nes.save_state_to_path(filepath)

    def load_state_from_path(self, filepath: str) -> None:
        """Load emulator state from a file.

        Args:
            filepath: Path to the state file to load
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Save state file not found: {filepath}")
        self._nes.load_state_from_path(filepath)

    def set_frame_speed(self, speed: float) -> None:
        """Set the frame speed for faster/slower emulation.

        Args:
            speed: Frame speed multiplier (1.0 = normal speed, 2.0 = 2x speed, etc.)
                   Must be positive.

        Raises:
            ValueError: If speed is not positive
        """
        if speed <= 0.0:
            raise ValueError("Frame speed must be positive")
        self._nes.set_frame_speed(speed)

    def get_frame_speed(self) -> float:
        """Get the current frame speed multiplier.

        Returns:
            Current frame speed (1.0 = normal speed)
        """
        return self._nes.get_frame_speed()

    def close(self) -> None:
        """Close the environment and clean up resources."""
        if hasattr(self, '_pygame_initialized') and self._pygame_initialized:
            import pygame
            pygame.quit()
            self._screen = None
            self._pygame_initialized = False
