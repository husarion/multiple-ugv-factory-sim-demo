# multiple-ugv-factory-sim-demo
Simulation of the Multiple Husarion Panther UGV Platforms in an Automated Factory Application

![world](.docs/world.png)
![robots](.docs/robots.png)

# Running

```bash
docker compose -f docker/compose.simulation.yaml up
```


```bash
docker compose -f docker/compose.navigation.yaml up
```

```bash
docker compose -f docker/compose.simulation.yaml exec simulation bash -c "source install/setup.bash && python3 src/husarion_ugv_pick_and_place_demo/husarion_ugv_pick_and_place_demo/robots_commander.py"
```

```bash
python3 src/husarion_ugv_pick_and_place_demo/husarion_ugv_pick_and_place_demo/robots_commander.py
```
