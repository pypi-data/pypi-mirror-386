"""
Reward functions for the Genesis Forge environment.
Each of these should return a float tensor with the reward value for each environment, in the shape (num_envs,).
"""

from __future__ import annotations

import torch
import genesis as gs
from genesis_forge.genesis_env import GenesisEnv
from genesis_forge.managers import (
    CommandManager,
    VelocityCommandManager,
    PositionActionManager,
    ContactManager,
    TerrainManager,
    EntityManager,
)
from genesis_forge.utils import entity_lin_vel, entity_ang_vel, entity_projected_gravity
from genesis_forge.managers import MdpFnClass
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from genesis.engine.entities import RigidEntity


"""
Aliveness
"""


def is_alive(env: GenesisEnv) -> torch.Tensor:
    """
    Reward for being alive and not terminating this step.
    This assumes that `env.extras["terminations"]` is a boolean tensor with the termination signals for the environments.
    """
    terminations: torch.Tensor = env.extras["terminations"]
    return (~terminations).float().detach()


def terminated(env: GenesisEnv) -> torch.Tensor:
    """
    Penalize terminated episodes that terminated.
    This assumes that `env.extras["terminations"]` is a boolean tensor with the termination signals for the environments.
    """
    terminations: torch.Tensor = env.extras["terminations"]
    return terminations.float().detach()


"""
Robot base position/state
"""


def base_height(
    env: GenesisEnv,
    target_height: Union[float, torch.Tensor] = None,
    height_command: CommandManager = None,
    terrain_manager: TerrainManager = None,
    entity_attr: str = "robot",
    entity_manager: EntityManager = None,
) -> torch.Tensor:
    """
    Penalize base height away from target, using the L2 squared kernel.

    Args:
        env: The Genesis environment containing the robot
        target_height: The target height to penalize the base height away from
        height_command: Get the target height from a height command manager. This expects the command to have a single range value.
        terrain_manager: The terrain manager will adjust the height based on the terrain height.
        entity_attr: The attribute name of the entity in the environment.
        entity_manager: The entity manager for the entity.

    Returns:
        torch.Tensor: Penalty for base height away from target
    """
    robot = None
    if entity_manager is not None:
        robot = entity_manager.entity
    else:
        robot = getattr(env, entity_attr)

    base_pos = robot.get_pos()
    height_offset = 0.0
    if terrain_manager is not None:
        height_offset = terrain_manager.get_terrain_height(
            base_pos[:, 0], base_pos[:, 1]
        )
    if height_command is not None:
        target_height = height_command.command.squeeze(-1)
    return torch.square(base_pos[:, 2] - height_offset - target_height)


def dof_similar_to_default(
    env: GenesisEnv,
    action_manager: PositionActionManager,
):
    """
    Penalize joint poses far away from default pose

    Args:
        env: The Genesis environment containing the robot
        action_manager: The DOF action manager

    Returns:
        torch.Tensor: Penalty for joint poses far away from default pose
    """
    dof_pos = action_manager.get_dofs_position()
    default_pos = action_manager.default_dofs_pos
    return torch.sum(torch.abs(dof_pos - default_pos), dim=1)


def lin_vel_z_l2(
    env: GenesisEnv,
    entity_attr: str = "robot",
    entity_manager: EntityManager = None,
) -> torch.Tensor:
    """
    Penalize z axis base linear velocity

    Args:
        env: The Genesis environment containing the entity
        entity_manager: The entity manager for the robot/entity the reward is being computed for.
                        This is slightly more performant than using the `entity_attr` parameter.
        entity_attr: The attribute name of the entity in the environment. This isn't necessary if `entity_manager` is provided.

    Returns:
        torch.Tensor: Penalty for z axis base linear velocity
    """
    linear_vel = None
    if entity_manager is not None:
        linear_vel = entity_manager.get_linear_velocity()
    else:
        robot = getattr(env, entity_attr)
        linear_vel = entity_lin_vel(robot)
    return torch.square(linear_vel[:, 2])


def ang_vel_xy_l2(
    env: GenesisEnv,
    entity_attr: str = "robot",
    entity_manager: EntityManager = None,
):
    """
    Penalize xy-axis base angular velocity using L2 squared kernel.

    Args:
        env: The Genesis environment containing the entity
        entity_manager: The entity manager for the robot/entity the reward is being computed for.
                        This is slightly more performant than using the `entity_attr` parameter.
        entity_attr: The attribute name of the entity in the environment. This isn't necessary if `entity_manager` is provided.

    Returns:
        torch.Tensor
    """
    angle_vel = None
    if entity_manager is not None:
        angle_vel = entity_manager.get_angular_velocity()
    else:
        robot = getattr(env, entity_attr)
        angle_vel = entity_ang_vel(robot)
    return torch.sum(torch.square(angle_vel[:, :2]), dim=1)


def flat_orientation_l2(
    env: GenesisEnv,
    entity_attr: str = "robot",
    entity_manager: EntityManager = None,
) -> torch.Tensor:
    """
    Penalize non-flat base orientation using L2 squared kernel.
    This is computed by penalizing the xy-components of the projected gravity vector.

    Args:
        env: The Genesis environment containing the robot
        entity_manager: The entity manager for the robot/entity the reward is being computed for.
                        This is slightly more performant than using the `entity_attr` parameter.
        entity_attr: The attribute name of the entity in the environment. This isn't necessary if `entity_manager` is provided.

    Returns:
        torch.Tensor: Penalty for non-flat base orientation
    """
    # Get the projected gravity vector in the robot's base frame
    # This represents how "tilted" the robot is from upright
    projected_gravity = None
    if entity_manager is not None:
        projected_gravity = entity_manager.get_projected_gravity()
    else:
        robot = getattr(env, entity_attr)
        projected_gravity = entity_projected_gravity(robot)

    # Penalize the xy-components (horizontal tilt) using L2 squared kernel
    # A flat orientation means these components should be close to zero
    return torch.sum(torch.square(projected_gravity[:, :2]), dim=1)


class body_acceleration_exp(MdpFnClass):
    """
    Penalize jerky body acceleration to encourage smooth locomotion.

    Args:
        env: The Genesis environment containing the robot
        entity_manager: The entity manager for the robot/entity the reward is being computed for.
                        This is slightly more performant than using the `entity_attr` parameter.
        entity_attr: The attribute name of the entity in the environment. This isn't necessary if `entity_manager` is provided.
        sensitivity: The sensitivity of the exponential decay. A lower value means the reward is more sensitive to the error.
    """

    def __init__(
        self,
        env: GenesisEnv,
        entity_attr: str = "robot",
        entity_manager: EntityManager = None,
        sensitivity: float = 0.10,
    ):
        super().__init__(env)

    def __call__(
        self,
        env: GenesisEnv,
        entity_attr: str = "robot",
        entity_manager: EntityManager = None,
        sensitivity: float = 0.10,
    ):
        # Current velocities
        curr_lin_vel = None
        curr_ang_vel = None
        if entity_manager is not None:
            curr_lin_vel = entity_manager.get_linear_velocity()
            curr_ang_vel = entity_manager.get_angular_velocity()
        else:
            robot = getattr(env, self._entity_attr)
            curr_lin_vel = entity_lin_vel(robot)
            curr_ang_vel = entity_ang_vel(robot)

        # Calculate acceleration from previous step
        if hasattr(self, "prev_lin_vel"):
            lin_acc = (curr_lin_vel - self.prev_lin_vel) / env.dt
            ang_acc = (curr_ang_vel - self.prev_ang_vel) / env.dt
        else:
            lin_acc = torch.zeros_like(curr_lin_vel)
            ang_acc = torch.zeros_like(curr_ang_vel)

        # Store for next step
        self.prev_lin_vel = curr_lin_vel.clone()
        self.prev_ang_vel = curr_ang_vel.clone()

        # Calculate penalty using exponential kernel
        pelvis_motion = torch.norm(lin_acc, dim=-1) + torch.norm(ang_acc, dim=-1)
        return 1 - torch.exp(-sensitivity * pelvis_motion)


"""
Action penalties.
"""


def action_rate_l2(env: GenesisEnv) -> torch.Tensor:
    """
    Penalize the rate of change of the actions using L2 squared kernel.

    Args:
        env: The Genesis environment containing the robot

    Returns:
        torch.Tensor: Penalty for changes in actions
    """
    actions = env.actions
    last_actions = env.last_actions
    if last_actions is None:
        return torch.zeros_like(actions, device=gs.device)
    return torch.sum(torch.square(last_actions - actions), dim=1)


"""
Velocity Command Rewards
"""


def command_tracking_lin_vel(
    env: GenesisEnv,
    command: torch.Tensor = None,
    vel_cmd_manager: VelocityCommandManager = None,
    sensitivity: float = 0.25,
    entity_attr: str = "robot",
    entity_manager: EntityManager = None,
) -> torch.Tensor:
    """
    Reward for tracking commanded linear velocity (xy axes)

    Args:
        env: The Genesis environment containing the robot
        command: The commanded XY linear velocity in the shape (num_envs, 2)
        vel_cmd_manager: The velocity command manager
        sensitivity: A lower value means the reward is more sensitive to the error
        entity_manager: The entity manager for the robot/entity the reward is being computed for.
                        This is slightly more performant than using the `entity_attr` parameter.
        entity_attr: The attribute name of the entity in the environment. This isn't necessary if `entity_manager` is provided.

    Returns:
        torch.Tensor: Reward for tracking of linear velocity commands (xy axes)
    """
    assert (
        command is not None or vel_cmd_manager is not None
    ), "Either command or vel_cmd_manager must be provided to command_tracking_lin_vel"

    linear_vel_local = None
    if entity_manager is not None:
        linear_vel_local = entity_manager.get_linear_velocity()
    else:
        robot = getattr(env, entity_attr)
        linear_vel_local = entity_lin_vel(robot)

    if vel_cmd_manager is not None:
        command = vel_cmd_manager.command[:, :2]

    lin_vel_error = torch.sum(torch.square(command - linear_vel_local[:, :2]), dim=1)
    return torch.exp(-lin_vel_error / sensitivity)


def command_tracking_ang_vel(
    env: GenesisEnv,
    commanded_ang_vel: torch.Tensor = None,
    vel_cmd_manager: VelocityCommandManager = None,
    sensitivity: float = 0.25,
    entity_attr: str = "robot",
    entity_manager: EntityManager = None,
) -> torch.Tensor:
    """
    Reward for tracking commanded angular velocity (yaw)

    Args:
        env: The Genesis Forge environment
        commanded_ang_vel: The commanded angular velocity in the shape (num_envs, 1)
        vel_cmd_manager: The velocity command manager
        sensitivity: A lower value means the reward is more sensitive to the error
        entity_manager: The entity manager for the robot/entity the reward is being computed for.
                        This is slightly more performant than using the `entity_attr` parameter.
        entity_attr: The attribute name of the entity in the environment. This isn't necessary if `entity_manager` is provided.

    Returns:
        torch.Tensor: Reward for tracking of angular velocity commands (yaw)
    """
    assert (
        commanded_ang_vel is not None or vel_cmd_manager is not None
    ), "Either commanded_ang_vel or vel_cmd_manager must be provided to command_tracking_ang_vel"

    angular_vel = None
    if entity_manager is not None:
        angular_vel = entity_manager.get_angular_velocity()
    else:
        robot = getattr(env, entity_attr)
        angular_vel = entity_ang_vel(robot)

    if vel_cmd_manager is not None:
        commanded_ang_vel = vel_cmd_manager.command[:, 2]

    ang_vel_error = torch.square(commanded_ang_vel - angular_vel[:, 2])
    return torch.exp(-ang_vel_error / sensitivity)


def stand_still_joint_deviation_l1(
    env,
    command_threshold: float = 0.06,
    vel_cmd_manager: VelocityCommandManager = None,
    action_manager: PositionActionManager = None,
) -> torch.Tensor:
    """
    Penalize offsets from the default joint positions when the command is very small.

    Args:
        env: The Genesis Forge environment
        command_threshold: The threshold for the command to be considered small
        vel_cmd_manager: The velocity command manager
        action_manager: The action manager to get the joint positions and recent actions from.

    Returns:
        torch.Tensor: Penalty for offsets from the default joint positions when the command is very small
    """
    command = vel_cmd_manager.command
    joint_pos = action_manager.get_dofs_position()
    default_pos = action_manager.default_dofs_pos
    joint_deviation = torch.sum(torch.abs(joint_pos - default_pos), dim=1)

    # Penalize motion when command is nearly zero.
    return joint_deviation * (torch.norm(command[:, :2], dim=1) < command_threshold)


"""
Contacts
"""


def has_contact(
    _env: GenesisEnv, contact_manager: ContactManager, threshold=1.0, min_contacts=1
) -> torch.Tensor:
    """
    One or more links in the contact manager are in contact with something.

    Args:
        env: The Genesis Forge environment
        contact_manager: The contact manager to check for contact
        threshold: The force threshold for contact detection (default: 1.0)
        min_contacts: The minimum number of contacts required. (default: 1)

    Returns:
        1 for each contact meeting the threshold
    """
    has_contact = contact_manager.contacts[:, :].norm(dim=-1) > threshold
    result = has_contact.sum(dim=1) >= min_contacts
    return result.float()


def contact_force(
    _env: GenesisEnv, contact_manager: ContactManager, threshold: float = 1.0
) -> torch.Tensor:
    """
    Reward for the total contact force acting on all the target links in the contact manager over the threshold.

    Args:
        env: The Genesis Forge environment
        contact_manager: The contact manager to check for contact
        threshold: The force threshold for contact detection (default: 1.0 N)

    Returns:
        The total force for the contact manager for each environment
    """
    violation = torch.norm(contact_manager.contacts[:, :, :], dim=-1) - threshold
    return torch.sum(violation.clip(min=0.0), dim=1)


def feet_air_time(
    env: GenesisEnv,
    contact_manager: ContactManager,
    time_threshold: float,
    time_threshold_max: float | None = None,
    vel_cmd_manager: VelocityCommandManager | None = None,
) -> torch.Tensor:
    """Reward long steps taken by the feet using L2-kernel.

    This function rewards the agent for taking steps that are longer than a threshold. This helps ensure
    that the robot lifts its feet off the ground and takes steps. The reward is computed as the sum of
    the time for which the feet are in the air.

    If the velocity commands are small (i.e. the agent is not supposed to take a step), then the reward is zero.

    Args:
        env: The Genesis Forge environment
        contact_manager: The contact manager to check for contact
        time_threshold: The minimum time (in seconds) the feet should be in the air
        time_threshold_max: (optional) The maximum time (in seconds) the feet should be in the air.
                            If the time is greater than this value, then the reward is zero.
        vel_cmd_manager: The velocity command manager

    Returns:
        The reward for the feet air time
    """
    made_contact = contact_manager.has_made_contact(env.dt)
    last_air_time = contact_manager.last_air_time

    # Calculate the air time
    air_time = (last_air_time - time_threshold) * made_contact
    if time_threshold_max is not None:
        air_time = torch.clamp(air_time, max=time_threshold_max - time_threshold)
    reward = torch.sum(air_time, dim=1)

    # no reward for zero velocity command
    if vel_cmd_manager is not None:
        reward *= torch.norm(vel_cmd_manager.command[:, :2], dim=1) > 0.1
    return reward


def feet_slide(
    env,
    contact_manager: ContactManager,
    entity_attr: str = "robot",
) -> torch.Tensor:
    """Penalize feet sliding.

    This function penalizes the agent for sliding its feet on the ground. The reward is computed as the
    norm of the linear velocity of the feet multiplied by a binary contact sensor. This ensures that the
    agent is penalized only when the feet are in contact with the ground.

    This penalty is less effective at longer foot-contact links (for example, long legs without dedicated foot links),
    because they might have some velocity while they're being used to move the robot. However, dedicated foot links
    will be stationary on the ground and not moving while pushing the robot forward.

    Args:
        env: The Genesis Forge environment
        contact_manager: The contact manager for the feet
        entity_attr: The attribute name of the robot entity that the feet are attached to.

    Returns:
        The penalty for the feet slide
    """
    # Get links in contact
    contacts = torch.norm(contact_manager.contacts[:, :, :], dim=-1) > 1.0

    # Get link velocities.
    # If the links aren't moving, then they're being used to move the robot and not sliding.
    link_ids = contact_manager.local_link_ids
    robot: RigidEntity = getattr(env, entity_attr)
    link_vel = robot.get_links_vel(links_idx_local=link_ids)

    return torch.sum(link_vel.norm(dim=-1) * contacts, dim=1)
