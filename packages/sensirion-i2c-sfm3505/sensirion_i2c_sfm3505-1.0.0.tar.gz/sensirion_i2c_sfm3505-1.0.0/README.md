# Python I2C Driver for Sensirion SFM3505

This repository contains the Python driver to communicate with a Sensirion SFM3505 sensor over I2C.

<img src="https://raw.githubusercontent.com/Sensirion/python-i2c-sfm3505/master/images/SFM3505.png"
    width="300px" alt="SFM3505 picture">


Click [here](https://sensirion.com/products/catalog/SFM3505) to learn more about the Sensirion SFM3505 sensor.



The default I²C address of [SFM3505](https://sensirion.com/products/catalog/SFM3505) is **0x2E**.



## Connect the sensor

You can connect your sensor over a [SEK-SensorBridge](https://developer.sensirion.com/product-support/sek-sensorbridge/).
For special setups you find the sensor pinout in the section below.

<details><summary>Sensor pinout</summary>
<p>
<img src="https://raw.githubusercontent.com/Sensirion/python-i2c-sfm3505/master/images/SFM3505-pinout.png"
     width="300px" alt="sensor wiring picture">

| *Pin* | *Cable Color* | *Name* | *Description*  | *Comments* |
|-------|---------------|:------:|----------------|------------|
| 1 | green | SDA | I2C: Serial data input / output |
| 2 | red | VDD | Supply Voltage | 3.3V to 3.4V
| 3 | black | GND | Ground |
| 4 | yellow | SCL | I2C: Serial clock input |
| 5 |  | SRDY |  |


</p>
</details>


## Documentation & Quickstart

See the [documentation page](https://sensirion.github.io/python-i2c-sfm3505) for an API description and a
[quickstart](https://sensirion.github.io/python-i2c-sfm3505/execute-measurements.html) example.


## Contributing

### Check coding style

The coding style can be checked with [`flake8`](http://flake8.pycqa.org/):

```bash
pip install -e .[test]  # Install requirements
flake8                  # Run style check
```

In addition, we check the formatting of files with
[`editorconfig-checker`](https://editorconfig-checker.github.io/):

```bash
pip install editorconfig-checker==2.0.3   # Install requirements
editorconfig-checker                      # Run check
```

## License

See [LICENSE](LICENSE).