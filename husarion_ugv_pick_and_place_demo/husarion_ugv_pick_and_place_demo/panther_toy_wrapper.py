import subprocess

def get_panther_toy_id():
    output = subprocess.run(["ign topic -e -n 1 -t /world/industrial-warehouse/pose/info | grep panther_toy_model -A 1 | grep id | cut -d \":\" -f 2"], capture_output=True, shell=True)
    panther_toy_id = output.stdout.decode('utf-8').strip()
    return panther_toy_id

def remove_panther_toy():
    panther_toy_id = get_panther_toy_id()
    subprocess.run([f"ign service -s /world/industrial-warehouse/remove   --reqtype ignition.msgs.Entity   --reptype ignition.msgs.Boolean   --req 'id: {panther_toy_id}'   --timeout 10000"], shell=True)

def create_panther_toy():
    create_command = '''
        ign service -s /world/industrial-warehouse/create   --reqtype ignition.msgs.EntityFactory   --reptype ignition.msgs.Boolean   --req '
        sdf_filename: "/ros2_ws/src/husarion_ugv_pick_and_place_demo/models/panther_toy/model.sdf",
        name: "panther_toy_model",
        pose {
        position { x: -1.7 y: -0.84 z: 1.05 }
        orientation { x: 0.7071 y: 0 z: 0 w: 0.7071 }
        }'   --timeout 10000
    '''
    subprocess.run([create_command], shell=True)

