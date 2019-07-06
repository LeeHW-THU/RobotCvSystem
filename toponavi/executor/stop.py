import wiringpi
import pathlib
import yaml

if __name__ == "__main__":
    wiringpi.wiringPiSetup()

    with (pathlib.Path(__file__).parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)

    pins = config['pins']['motor']
    for m in ['left', 'right']:
        seg = pins[m]
        for p in ['forward', 'backward']:
            wiringpi.digitalWrite(seg[p], 0)
