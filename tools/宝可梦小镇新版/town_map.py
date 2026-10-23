"""Canonical 16x10 cells; shared by validation, clicks, and scene rendering."""
from town_state import SHOP

WIDTH,HEIGHT=16,10
def footprint(kind):return (2,1) if kind=='rug' else (1,1)
def blocked(area):
    cells=set()
    if area=='home':
        cells.update((x,y) for x in range(2,6) for y in range(1,4));cells.update((x,y) for x in (12,13) for y in (2,3));cells.update((x,8) for x in range(6,10))
    elif area=='plaza':cells.update((x,y) for x in (7,8) for y in range(HEIGHT))
    elif area=='orchard':
        cells.update((x,y) for left in (2,7,12) for x in (left,left+1) for y in (2,3));cells.update((x,8) for x in range(WIDTH))
    return cells
def cells_for(kind,x,y):
    w,h=footprint(kind);return {(i,j) for i in range(x,x+w) for j in range(y,y+h)}
def can_place(data,area,kind,x,y,ignore_id=None):
    if area not in data['areas'] or kind not in SHOP or type(x) is not int or type(y) is not int:return False
    cells=cells_for(kind,x,y)
    if any(not (0<=i<WIDTH and 0<=j<HEIGHT) for i,j in cells) or cells&blocked(area):return False
    for item,position in data['placements'][area].items():
        if item!=ignore_id and cells&cells_for(data['inventory'][item],*position):return False
    return True
def walkable(data,area):
    occupied=blocked(area).copy()
    for item,pos in data['placements'][area].items():occupied|=cells_for(data['inventory'][item],*pos)
    return {(x,y) for x in range(WIDTH) for y in range(HEIGHT)}-occupied
