# Changelog

## 0.2.9

- Adjust to new routing keys for incoming and outgoing [almabtrieb#42](https://codeberg.org/bovine/almabtrieb/issues/42)
- Add almabtrieb as a script in pyproject.toml

## 0.2.8

- Add ability to wait for replies with trigger
- Add notice NoIncomingException was replaced [almabtrieb#37](https://codeberg.org/bovine/almabtrieb/issues/37)
- Add py.typed file [almabtrieb#38](https://codeberg.org/bovine/almabtrieb/issues/38)
- Add ability to configure logging and echo in CLI
- improve type hints
- add missing `accountName` to `InformationResponse`.

## 0.2.7

- Add `python -malmabtrieb err`
- Include CHANGES in docs
- Use unified Stream class for queues [alamabtrieb#32](https://codeberg.org/bovine/almabtrieb/issues/32)
- Improve index doc instructions [almabtrieb#31](https://codeberg.org/bovine/almabtrieb/issues/31)
- Repair auto_follow option in cli [almabtrieb#33](https://codeberg.org/bovine/almabtrieb/issues/33)
- Add logo

## 0.2.6

- Add missing methods to cli tool [almabtrieb#27](https://codeberg.org/bovine/almabtrieb/issues/27)
- Use proper InformationResponse [almabtrieb#29](https://codeberg.org/bovine/almabtrieb/issues/29)
- Fixed docs text [almabtrieb#26](https://codeberg.org/bovine/almabtrieb/issues/26)
- Repair docs [almabtrieb#28](https://codeberg.org/bovine/almabtrieb/issues/28)

## 0.2.5

- Add `on_disconnect` handler [almabtrieb#24](https://codeberg.org/bovine/almabtrieb/issues/24)
- Add `python -malmabtrieb info`

## 0.2.4

- Improved connection close behavior [almabtrieb#21](https://codeberg.org/bovine/almabtrieb/issues/21)
- Add command line tool

## 0.2.3

- Remove incorrect logging potentially containing passwords

## 0.2.2 ([Milestone](https://codeberg.org/bovine/almabtrieb/milestone/10249))

- Added timeout to MQTT [almabtried#18](https://codeberg.org/bovine/almabtrieb/issues/18)
- Added timeout to AMQP connect, [almabtrieb#15](https://codeberg.org/bovine/almabtrieb/issues/15)

## 0.2.1 ([Milestone](https://codeberg.org/bovine/almabtrieb/milestone/10246))

- Add automation of release [almabtrieb#13](https://codeberg.org/bovine/almabtrieb/issues/13)
- Add name argument to create actor [almabtrieb#12](https://codeberg.org/bovine/almabtrieb/issues/12)

## 0.2.0

- Change interface, get rid of `connect` method
- Update to new Cattle Drive version

## 0.1.3

- Validate used method in trigger against the allowed methods from `method_information` in the info response.

## 0.1.2

- Set RabbitMQ queues to auto delete

## 0.1.1

- Fix [almabtrieb#7](https://codeberg.org/bovine/almabtrieb/issues/7)

## 0.1.0

Initial version
