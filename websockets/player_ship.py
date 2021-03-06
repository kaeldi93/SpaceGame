import utils, math, json
import bullet
from utils import Point, Vector
from bullet import Bullet
from mover import Mover

# The Ship class represents player (and potentially later AI) driven ships. Currently,
# it has a very large constructor, as there are a lot of things to keep track
# of when a player is flying a spaceship. Hopefully in the future this class will
# include support for powerups, different types of ships, and various other fun
# things, but those are all theoretical at this point.

class Ship(Mover):
  
  def __init__(
    self,
    center = Point(utils.X_MAX / 2, utils.Y_MAX / 2),
    speed = Vector(0, 0),
    rotation = -math.pi/2,
    name = "testy mc testface",
    inputs = {
    "up": False,
    "down": False,
    "left": False,
    "right": False,
    "space": False,
    "F": False,},
    bullets = [],
    bullet_countdown = 0,
    bullet_recharge = 120,
    bullet_speed = 2.5,
    lives = 3,
    dead = False,
    death_countdown = 0,
    max_bullets = 7,
    size = 10/6,
    last_updated = None,
    leaving = False,
    score = 0,
    acceleration = 0.005,
    turn_speed = 0.0075,
    warp_countdown = 0,
    invuln_time = 2000
    ):
    # Center and speed must be copied, since Python precomputes the
    # value for default parameters, then passes references.
    # I am not a fan of this.
    super().__init__(center.copy(), speed.copy(), rotation)
    
    self.name = name
    self.inputs = inputs
    self.bullets = list(bullets)
    self.bullet_countdown = bullet_countdown
    self.bullet_recharge = bullet_recharge
    self.bullet_speed = bullet_speed
    self.lives = lives
    self.dead = dead
    self.death_countdown = death_countdown
    self.max_bullets = max_bullets
    self.size = size
    self.last_updated = utils.get_time() if last_updated == None else last_updated
    self.leaving = leaving
    self.score = score
    self.acceleration = acceleration
    self.turn_speed = turn_speed
    self.warp_countdown = warp_countdown
    self.invuln_time = invuln_time

  def from_dict(self, data):
    super().from_dict(data)
    bullet_list = [Bullet().from_dict(b) for b in data["bullets"]]
    
    self.name = data["name"]
    self.inputs = data["inputs"]
    self.bullets = bullet_list
    self.bullet_countdown = data["bullet_countdown"]
    self.bullet_recharge = data["bullet_recharge"]
    self.bullet_speed = data["bullet_speed"]
    self.lives = data["lives"]
    self.dead = data["dead"]
    self.death_countdown = data["death_countdown"]
    self.max_bullets = data["max_bullets"]
    self.size = data["size"]
    self.last_updated = data["last_updated"]
    self.leaving = data["leaving"]
    self.score = data["score"]
    self.acceleration = data["acceleration"]
    self.turn_speed = data["turn_speed"]
    self.warp_countdown = data["warp_countdown"]
    self.invuln_time = data["invuln_time"]
    
    # For chaining.
    return self

  def to_dict(self):
    inherited_entries = super().to_dict()
    raw_bullet_list = [b.to_dict() for b in self.bullets]
    new_entries = {
      "name": self.name,
      "inputs": self.inputs,
      "bullets": raw_bullet_list,
      "bullet_countdown": self.bullet_countdown,
      "bullet_recharge": self.bullet_recharge,
      "bullet_speed": self.bullet_speed,
      "lives": self.lives,
      "dead": self.dead,
      "death_countdown": self.death_countdown,
      "max_bullets": self.max_bullets,
      "size": self.size,
      "last_updated": self.last_updated,
      "leaving": self.leaving,
      "score": self.score,
      "acceleration": self.acceleration,
      "turn_speed": self.turn_speed,
      "warp_countdown": self.warp_countdown,
      "invuln_time": self.invuln_time,
    }
    return {**new_entries, **inherited_entries}
  
  def fire(self):
    if self.bullet_countdown <= 0 and not self.dead:
      self.bullets.append(self.createBullet())
      if len(self.bullets) > self.max_bullets:
        self.bullets.pop(0)

      self.bullet_countdown = self.bullet_recharge

  def createBullet(self):
    start_point = self.nose().copy()
    direction = self.rotation
    unit_vector_for_direction = Vector.unit_vector(direction)
    # The bullet will always fire straight, but if the ship is going fast the bullets should still outrun it.
    # To do this, we project the ships speed along the unit vector in the direction the bullet will be travelling.
    # Then we add the base bullet speed. This should only have noticable effect when travelling quickly and firing forwards.
    # TODO: Fix this. Currently when travelling at a high speed vertically and firing horizontally, the bullets can
    # sometimes fly backwards. Something about the projection is off, possibly even the idea.
    bullet_speed = self.speed.dot_product(unit_vector_for_direction) + self.bullet_speed
    speed = Vector.dir_mag(direction, bullet_speed)
    return Bullet(start_point, speed)

  def update_bullets(self):
    i = 0
    length = len(self.bullets)
    while i < length:
      if self.bullets[i].dead:
        self.bullets.pop(i)
        length -= 1
      else:
        self.bullets[i].update()
        i += 1
    
  def accelerate(self, amount):
    self.speed.add_in_direction(amount, self.rotation)
    
  def rotate(self, rads):
    self.rotation += rads
    
      
  # TODO: Use delta time for all called methods as well.
  def update(self, dt):
    if not self.dead:
      if self.inputs.get("up"):
        self.accelerate(self.acceleration * dt)
      if self.inputs.get("down"):
        self.accelerate(-self.acceleration * dt)
      if self.inputs.get("left"):
        self.rotate(-self.turn_speed * dt)
      if self.inputs.get("right"):
        self.rotate(self.turn_speed * dt)
      if self.inputs.get("space"):
        self.fire()
      if self.inputs.get("F"):
        self.warp()
    
    if self.dead and self.death_countdown == 0:
      self.bullets = []
      self.bullet_countdown = self.bullet_recharge
      self.death_countdown = 3000
      self.speed = Vector(0, 0)
      # Set to 5000 so that after the death countdown finishes, we still have 2000 left over.
      self.invuln_time = 5000
      self.lives -= 1
    
    if self.death_countdown > 0:
      self.death_countdown -= min(self.death_countdown, dt)
      # This rotation is a bit of a hack to make a pretty death animation.
      self.rotate(self.turn_speed / 3 * dt)
      # Resurrect them when the countdown runs out, unless they're out of lives, in which case:
      # Tough luck.
      if self.death_countdown == 0 and self.lives > 0:
        self.dead = False
        self.rotation = -math.pi/2
        self.center = Point(utils.X_MAX / 2, utils.Y_MAX / 2)
      
    if self.warp_countdown > 0:
      self.warp_countdown -= min(self.warp_countdown, dt)
      
    if self.bullet_countdown > 0:
      self.bullet_countdown -= min(self.bullet_countdown, dt)
      
    if self.invuln_time > 0:
      self.invuln_time -= min(self.invuln_time, dt)
      
    super().move()
    self.update_bullets()
    
  def set_update_time(time):
    self.last_updated = time
    
  def set_inputs(self, keys):
    self.inputs = keys
    
  def warp(self):
    if self.warp_countdown <= 0:
      self.center = Point.random()
      self.warp_countdown += 1000
      self.invuln_time += 950
      
  def is_invulnerable(self):
    return self.invuln_time > 0
    
  def getBoundingBox(self):
    backLeft = Point.rotate(Point(self.center.x - self.size, self.center.y + self.size), self.center, self.rotation)
    backRight = Point.rotate(Point(self.center.x + self.size, self.center.y + self.size), self.center, self.rotation)
    frontLeft = Point.rotate(Point(self.center.x - self.size, self.center.y - self.size), self.center, self.rotation)
    frontRight = Point.rotate(Point(self.center.x + self.size, self.center.y - self.size), self.center, self.rotation)
    return (frontLeft, frontRight, backRight, backLeft)
    
  def nose(self):
    return Point.rotate(Point(self.center.x + 2*self.size, self.center.y), self.center, self.rotation)
  
  
  
  
  
  
  
  
  
  
  