# Cellmorph ScreenA

## Calculation

1344x1024, Z=1, T=1, 3 channels
Images contain 4 separate tiles/fields in the same image, e.g. https://idr.openmicroscopy.org/webclient/img_detail/1824426/

Features are calculated for one of the quarters:
- (0,0)-(671,511)
- independent channels

```
python calc.py --user celery
    --out-dir /uod/idr-scratch/idr0012-screenA --broker redis://:PASSWORD@example.org:6379
    /uod/idr/features/idr0012-fuchs-cellmorph/screenA/input/
    --
    -l -W 672 -H 512 --offset-x 0 --offset-y 0 -x 1344 -y 1024
```
