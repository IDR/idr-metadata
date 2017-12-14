# Condensation ScreenA

## Calculation

1344x1024, Z=1, T=1, 1 channel
Features are calculated for the middle 50% at three time-points offset from the last timepoint:
- (336,256) - (1007,767)
- T: [-5, -150, -280]

```
python calc.py --broker BROKER_URL
    --out-dir /uod/idr-scratch/idr0002-screenA
    /uod/idr/features/idr0002-heriche-condensation/screenA/input/
    --docker-img manics/pyfeatures:merge -l idr0002-A.taskids
    --
    -l --tsubset=-5,-150,-280 -W 672 -H 512 --offset-x 336 --offset-y 256
    -x 1344 -y 1024
```

Trello cards:
- https://trello.com/c/ILUModaH/18-condensation-feature-calculation
