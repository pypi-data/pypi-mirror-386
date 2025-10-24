# Karabo SCADA Framework - Services
![Karabo Badge](https://img.shields.io/badge/Karabo-Services-blue?style=social&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAIRlWElmTU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAIAAIdpAAQAAAABAAAAWgAAAAAAAABIAAAAAQAAAEgAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAABigAwAEAAAAAQAAABgAAAAAEQ8YrgAAAAlwSFlzAAALEwAACxMBAJqcGAAAAVlpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDYuMC4wIj4KICAgPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgICAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iPgogICAgICAgICA8dGlmZjpPcmllbnRhdGlvbj4xPC90aWZmOk9yaWVudGF0aW9uPgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KGV7hBwAAB4lJREFUSA1tVQlwU9cVPX%2FXZmuxZcuSjWyMwQaDsUvLWmo7bEOHLSnETckQBgITWpO2CSmTlqnatEyazNCWpmEZYEpCS7DLpA3FbVPWTAIJ2GZfHNsgL1iWZGuz9S19Sf%2F1fWfSYdpeaeZ96f13l3PPuY%2FZsuWA0CfdZlFWhsDR22pb28EUHrOT2yt2jcrJpWlVcqWUaFEqMcDprTXQm10RNtF%2FNdfQ%2BeLiN0bvPXZk%2FLHW4%2BH1NhvH%2FPeG9vvNG4PGHXd99p3Xji%2FfZn3j93ZrHkZVFhkIAKMDUkGVVSJsJg00%2B585v73i%2BT0vS6PDCYur56mV1YE6hqE7X5gWwFD5zafdtvKaCpImlUl5pJIjqFCM5pLcRMi41%2FV6anIR9W0ATz8cVDDQjsehen1Qfte3WdfElaIkPqSOESZgMFt6ddlZDxgl0clmZXfwjUdOt930DRUakTFF%2FX6M%2BANIyTLUTAZ9LEfez%2FmRUC%2BnhVyavMAQEOpbSbHwj4H9LAHd5VA0Q4LtiFA4IEoOnSA4THbH10IZgqlmmlUKnFU0ZJv0AqvqbHZic5dkFDlOg4wwylic%2B2Uwxey8F4FFL8GpE5EhBB1yAoiNAkYd5hZO5MrLdCqnN6YFSa%2BC40k6EmIu3HnI1q36Bs%2FHlNSVzjPnViS7vCn3E3Ml5%2FQqTjLbkFGSFAuCRckxxKNhhINBDA08wmg4jEpnAXKnToTRagMr6UEYhiWEsDq9Af23buLRgSO00GIms2JhiOd5od9sz8GN0wcYX0cvlr5qRv6kMqR1OgR6e8BxPLLyXLC4iuGunAllNEobTVvHsEiMxDD84C6sBQWw5ORgqNeLwJV2JGFSMd%2FNyWk1wDM879VlmSiyZaS8qhj%2F3H0YmDwFVfWVkD%2B9gs7rXrjnTYO1uAiumhqIhixEB%2FrRc%2FlT9LV7oUS8KJhZDZ%2FMAZ8HqZ8RTDQaSFDgkQIJsYIk9PCShBxE2Ps3OvHK7k349Y4VCN%2FroM79KJnsQs%2Blh7j%2Bp99AHh4Gy%2FNIRKPoPncMlmwB2TnFiJuy8NOty%2FDR1bew81db8SB%2BFVUuO1SWC%2FOEZfoLCp34BEXc6k215OUXnmVyzCY8tWoZdh9sxv6feFA%2Bax7utxKKzBey4UQBkjQXVjaDjuEUDr2yGasXzKTEiOE7y79OHnhfRbfNDYHjo2yByA2yBkMK65exP%2FvBc0SJjyIwOIgiuwVb1i4FapYg2toPkRaf0ZSlGQ2UR1Lo8N7Fih%2BuQVWxAx237%2BDa9Tuwm41YvmgB00ZFIzGIsjkWw7BKyDCsFhj0OlWWxzAYGEZz8wcoddjw7i82w4cgyqAgnc6M%2B%2BdYFn3K55Qo89CweB7I2Ag4UURl1XRkOAnJRBIOWiUYEmW%2FXzszSsXhAysgGhtRbTkWHD58AuXlZcjONmHJnBn49s5G3EE7skQeVAYQqTPAhKcbFqK6rAjuCS44CvIRDkUotQE5HmcHKa15UYyyFFciZFKPcOEmzXxIpWFRUuwET1mgqiosJj1qZ5QCdd9DfukkpKk%2BDDYb8jZvhSNLD53AYcAXxIWLn%2BHGjbuIyQly9szHTFlkCGlWiLJazVQovRp13953nPTSl1etXIre3gGEwxGwHAdWGxB5FjACLZuWQHUFSa8fz1Y7393thd8fRGGhA5%2B03sTfmvaj1JkHJZ2JjQeQVaZ3%2BdxKtPzlIHP67CUUuSdgWsUkdHY%2BBE%2FxNpuzKb3HQOh80pyDqHSuEiRSaToZeOTbbVi5vA7Fk0px7OSHNKQFyaRCURAj4wF4ke%2BP0D%2FMFJ9dLx4ll9pvw1lUiK%2FOqkJfIIQP%2FnERViFDhaMpmLKJBnFLPPZ7jqG55TyKSidCpYrfd%2BQ9nP%2FzvrTZOBWixQomkx6j8qNMXLvJSjuyUVb0fNh7LX300DlIFpYR9Abm5789ivfe8qBQpmp35cFI8U%2FEIuj61zlEHj3Ah6daESWjePfURfX4xfuZKdVzhOr1a%2BDIsb6zcIp5v9Z0eDwetrt4weZ4PL4r1NNTqFHurC%2BQxuG%2FU%2FBjQulXytHddg3T161BWX09Yo96cea1A8iblAcmMAp%2FuVuZv2Sh6HS5wMgjQ26XY9ubDU80a7413jEehqHswUFP68CxLlPWS4qiND43o9ouz6rBpUPvJLrbung6rHmGNlzDX1utJXYEuryqmOVQVjQ8qTMaKaOSoyfqqmq%2Bu2FRxTCwliOkibC0azRLoLGlRfLMcsrHNtS%2FJqrxqnhgcA8RhPi0b63W2adP4JP4OJGKyxqF6JdB%2BGGnwjmd6vzGdTo9q%2FrsJPHMH7Y3NGjOG%2Fe2SPQy1VRJxiHSAmhW6znPw%2B3lL2zcSG8UYP3bf52SFsQdY7K8yd%2FZhajPl6mor1Pl4SDpuXVLnDJ7NnKzjX%2BcnZ%2F%2F0vOr5vixtonzTAPn8axTtPP0jqCp%2FB9b29QkBu%2Fa1QueuvHhs%2BXk5ZpYOPpjJZV%2BkvISybE4DKoSKMrN3bbn2cUnx13s3St5QqEU7acG97hpAb58%2Ft%2BVbm450EqV9R89YcOJj%2BY37DvV%2BsLB90%2B1tHfatUNNTU3cXgrvl8609bFn7t8fxThrSai%2FQAAAAABJRU5ErkJggg%3D%3D)
![PyPI - Version](https://img.shields.io/pypi/v/karabo-services)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/karabo-services)
![PyPI - License](https://img.shields.io/pypi/l/karabo-services)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/karabo-services)
![GitHub language count](https://img.shields.io/github/languages/count/European-XFEL/Karabo)
![GitHub top language](https://img.shields.io/github/languages/top/European-XFEL/Karabo)
![GitHub contributors](https://img.shields.io/github/contributors/European-XFEL/Karabo)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/European-XFEL/Karabo)
![GitHub Repo stars](https://img.shields.io/github/stars/European-XFEL/Karabo)


This package provides the service commands required in a Karabo environment.

Please check https://pypi.org/project/Karabo/ for an overview of Karabo's components
and ways to install the full system.

# Installation

To install run 

```bash
pip install karabo.services
```

or use the `full` or `services` options when installing the `karabo` package:

```bash
pip install karabo[full]
pip install karabo[services]
```

This package itself is pure Python but depends on `karabo.daemontools` which requires compiled code.

You can add the option `with_cpp` to also install `karabo.cpp` and the associated services

```bash
pip install karabo.services[with_cpp]
```



# List of commands

## karabo-activate

Initially activates a Karabo environment by initializing structures into a user
defined directory. You will need to execute this command first, before most 
other commands succeed (you'll get a message that Karabo was not found if you didn't).

Execute 

```bash
karabo-activate --init-to $PATH --help
```

to see the options for creating a Karabo environment in `PATH`. 
You can use the the `--broker-host` and `--broker-topic` modifiers
to configure the default broker settings Karabo servers added to this environment will use. Run `karabo-activate`
again (you can omit `--init-to` now) to reconfigure these settings. The `--backbone` option will only take effect
when an environment is first created, and will install the Karabo backbone services into this environment.


## Starting a Karabo standalone system

If you wish to run Karabo standalone you can do this if you have `podman` or `docker` installed on the system.

First, run

```bash
karabo-activate --init-to PATH --standalone
```

Then run 

```bash
podman-compose -f $PATH/var/containers/compose.yaml up
```

or (`docker-compose ...`). This will start containerized version of the services a full 
Karabo installation requires:

- A RabbitMQ broker (user: xfel, pw: karabo)
- An Influx database instance for logging (user: infadm, pw: admpwd)
- A Grafana installation with the Influx database as a pre-provisioned source (user: admin, pw: admin)

Note that the Grafana provisioning assumes `karabo` as the broker topic in use. If you've
used `karabo-activate --broker-topic TOPIC` you'll need to edit the data source to refer to
a database of `TOPIC` from inside Grafana.

Additionally, the above setup will use a local `sqlite` database for projects.
You can switch this to ` MySQL` database by providing the following arguments
to `karabo-activate`:

- `--project-db HOST:PORT`
- `--project-db-user USER`
- `--project-db-pw PASSWORD`
- `--project-db-name DATABASE_NAME`


Finally, run

```bash
$PATH/activate
```

followed by 

```bash
karabo-start
```

## ikarabo

The interactive Karabo Python shell. Includes device orchistration and scripting using Karathon.

## karabo-start, karabo-stop, karabo-kill

Scripts that start, stop, or kill a Karabo device server managed by karabo.daemontools or all such servers.

## karabo-check

Outputs the current status of Karabo services managed by karabo.daemontools

## karabo-add-deviceserver, karabo-remove-deviceserver

Adds or removes a Karabo device server to the services managed by karabo.daemontools.

## Additional commands.

This package exposes additional (internal) commands as entrypoints which are not further described here.