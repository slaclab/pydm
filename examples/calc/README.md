# Calculation Plugin Example

# Running the Examples
This example uses an EPICS IOC via the `demo.db`.
The Process Variables available are:

- `DEMO:ANGLE`, the angle in degrees which increments by one every 0.1s
- `DEMO:SIN`, the sine of the angle
- `DEMO:COS`, the cosine of the angle
- `DEMO:TAN`, the tangent of the angle

To run the IOC do:
```shell script
softIoc -d demo.db
```

To run the screen do:

```shell script
pydm sin_cos_tan.ui
```
