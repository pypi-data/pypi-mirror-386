from .joints import hexSnapFeature

# include new functions to cadquery
cq.Workplane.hexSnapFeature = hexSnapFeature