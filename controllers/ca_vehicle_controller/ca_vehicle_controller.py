import os
import subprocess
import random
import asyncio
from controller import Robot, Supervisor
import circle_functions as cf

# Constants
TIMESTEP = 128
MAX_SPEED = 10

CA_PATH = os.path.join("CyberneticAutomata", "ca.exe")
CONFIG_PATH = os.path.join("CyberneticAutomata", "webot_skinner_config.cfg")

def setup_motors(robot: Robot) -> list:
    """
    Initialize the motors and set their initial positions and velocities.

    Args:
        robot (Robot): The robot object.

    Returns:
        list: List of motor devices.
    """
    wheel_names = ("wheel1", "wheel2", "wheel3", "wheel4")
    wheels = [robot.getDevice(name) for name in wheel_names]
    for wheel in wheels:
        wheel.setPosition(float('inf'))
        wheel.setVelocity(0.0)
    return wheels

def setup_sensors(robot: Robot) -> list:
    """
    Enable light sensors and set their initial parameters.

    Args:
        robot (Robot): The robot object.

    Returns:
        list: List of sensor devices.
    """
    sensor_names = ("ls_left", "ls_right")
    sensors = [robot.getDevice(name) for name in sensor_names]
    for sensor in sensors:
        sensor.enable(TIMESTEP)
    return sensors

def set_wheel_speeds(wheels: list, left_speed: float, right_speed: float) -> None:
    """
    Set the velocities of the wheels based on the given speeds.

    Args:
        wheels (list): List of wheel devices.
        left_speed (float): Speed for the left wheels.
        right_speed (float): Speed for the right wheels.
    """
    wheels[0].setVelocity(left_speed)
    wheels[2].setVelocity(left_speed)
    wheels[1].setVelocity(right_speed)
    wheels[3].setVelocity(right_speed)

def get_stimulus(sensors: list) -> tuple:
    """
    Calculate the stimulus and strength based on sensor values.

    Args:
        sensors (list): List of sensor devices.

    Returns:
        tuple: Stimulus value and strength.
    """
    left_value, right_value = sensors[0].getValue() / 100, sensors[1].getValue() / 100
    strength = round(((left_value + right_value) / 2) / 10, 3)

    if left_value == 10 and right_value == 10:
        stimulus = 5
    elif left_value > 1 and right_value > 1 and abs(left_value - right_value) <= 0.075:
        stimulus = 1
    elif left_value > right_value:
        stimulus = 2
    elif right_value > left_value:
        stimulus = 3
    else:
        stimulus = 4

    return stimulus, max(strength, 0.001)

def get_direction(response: list) -> str:
    """
    Map the response from the cybernetic automaton to a direction.

    Args:
        response (list): List containing response information.

    Returns:
        str: Mapped direction.
    """
    direction_map = ("idle", "forward", "left", "right", "backward")
    try:
        response_code = int(response[0])
        return direction_map[response_code] if 0 <= response_code < len(direction_map) else "unknown"
    except (ValueError, IndexError):
        return "unknown"

async def read_response(pid: subprocess.Popen) -> str:
    """
    Asynchronously read a response from the cybernetic automaton.

    Args:
        pid (subprocess.Popen): Process ID of the cybernetic automaton subprocess.

    Returns:
        str: Response from the cybernetic automaton.
    """
    return await asyncio.get_event_loop().run_in_executor(None, pid.stdout.readline)

async def write_response(pid: subprocess.Popen, input_data: str) -> None:
    """
    Asynchronously write an input to the cybernetic automaton.

    Args:
        pid (subprocess.Popen): Process ID of the cybernetic automaton subprocess.
        input_data (str): Data to be written.
    """
    await asyncio.get_event_loop().run_in_executor(None, pid.stdin.write, input_data)
    await asyncio.get_event_loop().run_in_executor(None, pid.stdin.flush)

async def main() -> None:
    """
    Main asynchronous function to control the robot and interact with the cybernetic automaton.
    """
    my_robot = Robot()
    wheels = setup_motors(my_robot)
    light_sensors = setup_sensors(my_robot)

    supervisor = Supervisor()
    mouse_node = supervisor.getFromDef('mouse')
    wheel_nodes = [supervisor.getFromDef(wheel_name) for wheel_name in ["wheel_end1", "wheel_end2", "wheel_end3", "wheel_end4"]]

    rotation_presets = (
        [0.577351, 0.577349, 0.577351, 2.0944],    # N 0
        [0.862855, 0.35741, 0.357406, 1.71779],    # NE 1
        [-1, 0, 0, -1.57081],                      # E 2
        [-0.86286, 0.357395, 0.357409, -1.71778],  # SE 3
        [-0.577352, 0.577346, 0.577352, -2.0944],  # S 4
        [-0.281086, 0.678592, 0.678605, -2.59356], # SW 5
        [0, 0.707104, 0.707109, -3.14159],         # W 6 
        [0.281087, 0.678594, 0.678601, 2.59358]    # NW 7
    )

    wheel_positions = (
        [0.06, 0, 0.05],
        [-0.06, 0, 0.05],
        [0.06, 0, -0.05],
        [-0.06, 0, -0.05]
    )

    with subprocess.Popen([CA_PATH, CONFIG_PATH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as pid:
        try:
            for i in range(300):
                x, y = cf.generate_random_point_in_circle(2.4)
                distance, quadrant = cf.origin_distance_quadrant(x, y)
                rotation_adjusted = cf.rotate_tuple(rotation_presets, quadrant)
                rotation_num = random.randint(0, 7)
                min_steps = cf.calculate_min_steps(distance, rotation_num)
                
                my_robot.step(TIMESTEP * 5)
                mouse_node.getField('translation').setSFVec3f([x, y, 0.05])
                mouse_node.getField('rotation').setSFRotation(rotation_adjusted[rotation_num])
                
                for wheel, wheel_node in enumerate(wheel_nodes):
                    wheel_node.getField('translation').setSFVec3f(wheel_positions[wheel])
                    wheel_node.getField('rotation').setSFRotation([0, 1, 0, 1.5708])
                
                my_robot.step(TIMESTEP * 5)

                hunger = 0
                step = 0
                while my_robot.step(TIMESTEP) != -1:
                    stimulus, strength = get_stimulus(light_sensors)

                    if stimulus == 4:
                        hunger = max(0.001, min(1, hunger))
                        strength = 1
                        hunger += 0.003

                    elif stimulus == 5:
                        strength = 1
                        await write_response(pid, f"{stimulus}/{strength:.3f}\n")
                        await read_response(pid)
                        break
                    
                    await write_response(pid, f"{stimulus}/{strength:.3f}\n")
                    response = await read_response(pid)
                    response = response.strip().split(" ")

                    direction = get_direction(response)
                    speed = float(response[1]) * 10

                    match direction:
                        case "forward":
                            left_speed = right_speed = max(5, speed)
                        case "left":
                            left_speed = max(5, speed)
                            right_speed = 0
                        case "right":
                            left_speed = 0
                            right_speed = max(5, speed)
                        case "backward":
                            left_speed = right_speed = -max(5, speed)
                        case _:
                            left_speed = right_speed = 0

                    set_wheel_speeds(wheels, left_speed, right_speed)
                    
                    my_robot.step(TIMESTEP * 2)
                    
                    step += 1
                    if step >= 188 + min_steps:
                        break

                await write_response(pid, "0/1\n")
                await read_response(pid)
                print(i, max(0, (step - min_steps)))
        finally:
            pid.stdin.close()
            pid.terminate()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
            break
        except Exception as e:
            print("An error occurred:", e)
            print("Restarting the program...")
            continue

