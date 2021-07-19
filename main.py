import pygame
import sys
import os
import _thread
import random

import animation

screen = pygame.display.set_mode((700, 500))

ok = False

fpsclock = pygame.time.Clock()

def load():
    # 加载的动画
    load = animation.Load(screen, x=300, y=200)
    while not ok:
        screen.fill((255, 255, 255))
        load.update()
        load.draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()
        fpsclock.tick(30)

# 让程序边加载边刷新屏幕，使用多线程
_thread.start_new_thread(load, ())

pygame.init()

pygame.display.set_caption('火星探测')

# 加载图片
bg = pygame.image.load('images/bg.png')
ship1 = pygame.image.load('images/ship1.png')
ship2 = pygame.image.load('images/ship2.png')
ship3 = pygame.image.load('images/ship3.png')
alienimg = pygame.image.load('images/alien.png')
alienbossimg = pygame.image.load('images/alienboss.png')
goldimg = pygame.image.load('images/gold.png')
diamondimg = pygame.image.load('images/diamond.png')
bulletimg = pygame.image.load('images/bullet.png')
alienbulletimg = pygame.image.load('images/alienbullet.png')
blastimgs = []
for i in range(1, 12):
    blastimgs.append(pygame.image.load(f'images/b{i}.gif'))
skillimgs = []
for i in range(1, 3):
    skillimgs.append(pygame.image.load(f'images/skills/skill{i}.jpg'))

BULLET_LIMIT = 5
BULLET_MAX_LIMIT = 5
ALIEN_BULLET_LIMIT = 1
ORE_SPEED_LIMIT = 100
BOSS_PER_KILLED = 20
BOSS_INC_PER_KILLED = 10

font = pygame.font.Font('fonts/simsun.ttc', 20)
font2 = pygame.font.Font('fonts/Fixedsys500c.ttf', 30)
font2.set_bold(True)
font3 = pygame.font.Font('fonts/Fixedsys500c.ttf', 25)

class Bg:
    '''
    基于本游戏的背景类，没有参数，所有属性都是硬编码的。
    '''
    def __init__(self):
        self.img = bg
        # 把图片垂直翻转，形成无缝贴图
        self.img2 = pygame.transform.flip(self.img, False, True)
        self.height = 588
        self.y = self.height
        self.flip = True
    def draw(self):
        '''
        绘制连贯的背景图像。
        '''
        if self.flip:
            screen.blit(self.img, (0, self.y))
            screen.blit(self.img2, (0, self.y - self.height))
        else:
            screen.blit(self.img2, (0, self.y))
            screen.blit(self.img, (0, self.y - self.height))
    def update(self):
        self.y += 0.5
        if self.y >= self.height:
            self.y -= self.height
            self.flip = not self.flip

class FlyObject(pygame.sprite.Sprite):
    '''
    游戏元素共同的父类：飞行物体。
    '''
    def __init__(self, img):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        # 内置属性
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        # 基于图像生成遮罩
        self.mask = pygame.mask.from_surface(self.image)
    def draw(self):
        '''
        默认的绘图方法。
        '''
        screen.blit(self.image, self.rect)
    def update(self):
        # 父类的虚方法
        raise NotImplementedError('abstract')

class Ship(FlyObject):
    '''
    玩家的飞船类。
    '''
    def __init__(self):
        FlyObject.__init__(self, ship1)
        self.rect.center = (350, 300)
        self.right = 0
        self.down = 0
        self.speed = 6
        # 记录三种状态的列表
        self.imgs = [None, ship1, ship2, ship3]
        self.imgnum = 1
        self.golds = 0
        self.diamonds = 0
        self.life = 3
        self.killed = 0
        self.boss_killed = 0
        self.health = self.health_max = self.imgnum * 50
        self.lasthealth = pygame.time.get_ticks()
        # None表示没有对象，之后会动态添加
        self.lasering = None
        self.shield = None
    def die(self):
        global state
        self.life -= 1
        # 飞船爆炸的动画
        screen.fill((255, 255, 255))
        pygame.display.update()
        aliens.empty()
        golds.empty()
        diamonds.empty()
        alienbullets.empty()
        bullets.empty()
        pygame.time.delay(100)
        self.rect.center = (350, 300)
        if ship.life < 0:
            # 结束时
            state = 'over'
            pygame.mouse.set_visible(True)
            pygame.time.delay(100)
    def shoot(self):
        num = self.imgnum + min(self.boss_killed, BULLET_MAX_LIMIT)
        if len(bullets) < BULLET_LIMIT * num:
            # 生成子弹成排出现的效果
            for i in range(1, num + 1):
                bx = self.rect.centerx + (num - i) * 50 - (num - 1) * 25
                by = self.rect.top
                speedx = (num - i - int((num - 1) / 2)) * 2 - int(not num % 2)
                bullets.add(Bullet(bx, by, speedx))
    def set_img(self, img):
        orig = self.imgnum
        self.imgnum = img
        center = self.rect.center
        # 重新加载属性
        FlyObject.__init__(self, self.imgs[img])
        self.rect.center = center
        if self.imgnum != orig:
            self.health = self.health_max = self.imgnum * 50
            # 按照等级添加技能
            if self.imgnum == 2:
                skills.add(Skill(0))
            elif self.imgnum == 3:
                skills.add(Skill(1))
    def laser(self):
        if self.lasering == None and self.diamonds >= 1:
            self.diamonds -= 1
            self.lasering = Laser(*self.rect.center, self)
            lasers.add(self.lasering)
    def update(self):
        # 产生飞船速度渐渐变快或变慢的效果
        if self.right in (-1, -2, -3, -4, -5, -6, 1, 2, 3, 4, 5, 6):
            self.rect.x += self.right / 2
            self.right += int(self.right / abs(self.right))
        elif self.right in (-7, 7):
            self.rect.x += self.right * self.speed / abs(self.right)
        elif self.right in (-8, -9, -10, -11, -12, -13, 8, 9, 10, 11, 12, 13):
            self.rect.x += self.right * (8 - self.right) / abs(self.right) / 2
            self.right += int(self.right / abs(self.right))
        elif self.right in (-14, 14):
            self.right = 0
        if self.down in (-1, -2, -3, -4, -5, -6, 1, 2, 3, 4, 5, 6):
            self.rect.y += self.down / 2
            self.down += int(self.down / abs(self.down))
        elif self.down in (-7, 7):
            self.rect.y += self.down * self.speed / abs(self.down)
        elif self.down in (-8, -9, -10, -11, -12, -13, 8, 9, 10, 11, 12, 13):
            self.rect.y += self.down * (8 - self.down) / abs(self.down) / 2
            self.down += int(self.down / abs(self.down))
        elif self.down in (-14, 14):
            self.down = 0
        # 防止移出窗口外
        self.rect.centerx = max(min(self.rect.centerx, 700), 0)
        self.rect.centery = max(min(self.rect.centery, 500), 0)
        # 耐久度自然回升的间隔
        current = pygame.time.get_ticks()
        if current - self.lasthealth >= 2000:
            self.health = min(self.health + 1, self.health_max)
            self.lasthealth = current
        # 判断和子弹的碰撞
        b = pygame.sprite.spritecollide(self, alienbullets, True, pygame.sprite.collide_mask)
        if b:
            self.health -= 15
            blasts.add(Blast(*self.rect.center))
        # 耐久度小于等于0时判断飞船损毁
        if self.health <= 0:
            self.health = self.health_max
            self.die()

class Alien(FlyObject):
    '''
    外星人类。
    '''
    def __init__(self):
        FlyObject.__init__(self, alienimg)
        self.rect.centerx = random.randint(100, 600)
        self.rect.y = -self.height
        self.speedx = random.randint(-2, 2)
        self.speedy = 2 + ship.imgnum + ship.boss_killed
        self.life = ship.imgnum
        self.fired = 0
        self.lastfire = pygame.time.get_ticks()
        self.lastcenter = self.rect.center
    def hurt(self):
        '''
        外星人遭受到攻击。
        '''
        global alienboss
        self.life -= 1
        if self.life <= 0:
            ship.killed += 1
            # 如果击杀了一定数量的外星人就产生一个Boss
            if ship.killed % (BOSS_PER_KILLED * (ship.boss_killed + 1) + BOSS_INC_PER_KILLED * ship.boss_killed) == 0:
                alienboss = AlienBoss()
            aliens.remove(self)
        blasts.add(Blast(*self.rect.center))
    def shoot(self):
        '''
        外星人对玩家发动攻击。
        '''
        if len(alienbullets) < ALIEN_BULLET_LIMIT:
            alienbullets.add(AlienBullet(*self.rect.midbottom))
    def update(self):
        self.lastcenter = self.rect.center
        self.speedy = 2 + ship.imgnum + ship.boss_killed
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        # 出左右边界反弹
        if self.rect.left <= 0 or self.rect.right >= 700:
            self.speedx *= -1
        # 出下边界删除
        if self.rect.y >= 500 - self.height:
            ship.health -= 2
            blasts.add(Blast(*self.rect.center))
            aliens.remove(self)
        # 检测和玩家的碰撞
        b = pygame.sprite.collide_mask(self, ship)
        if b:
            # 损毁一艘飞船
            ship.die()
        else:
            # 和子弹碰撞就少一条命
            b = pygame.sprite.spritecollide(self, bullets, True, pygame.sprite.collide_mask)
            if b:
                self.hurt()
            else:
                # 随机发射子弹
                current = pygame.time.get_ticks()
                if (self.fired < ship.imgnum + ship.boss_killed and
                    current - self.lastfire >= 200 and
                    ship.rect.left <= self.rect.centerx <= ship.rect.right and
                    self.rect.y <= ship.rect.y):
                    self.fired += 1
                    if random.randint(1, 3) == 1:
                        self.shoot()
                    self.lastfire = current

class AlienBoss(FlyObject):
    '''
    罕见的Boss外星人。
    '''
    times = 1
    def __init__(self):
        FlyObject.__init__(self, alienbossimg)
        self.rect.y = -self.height
        self.y = self.rect.y
        self.rect.centerx = 350
        self.speedx = random.randint(-2, 2)
        self.life = self.life_max = 170 + self.times * 100
        AlienBoss.times += 1
        current = pygame.time.get_ticks()
        self.lastbullet = current
        self.lastlaser = current
        self.laser = None
    def hurt(self, sub=1):
        global alienboss
        self.life -= sub
        if self.life <= 0:
            ship.killed += 1
            alienboss = None
            if self.laser:
                lasers.remove(self.laser)
            ship.life += 1
            ship.health_max += 20
            ship.health = min(ship.health + 20, ship.health_max)
            ship.boss_killed += 1
            for i in range(10):
                # 击败Boss时的特效
                blasts.add(Blast(random.randint(48, 652), random.randint(48, 452)))
                break
        blasts.add(Blast(*self.rect.center))
    def draw(self):
        FlyObject.draw(self)
        pygame.draw.rect(screen, (255, 0, 0), (self.rect.centerx - 100, self.rect.top, self.life / self.life_max * 200, 10), 0)
        pygame.draw.rect(screen, (200, 0, 0), (self.rect.centerx - 100, self.rect.top, 200, 10), 1)
    def update(self):
        global lastalien
        self.y += 0.2
        self.rect.y = self.y
        self.speedx += random.randint(-1, 1)
        self.rect.x += self.speedx
        if self.rect.left <= 0 or self.rect.right >= 700:
            self.speedx *= -1
        if self.speedx >= 5:
            self.speedx = 3
        elif self.speedx <= -5:
            self.speedx = -3
        for bullet in bullets:
            if self.rect.colliderect(bullet.rect):
                self.hurt()
                bullets.remove(bullet)
        # 和玩家碰撞直接结束游戏
        b = pygame.sprite.collide_mask(self, ship)
        if b:
            ship.life = -1
            ship.die()
        current = pygame.time.get_ticks()
        # 对玩家发动攻击
        lastalien = current
        if current - self.lastbullet >= 800:
            alienbullets.add(AlienBullet(*self.rect.midbottom, random.randint(-2, 2)))
            self.lastbullet = current
        if current - self.lastlaser >= 7000:
            self.laser = Laser(*self.rect.center, self)
            lasers.add(self.laser)
            self.lastlaser = current
        if self.rect.y >= 500 - self.height:
            ship.life = -1
            ship.die()

class Ore(FlyObject):
    '''
    金矿和钻石的父类。
    由于金矿和钻石同属矿石，因此定义一个共同的父类。
    '''
    def __init__(self, img, callback):
        FlyObject.__init__(self, img)
        self.rect.centerx = random.randint(100, 600)
        self.rect.y = self.y = -self.height
        self.speed = 0
        self.speed_limit = ORE_SPEED_LIMIT
        self.callback = callback
    def update(self):
        self.y += 0.5
        self.rect.y = self.y
        if self.y >= 500:
            golds.remove(self)
        xx = ship.rect.centerx - self.rect.centerx
        yy = ship.rect.centery - self.rect.centery
        dis = animation.cal_distance(self.rect.center, ship.rect.center)
        if dis <= 150:
            self.speed += 1
        if self.speed:
            self.speed += 1
            if dis > 0 and self.speed < self.speed_limit:
                # 把矿石吸过来的算法
                x_inc = xx  / dis * self.speed_limit / (self.speed_limit - self.speed)
                y_inc = yy / dis * self.speed_limit / (self.speed_limit - self.speed)
                self.rect.x += x_inc
                self.rect.y += y_inc
            else:
                self.rect.center = ship.rect.center
            pygame.draw.line(screen, (100, 100, 100), self.rect.center, ship.rect.center, 2)
        if self.rect.center == ship.rect.center:
            self.callback()

class Gold(Ore):
    '''金矿。'''
    def __init__(self):
        def callback():
            ship.golds += 1
            ship.set_img(min(int(ship.golds / 2 + 0.5), len(ship.imgs) - 1))
            ship.health = min(ship.health_max, ship.health + 5 * ship.imgnum)
            golds.remove(self)
        Ore.__init__(self, goldimg, callback)

class Diamond(Ore):
    '''钻石。'''
    def __init__(self):
        def callback():
            ship.diamonds += 1
            ship.health = min(ship.health_max, ship.health + 10 * (ship.imgnum + ship.boss_killed))
            diamonds.remove(self)
        Ore.__init__(self, diamondimg, callback)

class Bullet(FlyObject):
    '''玩家的子弹。'''
    def __init__(self, x, y, speedx):
        FlyObject.__init__(self, bulletimg)
        self.rect.center = (x, y)
        self.speedx = speedx
    def update(self):
        self.rect.y -= 8
        self.rect.x += self.speedx
        if self.rect.y <= -self.height:
            bullets.remove(self)

class AlienBullet(FlyObject):
    '''外星人的子弹。'''
    def __init__(self, x, y, speedx=0):
        FlyObject.__init__(self, alienbulletimg)
        self.image = pygame.transform.flip(self.image, True, False)
        self.rect.center = (x, y)
        self.speedx = speedx
    def update(self):
        self.rect.y += 7
        self.rect.x += self.speedx
        if self.rect.y >= 500:
            alienbullets.remove(self)

class Laser(FlyObject):
    '''激光类。'''
    def __init__(self, x, y, owner):
        # 自动生成激光图像
        img = pygame.Surface((10, 600)).convert_alpha()
        img.fill((100, 230, 255, 180))
        pygame.draw.rect(img, (255, 255, 255), (3, 0, 4, 600), 0)
        FlyObject.__init__(self, img)
        if owner is alienboss:
            self.rect.midtop = alienboss.rect.center
        elif owner is ship:
            self.rect.centerx = ship.rect.centerx
        self.y = 0
        self.owner = owner
    def update(self):
        global laser
        self.y += 5
        if self.y >= 500:
            lasers.remove(self)
            if self.owner is alienboss:
                alienboss.laser = None
            elif self.owner is ship:
                ship.lasering = None
        # 跟随主人移动和碰撞检测
        if self.owner is alienboss:
            self.rect.midtop = alienboss.rect.center
            b = pygame.sprite.collide_mask(self, ship)
            if b:
                ship.health -= 5
                blasts.add(Blast(*ship.rect.center))
        elif self.owner is ship:
            self.rect.centerx = ship.rect.centerx
            b = pygame.sprite.spritecollide(self, aliens, False, pygame.sprite.collide_mask)
            for alien in b:
                alien.hurt()
            if alienboss:
                b = pygame.sprite.collide_mask(self, alienboss)
                if b:
                    alienboss.hurt()

class Shield(FlyObject):
    '''
    保护罩类。
    '''
    def __init__(self):
        # 自动生成保护罩图像
        shieldimg = pygame.Surface((120, 120)).convert_alpha()
        shieldimg.fill((0, 0, 0, 0))
        pygame.draw.circle(shieldimg, (10, 130, 255, 230), (60, 60), 60, 1)
        pygame.draw.circle(shieldimg, (100, 230, 255, 200), (60, 60), 59, 2)
        pygame.draw.circle(shieldimg, (120, 240, 255, 150), (60, 60), 57, 2)
        pygame.draw.circle(shieldimg, (150, 245, 255, 40), (60, 60), 55, 0)
        FlyObject.__init__(self, shieldimg)
        self.lastshipcenter = ship.rect.center
        self.rect.center = ship.rect.center
        self.health_max = self.health = 20
    def draw(self):
        FlyObject.draw(self)
        pygame.draw.rect(screen, (0, 255, 0), (self.rect.centerx - 30, self.rect.top + 7, self.health / self.health_max * 60, 5), 0)
        pygame.draw.rect(screen, (0, 200, 0), (self.rect.centerx - 30, self.rect.top + 7, 60, 5), 1)
    def update(self):
        shipcenter = ship.rect.center
        # 跟随玩家移动
        self.rect.center = ship.rect.center
        # 碰撞检测
        b = pygame.sprite.spritecollide(self, aliens, True, pygame.sprite.collide_mask)
        for alien in b:
            self.health -= 7
            blasts.add(Blast(*alien.rect.center))
        b = pygame.sprite.spritecollide(self, alienbullets, True, pygame.sprite.collide_mask)
        for bullet in b:
            self.health -= 3
            blasts.add(Blast(*bullet.rect.center))
        if self.health <= 0:
            ship.shield = None
        # 自动损毁
        self.health -= 0.02

class Blast(pygame.sprite.Sprite):
    '''
    爆炸类。这是一个动画。
    '''
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.frames = blastimgs
        self.frame = 0
        self.lastframe = len(self.frames) - 1
        self.last = pygame.time.get_ticks()
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.mask = pygame.mask.from_surface(self.image)
    def draw(self):
        screen.blit(self.image, self.rect)
    def update(self):
        # 增加帧
        self.frame += 1
        if self.frame >= self.lastframe:
            blasts.remove(self)
        self.image = self.frames[self.frame]

class Skill(FlyObject):
    '''
    技能类。
    '''
    def __init__(self, num):
        self.num = num
        self.image = skillimgs[self.num]
        FlyObject.__init__(self, self.image)
        self.rect.x = 7
        self.rect.y = 60 + self.num * 62
        self.wait_max = self.wait = 15 + self.num * 10
        self.lastwait = pygame.time.get_ticks()
    # 技能回调函数
    def skill0(self):
        ship.shield = Shield()
    def skill1(self):
        for alien in aliens:
            alien.life = 0
            alien.hurt()
        bullets.empty()
        if alienboss:
            alienboss.hurt(70)
    def invoke(self):
        if self.wait <= 0:
            self.wait = self.wait_max
            getattr(self, f'skill{self.num}')()
    def draw_shadow(self):
        if self.wait > 0:
            shadow = self.image.copy().convert_alpha()
            shadow.fill((0, 0, 0, 150))
            screen.blit(shadow, self.rect)
            fill_text(screen, font, str(self.wait), self.rect.center, shadow=True, center=True)
    def update(self):
        current = pygame.time.get_ticks()
        if self.wait > 0:
            if current - self.lastwait >= 1000:
                self.wait -= 1
                self.lastwait = current

class TextButton:
    '''
    文字按钮类。
    '''
    def __init__(self, text, x, y, callback):
        self.text = text
        self.x = x
        self.y = y
        self.img1 = font.render(text, True, (255, 255, 255))
        font2 = pygame.font.Font('fonts/simsun.ttc', 30)
        self.img2 = font2.render(text, True, (255, 255, 255))
        self.img3 = font2.render(text, True, (180, 180, 180))
        self.state = 'normal'
        self.callback = callback
        self.refresh()
    def refresh(self):
        if self.state == 'normal':
            self.img = self.img1
        elif self.state == 'enter':
            self.img = self.img2
        elif self.state == 'pressed':
            self.img = self.img3
        self.rect = self.img.get_rect()
        self.rect.center = (self.x, self.y)
    def draw(self):
        screen.blit(self.img, self.rect)
    def update(self):
        mx, my = pygame.mouse.get_pos()
        b1, b2, b3 = pygame.mouse.get_pressed()
        orig = self.state
        self.state = 'normal'
        if self.rect.collidepoint(mx, my):
            self.state = 'enter'
            if b1:
                self.state = 'pressed'
                if orig != self.state:
                    self.callback()
        self.refresh()

def update_and_draw(current):
    '''更新和绘图函数。'''
    background.update()
    background.draw()
    aliens.update()
    aliens.draw(screen)
    golds.update()
    golds.draw(screen)
    diamonds.update()
    diamonds.draw(screen)
    alienbullets.update()
    alienbullets.draw(screen)
    bullets.update()
    bullets.draw(screen)
    lasers.update()
    lasers.draw(screen)
    ship.update()
    ship.draw()
    if alienboss:
        alienboss.draw()
        alienboss.update()
    if ship.shield:
        ship.shield.draw()
        ship.shield.update()
    blasts.update()
    blasts.draw(screen)
    skills.update()
    skills.draw(screen)
    for skill in skills:
        skill.draw_shadow()
    draw_info(current)

def draw_info(current):
    x = 0
    for i in range(ship.life):
        screen.blit(pygame.transform.smoothscale(ship.image, (30, 30)), (x, 30))
        x += 30
    x = 0
    for i in range(ship.diamonds):
        screen.blit(pygame.transform.smoothscale(diamondimg, (20, 20)), (x, 480))
        x += 20
    fill_health()
    fill_text(screen, font, f'击杀数：{ship.killed}', (580, 3), shadow=True)
    fill_text(screen, font, '用时：%.1f' % (time / 1000), (580, 26), shadow=True)

def fill_text(surface, font, text, pos, color=(0, 0, 0), shadow=False, center=False):
    text1 = font.render(text, True, color)
    text_rect = text1.get_rect()
    if shadow:
        text2 = font.render(text, True, (255 - color[0], 255 - color[1], 255 - color[2]))
        for p in [(pos[0] - 1, pos[1] - 1),
                  (pos[0] + 1, pos[1] - 1),
                  (pos[0] - 1, pos[1] + 1),
                  (pos[0] + 1, pos[1] + 1)]:
            if center:
                text_rect.center = p
            else:
                text_rect.x = p[0]
                text_rect.y = p[1]
            screen.blit(text2, text_rect)
    if center:
        text_rect.center = pos
    else:
        text_rect.x = pos[0]
        text_rect.y = pos[1]
    screen.blit(text1, text_rect)

def fill_health():
    width_max = 200
    width = ship.health / ship.health_max * 200
    pygame.draw.rect(screen, (0, 255, 0), (5, 5, width, 20), 0)
    pygame.draw.rect(screen, (0, 200, 0), (5, 5, width_max, 20), 1)
    fill_text(screen, font, f'{ship.health}/{ship.health_max}', (105, 15), shadow=True, center=True)

def reset():
    global background, ship, aliens, alienboss, lastalien, golds, lastgold, diamonds, lastdiamond, bullets, alienbullets, lasers,\
           blasts, skills, last, time, state
    current = pygame.time.get_ticks()
    background = Bg()
    ship = Ship()
    aliens = pygame.sprite.Group()
    alienboss = None
    lastalien = current
    golds = pygame.sprite.Group()
    lastgold = current - 3000
    diamonds = pygame.sprite.Group()
    lastdiamond = current
    bullets = pygame.sprite.Group()
    alienbullets = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    blasts = pygame.sprite.Group()
    skills = pygame.sprite.Group()
    last = 0
    time = 0
    state = 'pause'

    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

def terminate():
    pygame.quit()
    os._exit(0)

text2 = font2.render('GAME OVER', True, (255, 255, 255))
text2 = pygame.transform.scale(text2, (500, 150))
text2_rect = text2.get_rect()
text2_rect.center = (350, 120)
textbtn1 = TextButton('重新开始', 350, 300, reset)
textbtn2 = TextButton('退出游戏', 350, 370, terminate)

reset()

ok = True
while True:
    current = pygame.time.get_ticks()
    if state == 'running':
        update_and_draw(current)
        time += current - last
        if current - lastalien >= max(1600 - (ship.imgnum + ship.boss_killed * 1.5) * 100, 500):
            aliens.add(Alien())
            lastalien = current
        if current - lastgold >= 5000:
            golds.add(Gold())
            lastgold = current
        if current - lastdiamond >= 16000 and ship.imgnum >= 3:
            diamonds.add(Diamond())
            lastdiamond = current
    elif state == 'pause':
        pygame.event.set_grab(False)
        background.draw()
        aliens.draw(screen)
        golds.draw(screen)
        diamonds.draw(screen)
        alienbullets.draw(screen)
        bullets.draw(screen)
        lasers.draw(screen)
        ship.draw()
        if alienboss:
            alienboss.draw()
        if ship.shield:
            ship.shield.draw()
        blasts.draw(screen)
        skills.draw(screen)
        for skill in skills:
            skill.draw_shadow()
        draw_info(current)
    elif state == 'over':
        screen.fill((0, 0, 0))
        screen.blit(text2, text2_rect)
        text3 = font3.render(f'TOTAL SCORE: {int((ship.killed + ship.boss_killed * 5) / (time / 1000) * 100)}', True, (255, 255, 255))
        text3_rect = text3.get_rect()
        text3_rect.center = (350, 220)
        screen.blit(text3, text3_rect)
        textbtn1.update()
        textbtn1.draw()
        textbtn2.update()
        textbtn2.draw()
    last = current
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                terminate()
        if state in ('running', 'pause'):
            if event.type == pygame.KEYDOWN:
                if state == 'pause':
                    state = 'running'
                    last = current
                else:
                    if event.key == pygame.K_RETURN:
                        state = 'pause'
                if event.key == pygame.K_LEFT:
                    ship.right = -1
                elif event.key == pygame.K_RIGHT:
                    ship.right = 1
                elif event.key == pygame.K_UP:
                    ship.down = -1
                elif event.key == pygame.K_DOWN:
                    ship.down = 1
                elif event.key == pygame.K_SPACE:
                    ship.shoot()
                elif event.key == pygame.K_z:
                    ship.laser()
                elif 49 <= event.key <= 50:
                    skls = sorted(skills.sprites(), key=lambda skl: skl.num)
                    try:
                        skls[event.key - 49].invoke()
                    except IndexError:
                        pass
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    ship.right = 0
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    ship.down = 0
    pygame.display.update()
    fpsclock.tick(50)
