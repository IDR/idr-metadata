# Mitocheck ScreenB

## Calculation

1344x1024, Z=1, T=1, 1 channel
Features are calculated for the middle 50% at three time-points:
- (336,256) - (1007,767)
- T: [6, 46, 86]

```
python calc.py --user celery
    --out-dir /uod/idr-scratch/idr0013-screenB --broker redis://:PASSWORD@example.org:6379
    /uod/idr/features/idr0013-neumann-mitocheck/screenB/serialize/data/
    --
    -l -W 672 -H 512 --offset-x 336 --offset-y 256 -x 1344 -y 1024
```
