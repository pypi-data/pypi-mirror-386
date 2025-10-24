import site
site.addsitedir("C:\\Users\\hatte\\AppData\\Roaming\\Python\\Python312\\site-packages")

# Core Python modules
import os
import sys
import json
import sqlite3
import hashlib
import secrets
import platform
import threading
import time
import shutil
import subprocess
import gzip
import traceback
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Optional, Union, Dict, List, Any, Callable, Type, Tuple, Set

try:
    # External dependencies
    import pygame
    import winsound
    import simpleaudio as sa
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    
except ImportError as e:
    raise ImportError(f"Required module not found: {e.name}")

   #? #################### MEMORY API ##############################

from ursina import (
    Ursina, Entity, scene, Vec3, color, destroy,
    application, EditorCamera, Audio,
    Text, Button, Sprite, Panel, WindowPanel,
    PointLight, DirectionalLight, AmbientLight, SpotLight,
    BoxCollider, SphereCollider, MeshCollider, CapsuleCollider,
    curve, held_keys, time
)
import random

def lerp(start, end, t):
    """Linear interpolation between start and end values"""
    return start + (end - start) * t

class PhysicsSystem:
    """Simple physics system for basic collision detection"""
    def __init__(self):
        self.entities = []
        
    def add_entity(self, entity):
        if entity not in self.entities:
            self.entities.append(entity)
            
    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
            
    def update(self):
        # Basic collision detection between entities
        for i, entity1 in enumerate(self.entities):
            if not hasattr(entity1, 'collider'):
                continue
                
            for entity2 in self.entities[i+1:]:
                if not hasattr(entity2, 'collider'):
                    continue
                    
                # Simple AABB collision check
                if self._check_collision(entity1, entity2):
                    if hasattr(entity1, 'on_collision'):
                        entity1.on_collision(entity2)
                    if hasattr(entity2, 'on_collision'):
                        entity2.on_collision(entity1)
                        
    def _check_collision(self, entity1, entity2):
        """Simple AABB collision check"""
        bounds1 = self._get_bounds(entity1)
        bounds2 = self._get_bounds(entity2)
        
        return (bounds1[0] < bounds2[1] and bounds1[1] > bounds2[0] and
                bounds1[2] < bounds2[3] and bounds1[3] > bounds2[2])
                
    def _get_bounds(self, entity):
        """Get entity bounds as [min_x, max_x, min_y, max_y]"""
        pos = entity.position
        scale = entity.scale
        return [
            pos.x - scale.x/2,
            pos.x + scale.x/2,
            pos.y - scale.y/2,
            pos.y + scale.y/2
        ]
from typing import Optional, Dict, List, Union
import math


    #? #################### PYQT6 FRAMEWORK API ##############################

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class PyQt6Framework:
    def __init__(self, app=None):
        self.App = app
        self.QtApp = QApplication([])
        self.Windows = {}
        
    def CreateWindow(self, name: str, title: str = "Window", size: tuple = (800, 600)) -> QMainWindow:
        window = QMainWindow()
        window.setWindowTitle(title)
        window.resize(*size)
        self.Windows[name] = window
        return window
    
    def CreateWidget(self, type_name: str, *args, **kwargs) -> QWidget:
        widget_types = {
            "button": QPushButton,
            "label": QLabel,
            "input": QLineEdit,
            "checkbox": QCheckBox,
            "combobox": QComboBox,
            "slider": QSlider,
            "progressbar": QProgressBar,
            "table": QTableWidget,
            "tree": QTreeWidget,
            "text": QTextEdit,
            "group": QGroupBox,
            "tab": QTabWidget,
            "scroll": QScrollArea
        }
        
        if type_name not in widget_types:
            raise ValueError(f"Unknown widget type: {type_name}")
            
        return widget_types[type_name](*args, **kwargs)
    
    def CreateLayout(self, type_name: str) -> QLayout:
        layout_types = {
            "vertical": QVBoxLayout,
            "horizontal": QHBoxLayout,
            "grid": QGridLayout,
            "form": QFormLayout
        }
        
        if type_name not in layout_types:
            raise ValueError(f"Unknown layout type: {type_name}")
            
        return layout_types[type_name]()
    
    def CreateMenu(self, window_name: str) -> QMenuBar:
        if window_name not in self.Windows:
            raise ValueError(f"Window '{window_name}' not found")
            
        return self.Windows[window_name].menuBar()
    
    def CreateDialog(self, dialog_type: str, title: str, text: str, buttons=None) -> QDialog:
        dialog_types = {
            "info": QMessageBox.information,
            "warning": QMessageBox.warning,
            "error": QMessageBox.critical,
            "question": QMessageBox.question
        }
        
        if dialog_type not in dialog_types:
            raise ValueError(f"Unknown dialog type: {dialog_type}")
            
        return dialog_types[dialog_type](None, title, text, buttons or QMessageBox.Ok)
    
    def CreateStyleSheet(self, element: QWidget, style: dict):
        style_str = "".join([f"{k}: {v};" for k, v in style.items()])
        element.setStyleSheet(style_str)
    
    def StartEventLoop(self):
        self.QtApp.exec()
    
    def QuitApplication(self):
        self.QtApp.quit()



    #? #################### URSINA FRAMEWORK API ##############################


class UrsinaFramework:
    def __init__(self, app=None):
        self.App = app
        self.Engine = None
        self.Entities = {}
        self.Scenes = {}
        self.ActiveScene = None
        self.DefaultCamera = None
        self.Physics = False
        
    def CreateGame(self):
        """Initialisiert die Ursina Engine und erstellt das Spielfenster."""
        if not self.Engine:
            self.Engine = Ursina()
            self.Engine.update = self.GameUpdate
            self.Engine.input = self.GameInput
        return self.Engine
        
    def GameUpdate(self):
        """Update-Funktion für die Spiellogik"""
        pass
        
    def GameInput(self, key):
        """Input-Handler für Spieleingaben"""
        pass
        
    def CreateScene(self, name: str):
        new_scene = scene.Scene()
        self.Scenes[name] = new_scene
        if not self.ActiveScene:
            self.ActiveScene = new_scene
        return new_scene
    
    def SetActiveScene(self, name: str):
        if name in self.Scenes:
            self.ActiveScene = self.Scenes[name]
            return True
        return False
    
    def CreateEntity(self, name: str, model: str = 'cube', texture: str = None, 
                    position: tuple = (0,0,0), rotation: tuple = (0,0,0), 
                    scale: tuple = (1,1,1), entity_color = color.white):
        entity = Entity(
            model=model,
            texture=texture,
            position=Vec3(*position),
            rotation=Vec3(*rotation),
            scale=Vec3(*scale),
            color=entity_color
        )
        self.Entities[name] = entity
        return entity
    
    def CreateLight(self, type_name: str = 'point', position: tuple = (0,0,0), 
                   light_color = color.white, intensity: float = 1.0):
        light_types = {
            'point': PointLight,
            'directional': DirectionalLight,
            'ambient': AmbientLight,
            'spot': SpotLight
        }
        
        if type_name not in light_types:
            raise ValueError(f"Unknown light type: {type_name}")
            
        light = light_types[type_name](
            position=Vec3(*position),
            color=light_color,
            intensity=intensity
        )
        return light
    
    def SetupCamera(self, position: tuple = (0,0,-10), rotation: tuple = (0,0,0), 
                   fov: float = 60, orthographic: bool = False):
        self.DefaultCamera = EditorCamera()
        self.DefaultCamera.position = Vec3(*position)
        self.DefaultCamera.rotation = Vec3(*rotation)
        self.DefaultCamera.fov = fov
        self.DefaultCamera.orthographic = orthographic
        return self.DefaultCamera
    
    def EnablePhysics(self, gravity: tuple = (0,-9.81,0)):
        self.Physics = True
        application.physics_system = PhysicsSystem()
        application.physics_system.setGravity(Vec3(*gravity))
    
    def AddCollider(self, entity: Entity, type_name: str = 'box'):
        collider_types = {
            'box': BoxCollider,
            'sphere': SphereCollider,
            'mesh': MeshCollider,
            'capsule': CapsuleCollider
        }
        
        if type_name not in collider_types:
            raise ValueError(f"Unknown collider type: {type_name}")
            
        return collider_types[type_name](entity)
    
    def CreateAnimation(self, entity: Entity, attribute: str, value, 
                       duration: float = 1.0, animation_curve = curve.linear):
        # Manuelle Animation statt animate()
        start_value = getattr(entity, attribute)
        
        def update_animation():
            nonlocal start_value
            t = time.dt / duration
            current = lerp(start_value, value, t)
            setattr(entity, attribute, current)
            
            if t >= 1:
                entity.update = None
                
        entity.update = update_animation
        return entity
    
    def CreateSound(self, path: str, autoplay: bool = False, loop: bool = False):
        audio = Audio(path, autoplay=autoplay, loop=loop)
        return audio
    
    def CreateParticleSystem(self, position: tuple = (0,0,0), 
                           particle_count: int = 100,
                           particle_lifetime: float = 1.0,
                           emission_rate: float = 10,
                           particle_speed: float = 1.0,
                           particle_scale: float = 0.1,
                           particle_color_start = color.white,
                           particle_color_end = color.clear,
                           particle_direction: tuple = (0,1,0)):
        """
        Erstellt ein erweitertes Partikelsystem
        """
        particle_system = Entity(position=Vec3(*position))
        particle_system.particles = []
        particle_system.max_particles = particle_count
        particle_system.emission_timer = 0
        particle_system.emission_rate = emission_rate
        
        # Erstelle ein Partikel-Präfab für bessere Performance
        particle_prefab = Entity(
            model='sphere',
            scale=particle_scale,
            color=particle_color_start,
            enabled=False  # Deaktiviert, wird nur als Template verwendet
        )
        
        def emit_particle():
            if len(particle_system.particles) >= particle_system.max_particles:
                return
                
            # Erstelle neuen Partikel
            particle = Entity(
                model=particle_prefab.model,
                parent=particle_system,
                position=Vec3(
                    random.uniform(-0.1, 0.1),
                    random.uniform(-0.1, 0.1),
                    random.uniform(-0.1, 0.1)
                ),
                scale=particle_scale
            )
            
            # Setze Partikel-Eigenschaften
            particle.velocity = Vec3(
                random.uniform(-0.5, 0.5) + particle_direction[0],
                random.uniform(-0.5, 0.5) + particle_direction[1],
                random.uniform(-0.5, 0.5) + particle_direction[2]
            ) * particle_speed
            
            particle.lifetime = particle_lifetime
            particle.age = 0
            particle.color_start = particle_color_start
            particle.color_end = particle_color_end
            
            particle_system.particles.append(particle)
        
        def update_particles():
            # Aktualisiere Emission
            particle_system.emission_timer += time.dt
            if particle_system.emission_timer >= 1.0 / emission_rate:
                emit_particle()
                particle_system.emission_timer = 0
            
            # Aktualisiere existierende Partikel
            particles_to_remove = []
            for particle in particle_system.particles:
                particle.age += time.dt
                life_ratio = particle.age / particle.lifetime
                
                if life_ratio >= 1:
                    particles_to_remove.append(particle)
                    continue
                
                # Bewege Partikel
                particle.position += particle.velocity * time.dt
                
                # Aktualisiere Farbe mit Überblendung
                particle.color = color.rgba(
                    lerp(particle.color_start.r, particle.color_end.r, life_ratio),
                    lerp(particle.color_start.g, particle.color_end.g, life_ratio),
                    lerp(particle.color_start.b, particle.color_end.b, life_ratio),
                    lerp(particle.color_start.a, particle.color_end.a, life_ratio)
                )
                
                # Optional: Füge Rotation hinzu
                particle.rotation_y += random.uniform(-90, 90) * time.dt
            
            # Entferne tote Partikel
            for particle in particles_to_remove:
                if particle in particle_system.particles:
                    particle_system.particles.remove(particle)
                    destroy(particle)
        
        particle_system.update = update_particles
        return particle_system

    def lerp(self, start, end, t):
        return start + (end - start) * t
    
    def CreateUI(self, type_name: str, **kwargs):
        ui_types = {
            'text': Text,
            'button': Button,
            'panel': Panel,
            'image': Sprite,
            'window': WindowPanel
        }
        
        if type_name not in ui_types:
            raise ValueError(f"Unknown UI type: {type_name}")
            
        return ui_types[type_name](**kwargs)
    
    def StartGame(self):
        """Startet das Spiel, wenn die Engine initialisiert wurde"""
        if self.Engine:
            self.Engine.run()
        else:
            raise RuntimeError("Engine wurde noch nicht initialisiert. Rufen Sie zuerst CreateGame() auf.")
    
    def QuitGame(self):
        """Beendet das Spiel, wenn die Engine läuft"""
        if self.Engine:
            application.quit()
        else:
            raise RuntimeError("Engine wurde noch nicht initialisiert.")
        
        
    

class MemoryAPI:
    def __init__(self, app):
        self.App = app
        self.LocalMemory = LocalMemoryAPI(self)
        self.Sql = SQLAPI(self)
        self.SystemAppData = SystemAppDataAPI()
        self.Cloud = CloudMemoryAPI()
        self.BackendManager = MemoryBackendManager(app)
        
        self.MEMORY = []
        self.LOCALMEMORY = []
        self.USE_PERSISTANT = False
        self._lock = Lock()
        self.path = ""
        self.current_backend = "local"  # Default backend
        
    def set_backend(self, backend_name: str) -> bool:
        """Set the current memory backend"""
        if backend_name in self.BackendManager.list_backends():
            self.current_backend = backend_name
            return True
        return False
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get status of all memory backends"""
        return self.BackendManager.backend_status()
        
    def EnableMemoryConsistent(self, path: str, option: bool = True):
        self.ConsistentLoad(path)
            
    def Update(self):
        if self.USE_PERSISTANT and self.path:
            self.MEMORY = []
            self.MEMORY = self.ConsistentLoad(self.path)
        
    def Reload(self):
        if self.USE_PERSISTANT and self.path:
            self.ConsistentLoad(self.path)

    def KnowThis(self, name: str, meta: dict, backend: str = None):
        """Save Data in Memory with optional backend specification
        
        Data -> MEMORY -> __global__ 
        """
        # Update in-memory storage
        for mem in self.MEMORY:
            if mem['name'] == name:
                mem['meta'].update(meta)
                # Also store in backend if specified
                if backend or self.current_backend != "local":
                    self.BackendManager.store_data(backend or self.current_backend, name, meta)
                return
        
        self.MEMORY.append({'name': name, 'meta': meta})
        
        # Store in backend if specified
        if backend or self.current_backend != "local":
            self.BackendManager.store_data(backend or self.current_backend, name, meta)

    def Remember(self, name: str, keyword: str = None, _dict: str = None, dict_in_dict: bool = False, backend: str = None):
        """Get Saved Data from Memory with optional backend fallback
        
        __global__ -> Return
        """
        # First try in-memory storage
        for mem in self.MEMORY:
            if mem['name'] == name:
                if dict_in_dict and _dict:
                    return mem['meta'].get(_dict, {}).get(keyword)
                elif keyword:
                    return mem['meta'].get(keyword)
                return mem['meta']
        
        # If not found in memory, try backend
        if backend or self.current_backend != "local":
            data = self.BackendManager.retrieve_data(backend or self.current_backend, name)
            if data:
                if dict_in_dict and _dict:
                    return data.get(_dict, {}).get(keyword)
                elif keyword:
                    return data.get(keyword)
                return data
        
        return None

    def ForgetThis(self, name: str, keyword: str = None, _dict: str = None, dict_in_dict: bool = False, _all: bool = False, backend: str = None):
        """Delete Data from Memory and optionally from backend
        
         -> Memory [Operation]
        """
        success = False
        
        # Remove from in-memory storage
        for mem in self.MEMORY:
            if mem['name'] == name:
                if _all:
                    self.MEMORY.remove(mem)
                    success = True
                    break
                if dict_in_dict and _dict:
                    if _dict in mem['meta'] and keyword in mem['meta'][_dict]:
                        del mem['meta'][_dict][keyword]
                        success = True
                elif keyword and keyword in mem['meta']:
                    del mem['meta'][keyword]
                    success = True
                break
        
        # Also remove from backend if specified
        if success and (backend or self.current_backend != "local"):
            # For partial deletions, we need to update the backend with modified data
            if not _all:
                remaining_data = self.Remember(name)
                if remaining_data:
                    self.BackendManager.store_data(backend or self.current_backend, name, remaining_data)
            # For complete deletion, remove from backend
            else:
                # Implement backend deletion logic here
                pass
        
        return success

    def Learn(self, name: str, keyword: str, value, dict_in_dict: bool = False, _dict: str = None, backend: str = None):
        """Change Data in Memory and optionally in backend
        
        NewData -> MEMORY -> new __global__
        """
        success = False
        
        for mem in self.MEMORY:
            if mem['name'] == name:
                if dict_in_dict and _dict:
                    if _dict not in mem['meta']:
                        mem['meta'][_dict] = {}
                    mem['meta'][_dict][keyword] = value
                else:
                    mem['meta'][keyword] = value
                success = True
                
                # Update backend if specified
                if backend or self.current_backend != "local":
                    self.BackendManager.store_data(backend or self.current_backend, name, mem['meta'])
                
                break
        
        return success
    
    def MakeGlobal(self, name: str, use_value: bool = False, keyword: str = None, _dict: str = None, dict_in_dict: bool = False):
        """Promote a Memory entry into the top-level App.__global__.

        If use_value is True and keyword/_dict provided, extract that value from the stored meta.
        Otherwise the whole meta dict is promoted. If a global entry with the same name exists,
        the promoted item is appended to an 'entries' list on that global record.
        """
        meta = None
        for mem in self.MEMORY:
            if mem.get('name') == name:
                if use_value:
                    if dict_in_dict and _dict and keyword:
                        meta = mem.get('meta', {}).get(_dict, {}).get(keyword)
                    elif keyword:
                        meta = mem.get('meta', {}).get(keyword)
                    else:
                        meta = mem.get('meta')
                else:
                    meta = mem.get('meta')
                break
        if meta is None:
            return False
        app_globals = getattr(self.App, "__global__", None)
        if app_globals is None:
            try:
                self.App.__global__ = []
                app_globals = self.App.__global__
            except Exception:
                return False
        for global_mem in app_globals:
            if isinstance(global_mem, dict) and global_mem.get('name') == name:
                if 'entries' not in global_mem or not isinstance(global_mem['entries'], list):
                    global_mem['entries'] = []
                global_mem['entries'].append({'id': name, 'meta': meta})
                return True
        app_globals.append({'name': name, 'entries': [{'id': name, 'meta': meta}]})
        return True

    def DeleteGlobal(self, id):
        """Delete a top-level App.__global__ entry by name."""
        app_globals = getattr(self.App, "__global__", None)
        if app_globals is None:
            return False
        for global_mem in app_globals:
            if isinstance(global_mem, dict) and global_mem.get('name') == id:
                app_globals.remove(global_mem)
                return True
        return False
    
    def QuickEditGlobal(self, id, key, value, dict_in_dict: bool = False, _dict: str = None):
        """Quickly edit a top-level App.__global__ entry by name."""
        app_globals = getattr(self.App, "__global__", None)
        if app_globals is None:
            return False
        for global_mem in app_globals:
            if isinstance(global_mem, dict) and global_mem.get('name') == id:
                if dict_in_dict and _dict:
                    if _dict not in global_mem:
                        global_mem[_dict] = {}
                    global_mem[_dict][key] = value
                else:
                    global_mem[key] = value
                return True
        return False
    
    def ConsistentSave(self, name: str):
        self.LocalMemory.WriteLocal(self.path, self.Remember(name))
        
    def ConsistentLoad(self, path):
        self.path = path
        data = self.LocalMemory.ReadLocal(path)
        self.MEMORY = data

class SystemAppDataAPI:
    """
    Erweiterte System AppData Memory API - Vollständiges Datenmanagement-System
    
    Features:
    - OS-spezifische AppData-Verzeichnisse
    - Integrierte SQL-Datenbank
    - Cache-Management
    - Temporäre Dateien
    - Lokale Memory-Integration
    - Strukturierte Datenschemata
    - Funktionsbasierte Konfiguration
    """
    
    def __init__(self):
        # Basis-Konfiguration
        self.app_name = "ToolOS"
        self.version = "1.0.0"
        self.initialized = False
        
        # Pfade
        self.appdata_path = None
        self.db_path = None
        self.cache_path = None
        self.temp_path = None
        self.logs_path = None
        
        # Datenbankverbindung
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        
        # Konfiguration
        self.config = {
            "auto_cleanup": True,
            "compression": False,
            "encryption": False,
            "max_cache_size": 100,  # MB
            "max_temp_age": 24,     # Stunden
            "backup_enabled": True,
            "schema_validation": True
        }
        
        # Vordefinierte Schemas
        self.schemas = {
            "user_data": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "username": "TEXT NOT NULL",
                "email": "TEXT",
                "preferences": "TEXT",  # JSON
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            "app_settings": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "key": "TEXT UNIQUE NOT NULL",
                "value": "TEXT",
                "category": "TEXT DEFAULT 'general'",
                "type": "TEXT DEFAULT 'string'",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            "cache_entries": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "cache_key": "TEXT UNIQUE NOT NULL",
                "data": "BLOB",
                "expires_at": "TIMESTAMP",
                "size_bytes": "INTEGER",
                "access_count": "INTEGER DEFAULT 0",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            "temp_files": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "filename": "TEXT NOT NULL",
                "filepath": "TEXT NOT NULL",
                "size_bytes": "INTEGER",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "expires_at": "TIMESTAMP"
            },
            "memory_storage": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "namespace": "TEXT NOT NULL",
                "key": "TEXT NOT NULL",
                "data": "TEXT",  # JSON
                "type": "TEXT DEFAULT 'object'",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
        }
        
        # Memory-Cache für bessere Performance
        self.memory_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "deletes": 0
        }
    
    # ==================== KONFIGURATION ====================
    
    def setName(self, name: str) -> bool:
        """Setzt den Anwendungsnamen für AppData-Pfade"""
        if not name or not isinstance(name, str):
            return False
        self.app_name = name
        if self.initialized:
            self._update_paths()
        return True
    
    def setVersion(self, version: str) -> bool:
        """Setzt die Anwendungsversion"""
        if not version or not isinstance(version, str):
            return False
        self.version = version
        return True
    
    def setConfig(self, key: str, value: Any) -> bool:
        """Setzt eine Konfigurationsoption"""
        if key not in self.config:
            return False
        self.config[key] = value
        return True
    
    def getConfig(self, key: str = None) -> Union[Any, Dict[str, Any]]:
        """Holt eine oder alle Konfigurationsoptionen"""
        if key:
            return self.config.get(key)
        return self.config.copy()
    
    def enableCompression(self, enabled: bool = True) -> bool:
        """Aktiviert/deaktiviert Datenkompression"""
        self.config["compression"] = enabled
        return True
    
    def enableEncryption(self, enabled: bool = True) -> bool:
        """Aktiviert/deaktiviert Datenverschlüsselung"""
        self.config["encryption"] = enabled
        return True
    
    def setMaxCacheSize(self, size_mb: int) -> bool:
        """Setzt maximale Cache-Größe in MB"""
        if size_mb <= 0:
            return False
        self.config["max_cache_size"] = size_mb
        return True
    
    def setTempFileMaxAge(self, hours: int) -> bool:
        """Setzt maximales Alter für temporäre Dateien"""
        if hours <= 0:
            return False
        self.config["max_temp_age"] = hours
        return True
    
    # ==================== INITIALISIERUNG ====================
    
    def initialize(self) -> bool:
        """Initialisiert das AppData-System"""
        try:
            self._setup_paths()
            self._ensure_directories()
            self._initialize_database()
            self._setup_schemas()
            self._cleanup_expired_data()
            self.initialized = True
            return True
        except Exception as e:
            print(f"AppData initialization error: {e}")
            return False
    
    def _setup_paths(self):
        """Konfiguriert OS-spezifische Pfade"""
        self.appdata_path = self._get_appdata_path()
        self.db_path = os.path.join(self.appdata_path, "database.sqlite")
        self.cache_path = os.path.join(self.appdata_path, "cache")
        self.temp_path = os.path.join(self.appdata_path, "temp")
        self.logs_path = os.path.join(self.appdata_path, "logs")
    
    def _update_paths(self):
        """Aktualisiert Pfade nach Namensänderung"""
        was_initialized = self.initialized
        if was_initialized:
            self.close()
        self._setup_paths()
        if was_initialized:
            self.initialize()
    
    def _get_appdata_path(self) -> str:
        """Holt platform-spezifisches AppData-Verzeichnis"""
        if platform.system() == "Windows":
            base = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        elif platform.system() == "Darwin":  # macOS
            base = os.path.expanduser("~/Library/Application Support")
        else:  # Linux und andere
            base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        
        return os.path.join(base, self.app_name)
    
    def _ensure_directories(self):
        """Erstellt notwendige Verzeichnisse"""
        directories = [self.appdata_path, self.cache_path, self.temp_path, self.logs_path]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    # ==================== DATENBANK-MANAGEMENT ====================
    
    def _initialize_database(self) -> bool:
        """Initialisiert die SQLite-Datenbank"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.connection.cursor()
            
            # Optimierungen aktivieren
            self.cursor.execute("PRAGMA journal_mode=WAL")
            self.cursor.execute("PRAGMA synchronous=NORMAL")
            self.cursor.execute("PRAGMA cache_size=10000")
            self.cursor.execute("PRAGMA temp_store=MEMORY")
            
            return True
        except Exception as e:
            print(f"Database initialization error: {e}")
            return False
    
    def _setup_schemas(self):
        """Erstellt alle vordefinierten Tabellen"""
        for table_name, schema in self.schemas.items():
            self.createTable(table_name, schema)
    
    def createTable(self, table_name: str, schema: Dict[str, str]) -> bool:
        """Erstellt eine neue Tabelle mit gegebenem Schema"""
        try:
            columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
            self.cursor.execute(query)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Table creation error: {e}")
            return False
    
    def addSchema(self, name: str, schema: Dict[str, str]) -> bool:
        """Fügt ein neues Schema hinzu"""
        if not name or not schema:
            return False
        
        self.schemas[name] = schema
        if self.initialized:
            return self.createTable(name, schema)
        return True
    
    def getSchema(self, name: str) -> Optional[Dict[str, str]]:
        """Holt ein Schema"""
        return self.schemas.get(name)
    
    def listSchemas(self) -> List[str]:
        """Listet alle verfügbaren Schemas"""
        return list(self.schemas.keys())
    
    def validateSchema(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Validiert Daten gegen ein Schema"""
        if not self.config["schema_validation"]:
            return True
        
        schema = self.schemas.get(table_name)
        if not schema:
            return True  # Kein Schema = keine Validierung
        
        for column, dtype in schema.items():
            if column in data:
                # Basis-Validierung (erweiterte Validierung wäre hier möglich)
                if "INTEGER" in dtype and not isinstance(data[column], int):
                    if not str(data[column]).isdigit():
                        return False
                elif "TEXT" in dtype and not isinstance(data[column], str):
                    return False
        
        return True
    
    # ==================== SQL-OPERATIONEN ====================
    
    def sqlInsert(self, table: str, data: Dict[str, Any]) -> bool:
        """Fügt Daten in eine Tabelle ein"""
        if not self.initialized or not self.validateSchema(table, data):
            return False
        
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            self.cursor.execute(query, list(data.values()))
            self.connection.commit()
            self.cache_stats["writes"] += 1
            return True
        except Exception as e:
            print(f"SQL Insert error: {e}")
            return False
    
    def sqlSelect(self, table: str, where: Dict[str, Any] = None, columns: List[str] = None) -> List[Dict[str, Any]]:
        """Liest Daten aus einer Tabelle"""
        if not self.initialized:
            return []
        
        try:
            cols = ", ".join(columns) if columns else "*"
            query = f"SELECT {cols} FROM {table}"
            params = []
            
            if where:
                conditions = []
                for key, value in where.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                query += " WHERE " + " AND ".join(conditions)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            # Konvertiere zu Dictionary-Liste
            if columns:
                column_names = columns
            else:
                column_names = [description[0] for description in self.cursor.description]
            
            result = []
            for row in rows:
                result.append(dict(zip(column_names, row)))
            
            return result
        except Exception as e:
            print(f"SQL Select error: {e}")
            return []
    
    def sqlUpdate(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Aktualisiert Daten in einer Tabelle"""
        if not self.initialized or not where or not self.validateSchema(table, data):
            return False
        
        try:
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            where_clause = " AND ".join([f"{key} = ?" for key in where.keys()])
            
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            params = list(data.values()) + list(where.values())
            
            self.cursor.execute(query, params)
            self.connection.commit()
            self.cache_stats["writes"] += 1
            return True
        except Exception as e:
            print(f"SQL Update error: {e}")
            return False
    
    def sqlDelete(self, table: str, where: Dict[str, Any]) -> bool:
        """Löscht Daten aus einer Tabelle"""
        if not self.initialized or not where:
            return False
        
        try:
            where_clause = " AND ".join([f"{key} = ?" for key in where.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            self.cursor.execute(query, list(where.values()))
            self.connection.commit()
            self.cache_stats["deletes"] += 1
            return True
        except Exception as e:
            print(f"SQL Delete error: {e}")
            return False
    
    def sqlExecute(self, query: str, params: List[Any] = None) -> Union[List[Dict[str, Any]], bool]:
        """Führt beliebige SQL-Abfragen aus"""
        if not self.initialized:
            return False
        
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                rows = self.cursor.fetchall()
                column_names = [description[0] for description in self.cursor.description]
                return [dict(zip(column_names, row)) for row in rows]
            else:
                self.connection.commit()
                return True
        except Exception as e:
            print(f"SQL Execute error: {e}")
            return False
    
    # ==================== CACHE-MANAGEMENT ====================
    
    def setCacheData(self, key: str, data: Any, expires_in_seconds: int = None) -> bool:
        """Speichert Daten im Cache"""
        if not self.initialized:
            return False
        
        try:
            # Serialisiere Daten
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                serialized_data = data.encode('utf-8')
            else:
                serialized_data = str(data).encode('utf-8')
            
            # Kompression wenn aktiviert
            if self.config["compression"]:
                import gzip
                serialized_data = gzip.compress(serialized_data)
            
            # Ablaufzeit berechnen
            expires_at = None
            if expires_in_seconds:
                expires_at = time.time() + expires_in_seconds
            
            # In Memory-Cache
            self.memory_cache[key] = {
                "data": data,
                "expires_at": expires_at,
                "access_count": 0
            }
            
            # In Datenbank
            cache_entry = {
                "cache_key": key,
                "data": serialized_data,
                "expires_at": expires_at,
                "size_bytes": len(serialized_data)
            }
            
            # Lösche existierenden Eintrag
            self.sqlDelete("cache_entries", {"cache_key": key})
            
            # Füge neuen Eintrag hinzu
            success = self.sqlInsert("cache_entries", cache_entry)
            
            if success:
                self._cleanup_cache_if_needed()
            
            return success
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def getCacheData(self, key: str) -> Any:
        """Holt Daten aus dem Cache"""
        if not self.initialized:
            return None
        
        # Prüfe Memory-Cache zuerst
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry["expires_at"] is None or entry["expires_at"] > time.time():
                entry["access_count"] += 1
                self.cache_stats["hits"] += 1
                return entry["data"]
            else:
                # Abgelaufen
                del self.memory_cache[key]
        
        try:
            # Suche in Datenbank
            results = self.sqlSelect("cache_entries", {"cache_key": key})
            if not results:
                self.cache_stats["misses"] += 1
                return None
            
            entry = results[0]
            
            # Prüfe Ablaufzeit
            if entry["expires_at"] and entry["expires_at"] < time.time():
                self.deleteCacheData(key)
                self.cache_stats["misses"] += 1
                return None
            
            # Deserialisiere Daten
            data = entry["data"]
            
            # Dekompression wenn nötig
            if self.config["compression"]:
                import gzip
                data = gzip.decompress(data)
            
            # Versuche JSON zu parsen
            try:
                decoded_data = data.decode('utf-8')
                try:
                    parsed_data = json.loads(decoded_data)
                    result = parsed_data
                except json.JSONDecodeError:
                    result = decoded_data
            except UnicodeDecodeError:
                result = data
            
            # Aktualisiere Access-Count
            self.sqlUpdate("cache_entries", 
                          {"access_count": entry["access_count"] + 1}, 
                          {"cache_key": key})
            
            # In Memory-Cache speichern
            self.memory_cache[key] = {
                "data": result,
                "expires_at": entry["expires_at"],
                "access_count": entry["access_count"] + 1
            }
            
            self.cache_stats["hits"] += 1
            return result
            
        except Exception as e:
            print(f"Cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    def deleteCacheData(self, key: str) -> bool:
        """Löscht Cache-Eintrag"""
        if not self.initialized:
            return False
        
        # Aus Memory-Cache entfernen
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Aus Datenbank entfernen
        return self.sqlDelete("cache_entries", {"cache_key": key})
    
    def clearCache(self) -> bool:
        """Löscht alle Cache-Einträge"""
        if not self.initialized:
            return False
        
        self.memory_cache.clear()
        return self.sqlExecute("DELETE FROM cache_entries")
    
    def getCacheStats(self) -> Dict[str, Any]:
        """Holt Cache-Statistiken"""
        if not self.initialized:
            return {}
        
        try:
            # Hole DB-Statistiken
            count_result = self.sqlExecute("SELECT COUNT(*) as count FROM cache_entries")
            size_result = self.sqlExecute("SELECT SUM(size_bytes) as total_size FROM cache_entries")
            
            entries_count = count_result[0]["count"] if count_result else 0
            total_size = size_result[0]["total_size"] if size_result and size_result[0]["total_size"] else 0
            
            return {
                **self.cache_stats,
                "entries_count": entries_count,
                "total_size_bytes": total_size,
                "memory_cache_entries": len(self.memory_cache)
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {
                **self.cache_stats,
                "entries_count": 0,
                "total_size_bytes": 0,
                "memory_cache_entries": len(self.memory_cache)
            }
    
    def _cleanup_cache_if_needed(self):
        """Bereinigt Cache wenn Größenlimit erreicht"""
        if not self.config["max_cache_size"]:
            return
        
        try:
            # Hole aktuelle Größe
            result = self.sqlExecute("SELECT SUM(size_bytes) as total FROM cache_entries")
            if not result:
                return
            
            total_size_bytes = result[0]["total"] or 0
            max_size_bytes = self.config["max_cache_size"] * 1024 * 1024  # MB zu Bytes
            
            if total_size_bytes > max_size_bytes:
                # Lösche älteste Einträge (LRU)
                self.sqlExecute("""
                    DELETE FROM cache_entries 
                    WHERE id IN (
                        SELECT id FROM cache_entries 
                        ORDER BY access_count ASC, created_at ASC 
                        LIMIT (SELECT COUNT(*) / 4 FROM cache_entries)
                    )
                """)
        except Exception as e:
            print(f"Cache cleanup error: {e}")
    
    # ==================== TEMPORÄRE DATEIEN ====================
    
    def createTempFile(self, filename: str, content: Union[str, bytes], expires_in_hours: int = None) -> bool:
        """Erstellt eine temporäre Datei"""
        if not self.initialized:
            return False
        
        try:
            filepath = os.path.join(self.temp_path, filename)
            
            # Schreibe Datei
            mode = 'wb' if isinstance(content, bytes) else 'w'
            encoding = None if isinstance(content, bytes) else 'utf-8'
            
            with open(filepath, mode, encoding=encoding) as f:
                f.write(content)
            
            # Registriere in Datenbank
            size_bytes = os.path.getsize(filepath)
            expires_at = None
            
            if expires_in_hours:
                expires_at = time.time() + (expires_in_hours * 3600)
            else:
                expires_at = time.time() + (self.config["max_temp_age"] * 3600)
            
            temp_entry = {
                "filename": filename,
                "filepath": filepath,
                "size_bytes": size_bytes,
                "expires_at": expires_at
            }
            
            return self.sqlInsert("temp_files", temp_entry)
            
        except Exception as e:
            print(f"Temp file creation error: {e}")
            return False
    
    def readTempFile(self, filename: str) -> Optional[Union[str, bytes]]:
        """Liest eine temporäre Datei"""
        if not self.initialized:
            return None
        
        try:
            results = self.sqlSelect("temp_files", {"filename": filename})
            if not results:
                return None
            
            entry = results[0]
            filepath = entry["filepath"]
            
            # Prüfe Ablaufzeit
            if entry["expires_at"] and entry["expires_at"] < time.time():
                self.deleteTempFile(filename)
                return None
            
            # Datei existiert?
            if not os.path.exists(filepath):
                self.deleteTempFile(filename)
                return None
            
            # Versuche als Bytes zu lesen (Original-Format behalten)
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Versuche zu erkennen ob es Text ist
            try:
                # Wenn es als UTF-8 decodiert werden kann, gib String zurück
                decoded = content.decode('utf-8')
                # Prüfe ob es tatsächlich Text ist (keine null bytes etc.)
                if '\x00' not in decoded:
                    return decoded
                else:
                    return content  # Binary content
            except UnicodeDecodeError:
                # Definitiv binary content
                return content
                    
        except Exception as e:
            print(f"Temp file read error: {e}")
            return None
    
    def deleteTempFile(self, filename: str) -> bool:
        """Löscht eine temporäre Datei"""
        if not self.initialized:
            return False
        
        try:
            results = self.sqlSelect("temp_files", {"filename": filename})
            if results:
                filepath = results[0]["filepath"]
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            return self.sqlDelete("temp_files", {"filename": filename})
        except Exception as e:
            print(f"Temp file deletion error: {e}")
            return False
    
    def listTempFiles(self) -> List[Dict[str, Any]]:
        """Listet alle temporären Dateien"""
        if not self.initialized:
            return []
        
        return self.sqlSelect("temp_files")
    
    def cleanupExpiredTempFiles(self) -> int:
        """Bereinigt abgelaufene temporäre Dateien"""
        if not self.initialized:
            return 0
        
        try:
            # Finde abgelaufene Dateien
            current_time = time.time()
            expired_files = self.sqlSelect("temp_files", 
                                         columns=["filename", "filepath"])
            
            count = 0
            for file_info in expired_files:
                result = self.sqlSelect("temp_files", 
                                      {"filename": file_info["filename"]})
                if result and result[0]["expires_at"] < current_time:
                    if self.deleteTempFile(file_info["filename"]):
                        count += 1
            
            return count
        except Exception as e:
            print(f"Temp cleanup error: {e}")
            return 0
    
    # ==================== LOKALE MEMORY-INTEGRATION ====================
    
    def storeMemoryData(self, namespace: str, key: str, data: Any, data_type: str = "object") -> bool:
        """Speichert Daten im Memory-Storage"""
        if not self.initialized:
            return False
        
        try:
            # Serialisiere Daten
            if isinstance(data, (dict, list, tuple)):
                serialized_data = json.dumps(data, ensure_ascii=False)
                data_type = "object"
            elif isinstance(data, bool):
                serialized_data = json.dumps(data)
                data_type = "boolean"
            elif isinstance(data, (int, float)):
                serialized_data = json.dumps(data)
                data_type = "number"
            else:
                serialized_data = str(data)
                data_type = "string"
            
            # Prüfe ob Eintrag existiert
            existing = self.sqlSelect("memory_storage", 
                                    {"namespace": namespace, "key": key})
            
            if existing:
                # Update
                return self.sqlUpdate("memory_storage",
                                    {"data": serialized_data, "type": data_type, "updated_at": time.time()},
                                    {"namespace": namespace, "key": key})
            else:
                # Insert
                memory_entry = {
                    "namespace": namespace,
                    "key": key,
                    "data": serialized_data,
                    "type": data_type
                }
                return self.sqlInsert("memory_storage", memory_entry)
                
        except Exception as e:
            print(f"Memory store error: {e}")
            return False
    
    def getMemoryData(self, namespace: str, key: str = None) -> Any:
        """Holt Daten aus dem Memory-Storage"""
        if not self.initialized:
            return None
        
        try:
            if key:
                # Einzelnen Wert holen
                results = self.sqlSelect("memory_storage", 
                                       {"namespace": namespace, "key": key})
                if not results:
                    return None
                
                entry = results[0]
                data = entry["data"]
                data_type = entry["type"]
                
                # Deserialisiere basierend auf Typ
                if data_type in ["object", "boolean", "number"]:
                    return json.loads(data)
                else:
                    return data
            else:
                # Alle Werte des Namespace holen
                results = self.sqlSelect("memory_storage", {"namespace": namespace})
                memory_dict = {}
                
                for entry in results:
                    entry_key = entry["key"]
                    data = entry["data"]
                    data_type = entry["type"]
                    
                    if data_type in ["object", "boolean", "number"]:
                        memory_dict[entry_key] = json.loads(data)
                    else:
                        memory_dict[entry_key] = data
                
                return memory_dict
                
        except Exception as e:
            print(f"Memory get error: {e}")
            return None
    
    def deleteMemoryData(self, namespace: str, key: str = None) -> bool:
        """Löscht Daten aus dem Memory-Storage"""
        if not self.initialized:
            return False
        
        if key:
            return self.sqlDelete("memory_storage", {"namespace": namespace, "key": key})
        else:
            return self.sqlDelete("memory_storage", {"namespace": namespace})
    
    def listMemoryNamespaces(self) -> List[str]:
        """Listet alle Memory-Namespaces"""
        if not self.initialized:
            return []
        
        try:
            results = self.sqlExecute("SELECT DISTINCT namespace FROM memory_storage")
            return [row["namespace"] for row in results] if results else []
        except Exception as e:
            print(f"Memory namespaces error: {e}")
            return []
    
    def listMemoryKeys(self, namespace: str) -> List[str]:
        """Listet alle Keys in einem Namespace"""
        if not self.initialized:
            return []
        
        try:
            results = self.sqlSelect("memory_storage", {"namespace": namespace}, ["key"])
            return [row["key"] for row in results]
        except Exception as e:
            print(f"Memory keys error: {e}")
            return []
    
    # ==================== EINSTELLUNGEN & KONFIGURATION ====================
    
    def storeSetting(self, key: str, value: Any, category: str = "general") -> bool:
        """Speichert eine Anwendungseinstellung"""
        if not self.initialized:
            return False
        
        try:
            # Serialisiere Wert
            if isinstance(value, (dict, list, bool)):
                serialized_value = json.dumps(value)
                value_type = "json"
            elif isinstance(value, (int, float)):
                serialized_value = str(value)
                value_type = "number"
            else:
                serialized_value = str(value)
                value_type = "string"
            
            # Prüfe ob Setting existiert
            existing = self.sqlSelect("app_settings", {"key": key})
            
            if existing:
                return self.sqlUpdate("app_settings",
                                    {"value": serialized_value, "category": category, "type": value_type},
                                    {"key": key})
            else:
                setting_entry = {
                    "key": key,
                    "value": serialized_value,
                    "category": category,
                    "type": value_type
                }
                return self.sqlInsert("app_settings", setting_entry)
                
        except Exception as e:
            print(f"Setting store error: {e}")
            return False
    
    def getSetting(self, key: str, default: Any = None) -> Any:
        """Holt eine Anwendungseinstellung"""
        if not self.initialized:
            return default
        
        try:
            results = self.sqlSelect("app_settings", {"key": key})
            if not results:
                return default
            
            entry = results[0]
            value = entry["value"]
            value_type = entry["type"]
            
            # Deserialisiere basierend auf Typ
            if value_type == "json":
                return json.loads(value)
            elif value_type == "number":
                return float(value) if "." in value else int(value)
            else:
                return value
                
        except Exception as e:
            print(f"Setting get error: {e}")
            return default
    
    def deleteSetting(self, key: str) -> bool:
        """Löscht eine Einstellung"""
        if not self.initialized:
            return False
        
        return self.sqlDelete("app_settings", {"key": key})
    
    def listSettings(self, category: str = None) -> Dict[str, Any]:
        """Listet alle Einstellungen"""
        if not self.initialized:
            return {}
        
        try:
            where_clause = {"category": category} if category else None
            results = self.sqlSelect("app_settings", where_clause)
            
            settings = {}
            for entry in results:
                key = entry["key"]
                value = entry["value"]
                value_type = entry["type"]
                
                if value_type == "json":
                    settings[key] = json.loads(value)
                elif value_type == "number":
                    settings[key] = float(value) if "." in value else int(value)
                else:
                    settings[key] = value
            
            return settings
        except Exception as e:
            print(f"Settings list error: {e}")
            return {}
    
    # ==================== WARTUNG & UTILITIES ====================
    
    def _cleanup_expired_data(self):
        """Bereinigt alle abgelaufenen Daten"""
        if not self.config["auto_cleanup"]:
            return
        
        current_time = time.time()
        
        # Cache-Einträge
        self.sqlExecute("DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at < ?", [current_time])
        
        # Temporäre Dateien
        self.cleanupExpiredTempFiles()
    
    def backup(self, backup_path: str = None) -> str:
        """Erstellt ein Backup der Datenbank"""
        if not self.initialized:
            return None
        
        try:
            if not backup_path:
                timestamp = int(time.time())
                backup_filename = f"appdata_backup_{timestamp}.sqlite"
                backup_path = os.path.join(self.appdata_path, backup_filename)
            
            # SQLite Backup
            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            return backup_path
        except Exception as e:
            print(f"Backup error: {e}")
            return None
    
    def restore(self, backup_path: str) -> bool:
        """Stellt Daten aus einem Backup wieder her"""
        if not os.path.exists(backup_path):
            return False
        
        try:
            # Schließe aktuelle Verbindung
            if self.connection:
                self.connection.close()
            
            # Ersetze Datenbank mit Backup
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            # Verbindung wiederherstellen
            return self._initialize_database()
        except Exception as e:
            print(f"Restore error: {e}")
            return False
    
    def getStorageInfo(self) -> Dict[str, Any]:
        """Holt umfassende Storage-Informationen"""
        if not self.initialized:
            return {}
        
        try:
            info = {
                "appdata_path": self.appdata_path,
                "database_size_bytes": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                "cache_stats": self.getCacheStats(),
                "temp_files_count": len(self.listTempFiles()),
                "memory_namespaces": self.listMemoryNamespaces(),
                "settings_count": len(self.listSettings()),
                "total_tables": len(self.schemas),
                "config": self.config.copy()
            }
            
            # Verzeichnisgrößen
            cache_size = sum(os.path.getsize(os.path.join(self.cache_path, f)) 
                           for f in os.listdir(self.cache_path) 
                           if os.path.isfile(os.path.join(self.cache_path, f))) if os.path.exists(self.cache_path) else 0
            
            temp_size = sum(os.path.getsize(os.path.join(self.temp_path, f)) 
                          for f in os.listdir(self.temp_path) 
                          if os.path.isfile(os.path.join(self.temp_path, f))) if os.path.exists(self.temp_path) else 0
            
            info["cache_directory_size_bytes"] = cache_size
            info["temp_directory_size_bytes"] = temp_size
            info["total_size_bytes"] = info["database_size_bytes"] + cache_size + temp_size
            
            return info
        except Exception as e:
            print(f"Storage info error: {e}")
            return {}
    
    def optimize(self) -> bool:
        """Optimiert die Datenbank"""
        if not self.initialized:
            return False
        
        try:
            self.cursor.execute("VACUUM")
            self.cursor.execute("REINDEX")
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Optimize error: {e}")
            return False
    
    def close(self) -> bool:
        """Schließt alle Verbindungen"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.cursor = None
            
            self.memory_cache.clear()
            self.initialized = False
            return True
        except Exception as e:
            print(f"Close error: {e}")
            return False
    
    # ==================== KOMFORTFUNKTIONEN ====================
    
    def isInitialized(self) -> bool:
        """Prüft ob das System initialisiert ist"""
        return self.initialized
    
    def getPath(self, path_type: str = "appdata") -> str:
        """Holt verschiedene Pfade"""
        paths = {
            "appdata": self.appdata_path,
            "database": self.db_path,
            "cache": self.cache_path,
            "temp": self.temp_path,
            "logs": self.logs_path
        }
        return paths.get(path_type, self.appdata_path)
    
    def reset(self) -> bool:
        """Setzt das komplette System zurück"""
        if not self.initialized:
            return False
        
        try:
            # Schließe Verbindungen
            self.close()
            
            # Lösche alle Dateien
            import shutil
            if os.path.exists(self.appdata_path):
                shutil.rmtree(self.appdata_path)
            
            # Neu initialisieren
            return self.initialize()
        except Exception as e:
            print(f"Reset error: {e}")
            return False

class CloudMemoryAPI:
    """Cloud Memory API - Interface for cloud storage backends"""
    
    def __init__(self, provider: str = "local", **config):
        self.provider = provider
        self.config = config
        self.backend = self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize the selected cloud backend"""
        if self.provider == "local":
            return LocalCloudBackend()
        # Future: Add real cloud providers
        # elif self.provider == "azure":
        #     return AzureBackend(**self.config)
        # elif self.provider == "aws":
        #     return AWSBackend(**self.config)
        else:
            raise ValueError(f"Unsupported cloud provider: {self.provider}")
    
    def upload(self, key: str, data: Dict[str, Any]) -> bool:
        """Upload data to cloud storage"""
        return self.backend.upload(key, data)
    
    def download(self, key: str) -> Optional[Dict[str, Any]]:
        """Download data from cloud storage"""
        return self.backend.download(key)
    
    def delete(self, key: str) -> bool:
        """Delete data from cloud storage"""
        return self.backend.delete(key)
    
    def list_keys(self) -> List[str]:
        """List all available keys"""
        return self.backend.list_keys()
    
    def sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        return self.backend.sync_status()

class LocalCloudBackend:
    """Local file system backend for cloud API (fallback/testing)"""
    
    def __init__(self):
        self.storage_path = os.path.join(os.getcwd(), "cloud_storage")
        os.makedirs(self.storage_path, exist_ok=True)
    
    def upload(self, key: str, data: Dict[str, Any]) -> bool:
        try:
            filepath = os.path.join(self.storage_path, f"{key}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def download(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            filepath = os.path.join(self.storage_path, f"{key}.json")
            if not os.path.exists(filepath):
                return None
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def delete(self, key: str) -> bool:
        try:
            filepath = os.path.join(self.storage_path, f"{key}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except Exception:
            return False
    
    def list_keys(self) -> List[str]:
        try:
            files = os.listdir(self.storage_path)
            return [f.replace('.json', '') for f in files if f.endswith('.json')]
        except Exception:
            return []
    
    def sync_status(self) -> Dict[str, Any]:
        return {
            "provider": "local",
            "status": "connected",
            "last_sync": time.time(),
            "file_count": len(self.list_keys())
        }

class MemoryBackendManager:
    """Unified manager for all memory backends"""
    
    def __init__(self, app):
        self.app = app
        self.backends = {}
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize all available memory backends"""
        # Core backends
        self.backends['local'] = LocalMemoryAPI(self.app)
        self.backends['sql'] = SQLAPI(self.app)
        self.backends['appdata'] = SystemAppDataAPI()
        self.backends['cloud'] = CloudMemoryAPI()
        
        # Future backends can be added here
        # self.backends['redis'] = RedisAPI() 
        # self.backends['mongodb'] = MongoAPI()
    
    def get_backend(self, backend_name: str):
        """Get a specific memory backend"""
        return self.backends.get(backend_name)
    
    def store_data(self, backend_name: str, key: str, data: Dict[str, Any]) -> bool:
        """Store data using specified backend"""
        backend = self.get_backend(backend_name)
        if not backend:
            return False
        
        if backend_name == 'local':
            return backend.WriteLocal(f"{key}.json", data)
        elif backend_name == 'appdata':
            return backend.write_data(f"{key}.json", data)
        elif backend_name == 'cloud':
            return backend.upload(key, data)
        elif backend_name == 'sql':
            # Implement SQL storage logic
            return self._store_sql(backend, key, data)
        
        return False
    
    def retrieve_data(self, backend_name: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data using specified backend"""
        backend = self.get_backend(backend_name)
        if not backend:
            return None
        
        if backend_name == 'local':
            return backend.ReadLocal(f"{key}.json")
        elif backend_name == 'appdata':
            return backend.read_data(f"{key}.json")
        elif backend_name == 'cloud':
            return backend.download(key)
        elif backend_name == 'sql':
            return self._retrieve_sql(backend, key)
        
        return None
    
    def _store_sql(self, backend, key: str, data: Dict[str, Any]) -> bool:
        """Store data in SQL backend"""
        try:
            if not backend.Connect():
                return False
            
            # Create table if not exists
            backend.TableCreate("memory_storage", {
                "key": "TEXT PRIMARY KEY",
                "data": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            })
            
            # Insert or update data
            json_data = json.dumps(data)
            success = backend.Insert("memory_storage", {
                "key": key,
                "data": json_data
            })
            
            backend.Close()
            return success
        except Exception:
            return False
    
    def _retrieve_sql(self, backend, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from SQL backend"""
        try:
            if not backend.Connect():
                return None
            
            result = backend.Read("memory_storage", ["data"], f"key = '{key}'")
            backend.Close()
            
            if result and len(result) > 0:
                return json.loads(result[0][0])
            return None
        except Exception:
            return None
    
    def list_backends(self) -> List[str]:
        """List all available backends"""
        return list(self.backends.keys())
    
    def backend_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all backends"""
        status = {}
        for name, backend in self.backends.items():
            try:
                if name == 'cloud':
                    status[name] = backend.sync_status()
                elif name == 'sql':
                    status[name] = {
                        "connected": backend.DbExists(),
                        "type": "sqlite3"
                    }
                else:
                    status[name] = {"status": "available"}
            except Exception:
                status[name] = {"status": "error"}
        
        return status

class LocalMemoryAPI:
    """
    MEMORY -> __local__ -> MEMORY
    """

    def __init__(self, app):
        import json
        self.js = json
        self.App = app
        self.Inserts = []

    def ReadLocal(self, path: str):
        """Format expected: a list of {'name': 'example', 'data': {...}}"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = self.js.load(f)
                self.App.LOCALMEMORY = data
                return data
        except Exception:
            return None

    def WriteLocal(self, path: str, data: dict):
        try:
            with open(path, "w", encoding="utf-8") as f:
                self.js.dump(data, f, indent=4)
                self.App.LOCALMEMORY = data
                return True
        except Exception:
            return False

    def InsertLocal(self, name: str = None, meta: dict = None):
        """
        Insert a single local entry or flush pending Inserts into the __global__.

        - If name and meta provided: append to MemoryAPI.LOCALMEMORY and to internal Inserts.
        - If called with neither name nor meta: flush internal Inserts into __global__ via KnowThis.
        """
        if name is not None and meta is not None:
            entry = {"name": name, "data": meta}
            self.Inserts.append(entry)
            try:
                if self.App.LOCALMEMORY is None:
                    self.App.LOCALMEMORY = []
            except Exception:
                self.App.LOCALMEMORY = []
            self.App.LOCALMEMORY.append(entry)
            return True

        if name is None and meta is None:
            try:
                for item in self.Inserts:
                    try:
                        self.App.KnowThis(item["name"], item.get("data", {}))
                    except Exception:
                        top_api = getattr(self.App, "App", None)
                        if top_api and getattr(top_api, "Memory", None):
                            top_api.Memory.KnowThis(item["name"], item.get("data", {}))

                self.Inserts.clear()
                return True
            except Exception:
                return False
        return False

    def Split(self):
        """
        Generator that yields entries from MemoryAPI.LOCALMEMORY as {'name': ..., 'data': ...}
        Also accumulates them into self.Inserts and returns the list at the end.
        """
        inserts = []
        try:
            for i in (self.App.LOCALMEMORY or []):
                new = {"name": i.get("name"), "data": i.get("data", {})}
                self.Inserts.append(new)
                inserts.append(new)
                yield new
        finally:
            return inserts
        
class SQLAPI:
    """
    SQLAPI - Eine moderne, kontrollierte SQL-API mit Framework-Feeling.
    Designed für Toolos 3.0+ Framework Integration.

    > Features:
      - Datenbankprüfung & Erstellung
      - Tabellenmanagement (Existenz, Create, Drop)
      - CRUD + Search Funktionen
      - Automatisches Path-Handling über Settings
      - Einfache Syntax: self.Sql.TableExists("users")
    """

    def __init__(self, app):
        import sqlite3, os
        self.sqlite3 = sqlite3
        self.App = app
        # Settings-Attribut korrekt auflösen
        if hasattr(app, "Settings"):
            self.db_path = getattr(app.Settings, "SETTINGSPATH", "settings.db")
        elif hasattr(app, "App") and hasattr(app.App, "Settings"):
            self.db_path = getattr(app.App.Settings, "SETTINGSPATH", "settings.db")
        else:
            self.db_path = "settings.db"
        self.connection = None
        self.cursor = None
    # ? #############################################
    # ? BASIC CONNECTION
    # ? #############################################

    def Connect(self, path: str = None):
        """Öffnet eine Connection (automatisch wenn nicht offen)."""
        if not path:
            path = self.db_path
        try:
            self.connection = self.sqlite3.connect(path, check_same_thread=False)
            self.cursor = self.connection.cursor()
            self.db_path = path
            return True
        except Exception as e:
            print(f"[SQL] Connection error: {e}")
            return False

    def Close(self):
        """Schließt aktuelle Connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            return True
        return False

    # ? #############################################
    # ? DATABASE CONTROL
    # ? #############################################

    def DbExists(self, path: str = None) -> bool:
        """Check ob DB-Datei existiert"""
        import os
        return os.path.exists(path or self.db_path)

    def DbSearch(self, directory: str = ".") -> list:
        """Sucht nach SQLite-Dateien im Ordner"""
        import os
        return [f for f in os.listdir(directory) if f.endswith(".db") or f.endswith(".sqlite")]

    def DeleteDb(self, path: str = None) -> bool:
        """Löscht eine Datenbank"""
        import os
        path = path or self.db_path
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    # ? #############################################
    # ? TABLE MANAGEMENT
    # ? #############################################

    def TableExists(self, name: str) -> bool:
        """Prüft, ob Tabelle existiert"""
        try:
            self.Connect()
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,)
            )
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"[SQL] TableExists Error: {e}")
            return False

    def TableCreate(self, name: str, columns: dict):
        """Erstellt neue Tabelle: { 'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT', ... }"""
        try:
            self.Connect()
            col_str = ', '.join([f"{col} {typ}" for col, typ in columns.items()])
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} ({col_str});")
            self.connection.commit()
            print(f"[SQL] Table '{name}' created or already exists.")
            return True
        except Exception as e:
            print(f"[SQL] TableCreate Error: {e}")
            return False

    def TableDelete(self, name: str):
        """Löscht Tabelle"""
        try:
            self.Connect()
            self.cursor.execute(f"DROP TABLE IF EXISTS {name};")
            self.connection.commit()
            return True
        except Exception as e:
            print(f"[SQL] TableDelete Error: {e}")
            return False

    def TableList(self) -> list:
        """Listet alle Tabellen in der DB"""
        try:
            self.Connect()
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [t[0] for t in self.cursor.fetchall()]
        except Exception:
            return []

    # ? #############################################
    # ? CRUD (Create, Read, Update, Delete)
    # ? #############################################

    def Insert(self, table: str, data: dict):
        """Fügt Datensatz hinzu"""
        try:
            self.Connect()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(sql, tuple(data.values()))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"[SQL] Insert Error: {e}")
            return None

    def Read(self, table: str, where: dict = None):
        """Liest Daten (optional mit where dict)"""
        try:
            self.Connect()
            if where:
                conditions = ' AND '.join(f"{k}=?" for k in where.keys())
                sql = f"SELECT * FROM {table} WHERE {conditions}"
                self.cursor.execute(sql, tuple(where.values()))
            else:
                sql = f"SELECT * FROM {table}"
                self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"[SQL] Read Error: {e}")
            return []

    def Update(self, table: str, updates: dict, where: dict):
        """Updatet Datensätze"""
        try:
            self.Connect()
            update_str = ', '.join(f"{k}=?" for k in updates.keys())
            where_str = ' AND '.join(f"{k}=?" for k in where.keys())
            sql = f"UPDATE {table} SET {update_str} WHERE {where_str}"
            self.cursor.execute(sql, tuple(updates.values()) + tuple(where.values()))
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            print(f"[SQL] Update Error: {e}")
            return 0

    def Delete(self, table: str, where: dict = None):
        """Löscht Datensätze (optional mit WHERE)"""
        try:
            self.Connect()
            if where:
                conditions = ' AND '.join(f"{k}=?" for k in where.keys())
                sql = f"DELETE FROM {table} WHERE {conditions}"
                self.cursor.execute(sql, tuple(where.values()))
            else:
                sql = f"DELETE FROM {table}"
                self.cursor.execute(sql)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            print(f"[SQL] Delete Error: {e}")
            return 0

    # ? #############################################
    # ? SEARCH & META
    # ? #############################################

    def TableSearch(self, table: str, column: str, keyword: str):
        """Einfacher Textsuche in Spalte"""
        try:
            self.Connect()
            sql = f"SELECT * FROM {table} WHERE {column} LIKE ?"
            self.cursor.execute(sql, (f"%{keyword}%",))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"[SQL] TableSearch Error: {e}")
            return []

    def FetchColumns(self, table: str):
        """Gibt alle Spaltennamen der Tabelle zurück"""
        try:
            self.Connect()
            self.cursor.execute(f"PRAGMA table_info({table});")
            return [col[1] for col in self.cursor.fetchall()]
        except Exception as e:
            print(f"[SQL] FetchColumns Error: {e}")
            return []

    def Count(self, table: str) -> int:
        """Zählt Einträge"""
        try:
            self.Connect()
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            return self.cursor.fetchone()[0]
        except Exception:
            return 0

class ImageAPI:
    def __init__(self, app):
        self.App = app

    def LoadImage(self, image_path):
        # Load an image from the given path
        pass

    def DisplayImage(self, image):
        # Display the image
        pass

    def ResizeImage(self, image, size):
        # Resize the image to the given size
        pass

    def SaveImage(self, image, save_path):
        # Save the image to the given path
        pass

    #? ################  SOUND API #####################
from enum import Enum
from typing import Optional, Union
import subprocess
from threading import Lock
import pygame
import platform
import os

class PlayerType(Enum):
    NONE = "none"
    PYGAME = "pygame"
    WINSOUND = "winsound"
    AFPLAY = "afplay"
    APLAY = "aplay"
    MPG123 = "mpg123"

class SoundAPI:
    def __init__(self, app):
        self.App = app
        self._player_type = PlayerType.NONE
        self._proc: Optional[subprocess.Popen] = None
        self._is_paused = False
        self._current_file: Optional[str] = None
        self._volume = 1.0
        self._loop = False
        self._lock = Lock()

        # Try pygame mixer first (best feature set)
        try:
            pygame.mixer.init()
            self._pygame = pygame
            self._player_type = "pygame"
        except Exception:
            self._pygame = None
            # Try windows winsound (only wav, minimal control)
            try:
                self._winsound = winsound
                self._player_type = "winsound"
            except Exception:
                self._winsound = None
                # fallback to subprocess based players
                plt = platform.system().lower()
                if plt == "darwin":
                    # afplay is commonly available on macOS
                    self._player_type = "subprocess"
                    self._preferred_cmd = ["afplay"]
                elif plt == "linux":
                    # try a list of common linux players; we'll try them at runtime
                    self._player_type = "subprocess"
                    self._preferred_cmd = ["paplay", "aplay", "mpg123", "ffplay", "play"]
                else:
                    self._player_type = "subprocess"
                    self._preferred_cmd = ["afplay", "paplay", "aplay", "mpg123", "ffplay", "play"]

    def _log(self, msg):
        try:
            if getattr(self.app, "Log", None):
                self.app.Log.WriteLog("sound.log", msg)
        except Exception:
            pass

    def PlaySound(self, sound_file, loop: bool = False, blocking: bool = False):
        """
        Play a sound file.
        - sound_file: path to file
        - loop: if True, attempt to loop indefinitely (pygame supports).
        - blocking: if True, block until playback finishes (where supported).
        Returns True on success, False otherwise.
        """
        self.StopSound()  # stop current if any
        self._current_file = sound_file
        self._loop = loop
        self._is_paused = False

        try:
            if self._player_type == "pygame" and self._pygame:
                try:
                    self._pygame.mixer.music.load(sound_file)
                    self._pygame.mixer.music.set_volume(self._volume)
                    loops = -1 if loop else 0
                    self._pygame.mixer.music.play(loops=loops)
                    if blocking:
                        while self._pygame.mixer.music.get_busy():
                            self._pygame.time.wait(100)
                    return True
                except Exception as e:
                    self._log(f"pygame play error: {e}")
                    return False

            elif self._player_type == "winsound" and self._winsound:
                # winsound only supports WAV and async play; no pause/volume
                flags = self._winsound.SND_FILENAME | self._winsound.SND_ASYNC
                if not loop:
                    self._winsound.PlaySound(sound_file, flags)
                else:
                    # manual loop: play async then re-play in a thread if needed

                    def _loop_play():
                        try:
                            while True:
                                self._winsound.PlaySound(sound_file, flags)
                                # no reliable blocking call to detect end, so sleep a bit
                                time.sleep(0.5)
                                if not self._loop:
                                    break
                        except Exception:
                            pass

                    t = threading.Thread(target=_loop_play, daemon=True)
                    self._proc = t
                    t.start()
                return True

            else:
                # subprocess-based playback
                cmd = None
                if isinstance(self._preferred_cmd, (list, tuple)):
                    for c in self._preferred_cmd:
                        if shutil.which(c):
                            cmd = c
                            break
                else:
                    cmd = self._preferred_cmd if shutil.which(self._preferred_cmd) else None

                if not cmd:
                    # try python built-in simpleaudio if installed
                    try:
                        wave_obj = sa.WaveObject.from_wave_file(sound_file)
                        play_obj = wave_obj.play()
                        self._proc = play_obj
                        # simpleaudio play_obj has is_playing and stop
                        if blocking:
                            play_obj.wait_done()
                        return True
                    except Exception:
                        self._log("No playback utility found.")
                        return False

                # build command
                args = [cmd, sound_file]
                # ffplay/ffmpeg/sox variants may need flags to suppress output and auto-exit
                if cmd in ("ffplay", "ffmpeg", "play"):
                    # ffplay: -nodisp -autoexit -loglevel quiet
                    if cmd == "ffplay":
                        args = [cmd, "-nodisp", "-autoexit", "-loglevel", "quiet", sound_file]
                    elif cmd == "ffmpeg":
                        args = [cmd, "-i", sound_file, "-nodisp", "-loglevel", "quiet"]
                    elif cmd == "play":
                        args = [cmd, sound_file, ">/dev/null", "2>&1"]
                # start subprocess
                # for blocking we wait
                popen = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._proc = popen
                if blocking:
                    popen.wait()
                return True

        except Exception as e:
            self._log(f"PlaySound error: {e}")
            return False

    def StopSound(self):
        """Stop playback."""
        try:
            if self._player_type == "pygame" and self._pygame:
                self._pygame.mixer.music.stop()
                self._is_paused = False
                self._current_file = None
                return True

            elif self._player_type == "winsound" and self._winsound:
                # stop winsound
                try:
                    self._winsound.PlaySound(None, self._winsound.SND_PURGE)
                except Exception:
                    try:
                        self._winsound.PlaySound(None, 0)
                    except Exception:
                        pass
                self._current_file = None
                self._is_paused = False
                return True

            else:
                if self._proc:
                    try:
                        # simpleaudio.PlayObject
                        if hasattr(self._proc, "stop"):
                            self._proc.stop()
                        else:
                            # subprocess.Popen
                            self._proc.terminate()
                        self._proc = None
                        self._current_file = None
                        self._is_paused = False
                        return True
                    except Exception:
                        try:
                            self._proc.kill()
                            self._proc = None
                            return True
                        except Exception:
                            return False
                return True
        except Exception as e:
            self._log(f"StopSound error: {e}")
            return False

    def SetVolume(self, volume: float):
        """
        Set volume 0.0 .. 1.0. Not all backends support volume; in that case value is stored.
        Returns True on success (or stored), False on error.
        """
        try:
            self._volume = max(0.0, min(1.0, float(volume)))
            if self._player_type == "pygame" and self._pygame:
                self._pygame.mixer.music.set_volume(self._volume)
            else:
                # other backends: can't set volume programmatically here
                pass
            return True
        except Exception as e:
            self._log(f"SetVolume error: {e}")
            return False

    def GetVolume(self):
        return self._volume

    def PauseSound(self):
        """Pause playback (best-effort)."""
        try:
            if self._player_type == "pygame" and self._pygame:
                self._pygame.mixer.music.pause()
                self._is_paused = True
                return True
            # winsound and subprocess fallbacks: not supported reliably
            return False
        except Exception as e:
            self._log(f"PauseSound error: {e}")
            return False

    def ResumeSound(self):
        """Resume previously paused playback (best-effort)."""
        try:
            if self._player_type == "pygame" and self._pygame:
                self._pygame.mixer.music.unpause()
                self._is_paused = False
                return True
            return False
        except Exception as e:
            self._log(f"ResumeSound error: {e}")
            return False

    def IsPlaying(self):
        """Return True if a sound is playing."""
        try:
            if self._player_type == "pygame" and self._pygame:
                return self._pygame.mixer.music.get_busy() and not self._is_paused
            elif self._player_type == "winsound" and self._winsound:
                # winsound has no query; assume if current_file set and not paused it's playing
                return bool(self._current_file and not self._is_paused)
            else:
                if not self._proc:
                    return False
                # simpleaudio.PlayObject
                if hasattr(self._proc, "is_playing"):
                    return self._proc.is_playing()
                # subprocess
                if hasattr(self._proc, "poll"):
                    return self._proc.poll() is None
                return False
        except Exception:
            return False

    def ConnectSequenceAPI(self, sequence_api):
        self.Sequence = sequence_api

    def CreateSoundSequence(self, sound_file, sequence_name):
        if hasattr(self, 'Sequence'):
            sound = {
                "sequence": sequence_name,
                "meta": [
                    {'instance': self, 'method': 'PlaySound', 'args': [sound_file], 'kwargs': {}}
                ]
            }
            self.Sequence.AddSequence(sound)
            return sound
        return False

class SettingsAPI:

    def __init__(self, app, settings_path: str=None, basepath=None, generate_basepath=False):
        self.USE_SETTINGS_DICT = False
        self.app = app
        self.SETTINGSPATH = self.app.SDK.SDK_SETTINGS if not settings_path else settings_path
        if not generate_basepath and basepath:
            self.UpdateBasepath(basepath=basepath)
        if generate_basepath:
            import os
            basepath = os.path.dirname(os.path.abspath(__file__))
            self.UpdateBasepath(basepath=basepath)
        try:
            
            if not basepath:
                self.SETTINGS = self.LoadSettings()
                self.VERSION = self.SETTINGS.get("version") if self.SETTINGS.get("version") else None
                self.LANGUAGE = self.SETTINGS.get("language") if self.SETTINGS.get("language") else None
                self.PACKAGEPATH = self.SETTINGS.get("packagepath") if self.SETTINGS.get("packagepath") else None
                self.CACHEPATH = self.SETTINGS.get("cachepath") if self.SETTINGS.get("cachepath") else None
                self.TEMPPATH = self.SETTINGS.get("temppath") if self.SETTINGS.get("temppath") else None
                self.LOGPATH = self.SETTINGS.get("logpath") if self.SETTINGS.get("logpath") else None
                self.APIPATH = self.SETTINGS.get("apipath") if self.SETTINGS.get("apipath") else None
                self.LANGUAGEPATH = self.SETTINGS.get("languagepath") if self.SETTINGS.get("languagepath") else None
                self.MODPATH = self.SETTINGS.get("modpath") if self.SETTINGS.get("modpath") else None
                self.MODS_ENABLED = self.SETTINGS.get("mods_enabled") if self.SETTINGS.get ("mods_enabled") else False
            if basepath:
                self.SETTINGS = self.LoadSettings()
                self.VERSION = self.SETTINGS.get("version") if self.SETTINGS.get("version") else None
                self.LANGUAGE = self.SETTINGS.get("language") if self.SETTINGS.get("language") else None
                self.PACKAGEPATH = f"{basepath}\\{self.SETTINGS.get('packagepath')}"
                self.CACHEPATH = f"{basepath}\\{self.SETTINGS.get("cachepath") if self.SETTINGS.get("cachepath") else None}"
                self.TEMPPATH = f"{basepath}\\{self.SETTINGS.get("temppath") if self.SETTINGS.get("temppath") else None}"
                self.LOGPATH = f"{basepath}\\{self.SETTINGS.get("logpath") if self.SETTINGS.get("logpath") else None}"
                self.APIPATH = f"{basepath}\\{self.SETTINGS.get("apipath") if self.SETTINGS.get("apipath") else None}"
                self.LANGUAGEPATH = f"{basepath}\\{self.SETTINGS.get("languagepath") if self.SETTINGS.get("languagepath") else None}"
                self.MODPATH = f"{self.SETTINGS.get("modpath") if self.SETTINGS.get("modpath") else None}"
                self.MODS_ENABLED = self.SETTINGS.get("mods_enabled") if self.SETTINGS.get ("mods_enabled") else False
        except Exception:
            pass
        
    def AddSetting(self, key, value):
        if self.USE_SETTINGS_DICT:
            self.DICT_SETTINGS[key] = value
            return True
        try:
            self.SETTINGS[key] = value
            import json
            with open(self.SETTINGSPATH, 'w', encoding='utf-8') as f:
                json.dump(self.SETTINGS, f, indent=4)
            return True
        except Exception:
            return False

    def LoadSettings(self, own=False, settings: dict=None):
        if self.USE_SETTINGS_DICT:
            return self.DICT_SETTINGS
        try:
            import json
            if own and settings:
                return settings
            with open(self.SETTINGSPATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            raise FileNotFoundError(f"Einstellungsdatei nicht gefunden: {self.SETTINGSPATH}")
        
    def Global(self, key):
        if self.USE_SETTINGS_DICT:
            return self.DICT_SETTINGS.get(key, None)
        return self.SETTINGS.get(key, None)
    
    def SetUpdate(self):
        try:
            self.SETTINGS["update"] = True
            import json
            with open(self.SETTINGSPATH, 'w', encoding='utf-8') as f:
                json.dump(self.SETTINGS, f, indent=4)
        except Exception:
            return False
            
    def CheckIfUpdate(self):
        return self.SETTINGS.get("update", False)
    
    def UpdateBasepath(self, basepath):
        if not self.USE_SETTINGS_DICT:
            with open(self.SETTINGSPATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            settings["basepath"] = basepath
            with open(self.SETTINGSPATH, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
    
    def SetSettingsPath(self, path):
        self.SETTINGSPATH = path
        self.Update()
        
    def SetSettings(self, settings: dict):
        if not isinstance(settings, dict):
            return False
        self.USE_SETTINGS_DICT = True
        self.DICT_SETTINGS = settings
        self.LoadSettings(own=True, settings=settings)
    
    
    def Update(self):
        try:
            import json
            with open(self.SETTINGSPATH, 'r', encoding='utf-8') as f:
                self.SETTINGS = json.load(f)
            self.VERSION = self.SETTINGS.get("version") if self.SETTINGS.get("version") else None
            self.LANGUAGE = self.SETTINGS.get("language") if self.SETTINGS.get("language") else None
            self.PACKAGEPATH = self.SETTINGS.get("packagepath") if self.SETTINGS.get("packagepath") else None
            self.CACHEPATH = self.SETTINGS.get("cachepath") if self.SETTINGS.get("cachepath") else None
            self.TEMPPATH = self.SETTINGS.get("temppath") if self.SETTINGS.get("temppath") else None
            self.LOGPATH = self.SETTINGS.get("logpath") if self.SETTINGS.get("logpath") else None
            self.APIPATH = self.SETTINGS.get("apipath") if self.SETTINGS.get("apipath") else None
            self.LANGUAGEPATH = self.SETTINGS.get("languagepath") if self.SETTINGS.get("languagepath") else None
            self.MODPATH = self.SETTINGS.get("modpath") if self.SETTINGS.get("modpath") else None
            self.MODS_ENABLED = self.SETTINGS.get("mods_enabled") if self.SETTINGS.get ("mods_enabled") else False
        except Exception:
            return False

    #? ################  StateMachine API #####################
    
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from threading import Lock

class StateType(Enum):
    STEP1 = "step_1"
    STEP2 = "step_2"
    STEP3 = "step_3"
    STEP4 = "step_4"
    STEP5 = "step_5"
    EXIT = "exit"
    MAIN_MENU = "main_menu"
    FIRST_ENTRY = "first_entry"
    LOGIN = "login"
    VERIFIED = "verified"
    START = "start"
    CHECK = "check"
    MAIN = "main"
    RED = "red"
    GREEN = "green"
    NEW = "new"
    USER = "user"
    REGISTER = "register"
    # Buttons
    DKEY = "d_key"
    WKEY = "w_key"
    AKEY = "a_key"
    SKEY = "s_key"
    QKEY = "q_key"
    EKEY = "e_key"
    LEFT = "arrow_left"
    RIGHT = "arrow_right"
    DOWN = "arrow_down"
    UP = "arrow_up"
    #Game States
    KILLED = "killed"
    ENTITY = "entity"
    PLAYER = "player"
    MOVING = "moving"
    JUMPING = "jumping"
    ATTACKING = "attacking"
    LOW_HEALTH = "low_health"
    
    
    

@dataclass
class State:
    name: str
    data: Dict
    frozen: bool = False
    sequence: Optional[Dict] = None

class StateMachineAPI:
    def __init__(self, app):
        self.App = app
        self.StateType = StateType
        self.SequenceApi = self.App.Sequence
        self.STATES = []
        self._lock = Lock()
        self.sSTATE = self.StateType.FIRST_ENTRY.value
        
   #? Single State Functions
    
    def sSetState(self, new_state):
        self.sSTATE = new_state

    def sGetState(self):
        return self.sSTATE

    def sIsState(self, check_state):
        return self.sSTATE == check_state

    def sStateIsNot(self, state: str):
        return self.sSTATE != state

   #? Single State Functions with Key (format: 'state:key')

    def sSetStateKey(self, state: str, key: str):
        self.sSTATE = f"{state}:{key}"

    def sGetStateKey(self):
        if ":" in self.sSTATE:
            return self.sSTATE.split(":")[1]
        return None
    
    def sStateKeyIs(self, key: str):
        if ":" in self.sSTATE:
            return self.sSTATE.split(":")[1] == key
        return False
    
    def sIsStateKey(self, state: str, key: str):
        if ":" in self.sSTATE:
            s, k = self.sSTATE.split(":")
            return s == state and k == key
        return False
    
    
   #? Multi State Functions #########################################
   
   
   #? Core
    def mAddState(self, statename: str, data: dict=None):
        """Adding a New Multi-State"""
        if not any(s['state'] == statename for s in self.STATES):
            self.STATES.append({"state": statename, "data": data if data else {}})
            return True
        return False
    
    def mRemoveState(self, statename: str):
        """Removes State"""
        for state in self.STATES:
            if state['state'] == statename:
                self.STATES.remove(state)
                return True
        return False
    
    def mStateExists(self, statename: str):
        """Checks if State Exists"""
        return any(s['state'] == statename for s in self.STATES)
    
   #? Checks 
    
    def mStateHasKey(self, statename: str, key: str):
        """Checks if a State has This key in 'data'"""
        for state in self.STATES:
            if state['state'] == statename:
                return key in state['data']
        return False
    
    def mGetSuperMeta(self, statename, supermetakey):
        """Return Dict in 'data'"""
        for state in self.STATES:
            if state['state'] == statename:
                return state['data'][supermetakey]
            return False
        
    
    def mStateHasValueInKey(self, statename: str, key: str, value):
        """Checks if the Key has The Value"""
        for state in self.STATES:
            if state['state'] == statename:
                return state['data'].get(key) == value
        return False
    
    
    #? Options
    def mAddKeyToState(self, statename: str, key: str, value):
        """Adding a New Key to a State function:
        ```
        {
            'state': 'name',
            'data': {
                'newkey', 'newvalue'
            }
        }"""
             
        for state in self.STATES:
            if state['state'] == statename:
                state['data'][key] = value
                return True
        return False
    
    
    def mVarIs(self, statename: str, key: str, var: str):
        """Checks if The Key is in Keyword"""
        for state in self.STATES:
            if state['state'] == statename:
                if state['data'][key] == var:
                    return True
                return False
            return False
    
    
    def mRemoveKeyFromState(self, statename: str, key: str):
        """Removes Keyword from State"""
        for state in self.STATES:
            if state['state'] == statename:
                if key in state['data']:
                    del state['data'][key]
                    return True
        return False
    
    # def mAddValueToKey(self, statename: str, key: str, value):
    #     """Changes The Current Value in Keyword"""
    #     for state in self.STATES:
    #         if state['state'] == statename:
    #             if key in state['data']:
    #                 if isinstance(state['data'][key], list):
    #                     state['data'][key].append(value)
    #                 else:
    #                     state['data'][key] = [state['data'][key], value]
    #             else:
    #                 state['data'][key] = [value]
    #             return True
    #     return False
    
    def mEditValueOnKey(self, statename: str, key: str, new_value):
        """Change Value on a Key"""
        for state in self.STATES:
            if state['state'] == statename:
                state['data'][key] = new_value
                return True
        return False

    
    def mGetStates(self):
        """Return All States"""
        return self.STATES
    

    
    def mReadVar(self, statename: str, key: str):
        """Return Var in Keyword"""
        for state in self.STATES:
            if state['state'] == statename:
                return state['data'].get(key, None)
        return None
    
    def mDeleteKey(self, statename: str, key: str):
        """Deletes a Key in the State"""
        for state in self.STATES:
            if state['state'] == statename:
                if key in state['data']:
                    del state['data'][key]
                    return True
        return False
    
    
    def mFreezeState(self, statename: str):
        """Freezes The State. The State can't change"""
        for state in self.STATES:
            if state['state'] == statename:
                for i in state['data']:
                    if not i.get('frezze'):
                        i['frezze'] = True
                    else:
                        i['frezze'] = True
                return True
        return False
    
    def mUnfreezeState(self, statename: str):
        """Unfreeze The State"""
        for state in self.STATES:
            if state['state'] == statename:
                for i in state['data']:
                    if i.get('frezze'):
                        i['frezze'] = False
                    else:
                        i['frezze'] = False
                return True
        return False
    
    def mIsFrozen(self, statename: str):
        """Checks if a State is Frozen"""
        for state in self.STATES:
            if state['state'] == statename:
                for i in state['data']:
                    if i.get('frezze'):
                        return True
        return False
    
    def mGetStateData(self, statename: str):
        """Returns Dict 'data' of State"""
        for state in self.STATES:
            if state['state'] == statename:
                return state['data']
        return None
    
   #? ################  Sequence Functions #####################
   
    def mLinkSequenceToState(self, statename: str, sequence_name: str = None, sequence_data: dict = None):
        if self.sequenceapi and self.mStateExists(statename):
            if not sequence_data:
                sequence = self.sequenceapi.ReadSequence(sequence_name)
            else:                                                         
                sequence = sequence_data

            self.mAddKeyToState(statename, "sequence", sequence)
            return True
        return False
    
    def mUnlinkSequenceFromState(self, statename: str):
        if self.mStateExists(statename):
            return self.mRemoveKeyFromState(statename, "sequence")
        return False
    
    def mRunSequenceIf(self, statename: str, if_key: str, if_value, allow_clear: bool=False, enable_header: bool=False, library: str="standard"):
        if self.sequenceapi and self.mStateExists(statename):
            if self.mVarIs(statename, if_key, if_value):
                sequence = self.mReadVar(statename, "sequence")
                if sequence:
                    seq_name = sequence['sequence'] if isinstance(sequence, dict) else sequence
                    return self.sequenceapi.DoSequence(seq_name, allow_clear=allow_clear, enable_header=enable_header, library=library)
        return False
    
    
    

class CacheAPI:
    
    def __init__(self, cache_path=None):
        self.CACHEPATH = cache_path if cache_path else "./cache"
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self):
        """Stellt sicher, dass das Cache-Verzeichnis existiert"""
        if self.CACHEPATH:
            try:
                os.makedirs(self.CACHEPATH, exist_ok=True)
            except Exception as e:
                print(f"Fehler beim Erstellen des Cache-Verzeichnisses: {e}")
    
    def SetCachePath(self, path):
        """Setzt den Cache-Pfad und erstellt das Verzeichnis falls nötig"""
        if not path:
            raise ValueError("Cache-Pfad darf nicht None oder leer sein")
        self.CACHEPATH = path
        self._ensure_cache_directory()
        
        
    def WriteCacheFile(self, filename, content):
        with open(f"{self.CACHEPATH}/{filename}", 'w', encoding='utf-8') as f:
            f.write(content)
            
    def ReadCacheFile(self, filename):
        with open(f"{self.CACHEPATH}/{filename}", 'r', encoding='utf-8') as f:
            return f.read()
    
    def AddContent(self, filename, content):
        with open(f"{self.CACHEPATH}/{filename}", 'a', encoding='utf-8') as f:
            f.write(content + "\n")
            
    def RemoveCacheFile(self, filename):
        import os
        os.remove(f"{self.CACHEPATH}/{filename}")
        
    def CacheExists(self, filename=None):
        try:
            import os
            if filename:
                return os.path.exists(f"{self.CACHEPATH}/{filename}")
            return os.path.exists(self.CACHEPATH)
        except Exception:
            return False

    #? ################  TEMP API #####################

class TempAPI:
    
    def __init__(self, temp_path=None):
        try:
            self.TEMPPATH = temp_path
            if not self.TempExists():
                import os
                os.makedirs(temp_path)
        except Exception:
            pass
        
    def SetTempPath(self, path):
        self.TEMPPATH = path
        if not self.TempExists():
            import os
            os.makedirs(path)
        
    def WriteTempFile(self, filename, content):
        with open(f"{self.TEMPPATH}/{filename}", 'w', encoding='utf-8') as f:
            f.write(content)
            
    def ReadTempFile(self, filename):
        with open(f"{self.TEMPPATH}/{filename}", 'r', encoding='utf-8') as f:
            return f.read()
        
    def AddContent(self, filename, content):
        with open(f"{self.TEMPPATH}/{filename}", 'a', encoding='utf-8') as f:
            f.write(content + "\n")
    
    def TempExists(self, filename=None):
        try:
            import os
            if filename:
                return os.path.exists(f"{self.TEMPPATH}/{filename}")
            return os.path.exists(self.TEMPPATH)
        except Exception:
            return False

    def RemoveTempFile(self, filename=None):
        if not filename: # leere Temp ordner
            import os
            for file in os.listdir(self.TEMPPATH):
                file_path = os.path.join(self.TEMPPATH, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
            return True
        try:
            import os
            os.remove(f"{self.TEMPPATH}/{filename}")
        except Exception:
            return False

    #? ################  PACKAGE API #####################

class PackageAPI:
    
    def __init__(self, package_path=None):
        self.PACKAGEPATH = package_path
        self.isLoggedIn = False
        self.USERNAME = None
        
    def SetPackagePath(self, path):
        self.PACKAGEPATH = path
        if not self.PackageExists():
            import os
            os.makedirs(path)
        
    def Login(self, username, password):
        if username == "admin" and password == "password":
            self.isLoggedIn = True
            self.USERNAME = username
            return True
        return False
    
    def Logout(self):
        self.isLoggedIn = False
        self.USERNAME = None
        
    def WritePackageFile(self, filename, content):
        with open(f"{self.PACKAGEPATH}/{filename}", 'w', encoding='utf-8') as f:
            f.write(content)
            
    def ReadPackageFile(self, filename):
        with open(f"{self.PACKAGEPATH}/{filename}", 'r', encoding='utf-8') as f:
            return f.read()
        
    def AddContent(self, filename, content):
        with open(f"{self.PACKAGEPATH}/{filename}", 'a', encoding='utf-8') as f:
            f.write(content + "\n")
    
    def RemovePackageFile(self, filename):
        import os
        os.remove(f"{self.PACKAGEPATH}/{filename}")
        
        
        
        
        
    #? ################  LOG API #####################
        
        
class LogAPI:
    
    
    def __init__(self, log_path=None):
        try:
            self.LOGPATH = log_path
            if not self.LogExists():
                import os
                os.makedirs(log_path)
        except Exception:
            pass
            
    def SetLogPath(self, path):
        self.LOGPATH = path
        if not self.LogExists():
            import os
            os.makedirs(path)
        
    def WriteLog(self, filename, message):
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        with open(f"{self.LOGPATH}/{filename}", 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def ReadLog(self, filename):
        with open(f"{self.LOGPATH}/{filename}", 'r', encoding='utf-8') as f:
            return f.read()
        
    def DeleteLog(self, filename):
        import os
        os.remove(f"{self.LOGPATH}/{filename}")
        
    def ClearLog(self, filename):
        with open(f"{self.LOGPATH}/{filename}", 'w') as f:
            f.write("")
               
    def LogExists(self, filename=None):
        try:
            import os
            if filename:
                return os.path.exists(f"{self.LOGPATH}/{filename}")
            return os.path.exists(self.LOGPATH)
        except Exception:
            return False
        
        #? ######################## EVENT API #############################
        
class EventOptions:
    """Globale Optionen für alle Events."""
    def __init__(self):
        self.AutoUnbindAfterTrigger = False
        self.DefaultPriority = 1
        self.AllowAsync = True
        self.LogEvents = True
        self.AutoLinkStateMachine = True
        self.AutoLinkSequenceAPI = True
        self.DebugMode = False

        
        
import threading, asyncio, time, inspect

class EventAPI:
    def __init__(self, app):
        self.app = app
        self.EVENTS = []
        self.Options = EventOptions()
        self._lock = threading.Lock()

        # Auto-Integration
        self.StateMachine = getattr(app, "StateMachine", None)
        self.SequenceAPI = getattr(app, "Sequence", None)

    def AddEvent(self, name: str, func, priority: int = None, once: bool = False, tags: list[str] = None):
        """Registriert ein neues Event."""
        ev = {
            "name": name,
            "func": func,
            "priority": priority or self.Options.DefaultPriority,
            "once": once,
            "tags": tags or [],
            "handlers": [],
            "active": True,
            "created": time.time()
        }
        self.EVENTS.append(ev)
        if self.Options.LogEvents:
            print(f"[EventAPI] Added Event '{name}' (priority={ev['priority']})")
        return ev

    def AddHandler(self, event_name: str, condition=None, sequence=None, state_trigger=None):
        """Fügt einem Event einen Handler hinzu (Condition, Sequence oder State)."""
        for ev in self.EVENTS:
            if ev["name"] == event_name:
                ev["handlers"].append({
                    "condition": condition,
                    "sequence": sequence,
                    "state_trigger": state_trigger
                })
                if self.Options.LogEvents:
                    print(f"[EventAPI] Handler added to '{event_name}'")
                return True
        raise NameError(f"Event '{event_name}' not found")

    def Trigger(self, name: str, *args, **kwargs):
        """Startet das Event und seine Handler."""
        found = False
        for ev in sorted(self.EVENTS, key=lambda e: e["priority"], reverse=True):
            if ev["name"] == name and ev["active"]:
                found = True
                if inspect.iscoroutinefunction(ev["func"]) and self.Options.AllowAsync:
                    asyncio.run(ev["func"](*args, **kwargs))
                else:
                    ev["func"](*args, **kwargs)

                # Handler ausführen
                for h in ev["handlers"]:
                    if h["condition"] and not h["condition"]():
                        continue
                    if h["sequence"] and self.SequenceAPI:
                        self.SequenceAPI.DoSequence(h["sequence"])
                    if h["state_trigger"] and self.StateMachine:
                        self.StateMachine.sSetState(h["state_trigger"])

                if ev["once"] or self.Options.AutoUnbindAfterTrigger:
                    self.RemoveEvent(name)

        if not found:
            print(f"[EventAPI] Event '{name}' not found")
        return found

    def RemoveEvent(self, name: str):
        """Entfernt ein Event vollständig."""
        with self._lock:
            for ev in list(self.EVENTS):
                if ev["name"] == name:
                    self.EVENTS.remove(ev)
                    print(f"[EventAPI] Removed event '{name}'")
                    return True
        return False

    def ListEvents(self):
        """Zeigt alle registrierten Events an."""
        return [ev["name"] for ev in self.EVENTS]

    def LinkToSequence(self, event_name: str, sequence_name: str):
        return self.AddHandler(event_name, sequence=sequence_name)

    def LinkToState(self, event_name: str, state_name: str):
        return self.AddHandler(event_name, state_trigger=state_name)

        #? ######################## Modding SDK ###########################
        
class ModdingOptions:
    
    def __init__(self):
        self.LoadModsOnLaunch = False
        self.ModRequiresManifest = True
    
    def toggleModLoadingOnStart(self, toggle=True):
        """Enable/Disable ModLoading on Programm Start"""
        self.LoadModsOnLaunch = toggle
        return True
    
    def forceModManifest(self, toggle=True):
        """Allow/Block Mods with/without Manifest"""
        self.ModRequiresManifest = toggle
        return True
    
class ModdingSDK:
    """Under Development. Do NOT Use"""
    
    def __init__(self, app):
        self.app = app
        self.option = ModdingOptions()
        
    def setLocation(self, path):
        pass
    
    
    def setFlags(self, *flags):
        pass
    
    def setPolicy(self, reference: dict, sdkkeys: list[dict]=None):
        """Set The Policy of manifest.json
        
        example: (in mainfest)
        ```python
        {
            <keyword>: <key>
        }
        ```
        The Keyword is the 'sdkkey' and give acsess to Project data:
        
        Here is a basic example of Creating a Manifest-Policy:
        ```python
        ReferencePolicy = {
            "version": None,
            "author": None,
            "start": None,
            "exec": None
        }
        SdkKeys = [{"version": "version"}, {"author": "author"}, {"start": "start"}, {"exec": "exec"}]
        self.ModSDK.setPolicy(reference=ReferencePolicy, sdkkeys=SdkKeys)
        ```
        > By That you have directly Acsess to the Variables from the SdkKeys. You also are able to connect keys to functions.
        For Example when you want to execute a script or function of The loaded Mod. So Do This:
        **DO THIS PART BEFORE THE UPPER CODE**
        ```python
        self.ModSDK.addEvent(keyword="exec", func=self.ExecuteFunctionExample)
        ```
        If a mod getting Verified in 'VerifyContent()', the Event will Automaticly trigger.
        
        """
        pass
    
    def RegisterMod(self):
        pass
    
    def VerifyContent(self):
        pass
    
    def ExecuteEvents(self, eventname):
        pass
    
    def addEvent(keyword: str, func):
        pass
        
        
        
    
    #? ################  Sequence API #####################
    
    
class SequenceAPICreator:
    def __init__(self, sequence_api):
        self.sequence_api = sequence_api

    def CreateStateSequence(self, sequence_name: str, instance = None, method = None, lambda_func = None, args: list=None, kwargs: dict=None):
        """Erstellt eine neue Zustandssequenz.
        
        Args:
            sequence_name (str): Name der Sequenz
            instance: Instanz des Objekts für die Methodenaufrufe
            method (str, optional): Name der aufzurufenden Methode
            lambda_func (callable, optional): Lambda-Funktion oder Callable
            args (list, optional): Liste der Positionsargumente
            kwargs (dict, optional): Dictionary der Schlüsselwortargumente
            
        Returns:
            dict: Die erstellte Sequenz oder None bei Fehler
        """
        if not sequence_name:
            raise ValueError("sequence_name darf nicht leer sein")
            
        sequence = {
            "sequence": sequence_name,
            "meta": []
        }
        
        # Validiere und füge Methoden-basierte Aktion hinzu
        if instance and method:
            if not hasattr(instance, method):
                raise AttributeError(f"Instanz hat keine Methode '{method}'")
            sequence["meta"].append({
                "instance": instance,
                "method": method,
                "args": args if args else [],
                "kwargs": kwargs if kwargs else {}
            })
            
        # Füge Lambda/Callable-basierte Aktion hinzu
        if lambda_func:
            if not callable(lambda_func):
                raise TypeError("lambda_func muss callable sein")
            sequence["meta"].append({
                "instance": None,
                "method": lambda_func,
                "args": args if args else [],
                "kwargs": kwargs if kwargs else {}
            })
            
        if not sequence["meta"]:
            raise ValueError("Mindestens instance/method oder lambda_func muss angegeben werden")
            
        added = self.sequence_api.AddSequence(sequence)
        return sequence if added else None
    
    def CreateUrsinaSequence(self, sequence_name: str, ursina_entity, animation_type: str, duration: float, target_value, loop: bool=False):
        sequence = {
            "sequence": sequence_name,
            "meta": [
                {
                    "instance": ursina_entity,
                    "method": f"animate_{animation_type}",
                    "args": [target_value, duration],
                    "kwargs": {"loop": loop}
                }
            ]
        }
        added = self.sequence_api.AddSequence(sequence)
        if added:
            return sequence
        return None
    
    def CreateStartUpSequence(self, sequence_name: str, steps: list, wait: list):
        if not len(steps) == len(wait):
            raise ValueError("Steps and wait lists must be of the same length")
        sequence = {
            "sequence": sequence_name,
            "meta": {
                "steps": steps,
                "wait": wait
            }
        }
        added = self.sequence_api.AddSequence(sequence)
        if added:
            return sequence
        return None
    
    def CreateSequence(self, sequence_name: str, actions: list):
        sequence = {
            "sequence": sequence_name,
            "meta": actions
        }
        added = self.sequence_api.AddSequence(sequence)
        if added:
            return sequence
        return None
    
class LibraryAPI:
    def __init__(self, sequence_api):
        self.Sequence = sequence_api
        self.Libraries = []
        
    def Reload(self):
        self.Libraries = []
        for mod in self.Sequence.MODS:
            if mod['library'] not in self.Libraries:
                self.Libraries.append(mod)
                
    def GetInstancesByLibrary(self, library: str):
        for mod in self.Libraries:
            if mod['library'] == library:
                instance = mod['instance']
                return instance
        return None

    def RunSequence(self, sequence_name: str, library: str, enable_header: bool=False):
        """Führt eine Sequenz in einer bestimmten Bibliothek aus.
        
        Args:
            sequence_name (str): Name der auszuführenden Sequenz
            library (str): Name der Bibliothek
            enable_header (bool): Aktiviert Logging-Header
            
        Returns:
            bool: True bei erfolgreicher Ausführung, False sonst
            
        Raises:
            ValueError: Wenn die Bibliothek nicht existiert
            AttributeError: Wenn die Instanz keine DoSequence-Methode hat
        """
        if not library:
            raise ValueError("Library-Name darf nicht leer sein")
            
        instance = self.GetInstancesByLibrary(library)
        if not instance:
            raise ValueError(f"Library '{library}' nicht gefunden")
            
        if not hasattr(instance, 'DoSequence'):
            raise AttributeError(f"Library '{library}' hat keine DoSequence-Methode")
            
        if enable_header:
            self.Sequence.app.Log.WriteLog(
                f"{self.Sequence.app.Settings.Global('LOGPATH')}/sequence.log",
                f"Starting sequence: {sequence_name} in library: {library}"
            )
            
        try:
            result = instance.DoSequence(
                name=sequence_name,
                meta=self.Sequence.ReadSequenceMeta(sequence_name)
            )
            
            if enable_header:
                self.Sequence.app.Log.WriteLog(
                    f"{self.Sequence.app.Settings.Global('LOGPATH')}/sequence.log",
                    f"Finished sequence: {sequence_name} in library: {library}"
                )
                
            return result
            
        except Exception as e:
            if enable_header:
                self.Sequence.app.Log.WriteLog(
                    f"{self.Sequence.app.Settings.Global('LOGPATH')}/sequence.log",
                    f"Error in sequence: {sequence_name}, library: {library} - {str(e)}"
                )
            return False
        

class SequenceAPI:

    def __init__(self, app):
        self.app = app
        self.Sequences = []
        self.Creator = SequenceAPICreator(self)
        self.Library = LibraryAPI(self)
        self.MODS = []
        
    def RegisterSequenceMod(self, mod_instance, library: str):
        self.MODS.append({
            "instance": mod_instance,
            "library": library
        })
        self.Library.Reload()

    def AddSequence(self, sequence: dict):
        """A Sequence is in this Format:
        ```python
        your_sequence = {
            "sequence": "my_sequence_name",
            "meta": [
                {'instance': your_instance, 'method': 'method_name', 'args': [arg1, arg2], 'kwargs': {'key': value}},
                {'instance': None, 'method': lambda x: print(x), 'args': ['Hello'], 'kwargs': {}}
            ]
        ```
        """
        if not any(s['sequence'] == sequence['sequence'] for s in self.Sequences):
            self.Sequences.append(sequence)
            return True
        return False
    
    def RemoveSequence(self, sequence_name: str):
        for seq in self.Sequences:
            if seq['sequence'] == sequence_name:
                self.Sequences.remove(seq)
                return True
        return False
    
    def SequenceExists(self, sequence_name: str):
        return any(s['sequence'] == sequence_name for s in self.Sequences)
    
    def ReadSequence(self, sequence_name: str):
        for seq in self.Sequences:
            if seq['sequence'] == sequence_name:
                return seq
        return None
    
    def ReadSequenceMeta(self, sequence_name: str):
        for seq in self.Sequences:
            if seq['sequence'] == sequence_name:
                return seq['meta']
        return None
    
    def EditSequenceInstance(self, sequence_name: str, new_instance):
        for seq in self.Sequences:
            if seq['sequence'] == sequence_name:
                for action in seq['meta']:
                    action['instance'] = new_instance
                return True
        return False
    
    def EditSequenceMethod(self, sequence_name: str, action_index: int, new_method):
        for seq in self.Sequences:
            if seq['sequence'] == sequence_name:
                if 0 <= action_index < len(seq['meta']):
                    seq['meta'][action_index]['method'] = new_method
                    return True
        return False
    
    def EditSequenceArgs(self, sequence_name: str, action_index: int, new_args: list):
        for seq in self.Sequences:
            if seq['sequence'] == sequence_name:
                if 0 <= action_index < len(seq['meta']):
                    seq['meta'][action_index]['args'] = new_args
                    return True
        return False
    
    def EditSequenceKwargs(self, sequence_name: str, action_index: int, new_kwargs: dict):
        for seq in self.Sequences:
            if seq['sequence'] == sequence_name:
                if 0 <= action_index < len(seq['meta']):
                    seq['meta'][action_index]['kwargs'] = new_kwargs
                    return True
        return False
    
    def DoSequence(self, sequence: str, enable_header: bool=False, library: str="standard"):
        import time
        if library == "standard":
            for seq in self.Sequences:
                if seq['sequence'] == sequence:
                    if enable_header:
                        self.app.Log.WriteLog(f"{self.app.Settings.Global('LOGPATH')}/sequence.log", f"Starting sequence: {sequence}")
                    for action in seq['meta']:
                        instance = action.get('instance')
                        method = action.get('method')
                        args = action.get('args', [])
                        kwargs = action.get('kwargs', {})
                        if instance and method:
                            func = getattr(instance, method, None)
                            if callable(func):
                                func(*args, **kwargs)
                        elif callable(method):  # if method is a lambda or function
                            method(*args, **kwargs)
                    if enable_header:
                        self.app.Log.WriteLog(f"{self.app.Settings.Global('LOGPATH')}/sequence.log", f"Finished sequence: {sequence}")
                    return True
            return False
            
        elif library == "startup":
            for seq in self.Sequences:
                if seq['sequence'] == sequence:
                    steps = seq['meta'].get('steps', [])
                    wait = seq['meta'].get('wait', [])
                    if not len(steps) == len(wait):
                        raise ValueError("Steps and wait lists must be of the same length") 
                    
                    for step, sleep_time in zip(steps, wait):
                        print(f'{step}')
                        time.sleep(sleep_time)
                    return True
                    
        else:
            return self.Library.RunSequence(sequence, library, enable_header=enable_header)
        

        
        
        
   
    #? ################  MANAGER API #####################
    
    

class ManagerAPI:
    
    def __init__(self, api):
        self.api = api
        self.LocalStorage = []
        self.stg = []
        self.AppdataSDK = SystemAppDataAPI()
        
        
        
    #? ################  HELPER API #####################



class HelperAPI:
    
    def __init__(self, app):
        self.app = app

        self.command = CommandAPI(app)
        self.Sound = SoundAPI(app)
        self.Image = ImageAPI(app)
        self.PyQt = PyQt6Framework(self)
        self.Ursina = UrsinaFramework(self)
    
    
    
    #? ################  COMMAND API #####################



class CommandAPI:

    def __init__(self, app):
        try:
            self.app = app
        except Exception:
            pass

    def Execute(self, command):
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    
    
    
    
    
    
    

    #? #################### Developer API #####################
    
    
class DeveloperAPI:
    
    def __init__(self):
        self.DEBUG = False
    
    def DebugInfo(self, message):
        if self.DEBUG:
            print(f"[DEBUG] {message}")
        else:
            return None
        
    def EnableDebug(self):
        self.DEBUG = True
        
    def DisableDebug(self):
        self.DEBUG = False
    
    
    
    
    
    
    #? ####################  AI API #####################
    
    
class AiAPI:
    def __init__(self, api_key=None, model="gpt-4", temperature=0.7):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        
    def SetApiKey(self, api_key):
        self.api_key = api_key
        
    def GenerateText(self, prompt):
        if not self.api_key:
            raise ValueError("API key is not set.")
        import openai
        openai.api_key = self.api_key
        response = openai.Completion.create(
            engine=self.model,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=150
        )
        return response.choices[0].text.strip()






    #? ################  LANGUAGE API #################


class LanguageAPI:

    def __init__(self, settings, standard_library=True):
        try:
            self.Settings = settings
            self.LANGUAGE = self.Settings.Global("language")
            self.LANGUAGEPATH = self.Settings.Global("LANGUAGEPATH")
            self.PACKAGES = []
            if standard_library:
                import os
                package_dir = os.path.dirname(os.path.abspath(__file__))
                self.LANGUAGEPATH = os.path.join(package_dir, "data", "lang")
            self.language_data = self.LoadLanguageData(self.LANGUAGE)
        except Exception:
            pass
        
    #? Core Functions

    # Reloading language data (e.g. after changing language in settings or adding new language-packs)
    def Reload(self):
        """Reloading Language-Data and applied Language-Packages"""
        self.LANGUAGE = self.Settings.Global("language")
        self.language_data = self.LoadLanguageData(self.LANGUAGE)
        if self.PACKAGES:
            for package in self.PACKAGES:
                if package["language"] == self.LANGUAGE:
                    self.language_data.update(package["data"])

    def SetLanguageData(self, keys: dict=None, prefered_lang_reference=False):
        if prefered_lang_reference:
            # Verwende toolos package data/lang Verzeichnis
            import os
            package_dir = os.path.dirname(os.path.abspath(__file__))
            self.LANGUAGEPATH = os.path.join(package_dir, "data", "lang")
            self.language_data = self.LoadLanguageData(self.LANGUAGE)
        elif keys:
            self.language_data = keys
    
    # Loading Original Language-Data json formats from /assets/manager/lang/{'de', 'en', 'ru',..}.json    
    def LoadLanguageData(self, language):
        """Loading Language-Data by parameter: language"""
        import json
        try:
            with open(f"{self.LANGUAGEPATH}/{language}.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            try:
                with open(f"{self.LANGUAGEPATH}/de.json", 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                return {}

    #? Interaction Functions
    
    def Translate(self, key):
        """Translating Keyword by key with current language-data"""
        return self.language_data.get(key, key)
    
    def GetAllTranslationKeys(self):
        """Returning all translation keys"""
        return list(self.language_data.keys())
    
    def GetAvailableLanguages(self):
        """Returning all available languages from {self.LANGUAGEPATH}"""
        import os
        files = os.listdir(self.LANGUAGEPATH)
        languages = [f.split('.')[0] for f in files if f.endswith('.json')]
        return languages
    
    def AddLanguagePackage(self, language, datapath):
        import json
        with open(datapath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.PACKAGES.append({"language": language, "data": data})

   
   
   
   
   

    #? ################ Plugin API #####################
    
    
class PluginAPI:
    
    def __init__(self):
        self.plugins = []
        
    def AddPlugin(self, plugin, call):
        self.plugins.append({"plugin": plugin, "call": call})

    def RemovePlugin(self, call):
        for i in self.plugins:
            if i.get('call') == call:
                self.plugins.remove(i)
                return True
        return False

    def GetPlugin(self, call):
        for i in self.plugins:
            if i.get('call') == call:
                return i.get('plugin', None)
        return None
    
    def ListPlugins(self):
        return self.plugins
    
    def GetPluginInstances(self):
        return [p['plugin'] for p in self.plugins if 'plugin' in p]







    #? ################  APP API #####################
    
    
class AppAPI:
    
    def __init__(self, app):
        self.app = app
        self.MENU = []
        self.IMENU = []
        
    
    def BuildMenu(self, menus: list=None, start=0):
        if not menus:
            menu = self.MENU if not None else []
        else:
            menu = menus
        for i, key in enumerate(menu, start=start):
            self.InteractiveMenu = {
                "index": i,
                "name": key,
                "lambda": None
            }
            self.IMENU.append(self.InteractiveMenu)
            
    def AddLambdaToMenu(self, index, func):
        for item in self.IMENU:
            if item["index"] == index:
                item["lambda"] = func
                return True
        return False
    
    def ClearMenu(self):
        self.MENU = []
        self.IMENU = []
            
    def ShowMenu(self, menus: list=None):
        if menus:
            for i, key in enumerate(menus):
                print(f"{i}: {key}")
        else:
            for item in self.IMENU:
                print(f"{item['index']}: {item['name']}")

    def SelectMenuLambda(self, index):
        for item in self.IMENU:
            if item["index"] == index and item["lambda"]:
                return item["lambda"]
                    
                
    def SelectMenu(self, index, use_imenu: bool=False):
        if use_imenu:
            for item in self.IMENU:
                if item["index"] == index:
                    return item["name"]
        else:
            if index < len(self.MENU):
                return self.MENU[index]
        return None
    
    def GetIndexAndKey(self, index):
        for item in self.IMENU:
            if item["index"] == index:
                return item["name"], item["lambda"] if item["lambda"] else None
        return None, None
    
    def AskInput(self, input_style=None):
        if input_style == "terminal":
            return input("$ ")
        return input("> ")
            
        
        

    #? ################  TOOL API #####################

# class ToolAPI:

    # def __init__(self, sdk: dict=None, settings_path: str=None, enable_languages: bool=True):
    #     """Requires sdk{version, name}. Build for ToolOS
        
    #     # OUTDATED - use Api class instead!"""
    #     self.SDK = SDK(sdk)
    #     self.Settings = SettingsAPI(self)
    #     if self.CheckCompatibility(self.Settings.VERSION, self.SDK.SDK_VERSION):
    #         self.Cache = CacheAPI(self.Settings.CACHEPATH)
    #         self.Temp = TempAPI(self.Settings.TEMPPATH)
    #         self.Package = PackageAPI(self.Settings.PACKAGEPATH)
    #         self.Log = LogAPI(self.Settings.LOGPATH)
    #         self.manager = ManagerAPI()
    #         self.helper = HelperAPI(self)
    #         self.language = LanguageAPI(self.Settings, standard_library=self.SDK.SDK_LangLib)
    #         self.state_machine = StateMachineAPI()
    #         self.app = AppAPI(self)

    # def CheckCompatibility(self, api_version, sdk_version: str):
    #     major, minor, patch = sdk_version.split(".")
    #     if major != api_version.split(".")[0]:
    #         raise ValueError(f"Inkompatible Versionen: API {api_version} != SDK {sdk_version}")
    #     return True

    #? ################  Global API #####################
    
class Api:
    def __init__(self, sdk: dict=None, settings_path: str=None, enable_languages: bool=True, settings: dict=None, basepath: str =None, generate_basepath=False):
        """
            ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
            ## ToolAPI's API-SDK. made for general use.
        
            ## Parameters:
            ```python
            sdk: dict = None
            settings_path: str = None
            enable_languages: bool = True
            settings: dict = None
            basepath: str(path) = None
            generate_basepath = False
            ```
            > You can enable generating a own basepath with generate_basepath = True

            # Details\n
            Last Updated: 05.10.25\n
            Version: v3.0.5\n
            Api-Reference: https://pypi.org/project/toolos/\n
            Author: Lilias Hatterscheidt\n
            Copyright © 2025 ClayTechnologie. All rights reserved.\n
            
            
            """
        self.__global__ = []
        self.OwnSettings = settings
        self.IsRunning = True
        
        self.CACHEPATH = None
        self.TEMPPATH = None
        self.PACKAGEPATH = None
        self.LOGPATH = None
        
        self.SDK = SDK(sdk or {
            "version": "3.0.5",
            "name": "ToolOS",
            "settings_path": settings_path or "settings.json",
            "standard_language_library": True
        })
        self.Settings = SettingsAPI(self, settings_path=settings_path if settings_path else None, basepath=basepath, generate_basepath=generate_basepath)
        if not self.SDK.SDK_AVAILABLE:
            settings_path = settings_path
        if self.OwnSettings:
            self.Settings.SetSettings(settings=self.OwnSettings)
            if not self.Settings.USE_SETTINGS_DICT:
                self.CACHEPATH = None
                self.TEMPPATH = None
                self.PACKAGEPATH = None
                self.LOGPATH = None
            
            self.CACHEPATH = self.Settings.Global("CACHEPATH")
            self.TEMPPATH = self.Settings.Global("TEMPPATH")
            self.PACKAGEPATH = self.Settings.Global("PACKAGEPATH")
            self.LOGPATH = self.Settings.Global("LOGPATH")
        
        self.Cache = CacheAPI(self.CACHEPATH)
        self.Sequence = SequenceAPI(self)
        self.Temp = TempAPI(self.TEMPPATH)
        self.Package = PackageAPI(self.PACKAGEPATH)
        self.Log = LogAPI(self.LOGPATH)
        self.Manager = ManagerAPI(self)
        self.Helper = HelperAPI(self)
        self.Language = LanguageAPI(self.Settings, standard_library=self.SDK.SDK_LangLib if not enable_languages else False)
        self.StateMachine = StateMachineAPI(self)
        self.App = AppAPI(self)
        self.Plugin = PluginAPI()
        self.Dev = DeveloperAPI()
        self.Ai = AiAPI()
        self.Memory = MemoryAPI(self)
        self.Event = EventAPI(self)
        self.ModSDK = ModdingSDK(self)
        
        #? #### Built-in Functions
    # This Allowes Minimal LocalStorage / __global__ Data Management
    # Use MemeoryAPI for more Advanced __global__ and __local__ Memory Functions
        
    def New(self, data: dict) -> str:
        """### New(data) \n
        data --dict-->  'your-data' \n
        Creates a dict based entry in LocalStorage with encoding.\n
        It returns a hex-code based string which is the decoding-map key.\n
        You need this key for Acssesing data in LocalStorage.\n
        Always use the returned object[decodingkey] as parametr 'id' like:
        
        --------------------------------
        ```python
        Collect(id=object[decodingkey], ...)
        Insert(id=object[decodingkey], ...)
        ...
        ```
        Your **object[decodingkey]** can be:
        ```python
        variablewithkey = New({'text': 'hello'})}
        ```
        ### the "variablewithkey" holds the decoding-map key
        
        ----------
        nice-trick:      / using a decodeobject/ \n
        >> You can construct the object[decodingkey] with the Constructor. \n
        >> For This do: **'from toolos import DecodeObjectConstructor as DBC'** \n
        ```python
        mykey = New({'text': 'hello'})}
        decodeobject = DBC(mykey, self) 
        # The decodeobject now has features you can check:
        decodeobject.setName('Text Key')
        decodeobject.Key() # --> Returns decoding-flow 
        decodeobject.FreezeLock()
        decodeobject.forceGlobalKey()
        decodeobject.setFlagPolicy()
        decodeobject.Pair()
        decodeobject._destroyObject()
        ...
        
        ```
        
        
        """
        import secrets
        id = secrets.token_hex(16)
        memory = {'id': id, 'const': data}
        memory_json = json.dumps(memory).encode('utf-8')
        key_int = int(id, 16)
        encrypted = self.aes_gcm_encrypt(memory_json, key_int)
        self.Manager.LocalStorage.append(encrypted)
        return id

    def Delete(self, id: str):
        """Destroy stored_Object in LocalStorage"""
        for i, package in enumerate(self.Manager.LocalStorage):
            try:
                decrypted = self.aes_gcm_decrypt(package, int(id, 16))
                memory = json.loads(decrypted.decode('utf-8'))
            except Exception:
                continue
            if memory.get('id') == id:
                del self.Manager.LocalStorage[i]
                return True
        return False

    def Collect(self, id: str, forcekey: bool=False, key: str = None):
        """
        Collecting Data from LocalStorage with id decoding
        > Request(**object[decodingkey]**) -> LocalStorage -> decoding(**objetkt[decodingkey]**) -> return objekt[data]
        """
        import json
        self.forcekey = forcekey
        for package in self.Manager.LocalStorage:
            try:
                decrypted = self.aes_gcm_decrypt(package, int(id, 16))
                memory = json.loads(decrypted.decode('utf-8'))
            except Exception:
                continue
            if memory.get('id') == id:
                if not self.forcekey:
                    return memory.get('const')
                else:
                    return memory.get('const').get(key)
        return None

    def Insert(self, id: str, name: str):
        """
        Inserts Stored Object to a GlobalAcsessable Object
        > [stored_Object] -> encoding -> MemoryAPI > MEMORY
        """
        import json
        for i, package in enumerate(self.Manager.LocalStorage):
            try:
                decrypted = self.aes_gcm_decrypt(package, int(id, 16))
                memory = json.loads(decrypted.decode('utf-8'))
            except Exception:
                continue
            if memory.get('id') == id:
                self.Memory.KnowThis(name, memory.get('const'))
                del self.Manager.LocalStorage[i]
                return True
        return False
    
    def Fork(self, id, fork: dict):
        """Update Infos in stored_Object with the object[decodingkey]
        **UNCOMPLETE FUNCTION, DO NOT USE**
        """
        keyname = fork.get('keyword', None)
        newvar = fork.get('key', None)
        for i, package in enumerate(self.Manager.LocalStorage):
            try:
                decrypted = self.aes_gcm_decrypt(package, int(id, 16))
                memory = json.loads(decrypted.decode('utf-8'))
            except Exception:
                continue
            if memory.get('id') == id:
                pass
                
            
            
            
    def UpdateAPI(self, no_setting: bool=False, no_memory: bool=False):
        """Updates All API's
        > This means calling all update() func """
        if not no_setting: self.Settings.Update()
        if not no_memory: self.Memory.Update()
        


    def derive_key_from_int(self, key_int: int) -> bytes:
        return hashlib.sha256(str(key_int).encode()).digest()

    def aes_gcm_encrypt(self, plaintext: bytes, key_int: int):
        key = self.derive_key_from_int(key_int)
        nonce = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        return nonce + tag + ciphertext

    def aes_gcm_decrypt(self, package: bytes, key_int: int):
        key = self.derive_key_from_int(key_int)
        nonce = package[:12]
        tag = package[12:28]
        ciphertext = package[28:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

         
    def Quit(self, enable_animation: bool=True, sleep_time_per_step: list=[1, 1, 0.4], steps: list=['shutdown engines...', 'shutdown Memory...', 'Finishing Work']):

        if enable_animation:
            anim = []
            sleeps = sleep_time_per_step
            steps = steps
            cout = 0
            if len(sleeps) == len(steps):
                for i in steps:
                    step = i
                    for i in sleeps:
                        sleep = i
                    anim.append({
                        'cout': cout, 'step': step, 'sleep': sleep
                    })
                    cout += 1
            for steps in anim:
                import time
                print(steps.get('step'))
                time.sleep(steps.get('sleep'))

            exit(0)
        else:
            exit(0)
        
        
        
    #? ################  SDK #####################


class SDK:

    def __init__(self, sdk: dict):
        """ToolAPI's SDK. made for developers."""
        try:
            self.SDK = sdk
            self.SDK_VERSION = sdk.get("version", "2.4.7")
            self.SDK_SETTINGS = sdk.get("settings_path")
            self.SDK_NAME = sdk.get("name")
            self.SDK_LangLib = sdk.get("standard_language_library")
            self.SDK_AVAILABLE = True
            self.SDK_SOURCETAR = self.GetSDKSuperManifest()
        except Exception:
                self.SDK_AVAILABLE = False
                
    def GetSDKSuperManifest(self):
        import secrets
        import hashlib
        token = secrets.token_hex(16)  # Generate 32 hex chars
        return hashlib.sha256(token.encode()).hexdigest()





    #? ################  Drivers #####################
    
    
import asyncio
import websockets
import json
import secrets

class ServerDriver:
    def __init__(self, driver):
        self.driver = driver
        self.host = "0.0.0.0"
        self.port = 8080
        self.clients = {}
        self.rooms = {}
        self.data_store = {}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def handleConnection(self, websocket, path):
        clientId = secrets.token_hex(8)
        self.clients[clientId] = {
            "socket": websocket,
            "room": None,
            "data": {}
        }
        
        try:
            async for message in websocket:
                data = json.loads(message)
                response = await self.handleMessage(clientId, data)
                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            await self.handleDisconnect(clientId)
            
    async def handleMessage(self, clientId, data):
        command = data.get("command")
        payload = data.get("payload", {})
        
        if command == "join_room":
            return await self.joinRoom(clientId, payload.get("room"))
        elif command == "leave_room":
            return await self.leaveRoom(clientId)
        elif command == "store_data":
            return await self.storeData(clientId, payload.get("key"), payload.get("value"))
        elif command == "get_data":
            return await self.getData(clientId, payload.get("key"))
        elif command == "broadcast":
            return await self.broadcast(clientId, payload.get("message"))
        return {"error": "Unknown command"}

    async def joinRoom(self, clientId, room):
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(clientId)
        self.clients[clientId]["room"] = room
        return {"status": "joined", "room": room}

    async def leaveRoom(self, clientId):
        room = self.clients[clientId]["room"]
        if room and room in self.rooms:
            self.rooms[room].remove(clientId)
            if not self.rooms[room]:
                del self.rooms[room]
        self.clients[clientId]["room"] = None
        return {"status": "left"}

    async def storeData(self, clientId, key, value):
        if key:
            self.data_store[key] = {
                "value": value,
                "owner": clientId,
                "timestamp": asyncio.get_event_loop().time()
            }
            return {"status": "stored", "key": key}
        return {"error": "Invalid key"}

    async def getData(self, clientId, key):
        data = self.data_store.get(key)
        if data:
            return {"status": "success", "data": data["value"]}
        return {"error": "Data not found"}

    async def broadcast(self, clientId, message):
        room = self.clients[clientId]["room"]
        if room and room in self.rooms:
            for cid in self.rooms[room]:
                if cid != clientId:
                    try:
                        await self.clients[cid]["socket"].send(
                            json.dumps({
                                "type": "broadcast",
                                "from": clientId,
                                "message": message
                            })
                        )
                    except:
                        continue
            return {"status": "broadcasted"}
        return {"error": "Not in a room"}

    async def handleDisconnect(self, clientId):
        await self.leaveRoom(clientId)
        if clientId in self.clients:
            del self.clients[clientId]

    def getAddress(self):
        return (self.host, self.port)

    def start(self):
        server = websockets.serve(
            self.handleConnection,
            self.host,
            self.port
        )
        self.loop.run_until_complete(server)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        tasks = asyncio.all_tasks(self.loop)
        for task in tasks:
            task.cancel()
        self.loop.stop()
        self.loop.close()

        #?  ################  MAIN DRIVER #####################
        
class Driver(Api):
    
    def __init__(self, sdk = None, settings_path = None, enable_languages = True, settings = None):
        super().__init__(sdk, settings_path, enable_languages, settings)
        self.Server = ServerDriver(self)
        

# def test():
#     """Test function for basic API functionality"""
#     try:
#         app = Api(settings={
#             "language": "de",
#             "CACHEPATH": "./cache",
#             "TEMPPATH": "./temp",
#             "PACKAGEPATH": "./packages",
#             "LOGPATH": "./logs"
#         })
        
#         # Test state machine
#         if app.StateMachine.sIsState(app.StateMachine.StateType.FIRST_ENTRY.value):
#             print("First Entry State")
        
#         # Test memory system
#         key = app.New({
#             'item': '*'
#         })
#         print('Generated key:', key)
#         print('Collected data:', app.Collect(key))
#         print('Local storage length:', len(app.Manager.LocalStorage))
        
#         # Test memory API
#         app.Memory.KnowThis("test_data", {"value": 42, "status": "active"})
#         remembered = app.Memory.Remember("test_data")
#         print('Memory test:', remembered)
        
#         # Test backend status
#         backend_status = app.Memory.get_backend_status()
#         print('Backend status:', backend_status)
        
#         print("All tests completed successfully!")
        
#     except ImportError as e:
#         print(f"Import error: {e}")
#     except Exception as e:
#         print(f"Test error: {e}")
#         import traceback
#         traceback.print_exc()

# def test_comprehensive_appdata_system():
#     """
#     Vollständiger Test für das erweiterte SystemAppDataAPI-System
#     Testet alle Funktionen: SQL, Cache, Temp, Memory, Settings
#     """
#     print("=== COMPREHENSIVE APPDATA SYSTEM TEST ===")
    
#     # Initialisiere API
#     appdata = SystemAppDataAPI()
    
#     # Test 1: Konfiguration mit Funktionen
#     print("\n1. Testing function-based configuration...")
#     assert appdata.setName("TestApp") == True
#     assert appdata.setVersion("2.0.0") == True
#     assert appdata.setMaxCacheSize(50) == True
#     assert appdata.setTempFileMaxAge(2) == True
#     assert appdata.enableCompression(True) == True
#     assert appdata.enableEncryption(False) == True
#     print("✓ Configuration functions working")
    
#     # Test 2: System-Initialisierung
#     print("\n2. Testing system initialization...")
#     assert appdata.initialize() == True
#     assert appdata.isInitialized() == True
#     print("✓ System initialized successfully")
#     print(f"  AppData Path: {appdata.getPath('appdata')}")
#     print(f"  Database Path: {appdata.getPath('database')}")
    
#     # Test 3: Schema-Management
#     print("\n3. Testing schema management...")
#     test_schema = {
#         "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
#         "name": "TEXT NOT NULL",
#         "data": "TEXT",
#         "timestamp": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
#     }
#     assert appdata.addSchema("test_table", test_schema) == True
#     assert "test_table" in appdata.listSchemas()
#     print("✓ Schema management working")
    
#     # Test 4: SQL-Operationen
#     print("\n4. Testing SQL operations...")
    
#     # Insert
#     test_data = {"name": "TestUser", "data": "Sample data"}
#     assert appdata.sqlInsert("test_table", test_data) == True
#     print("✓ SQL Insert working")
    
#     # Select
#     results = appdata.sqlSelect("test_table", {"name": "TestUser"})
#     assert len(results) > 0
#     assert results[0]["name"] == "TestUser"
#     print("✓ SQL Select working")
    
#     # Update
#     assert appdata.sqlUpdate("test_table", {"data": "Updated data"}, {"name": "TestUser"}) == True
#     updated_results = appdata.sqlSelect("test_table", {"name": "TestUser"})
#     assert updated_results[0]["data"] == "Updated data"
#     print("✓ SQL Update working")
    
#     # Test 5: Cache-System
#     print("\n5. Testing cache system...")
    
#     # Cache mit verschiedenen Datentypen
#     assert appdata.setCacheData("string_test", "Hello World") == True
#     assert appdata.setCacheData("dict_test", {"key": "value", "number": 42}) == True
#     assert appdata.setCacheData("list_test", [1, 2, 3, "test"]) == True
#     assert appdata.setCacheData("temp_cache", "expires soon", 2) == True  # Expires in 2 seconds
    
#     # Cache lesen
#     assert appdata.getCacheData("string_test") == "Hello World"
#     dict_result = appdata.getCacheData("dict_test")
#     assert dict_result["key"] == "value"
#     assert dict_result["number"] == 42
#     assert appdata.getCacheData("list_test") == [1, 2, 3, "test"]
#     print("✓ Cache operations working")
    
#     # Cache-Statistiken
#     stats = appdata.getCacheStats()
#     print(f"  Cache Stats: {stats['hits']} hits, {stats['misses']} misses")
    
#     # Test 6: Memory-Storage
#     print("\n6. Testing memory storage...")
    
#     # Verschiedene Namespaces
#     assert appdata.storeMemoryData("app", "theme", "dark") == True
#     assert appdata.storeMemoryData("app", "language", "de") == True
#     assert appdata.storeMemoryData("user", "preferences", {"notifications": True, "sound": False}) == True
#     assert appdata.storeMemoryData("game", "score", 12500) == True
    
#     # Memory lesen
#     assert appdata.getMemoryData("app", "theme") == "dark"
#     prefs = appdata.getMemoryData("user", "preferences")
#     assert prefs["notifications"] == True
#     assert appdata.getMemoryData("game", "score") == 12500
    
#     # Alle Daten eines Namespace
#     app_data = appdata.getMemoryData("app")
#     assert "theme" in app_data
#     assert "language" in app_data
    
#     # Namespaces auflisten
#     namespaces = appdata.listMemoryNamespaces()
#     assert "app" in namespaces
#     assert "user" in namespaces
#     assert "game" in namespaces
#     print("✓ Memory storage working")
    
#     # Test 7: Temporäre Dateien
#     print("\n7. Testing temporary files...")
    
#     # Erstelle temporäre Dateien
#     assert appdata.createTempFile("test.txt", "This is a test file", 1) == True
#     assert appdata.createTempFile("data.json", '{"test": true}', 2) == True
#     assert appdata.createTempFile("binary.dat", b"Binary data here") == True
    
#     # Lese temporäre Dateien
#     content = appdata.readTempFile("test.txt")
#     assert content == "This is a test file"
    
#     json_content = appdata.readTempFile("data.json")
#     assert '{"test": true}' in json_content
    
#     binary_content = appdata.readTempFile("binary.dat")
#     # Binary content kann als bytes oder string zurückkommen, hauptsache der Inhalt stimmt
#     if isinstance(binary_content, bytes):
#         assert binary_content == b"Binary data here"
#     else:
#         assert "Binary data here" in str(binary_content)
    
#     # Liste temporäre Dateien
#     temp_files = appdata.listTempFiles()
#     assert len(temp_files) >= 3
#     print("✓ Temporary files working")
    
#     # Test 8: Einstellungen
#     print("\n8. Testing settings system...")
    
#     # Verschiedene Einstellungstypen
#     assert appdata.storeSetting("window_width", 1920, "ui") == True
#     assert appdata.storeSetting("window_height", 1080, "ui") == True
#     assert appdata.storeSetting("debug_mode", True, "system") == True
#     assert appdata.storeSetting("user_config", {"theme": "dark", "lang": "de"}, "user") == True
    
#     # Einstellungen lesen
#     assert appdata.getSetting("window_width") == 1920
#     assert appdata.getSetting("debug_mode") == True
#     user_config = appdata.getSetting("user_config")
#     assert user_config["theme"] == "dark"
    
#     # Einstellungen nach Kategorie
#     ui_settings = appdata.listSettings("ui")
#     assert "window_width" in ui_settings
#     assert "window_height" in ui_settings
#     print("✓ Settings system working")
    
#     # Test 9: Erweiterte SQL-Abfragen
#     print("\n9. Testing advanced SQL operations...")
    
#     # Benutzerdaten hinzufügen
#     user_data = {
#         "username": "testuser",
#         "email": "test@example.com",
#         "preferences": '{"theme": "dark", "notifications": true}'
#     }
#     assert appdata.sqlInsert("user_data", user_data) == True
    
#     # Komplexe Abfrage
#     users = appdata.sqlExecute("SELECT * FROM user_data WHERE username LIKE ?", ["%test%"])
#     assert len(users) > 0
#     assert users[0]["username"] == "testuser"
#     print("✓ Advanced SQL operations working")
    
#     # Test 10: Storage-Informationen
#     print("\n10. Testing storage information...")
#     storage_info = appdata.getStorageInfo()
#     assert "appdata_path" in storage_info
#     assert "database_size_bytes" in storage_info
#     assert "cache_stats" in storage_info
#     assert "total_size_bytes" in storage_info
    
#     print(f"  Total Storage: {storage_info['total_size_bytes'] / 1024:.2f} KB")
#     print(f"  Cache Entries: {storage_info['cache_stats']['entries_count']}")
#     print(f"  Memory Namespaces: {len(storage_info['memory_namespaces'])}")
#     print("✓ Storage information working")
    
#     # Test 11: Backup & Restore
#     print("\n11. Testing backup and restore...")
#     backup_path = appdata.backup()
#     assert backup_path is not None
#     assert os.path.exists(backup_path)
#     print(f"  Backup created: {os.path.basename(backup_path)}")
#     print("✓ Backup system working")
    
#     # Test 12: Cleanup & Optimierung
#     print("\n12. Testing cleanup and optimization...")
    
#     # Warte kurz für Cache-Ablauf
#     print("  Waiting for cache expiration...")
#     time.sleep(3)
    
#     # Prüfe abgelaufenen Cache
#     expired_cache = appdata.getCacheData("temp_cache")
#     assert expired_cache is None  # Sollte abgelaufen sein
    
#     # Cleanup temporärer Dateien
#     cleaned_files = appdata.cleanupExpiredTempFiles()
#     print(f"  Cleaned {cleaned_files} expired temp files")
    
#     # Optimiere Datenbank
#     assert appdata.optimize() == True
#     print("✓ Cleanup and optimization working")
    
#     # Test 13: Schema-Validierung
#     print("\n13. Testing schema validation...")
    
#     # Gültige Daten
#     valid_data = {"username": "validuser", "email": "valid@test.com"}
#     assert appdata.validateSchema("user_data", valid_data) == True
    
#     # Test mit aktivierter Validierung
#     assert appdata.setConfig("schema_validation", True) == True
#     assert appdata.sqlInsert("user_data", valid_data) == True
#     print("✓ Schema validation working")
    
#     # Finaler Status
#     print("\n=== FINAL SYSTEM STATUS ===")
#     final_stats = appdata.getCacheStats()
#     final_info = appdata.getStorageInfo()
    
#     print(f"Cache Performance: {final_stats['hits']} hits / {final_stats['misses']} misses")
#     print(f"Memory Namespaces: {len(appdata.listMemoryNamespaces())}")
#     print(f"Available Schemas: {len(appdata.listSchemas())}")
#     print(f"Total System Size: {final_info['total_size_bytes'] / 1024:.2f} KB")
#     print(f"Configuration: {appdata.getConfig()}")
    
#     # System schließen
#     assert appdata.close() == True
#     assert appdata.isInitialized() == False
    
#     print("\n🎉 ALL TESTS PASSED! Comprehensive AppData System is fully functional!")
#     return True
        
# if __name__ == "__main__":
#     # Führe beide Tests aus
#     print("Running basic API test...")
#     test()
    
#     print("\n" + "="*80 + "\n")
    
#     print("Running comprehensive AppData system test...")
#     test_comprehensive_appdata_system()  