
from JumpScale import j

j.base.loader.makeAvailable(j, 'remote')

from .Cuisine import OurCuisine

j.remote.cuisine = OurCuisine()
