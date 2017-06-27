# LightningTweeter

This script uses the AS9535 sensor to detect lightning strikes and send tweets with related information : lightning energy, distance to the storm.

## Dependencies

This script uses those libraries :

- [RaspberryPi-AS3935](https://github.com/pcfens/RaspberryPi-AS3935/) : `pip install RPi_AS3935`
- [Tweepy](http://www.tweepy.org/) : `pip install tweepy`

You also need to configure I2C on your Raspberry Pi. Adafruit made a [tutorial](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c) explaining how to.

If you want to know more about how I use it, you can read [this article](https://hexaly.se/2017/06/27/lightning-strikes-detection-station-that-tweets-storm-alerts/).
