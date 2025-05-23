import pygame
import pygame as pg
import math
import sys

pygame.init()
pygame.mixer.init()  # Initialize the mixer module

# Константы
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Солнечная система")
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (100, 100, 255)
RED = (255, 100, 100)
ORANGE = (255, 165, 0)
BROWN = (165, 120, 50)

# Загрузка и настройка фоновой музыки
try:
    pygame.mixer.music.load("space.mp3")
    pygame.mixer.music.play(-1)  # -1 означает бесконечное зацикливание
    pygame.mixer.music.set_volume(0.5)  # Установка громкости на 50%
    music_on = True
except:
    print("Не удалось загрузить фоновую музыку 'space.mp3'")
    music_on = False

# Класс Небесного Тела
class CelestialBody:
    def __init__(self, radius, color, orbit_radius, orbit_speed, tilt=0):
        self.radius = radius
        self.color = color
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.tilt = tilt
        self.angle = 0
        self.position = [0, 0, 0]
        self.rotation = 0
        self.rotation_speed = 0.01
        self.generate_sphere()
    
    def generate_sphere(self, resolution=10):
        self.vertices = []
        self.normals = []
        self.triangles = []
        for i in range(resolution + 1):
            phi = math.pi * i / resolution
            for j in range(resolution * 2):
                theta = 2 * math.pi * j / (resolution * 2)
                x = self.radius * math.sin(phi) * math.cos(theta)
                y = self.radius * math.sin(phi) * math.sin(theta)
                z = self.radius * math.cos(phi)
                self.vertices.append([x, y, z])
                normal = [x, y, z]
                mag = math.sqrt(x**2 + y**2 + z**2)
                normal = [x/mag, y/mag, z/mag] if mag > 0 else [0, 0, 0]
                self.normals.append(normal)
        for i in range(resolution):
            for j in range(resolution * 2):
                next_j = (j + 1) % (resolution * 2)
                p1 = i * (resolution * 2) + j
                p2 = i * (resolution * 2) + next_j
                p3 = (i + 1) * (resolution * 2) + j
                p4 = (i + 1) * (resolution * 2) + next_j
                if i != 0:
                    self.triangles.append([p1, p2, p3])
                if i != resolution - 1:
                    self.triangles.append([p3, p2, p4])
    
    def update(self, time):
        self.angle += self.orbit_speed * time
        self.rotation += self.rotation_speed * time
        x = self.orbit_radius * math.cos(self.angle)
        y = self.orbit_radius * math.sin(self.angle) * math.cos(self.tilt)
        z = self.orbit_radius * math.sin(self.angle) * math.sin(self.tilt)
        self.position = [x, y, z]

# Класс Источника Света
class Light:
    def __init__(self, position, color, intensity=1.0):
        self.position = position
        self.color = color
        self.intensity = intensity
        self.ambient = 0.2
        self.diffuse = 0.7
light = Light([0, 0, 0], YELLOW, 150)

# Вспомогательные функции
def rotate_point(point, angles):
    x, y, z = point
    ax, ay, az = angles
    y, z = (y * math.cos(ax) - z * math.sin(ax),
            y * math.sin(ax) + z * math.cos(ax))
    x, z = (x * math.cos(ay) + z * math.sin(ay),
            -x * math.sin(ay) + z * math.cos(ay))
    x, y = (x * math.cos(az) - y * math.sin(az),
            x * math.sin(az) + y * math.cos(az))
    return [x, y, z]

def project_point(point, camera_dist):
    x, y, z = point
    z = z + camera_dist
    if z <= 0:
        z = 0.001
    factor = 200 / z
    x = x * factor * scale
    y = y * factor * scale
    return (int(x + WIDTH // 2), int(y + HEIGHT // 2))

def calculate_lighting(vertex, normal, light_pos):
    light_dir = [
        light_pos[0] - vertex[0],
        light_pos[1] - vertex[1],
        light_pos[2] - vertex[2]
    ]
    light_mag = math.sqrt(light_dir[0]**2 + light_dir[1]**2 + light_dir[2]**2)
    if light_mag > 0:
        light_dir = [light_dir[0]/light_mag, light_dir[1]/light_mag, light_dir[2]/light_mag]
    dot_product = max(0, normal[0]*light_dir[0] + normal[1]*light_dir[1] + normal[2]*light_dir[2])
    intensity = light.ambient + light.diffuse * dot_product
    intensity = min(intensity, 1.0)
    return intensity

def draw_orbit(body, camera_dist, view_angles):
    points = []
    steps = 50
    for i in range(steps):
        angle = 2 * math.pi * i / steps
        x = body.orbit_radius * math.cos(angle)
        y = body.orbit_radius * math.sin(angle) * math.cos(body.tilt)
        z = body.orbit_radius * math.sin(angle) * math.sin(body.tilt)
        rotated = rotate_point([x, y, z], view_angles)
        projected = project_point(rotated, camera_dist)
        points.append(projected)
    for i in range(steps):
        if i % 2 == 0:
            pg.draw.line(window, (100, 100, 100), points[i], points[(i+1) % steps], 1)

def draw_body(body, camera_dist, view_angles):
    local_vertices = []
    local_normals = []
    for i in range(len(body.vertices)):
        vertex = body.vertices[i]
        normal = body.normals[i]
        rotated_vertex = rotate_point(vertex, [0, body.rotation, 0])
        rotated_normal = rotate_point(normal, [0, body.rotation, 0])
        moved_vertex = [
            rotated_vertex[0] + body.position[0],
            rotated_vertex[1] + body.position[1],
            rotated_vertex[2] + body.position[2]
        ]
        camera_rotated_vertex = rotate_point(moved_vertex, view_angles)
        camera_rotated_normal = rotate_point(rotated_normal, view_angles)
        local_vertices.append(camera_rotated_vertex)
        local_normals.append(camera_rotated_normal)
    triangle_list = []
    for triangle in body.triangles:
        depth = sum(local_vertices[i][2] for i in triangle) / 3
        triangle_list.append((depth, triangle))
    triangle_list.sort(key=lambda x: x[0], reverse=True)
    for _, triangle in triangle_list:
        points = [project_point(local_vertices[i], camera_dist) for i in triangle]
        avg_normal = [
            sum(local_normals[i][0] for i in triangle) / 3,
            sum(local_normals[i][1] for i in triangle) / 3,
            sum(local_normals[i][2] for i in triangle) / 3
        ]
        normal_mag = math.sqrt(avg_normal[0]**2 + avg_normal[1]**2 + avg_normal[2]**2)
        if normal_mag > 0:
            avg_normal = [avg_normal[0]/normal_mag, avg_normal[1]/normal_mag, avg_normal[2]/normal_mag]
        avg_pos = [
            sum(local_vertices[i][0] for i in triangle) / 3,
            sum(local_vertices[i][1] for i in triangle) / 3,
            sum(local_vertices[i][2] for i in triangle) / 3
        ]
        light_intensivity = calculate_lighting(avg_pos, avg_normal, [0, 0, 0])
        original_color = body.color
        color = (
            min(int(original_color[0] * light_intensivity), 255),
            min(int(original_color[1] * light_intensivity), 255),
            min(int(original_color[2] * light_intensivity), 255)
        )
        pygame.draw.polygon(window, color, points)

# Конфигурационное окно
def config_window(planets):
    global active_field
    font = pygame.font.Font(None, 32)
    radius_input_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 32)
    color_input_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 32)
    orbit_radius_input_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 32)
    speed_input_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 32)
    active_field = None
    planet_data = {'radius': '', 'color': '', 'orbit_radius': '', 'speed': ''}

    running_config = True  # Флаг, контролирующий выполнение окна конфигурации

    while running_config:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try:
                        # Обрабатываем данные и создаем новую планету
                        radius = float(planet_data['radius'])
                        color = tuple(map(int, planet_data['color'].split(',')))[:3]
                        orbit_radius = float(planet_data['orbit_radius'])
                        speed = float(planet_data['speed'])
                        new_planet = CelestialBody(radius, color, orbit_radius, speed)
                        planets.append(new_planet)
                        print("Новая планета создана:", new_planet.__dict__)
                    except Exception as e:
                        print(f"Ошибка при создании планеты: {e}")
                    finally:
                        running_config = False  # Выходим из окна конфигурации
                elif event.key == pygame.K_ESCAPE:
                    running_config = False  # Выходим из окна конфигурации
                elif event.key == pygame.K_TAB:
                    fields = ['radius', 'color', 'orbit_radius', 'speed']
                    current_idx = fields.index(active_field) if active_field else -1
                    next_idx = (current_idx + 1) % len(fields)
                    active_field = fields[next_idx]
                elif event.key == pygame.K_BACKSPACE:
                    if active_field:
                        planet_data[active_field] = planet_data[active_field][:-1]
                else:
                    if active_field:
                        # Проверяем, чтобы текст не был слишком длинным для поля ввода
                        test_text = planet_data[active_field] + event.unicode
                        text_width = font.size(test_text)[0]
                        if text_width < 190:  # Оставляем немного места в поле ввода
                            planet_data[active_field] += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if radius_input_rect.collidepoint(pos):
                    active_field = 'radius'
                elif color_input_rect.collidepoint(pos):
                    active_field = 'color'
                elif orbit_radius_input_rect.collidepoint(pos):
                    active_field = 'orbit_radius'
                elif speed_input_rect.collidepoint(pos):
                    active_field = 'speed'
                else:
                    active_field = None

        # Очистка экрана
        window.fill(BLACK)
        
        # Прорисовка заголовка
        title = font.render("Создание новой планеты", True, WHITE)
        window.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 150))
        
        # Прорисовка полей ввода
        field_names_map = {
            "Радиус": "radius",
            "Цвет (RGB)": "color",
            "Орбитальный радиус": "orbit_radius",
            "Скорость": "speed"
        }

        # Отображаем поля ввода
        for i, (rect, field_name) in enumerate(zip(
            [radius_input_rect, color_input_rect, orbit_radius_input_rect, speed_input_rect],
            ["Радиус:", "Цвет (RGB):", "Орбитальный радиус:", "Скорость:"]
        )):
            key = field_name.strip(":")
            if key in field_names_map:
                key = field_names_map[key]
            
            # Отображаем метку поля
            label = font.render(field_name, True, WHITE)
            window.blit(label, (rect.x - label.get_width() - 20, rect.y + 5))
            
            # Отображаем прямоугольник поля ввода
            pygame.draw.rect(window, WHITE, rect, 2)
            
            # Подсвечиваем активное поле
            if active_field == key:
                pygame.draw.rect(window, (100, 100, 255), rect.inflate(-4, -4), 1)
            
            # Отображаем текст в поле ввода
            value = planet_data[key]
            # Создаем поверхность для текста
            text_surface = font.render(value, True, WHITE)
            
            # Обрезаем текст, чтобы он помещался в поле
            rect_for_text = rect.inflate(-10, -10)  # Уменьшаем прямоугольник для текста
            if text_surface.get_width() > rect_for_text.width:
                # Если текст не помещается, отображаем только видимую часть
                window.blit(text_surface, (rect_for_text.x, rect_for_text.y), 
                           (text_surface.get_width() - rect_for_text.width, 0, rect_for_text.width, text_surface.get_height()))
            else:
                # Если текст помещается, отображаем полностью
                window.blit(text_surface, (rect_for_text.x, rect_for_text.y))
        
        # Инструкция
        help_text1 = font.render("Нажмите ENTER, чтобы сохранить новую планету.", True, WHITE)
        help_text2 = font.render("ESC для отмены. TAB для переключения полей.", True, WHITE)
        window.blit(help_text1, (WIDTH//2 - help_text1.get_width()//2, HEIGHT - 80))
        window.blit(help_text2, (WIDTH//2 - help_text2.get_width()//2, HEIGHT - 40))

        pygame.display.flip()

# Главный цикл программы
def main():
    global view_angles, camera_dist, scale, time_speed, paused, planets, music_on
    sun = CelestialBody(1.0, YELLOW, 0, 0)
    planets = []  # Здесь будем хранить созданные пользователем планеты
    light = Light([0, 0, 0], YELLOW, 150)
    view_angles = [0, 0, 0]
    camera_dist = 5
    scale = 1.0
    time_speed = 1.0
    paused = False
    resolution = 10
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pg.K_SPACE:
                    paused = not paused
                elif event.key == pg.K_PLUS or event.key == pg.K_EQUALS:
                    time_speed *= 1.5
                elif event.key == pg.K_MINUS:
                    time_speed /= 1.5
                    if time_speed < 0.1:  # Минимальная скорость времени
                        time_speed = 0.1
                elif event.key == pg.K_r:
                    view_angles = [0, 0, 0]
                elif event.key == pg.K_c:
                    config_window(planets)  # Открываем окно конфигурирования
                elif event.key == pg.K_m:  # Добавляем клавишу M для управления музыкой
                    music_on = not music_on
                    if music_on:
                        pygame.mixer.music.unpause() if pygame.mixer.music.get_busy() else pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.pause()
                elif event.key == pg.K_COMMA:  # Уменьшение громкости
                    new_volume = max(0.0, pygame.mixer.music.get_volume() - 0.1)
                    pygame.mixer.music.set_volume(new_volume)
                elif event.key == pg.K_PERIOD:  # Увеличение громкости
                    new_volume = min(1.0, pygame.mixer.music.get_volume() + 0.1)
                    pygame.mixer.music.set_volume(new_volume)
            elif event.type == pygame.MOUSEWHEEL:
                # Обработка колесика мыши
                if event.y > 0:
                    camera_dist -= 1  # Приближаем камеру при прокручивании вверх
                elif event.y < 0:
                    camera_dist += 1  # Отодвигаем камеру при прокручивании вниз
                scale = max(5, min(camera_dist, 20))  # Ограничиваем масштаб допустимыми границами
                    
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            view_angles[0] += 0.02
        if keys[pygame.K_DOWN]:
            view_angles[0] -= 0.02
        if keys[pygame.K_LEFT]:
            view_angles[1] -= 0.02
        if keys[pygame.K_RIGHT]:
            view_angles[1] += 0.02
        view_angles[0] = max(-1.5, min(view_angles[0], 1.5))

        if not paused:
            for planet in planets:
                planet.update(time_speed)

        window.fill(BLACK)
        for planet in planets:
            draw_orbit(planet, camera_dist, view_angles)
        sun_rotated = rotate_point([0, 0, 0], view_angles)
        sun_z = sun_rotated[2]
        all_bodies = planets + [sun]
        all_bodies.sort(key=lambda body: rotate_point(body.position, view_angles)[2], reverse=True)
        for body in all_bodies:
            draw_body(body, camera_dist, view_angles)

        # Информация о системе и инструкции
        font = pygame.font.SysFont(None, 24)
        instructions = [
            'Используйте стрелочки для поворота.',
            'Клавиша SPACE для паузы.',
            'Клавиша C для открытия окна конфигурации.',
            'Колёсико мыши для дистанции',
            '+ / - для изменения скорости времени',
            'M для включения/выключения музыки',
            ', / . для управления громкостью'
        ]
        
        for i, text in enumerate(instructions):
            text_surface = font.render(text, True, WHITE)
            window.blit(text_surface, (10, 10 + i * 25))
        
        # Отображение статуса симуляции
        status_font = pygame.font.SysFont(None, 30)
        
        # Статус паузы
        if paused:
            status_text = "ПАУЗА"
            status_color = RED
        else:
            status_text = "СИМУЛЯЦИЯ ЗАПУЩЕНА"
            status_color = (0, 255, 0)  # Зеленый
            
        status_surface = status_font.render(status_text, True, status_color)
        window.blit(status_surface, (WIDTH - status_surface.get_width() - 10, 10))
        
        # Скорость времени
        speed_text = f"Скорость времени: x{time_speed:.2f}"
        speed_surface = status_font.render(speed_text, True, WHITE)
        window.blit(speed_surface, (WIDTH - speed_surface.get_width() - 10, 40))

        # Отображение статуса звука
        music_text = f"Музыка: {'Вкл' if music_on else 'Выкл'}"
        music_volume = f"Громкость: {int(pygame.mixer.music.get_volume() * 100)}%"
        music_surface = status_font.render(music_text, True, WHITE)
        volume_surface = status_font.render(music_volume, True, WHITE)
        window.blit(music_surface, (WIDTH - music_surface.get_width() - 10, 70))
        window.blit(volume_surface, (WIDTH - volume_surface.get_width() - 10, 100))

        pygame.display.flip()
        clock.tick(60)

# Запускаем главное окно
main()