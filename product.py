import pygame 
import sys
import json
import os
from datetime import datetime
import itertools
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
from tkinter import filedialog

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (240, 240, 240)
DARK_GRAY = (60, 60, 60)
GREEN = (50, 200, 50)
GRID_COLOR = (230, 230, 230)  # Light gray for grid
CANVAS_COLOR = (252, 252, 252)  # Slightly off-white for better contrast
SIDEBAR_COLOR = (245, 245, 248)  # Slight blue tint for sidebar
COMPONENT_BG = (255, 255, 255)  # White background for components
WIRE_HOVER_COLOR = (100, 180, 255)  # Light blue for wire hover

# Button colors
BUTTON_COLOR = BLUE
BUTTON_HOVER_COLOR = (80, 170, 255)
BUTTON_TEXT_COLOR = WHITE

# Window dimensions
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800  # Add minimum window dimensions
MIN_WINDOW_HEIGHT = 600
SIDEBAR_WIDTH = 200
SIDEBAR_X = WINDOW_WIDTH - SIDEBAR_WIDTH + 50

# Component dimensions
COMPONENT_WIDTH = 80
COMPONENT_HEIGHT = 50
GATE_RADIUS = 5

# Add new constants
BUTTON_WIDTH = 90
BUTTON_HEIGHT = 35
SAVE_BUTTON_POS = (WINDOW_WIDTH - SIDEBAR_WIDTH + 10, WINDOW_HEIGHT - 70)
LOAD_BUTTON_POS = (WINDOW_WIDTH - SIDEBAR_WIDTH + 100, WINDOW_HEIGHT - 70)
TRUTH_TABLE_BUTTON_POS = (WINDOW_WIDTH - SIDEBAR_WIDTH + 55, WINDOW_HEIGHT - 110)
CIRCUITS_DIR = "saved_circuits"
GRID_SIZE = 20  # Size of grid squares
GRID_OPACITY = 128  # Grid line opacity (0-255)
COMPONENT_SHADOW_OFFSET = 3  # Pixels for component shadow effect

# Add new constants for undo/redo buttons
UNDO_BUTTON_POS = (WINDOW_WIDTH - SIDEBAR_WIDTH - 100, 10)
REDO_BUTTON_POS = (WINDOW_WIDTH - SIDEBAR_WIDTH - 50, 10)
MAX_HISTORY = 50  # Maximum number of states to keep in history

# Add new constant for trash button position
TRASH_BUTTON_POS = (10, WINDOW_HEIGHT - 50)  # Bottom left position

# Add new constant for expression button position
EXPRESSION_TO_CIRCUIT_POS = (10, 10)

# Add new constant for instructions button position
INSTRUCTIONS_BUTTON_POS = (10, 60)  # Below the expression button


class Component:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - COMPONENT_WIDTH//2, y - COMPONENT_HEIGHT//2, 
                              COMPONENT_WIDTH, COMPONENT_HEIGHT)
        self.inputs = []
        self.output = False
        self.max_inputs = 2
        
    def create_copy(self):
        return self.__class__(self.rect.centerx, self.rect.centery)
        
    def update(self):
        pass
        
    def get_input_pos(self):
        return (self.rect.left, self.rect.centery)
        
    def get_output_pos(self):
        return (self.rect.right, self.rect.centery)
        
    def draw(self, screen):
        # Draw shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += COMPONENT_SHADOW_OFFSET
        shadow_rect.y += COMPONENT_SHADOW_OFFSET
        pygame.draw.rect(screen, (200, 200, 200), shadow_rect, border_radius=GATE_RADIUS)
        
        # Draw component background with gradient effect
        pygame.draw.rect(screen, COMPONENT_BG, self.rect, border_radius=GATE_RADIUS)
        gradient_rect = self.rect.copy()
        gradient_rect.height = self.rect.height // 2
        pygame.draw.rect(screen, (245, 245, 245), gradient_rect, border_radius=GATE_RADIUS)
        
        # Draw border
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=GATE_RADIUS)
        
        # Draw connection points with subtle shadow
        for pos in [self.get_input_pos(), self.get_output_pos()]:
            pygame.draw.circle(screen, (200, 200, 200), (pos[0]+1, pos[1]+1), 5)
            pygame.draw.circle(screen, BLACK, pos, 4)
            pygame.draw.circle(screen, WHITE, pos, 3)

class Input(Component):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.state = False
        self.last_click_time = 0
        self.label = None  # For storing the label (either A,B,C or Input 1,2,3)
        
    def toggle(self):
        self.state = not self.state
        self.output = self.state
        
    def update(self):
        self.output = self.state
        
    def draw(self, screen):
        super().draw(screen)
        if self.state:
            color = GREEN
        else:
            color = RED
        pygame.draw.circle(screen, color, self.rect.center, 15)
        pygame.draw.circle(screen, BLACK, self.rect.center, 15, 2)
        
        # Draw toggle instruction
        toggle_text = pygame.font.SysFont("arial", 14).render("(click to toggle)", True, DARK_GRAY)
        screen.blit(toggle_text, (self.rect.centerx - toggle_text.get_width()//2, 
                          self.rect.bottom + 5))
        
        # Draw input label
        if self.label:
            label_font = pygame.font.SysFont("arial", 16, bold=True)
            label_text = label_font.render(self.label, True, DARK_GRAY)
            # Draw label below the toggle instruction
            screen.blit(label_text, (self.rect.centerx - label_text.get_width()//2,
                                   self.rect.bottom + toggle_text.get_height() + 10))

class Output(Component):
    def __init__(self, x, y):
        super().__init__(x, y)
        
    def update(self):
        self.output = any(wire.start.output for wire in self.inputs)
        
    def draw(self, screen):
        super().draw(screen)
        if self.output:
            color = GREEN
        else:
            color = RED
        pygame.draw.circle(screen, color, self.rect.center, 18)
        pygame.draw.circle(screen, BLACK, self.rect.center, 18, 2)
        
        # Add "OUTPUT" label below the component
        font = pygame.font.SysFont("arial", 14, bold=True)
        label = font.render("OUTPUT", True, DARK_GRAY)
        # Position the label below the component
        label_pos = (self.rect.centerx - label.get_width()//2,
                    self.rect.bottom + 5)  # Changed from top to bottom
        
        # Draw label with shadow for better visibility
        shadow = font.render("OUTPUT", True, (200, 200, 200))
        screen.blit(shadow, (label_pos[0]+1, label_pos[1]+1))
        screen.blit(label, label_pos)

class AndGate(Component):
    def update(self):
        self.output = all(wire.start.output for wire in self.inputs) if self.inputs else False
        
    def draw(self, screen):
        super().draw(screen)
        text = pygame.font.SysFont(None, 30).render("AND", True, BLACK)
        screen.blit(text, (self.rect.centerx - text.get_width()//2, 
                          self.rect.centery - text.get_height()//2))

class OrGate(Component):
    def update(self):
        self.output = any(wire.start.output for wire in self.inputs) if self.inputs else False
        
    def draw(self, screen):
        super().draw(screen)
        text = pygame.font.SysFont(None, 30).render("OR", True, BLACK)
        screen.blit(text, (self.rect.centerx - text.get_width()//2, 
                          self.rect.centery - text.get_height()//2))

class NotGate(Component):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_inputs = 1  # NOT gate takes only one input
    
    def update(self):
        self.output = not (self.inputs[0].start.output if self.inputs else True)
        
    def draw(self, screen):
        super().draw(screen)
        text = pygame.font.SysFont(None, 30).render("NOT", True, BLACK)
        screen.blit(text, (self.rect.centerx - text.get_width()//2, 
                          self.rect.centery - text.get_height()//2))

class NandGate(Component):
    def update(self):
        self.output = not all(wire.start.output for wire in self.inputs) if self.inputs else True
        
    def draw(self, screen):
        super().draw(screen)
        text = pygame.font.SysFont(None, 30).render("NAND", True, BLACK)
        screen.blit(text, (self.rect.centerx - text.get_width()//2, 
                          self.rect.centery - text.get_height()//2))

class NorGate(Component):
    def update(self):
        self.output = not any(wire.start.output for wire in self.inputs) if self.inputs else True
        
    def draw(self, screen):
        super().draw(screen)
        text = pygame.font.SysFont(None, 30).render("NOR", True, BLACK)
        screen.blit(text, (self.rect.centerx - text.get_width()//2, 
                          self.rect.centery - text.get_height()//2))

class XorGate(Component):
    def update(self):
        if not self.inputs:
            self.output = False
        else:
            count = sum(1 for wire in self.inputs if wire.start.output)
            self.output = count == 1
        
    def draw(self, screen):
        super().draw(screen)
        text = pygame.font.SysFont(None, 30).render("XOR", True, BLACK)
        screen.blit(text, (self.rect.centerx - text.get_width()//2, 
                          self.rect.centery - text.get_height()//2))

class Wire:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.end.inputs.append(self)
        self.is_hovered = False  # Add hover state
        
    def update(self):
        pass
        
    def is_near_point(self, point, threshold=5):
        """Check if a point is near the wire"""
        start_pos = self.start.get_output_pos()
        end_pos = self.end.get_input_pos()
        
        # Calculate control points for bezier curve
        control1 = (start_pos[0] + (end_pos[0] - start_pos[0]) * 0.4, start_pos[1])
        control2 = (start_pos[0] + (end_pos[0] - start_pos[0]) * 0.6, end_pos[1])
        
        # Check multiple points along the curve
        for t in range(0, 101, 5):  # Check every 5%
            t = t / 100
            x = (1-t)**3 * start_pos[0] + \
                3*(1-t)**2 * t * control1[0] + \
                3*(1-t) * t**2 * control2[0] + \
                t**3 * end_pos[0]
            y = (1-t)**3 * start_pos[1] + \
                3*(1-t)**2 * t * control1[1] + \
                3*(1-t) * t**2 * control2[1] + \
                t**3 * end_pos[1]
            
            # Check distance to point
            distance = ((x - point[0])**2 + (y - point[1])**2)**0.5
            if distance < threshold:
                return True
        return False
        
    def draw(self, screen):
        start_pos = self.start.get_output_pos()
        end_pos = self.end.get_input_pos()
        
        control1 = (start_pos[0] + (end_pos[0] - start_pos[0]) * 0.4, start_pos[1])
        control2 = (start_pos[0] + (end_pos[0] - start_pos[0]) * 0.6, end_pos[1])
        
        points = [start_pos]
        for t in range(1, 100):
            t = t / 100
            x = (1-t)**3 * start_pos[0] + \
                3*(1-t)**2 * t * control1[0] + \
                3*(1-t) * t**2 * control2[0] + \
                t**3 * end_pos[0]
            y = (1-t)**3 * start_pos[1] + \
                3*(1-t)**2 * t * control1[1] + \
                3*(1-t) * t**2 * control2[1] + \
                t**3 * end_pos[1]
            points.append((x, y))
        
        # Draw wire with gradient effect
        color = GREEN if self.start.output else DARK_GRAY
        hover_color = WIRE_HOVER_COLOR if self.is_hovered else color
        
        # Draw shadow first
        shadow_points = [(p[0]+2, p[1]+2) for p in points]
        pygame.draw.lines(screen, (200, 200, 200), False, shadow_points, 3)
        
        # Draw main wire
        pygame.draw.lines(screen, hover_color, False, points, 2)

class Button:
    def __init__(self, x, y, width, height, text, font_size=16, 
                 custom_colors=None):  # Add custom_colors parameter
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        self.enabled = True
        self.font_size = font_size
        # Use custom colors if provided, otherwise use default colors
        self.custom_colors = custom_colors  # (normal_color, hover_color)
        
    def draw(self, screen):
        # Choose colors based on state
        if self.custom_colors:
            normal_color, hover_color = self.custom_colors
        else:
            normal_color, hover_color = BUTTON_COLOR, BUTTON_HOVER_COLOR
            
        if not self.enabled:
            bg_color = (180, 180, 180)  # Disabled gray
            text_color = (120, 120, 120)
        elif self.hovered:
            bg_color = hover_color
            text_color = WHITE
        else:
            bg_color = normal_color
            text_color = WHITE
        
        # Draw button with shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pygame.draw.rect(screen, (100, 100, 100), shadow_rect, border_radius=5)
        
        # Draw main button
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, DARK_GRAY, self.rect, 2, border_radius=5)
        
        # Draw text
        font = pygame.font.SysFont("arial", self.font_size, bold=True)
        text = font.render(self.text, True, text_color)
        screen.blit(text, (self.rect.centerx - text.get_width()//2,
                          self.rect.centery - text.get_height()//2))

class LogicSimulator:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Logic Gate Simulator")
        
        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
        self.clock = pygame.time.Clock()
        self.components = []
        self.sidebar_components = []
        self.wires = []
        self.dragging = None
        self.drawing_wire = False
        self.wire_start = None
        self.double_click_time = 300  # Maximum milliseconds between clicks for double-click
        
        self.init_sidebar()
        
        # Create save directory if it doesn't exist
        if not os.path.exists(CIRCUITS_DIR):
            os.makedirs(CIRCUITS_DIR)
        
        # Add buttons
        self.save_button = Button(SAVE_BUTTON_POS[0], SAVE_BUTTON_POS[1], 
                                BUTTON_WIDTH, BUTTON_HEIGHT, "Save")
        self.load_button = Button(LOAD_BUTTON_POS[0], LOAD_BUTTON_POS[1], 
                                BUTTON_WIDTH, BUTTON_HEIGHT, "Load")
        self.truth_table_button = Button(TRUTH_TABLE_BUTTON_POS[0], TRUTH_TABLE_BUTTON_POS[1], 
                                       BUTTON_WIDTH * 1.5, BUTTON_HEIGHT, "Truth Table")
        self.logic_expr_button = Button(TRUTH_TABLE_BUTTON_POS[0], TRUTH_TABLE_BUTTON_POS[1] - 40,
                                      BUTTON_WIDTH * 1.5, BUTTON_HEIGHT, "Get Expression")

        # Add expression to circuit button
        self.expr_to_circuit_button = Button(EXPRESSION_TO_CIRCUIT_POS[0], EXPRESSION_TO_CIRCUIT_POS[1],
                                           160, 40, "Expression → Circuit", font_size=16,
                                           custom_colors=(BLUE, (80, 170, 255)))

        # Add instructions button
        self.instructions_button = Button(INSTRUCTIONS_BUTTON_POS[0], INSTRUCTIONS_BUTTON_POS[1],
                                       160, 40, "Instructions", font_size=16,
                                       custom_colors=((70, 130, 180), (100, 160, 210)))  # Steel blue colors

        # Define custom file extension
        self.FILE_EXTENSION = ".lcg"  # Logic Circuit Graph
        self.FILE_TYPE = [("Logic Circuit Files", f"*{self.FILE_EXTENSION}")]

        # Add undo/redo history
        self.history = []
        self.current_state = -1
        self.save_state()  # Save initial empty state
        
        # Add undo/redo buttons with labels
        self.undo_button = Button(UNDO_BUTTON_POS[0], UNDO_BUTTON_POS[1], 
                                80, 40, "↶ Undo", font_size=20)  # Made wider for label
        self.redo_button = Button(REDO_BUTTON_POS[0], REDO_BUTTON_POS[1], 
                                80, 40, "↷ Redo", font_size=20)  # Made wider for label

        # Add trash button
        self.trash_button = Button(TRASH_BUTTON_POS[0], TRASH_BUTTON_POS[1], 
                                  50, 50, "Clear", font_size=16, 
                                  custom_colors=(RED, (255, 100, 100)))  # Red button with lighter hover

        self.next_input_number = 1  # Add counter for input numbering

    def init_sidebar(self):
        self.sidebar_spacing = 80  # Make spacing an instance variable
        self.sidebar_start_y = 80  # Increase starting Y to make room for title
        y_pos = self.sidebar_start_y
        
        # Add gates to sidebar
        self.sidebar_components = []  # Clear and recreate sidebar components
        self.sidebar_components.append(AndGate(self.get_sidebar_x(), y_pos))
        y_pos += self.sidebar_spacing
        self.sidebar_components.append(OrGate(self.get_sidebar_x(), y_pos))
        y_pos += self.sidebar_spacing
        self.sidebar_components.append(NotGate(self.get_sidebar_x(), y_pos))
        y_pos += self.sidebar_spacing
        self.sidebar_components.append(NandGate(self.get_sidebar_x(), y_pos))
        y_pos += self.sidebar_spacing
        self.sidebar_components.append(NorGate(self.get_sidebar_x(), y_pos))
        y_pos += self.sidebar_spacing
        self.sidebar_components.append(XorGate(self.get_sidebar_x(), y_pos))
        y_pos += self.sidebar_spacing
        self.sidebar_components.append(Input(self.get_sidebar_x(), y_pos))
        y_pos += self.sidebar_spacing
        self.sidebar_components.append(Output(self.get_sidebar_x(), y_pos))

    def get_sidebar_x(self):
        """Calculate sidebar X position based on current window width"""
        return self.width - SIDEBAR_WIDTH + 50

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                width = max(event.w, MIN_WINDOW_WIDTH)
                height = max(event.h, MIN_WINDOW_HEIGHT)
                self.width = width
                self.height = height
                self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                
                # Update sidebar components positions
                self.update_sidebar_positions()
                
                # Update button positions
                self.update_button_positions()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left click
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        # Shift + Left click for wire drawing
                        for component in self.components:
                            if component.rect.collidepoint(mouse_pos):
                                self.drawing_wire = True
                                self.wire_start = component
                                break
                    elif pygame.key.get_pressed()[pygame.K_LALT]:
                        # Alt + Left click for component duplication
                        for component in self.components:
                            if component.rect.collidepoint(mouse_pos):
                                new_component = component.create_copy()
                                new_component.rect.x += 50  # Offset the copy
                                new_component.rect.y += 50
                                self.components.append(new_component)
                                break
                    else:
                        # Check for double-click on input components
                        current_time = pygame.time.get_ticks()
                        for component in self.components:
                            if isinstance(component, Input) and component.rect.collidepoint(mouse_pos):
                                if current_time - component.last_click_time < self.double_click_time:
                                    component.toggle()
                                component.last_click_time = current_time
                                break
                        
                        # Handle component dragging
                        for component in self.sidebar_components:
                            if component.rect.collidepoint(mouse_pos):
                                new_component = component.create_copy()
                                if isinstance(new_component, Input):
                                    # Label new inputs when created
                                    new_component.label = f"Input {self.next_input_number}"
                                    self.next_input_number += 1
                                elif isinstance(new_component, Output):
                                    if any(isinstance(c, Output) for c in self.components):
                                        continue
                                self.dragging = new_component
                                self.components.append(new_component)
                                break
                        
                        if not self.dragging:
                            for component in self.components:
                                if component.rect.collidepoint(mouse_pos):
                                    self.dragging = component
                                    break
                    
                    # Check buttons
                    if self.save_button.rect.collidepoint(mouse_pos):
                        self.save_circuit()
                    elif self.load_button.rect.collidepoint(mouse_pos):
                        self.load_circuit()
                    elif self.truth_table_button.rect.collidepoint(mouse_pos):
                        self.show_truth_table()
                    elif self.logic_expr_button.rect.collidepoint(mouse_pos):
                        self.show_logic_expression()
                    
                    # Check expression to circuit button
                    if self.expr_to_circuit_button.rect.collidepoint(mouse_pos):
                        self.create_circuit_from_expression()
                    
                    # Check instructions button
                    if self.instructions_button.rect.collidepoint(mouse_pos):
                        self.show_instructions()
                    
                    # Check undo/redo buttons
                    if self.undo_button.rect.collidepoint(mouse_pos):
                        self.undo()
                    elif self.redo_button.rect.collidepoint(mouse_pos):
                        self.redo()
                    
                    # Check trash button
                    if self.trash_button.rect.collidepoint(mouse_pos):
                        self.clear_canvas()
                
                elif event.button == 3:  # Right click
                    # Remove component and connected wires
                    for component in self.components:
                        if component.rect.collidepoint(mouse_pos):
                            self.wires = [w for w in self.wires if w.start != component and w.end != component]
                            self.components.remove(component)
                            self.save_state()  # Save after removing component
                            break

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    if self.dragging:
                        # If dropping a new input component
                        if isinstance(self.dragging, Input) and not any(c is self.dragging for c in self.components):
                            # Assign automatic label (Input 1, Input 2, etc.)
                            self.dragging.label = f"Input {self.next_input_number}"
                            self.next_input_number += 1
                        self.dragging = None
                        self.save_state()
                    elif self.drawing_wire:
                        mouse_pos = pygame.mouse.get_pos()
                        for component in self.components:
                            if component.rect.collidepoint(mouse_pos) and component != self.wire_start:
                                # Check if component can accept more inputs
                                if len(component.inputs) < component.max_inputs:
                                    self.wires.append(Wire(self.wire_start, component))
                                else:
                                    # Show error message
                                    window = tk.Tk()
                                    window.title("Error")
                                    gate_type = component.__class__.__name__
                                    max_inputs = "one" if component.max_inputs == 1 else "two"
                                    label = tk.Label(window, 
                                                   text=f"{gate_type} gate can only accept {max_inputs} input{'s' if max_inputs != 'one' else ''}!")
                                    label.pack(padx=20, pady=20)
                                    window.after(2000, window.destroy)
                                    window.mainloop()
                                break
                        self.drawing_wire = False
                        self.wire_start = None
                        self.save_state()  # Save after creating wire
                    self.dragging = None

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.dragging.rect.center = pygame.mouse.get_pos()

            elif event.type == pygame.KEYDOWN:
                # Get modifier keys state
                ctrl_pressed = pygame.key.get_mods() & pygame.KMOD_CTRL
                shift_pressed = pygame.key.get_mods() & pygame.KMOD_SHIFT
                alt_pressed = pygame.key.get_mods() & pygame.KMOD_ALT

                # Undo/Redo shortcuts
                if event.key == pygame.K_z and ctrl_pressed:
                    if shift_pressed:
                        self.redo()  # Ctrl+Shift+Z for redo
                    else:
                        self.undo()  # Ctrl+Z for undo

                # Save/Load shortcuts
                elif event.key == pygame.K_s and ctrl_pressed:
                    self.save_circuit()  # Ctrl+S for save
                elif event.key == pygame.K_o and ctrl_pressed:
                    self.load_circuit()  # Ctrl+O for open/load

                # Delete selected component
                elif event.key == pygame.K_DELETE:
                    if self.dragging:
                        self.components.remove(self.dragging)
                        self.wires = [w for w in self.wires if w.start != self.dragging and w.end != self.dragging]
                        self.dragging = None
                        self.save_state()

                # Clear canvas shortcut
                elif event.key == pygame.K_n and ctrl_pressed:
                    if shift_pressed:  # Ctrl+Shift+N for new circuit
                        self.clear_canvas()

                # Toggle input states with number keys
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                    # Convert key to input index (1-5)
                    input_num = event.key - pygame.K_1
                    # Find and toggle corresponding input
                    input_components = [c for c in self.components if isinstance(c, Input)]
                    if input_num < len(input_components):
                        input_components[input_num].toggle()

                # Show truth table with T
                elif event.key == pygame.K_t and ctrl_pressed:
                    self.show_truth_table()

                # Show logic expression with E
                elif event.key == pygame.K_e and ctrl_pressed:
                    self.show_logic_expression()

                # Escape key to cancel operations
                elif event.key == pygame.K_ESCAPE:
                    if self.drawing_wire:
                        self.drawing_wire = False
                        self.wire_start = None
                    if self.dragging:
                        self.dragging = None

    def update(self):
        # Update all components
        for component in self.components:
            if isinstance(component, Input):
                component.update()
        
        # Update wire hover states
        mouse_pos = pygame.mouse.get_pos()
        for wire in self.wires:
            wire.is_hovered = wire.is_near_point(mouse_pos)
        
        # Propagate signals through wires and update gates
        for wire in self.wires:
            wire.update()
        
        for component in self.components:
            if not isinstance(component, Input):
                component.update()

    def draw(self):
        # Fill background
        self.screen.fill(CANVAS_COLOR)
        
        # Draw grid
        self.draw_grid()
        
        # Draw sidebar with gradient effect
        sidebar_rect = pygame.Rect(self.width - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, self.height)
        gradient = pygame.Surface((SIDEBAR_WIDTH, self.height), pygame.SRCALPHA)
        for i in range(self.height):
            alpha = int(255 * (1 - i/self.height * 0.1))  # Subtle gradient
            pygame.draw.line(gradient, (*SIDEBAR_COLOR, alpha), 
                           (0, i), (SIDEBAR_WIDTH, i))
        self.screen.blit(gradient, sidebar_rect)
        
        # Draw sidebar border with shadow
        pygame.draw.line(self.screen, (200, 200, 200), 
                        (self.width - SIDEBAR_WIDTH + 2, 0),
                        (self.width - SIDEBAR_WIDTH + 2, self.height), 2)
        pygame.draw.line(self.screen, GRAY, 
                        (self.width - SIDEBAR_WIDTH, 0),
                        (self.width - SIDEBAR_WIDTH, self.height), 2)
        
        # Draw title with shadow effect
        font = pygame.font.SysFont("arial", 24, bold=True)
        title_shadow = font.render("Logic Gates", True, (150, 150, 150))
        title = font.render("Logic Gates", True, DARK_GRAY)
        title_x = self.width - SIDEBAR_WIDTH + 10
        title_y = 20
        self.screen.blit(title_shadow, (title_x+1, title_y+1))
        self.screen.blit(title, (title_x, title_y))
        
        # Draw separator with gradient
        separator_y = self.sidebar_start_y - 20
        gradient_width = SIDEBAR_WIDTH - 10
        for i in range(gradient_width):
            alpha = int(255 * (1 - abs(i - gradient_width/2)/(gradient_width/2)))
            pygame.draw.line(self.screen, (*GRAY, alpha),
                           (self.width - SIDEBAR_WIDTH + 5 + i, separator_y),
                           (self.width - SIDEBAR_WIDTH + 5 + i, separator_y), 1)
        
        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()
        self.save_button.hovered = self.save_button.rect.collidepoint(mouse_pos)
        self.load_button.hovered = self.load_button.rect.collidepoint(mouse_pos)
        self.truth_table_button.hovered = self.truth_table_button.rect.collidepoint(mouse_pos)
        self.logic_expr_button.hovered = self.logic_expr_button.rect.collidepoint(mouse_pos)
        
        # Update undo/redo button positions and states
        self.undo_button.rect.x = self.width - SIDEBAR_WIDTH - 180  # Adjusted for wider buttons
        self.redo_button.rect.x = self.width - SIDEBAR_WIDTH - 90
        
        # Update hover states
        self.undo_button.hovered = self.undo_button.rect.collidepoint(mouse_pos)
        self.redo_button.hovered = self.redo_button.rect.collidepoint(mouse_pos)
        
        # Draw components
        for component in self.sidebar_components:
            component.draw(self.screen)
        
        for component in self.components:
            component.draw(self.screen)
        
        # Draw wires
        for wire in self.wires:
            wire.draw(self.screen)
        
        # Draw wire being created
        if self.drawing_wire:
            start_pos = self.wire_start.get_output_pos()
            mouse_pos = pygame.mouse.get_pos()
            
            control1 = (start_pos[0] + (mouse_pos[0] - start_pos[0]) * 0.4, start_pos[1])
            control2 = (start_pos[0] + (mouse_pos[0] - start_pos[0]) * 0.6, mouse_pos[1])
            
            points = [start_pos]
            for t in range(1, 100):
                t = t / 100
                x = (1-t)**3 * start_pos[0] + \
                    3*(1-t)**2 * t * control1[0] + \
                    3*(1-t) * t**2 * control2[0] + \
                    t**3 * mouse_pos[0]
                y = (1-t)**3 * start_pos[1] + \
                    3*(1-t)**2 * t * control1[1] + \
                    3*(1-t) * t**2 * control2[1] + \
                    t**3 * mouse_pos[1]
                points.append((x, y))
            
            pygame.draw.lines(self.screen, BLACK, False, points, 2)
        
        # Draw components with input indicators
        for component in self.components:
            component.draw(self.screen)
            # Draw input count indicator
            if not isinstance(component, (Input, Output)):
                remaining = component.max_inputs - len(component.inputs)
                if remaining > 0:
                    text = pygame.font.SysFont("arial", 12).render(
                        f"Needs {remaining} more input{'s' if remaining > 1 else ''}", 
                        True, DARK_GRAY)
                    self.screen.blit(text, (component.rect.centerx - text.get_width()//2,
                                          component.rect.bottom + 2))
        
        # Draw buttons
        self.save_button.draw(self.screen)
        self.load_button.draw(self.screen)
        self.truth_table_button.draw(self.screen)
        self.logic_expr_button.draw(self.screen)
        
        # Draw expression to circuit button
        self.expr_to_circuit_button.draw(self.screen)
        
        # Draw instructions button
        self.instructions_button.draw(self.screen)
        
        # Draw undo/redo buttons with enabled/disabled states
        self.undo_button.enabled = self.current_state > 0
        self.redo_button.enabled = self.current_state < len(self.history) - 1
        self.undo_button.draw(self.screen)
        self.redo_button.draw(self.screen)
        
        # Draw trash button
        self.trash_button.draw(self.screen)
        
        pygame.display.flip()

    def draw_grid(self):
        """Draw a professional grid background"""
        # Draw major grid lines (darker)
        major_spacing = GRID_SIZE * 5
        for x in range(0, self.width - SIDEBAR_WIDTH, major_spacing):
            pygame.draw.line(self.screen, (*GRID_COLOR, 100), (x, 0), (x, self.height))
        for y in range(0, self.height, major_spacing):
            pygame.draw.line(self.screen, (*GRID_COLOR, 100), (0, y), 
                           (self.width - SIDEBAR_WIDTH, y))
        
        # Draw minor grid lines (lighter)
        for x in range(0, self.width - SIDEBAR_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, (*GRID_COLOR, 50), (x, 0), (x, self.height))
        for y in range(0, self.height, GRID_SIZE):
            pygame.draw.line(self.screen, (*GRID_COLOR, 50), (0, y), 
                           (self.width - SIDEBAR_WIDTH, y))

    def save_circuit(self):
        try:
            # Create circuit data
            circuit_data = {
                'components': [],
                'wires': [],
                'version': '1.0',  # Add version for compatibility checking
                'app_name': 'Logic Gate Simulator'
            }
            
            # Save components
            for component in self.components:
                comp_data = {
                    'type': component.__class__.__name__,
                    'x': component.rect.centerx,
                    'y': component.rect.centery,
                    'state': component.state if isinstance(component, Input) else None
                }
                circuit_data['components'].append(comp_data)
            
            # Save wires
            for wire in self.wires:
                wire_data = {
                    'start_idx': self.components.index(wire.start),
                    'end_idx': self.components.index(wire.end)
                }
                circuit_data['wires'].append(wire_data)
            
            # Open file dialog for saving
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Generate default filename with timestamp
            default_name = f"circuit_{datetime.now().strftime('%Y%m%d_%H%M%S')}{self.FILE_EXTENSION}"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=self.FILE_EXTENSION,
                filetypes=self.FILE_TYPE,
                initialfile=default_name,
                title="Save Logic Circuit"
            )
            
            if filepath:  # If user didn't cancel
                with open(filepath, 'w') as f:
                    json.dump(circuit_data, f, indent=2)
                
                # Show success message
                messagebox.showinfo("Success", "Circuit saved successfully!") #if the circuit is successful
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving circuit:\n{str(e)}") #error message if the circuit saving fails

    def load_circuit(self):
        try:
            # Open file dialog for loading
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            filepath = filedialog.askopenfilename(
                filetypes=self.FILE_TYPE,
                title="Load Logic Circuit"
            )
            
            if not filepath:  # If user cancelled
                return
                
            with open(filepath, 'r') as f:
                circuit_data = json.load(f)
            
            # Validate file format
            if not self._validate_circuit_file(circuit_data):
                messagebox.showerror("Error", "Invalid circuit file format!")
                return
            
            # Clear current circuit
            self.components = []
            self.wires = []
            
            # Create components
            component_classes = {
                'Input': Input,
                'Output': Output,
                'AndGate': AndGate,
                'OrGate': OrGate,
                'NotGate': NotGate,
                'NandGate': NandGate,
                'NorGate': NorGate,
                'XorGate': XorGate
            }
            
            # Load components
            for comp_data in circuit_data['components']:
                if comp_data['type'] not in component_classes:
                    raise ValueError(f"Unknown component type: {comp_data['type']}")
                    
                component_class = component_classes[comp_data['type']]
                component = component_class(comp_data['x'], comp_data['y'])
                
                if isinstance(component, Input) and comp_data['state'] is not None:
                    component.state = comp_data['state']
                    component.output = comp_data['state']
                
                self.components.append(component)
            
            # Load wires
            for wire_data in circuit_data['wires']:
                start_component = self.components[wire_data['start_idx']]
                end_component = self.components[wire_data['end_idx']]
                self.wires.append(Wire(start_component, end_component))
            
            messagebox.showinfo("Success", "Circuit loaded successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading circuit:\n{str(e)}")

    def _validate_circuit_file(self, data):
        """Validate that the loaded file is a valid circuit file"""
        required_keys = {'components', 'wires', 'version', 'app_name'}
        
        # Check if all required keys exist
        if not all(key in data for key in required_keys):
            return False
            
        # Verify this is our application's file
        if data['app_name'] != 'Logic Gate Simulator':
            return False
            
        # Version check (for future compatibility)
        if not data['version'].startswith('1.'):
            return False
            
        return True

    def generate_truth_table(self):
        # Get all input components and the output component
        input_components = [c for c in self.components if isinstance(c, Input)]
        output_component = next((c for c in self.components if isinstance(c, Output)), None)
        
        if not input_components or not output_component:
            return None
        
        # Generate all possible input combinations
        input_combinations = list(itertools.product([False, True], repeat=len(input_components)))
        truth_table = []
        
        # For each combination, set inputs and get output
        for combination in input_combinations:
            # Set inputs
            for input_comp, value in zip(input_components, combination):
                input_comp.state = value
                input_comp.output = value
            
            # Update circuit
            for wire in self.wires:
                wire.update()
            for component in self.components:
                if not isinstance(component, Input):
                    component.update()
            
            # Record result
            row = list(combination) + [output_component.output]
            truth_table.append(row)
        
        # Reset inputs to their original states
        for input_comp in input_components:
            input_comp.state = False
            input_comp.output = False
        self.update()
        
        return input_components, truth_table

    def show_truth_table(self):
        result = self.generate_truth_table()
        if not result:
            return
        
        input_components, truth_table = result
        
        # Create window
        window = tk.Tk()
        window.title("Truth Table")
        
        # Create treeview
        tree = ttk.Treeview(window)
        tree["columns"] = tuple(f"Input {i+1}" for i in range(len(input_components))) + ("Output",)
        tree["show"] = "headings"
        
        # Set column headings
        for i in range(len(input_components)):
            tree.heading(f"Input {i+1}", text=f"Input {i+1}")
            tree.column(f"Input {i+1}", width=60, anchor="center")
        tree.heading("Output", text="Output")
        tree.column("Output", width=60, anchor="center")
        
        # Add data
        for row in truth_table:
            tree.insert("", "end", values=tuple("1" if x else "0" for x in row))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Center window
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        window.mainloop()

    def create_toolbar(self):
        toolbar = tk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        create_button = tk.Button(toolbar, text="Create Circuit", command=self.create_circuit)
        create_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add new button for logical expression
        logic_expr_button = tk.Button(toolbar, text="Get Logic Expression", command=self.get_logic_expression)
        logic_expr_button.pack(side=tk.LEFT, padx=5, pady=5)

    def get_logic_expression(self):
        if not self.current_circuit:
            messagebox.showwarning("Warning", "Please create a circuit first!")
            return
        
        expression = self.current_circuit.generate_logical_expression()
        messagebox.showinfo("Logical Expression", f"Circuit Expression: {expression}")

    def show_logic_expression(self):
        """Show the logical expression for the current circuit"""
        # Get input components and output component
        input_components = [c for c in self.components if isinstance(c, Input)]
        output_component = next((c for c in self.components if isinstance(c, Output)), None)
        
        if not input_components or not output_component:
            window = tk.Tk()
            window.title("Error")
            label = tk.Label(window, text="Circuit must have at least one input and one output!")
            label.pack(padx=20, pady=20)
            window.after(2000, window.destroy)
            window.mainloop()
            return
            
        # Generate expression by traversing from output to inputs
        expression = self._generate_expression(output_component)
        
        # Show expression in dialog
        window = tk.Tk()
        window.title("Logical Expression")
        label = tk.Label(window, text=f"Circuit Expression:\n{expression}", 
                        font=("Arial", 12), wraplength=300)
        label.pack(padx=20, pady=20)
        
        # Add copy button
        def copy_to_clipboard():
            window.clipboard_clear()
            window.clipboard_append(expression)
            window.update()
        
        copy_btn = tk.Button(window, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_btn.pack(pady=10)
        
        window.mainloop()

    def _generate_expression(self, component):
        """Recursively generate expression for a component"""
        if isinstance(component, Input):
            return f"Input_{self.components.index(component)+1}"
            
        # Get input wires for this component
        input_wires = [w for w in self.wires if w.end == component]
        
        if not input_wires:
            return ""
            
        # Generate expressions for inputs
        input_expressions = [self._generate_expression(w.start) for w in input_wires]
        
        # Combine expressions based on component type
        if isinstance(component, AndGate):
            return f"({' AND '.join(input_expressions)})"
        elif isinstance(component, OrGate):
            return f"({' OR '.join(input_expressions)})"
        elif isinstance(component, NotGate):
            return f"NOT({input_expressions[0]})"
        elif isinstance(component, NandGate):
            return f"NOT({' AND '.join(input_expressions)})"
        elif isinstance(component, NorGate):
            return f"NOT({' OR '.join(input_expressions)})"
        elif isinstance(component, XorGate):
            return f"XOR({', '.join(input_expressions)})"
        else:
            return f"({' '.join(input_expressions)})"

    def update_sidebar_positions(self):
        """Update positions of sidebar components after resize"""
        y_pos = self.sidebar_start_y
        sidebar_x = self.get_sidebar_x()
        
        for component in self.sidebar_components:
            component.rect.centerx = sidebar_x
            component.rect.centery = y_pos
            y_pos += self.sidebar_spacing

    def update_button_positions(self):
        """Update positions of buttons after resize"""
        # Calculate new button positions based on window size
        save_x = self.width - SIDEBAR_WIDTH + 10
        load_x = self.width - SIDEBAR_WIDTH + 100
        button_y = self.height - 70
        
        self.save_button.rect.x = save_x
        self.save_button.rect.y = button_y
        self.load_button.rect.x = load_x
        self.load_button.rect.y = button_y
        
        # Truth table and logic expression buttons
        truth_table_x = self.width - SIDEBAR_WIDTH + 55
        self.truth_table_button.rect.x = truth_table_x
        self.truth_table_button.rect.y = button_y - 40
        
        self.logic_expr_button.rect.x = truth_table_x
        self.logic_expr_button.rect.y = button_y - 80

        # Update trash button position
        self.trash_button.rect.x = 10
        self.trash_button.rect.y = self.height - 50

        # Update expression to circuit button position
        self.expr_to_circuit_button.rect.x = EXPRESSION_TO_CIRCUIT_POS[0]
        self.expr_to_circuit_button.rect.y = EXPRESSION_TO_CIRCUIT_POS[1]

        # Update instructions button position
        self.instructions_button.rect.x = INSTRUCTIONS_BUTTON_POS[0]
        self.instructions_button.rect.y = INSTRUCTIONS_BUTTON_POS[1]

    def save_state(self):
        """Save current circuit state to history"""
        try:
            # Create state data
            state = {
                'components': [(c.__class__.__name__, c.rect.centerx, c.rect.centery, 
                              c.state if isinstance(c, Input) else None) 
                             for c in self.components],
                'wires': [(self.components.index(w.start), self.components.index(w.end)) 
                         for w in self.wires]
            }
            
            # If we're not at the end of history, truncate it
            if self.current_state < len(self.history) - 1:
                self.history = self.history[:self.current_state + 1]
            
            # Add new state
            self.history.append(state)
            self.current_state += 1
            
            # Limit history size
            if len(self.history) > MAX_HISTORY:
                self.history.pop(0)
                self.current_state -= 1
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self, state):
        """Load circuit state from history"""
        try:
            if not state:
                return
                
            self.components = []
            self.wires = []
            max_input_num = 0
            
            # Load components
            component_classes = {
                'Input': Input,
                'Output': Output,
                'AndGate': AndGate,
                'OrGate': OrGate,
                'NotGate': NotGate,
                'NandGate': NandGate,
                'NorGate': NorGate,
                'XorGate': XorGate
            }
            
            for comp_type, x, y, state_val in state['components']:
                component = component_classes[comp_type](x, y)
                if isinstance(component, Input):
                    if state_val is not None:
                        component.state = state_val
                        component.output = state_val
                    # Update max input number for proper numbering
                    if component.label and component.label.startswith("Input "):
                        num = int(component.label.split()[-1])
                        max_input_num = max(max_input_num, num)
                self.components.append(component)
            
            # Update next input number
            self.next_input_number = max_input_num + 1
            
            # Load wires
            for start_idx, end_idx in state['wires']:
                if start_idx < len(self.components) and end_idx < len(self.components):
                    self.wires.append(Wire(self.components[start_idx], self.components[end_idx]))
        except Exception as e:
            print(f"Error loading state: {e}")

    def undo(self):
        """Undo last action"""
        try:
            if self.current_state > 0:
                self.current_state -= 1
                if 0 <= self.current_state < len(self.history):
                    self.load_state(self.history[self.current_state])
        except Exception as e:
            print(f"Error in undo: {e}")

    def redo(self):
        """Redo last undone action"""
        try:
            if self.current_state < len(self.history) - 1:
                self.current_state += 1
                if 0 <= self.current_state < len(self.history):
                    self.load_state(self.history[self.current_state])
        except Exception as e:
            print(f"Error in redo: {e}")

    def clear_canvas(self):
        """Clear all components and wires from the canvas"""
        self.components = []
        self.wires = []
        self.next_input_number = 1  # Reset input numbering when clearing
        self.save_state()

    def create_circuit_from_expression(self):
        """Create circuit from logical expression"""
        # Create input dialog
        root = tk.Tk()
        root.title("Create Circuit from Expression")
        root.geometry("400x200")
        
        # Center the window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Add explanation label
        explanation = """Enter logical expression using:
AND, OR, NOT, NAND, NOR, XOR
Example: (A AND B) OR (NOT C)"""
        label = tk.Label(root, text=explanation, justify=tk.LEFT, padx=20, pady=10)
        label.pack()
        
        # Add entry field
        entry = tk.Entry(root, width=40)
        entry.pack(padx=20, pady=10)
        
        def on_submit():
            expression = entry.get().strip()
            if expression:
                try:
                    self.build_circuit_from_expression(expression)
                    root.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Invalid expression:\n{str(e)}")
            else:
                messagebox.showwarning("Warning", "Please enter an expression")
        
        # Add submit button
        submit_btn = tk.Button(root, text="Create Circuit", command=on_submit)
        submit_btn.pack(pady=10)
        
        root.mainloop()

    def build_circuit_from_expression(self, expression):
        """Parse expression and build corresponding circuit"""
        try:
            # Clear current circuit
            self.components = []
            self.wires = []
            
            # Parse and validate expression
            expression = expression.upper().replace(" ", "")
            if not self._validate_expression(expression):
                raise ValueError("Invalid expression format")
            
            # Build the circuit
            output_component = self._build_expression_circuit(expression)
            if output_component:
                self.arrange_circuit_components()
                self.save_state()
            
        except Exception as e:
            raise ValueError(f"Error building circuit: {str(e)}")

    def _validate_expression(self, expr):
        """Validate expression format"""
        # Basic validation rules
        valid_operators = {'AND', 'OR', 'NOT', 'NAND', 'NOR', 'XOR'}
        parentheses_count = 0
        
        # Check parentheses matching
        for char in expr:
            if char == '(':
                parentheses_count += 1
            elif char == ')':
                parentheses_count -= 1
            if parentheses_count < 0:
                return False
        
        if parentheses_count != 0:
            return False
        
        # Check for valid variables and operators
        tokens = self._tokenize_expression(expr)
        for token in tokens:
            if token not in valid_operators and not token.isalpha() and token not in '()':
                return False
            
        return True

    def _tokenize_expression(self, expr):
        """Split expression into tokens"""
        tokens = []
        current_token = ""
        
        i = 0
        while i < len(expr):
            if expr[i] in '()':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(expr[i])
            elif expr[i].isalpha():
                current_token += expr[i]
            else:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            i += 1
        
        if current_token:
            tokens.append(current_token)
        
        return tokens

    def _build_expression_circuit(self, expression):
        """Recursively build circuit from expression"""
        try:
            # Track created components to avoid duplicates
            self.input_vars = {}
            
            # Build the main circuit
            final_gate = self._build_subcircuit(expression)
            if not final_gate:
                raise ValueError("Failed to build circuit")
            
            # Add output component and connect it
            output = Output(400, 200)
            self.components.append(output)
            self.wires.append(Wire(final_gate, output))
            
            return output
        except Exception as e:
            raise ValueError(f"Error building circuit: {str(e)}")

    def _build_subcircuit(self, expr):
        """Recursively build part of the circuit"""
        if not expr:
            return None
        
        # Remove outer parentheses if they exist
        while expr.startswith('(') and expr.endswith(')'):
            inner = expr[1:-1]
            if self._validate_parentheses(inner):
                expr = inner
            else:
                break
        
        # Handle single variables (inputs)
        if expr.isalpha() and len(expr) == 1:
            if expr not in self.input_vars:
                input_comp = Input(100, 100)
                input_comp.label = expr  # Set the label to the variable name
                self.components.append(input_comp)
                self.input_vars[expr] = input_comp
            return self.input_vars[expr]
        
        # Handle all operators in order of precedence
        operators = [
            ("NAND", NandGate),
            ("NOR", NorGate),
            ("XOR", XorGate),
            ("AND", AndGate),
            ("OR", OrGate)
        ]
        
        for op_str, gate_class in operators:
            if op_str in expr:
                parts = self._split_by_operator(expr, op_str)
                if len(parts) > 1:
                    # For NAND, NOR, XOR: ensure exactly 2 inputs
                    if gate_class in (NandGate, NorGate, XorGate) and len(parts) != 2:
                        raise ValueError(f"{op_str} gate must have exactly 2 inputs")
                    
                    gate = gate_class(300, 200)
                    self.components.append(gate)
                    
                    for part in parts:
                        input_comp = self._build_subcircuit(part.strip())
                        if not input_comp:
                            raise ValueError(f"Invalid part in {op_str} expression: {part}")
                        self.wires.append(Wire(input_comp, gate))
                    
                    return gate
        
        # Handle NOT operation
        if expr.startswith("NOT"):
            remaining = expr[3:].strip()
            if remaining.startswith('('):
                paren_count = 1
                i = 1
                while i < len(remaining) and paren_count > 0:
                    if remaining[i] == '(':
                        paren_count += 1
                    elif remaining[i] == ')':
                        paren_count -= 1
                    i += 1
                inner_expr = remaining[1:i-1]
            else:
                inner_expr = remaining
            
            input_comp = self._build_subcircuit(inner_expr)
            if not input_comp:
                raise ValueError(f"Invalid NOT input: {inner_expr}")
            
            not_gate = NotGate(200, 200)
            self.components.append(not_gate)
            self.wires.append(Wire(input_comp, not_gate))
            return not_gate
        
        raise ValueError(f"Unable to parse expression: {expr}")

    def _validate_parentheses(self, expr):
        """Check if parentheses in expression are properly matched"""
        count = 0
        for char in expr:
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
            if count < 0:
                return False
        return count == 0

    def _split_by_operator(self, expr, operator):
        """Split expression by operator, respecting parentheses"""
        if operator not in expr:
            return [expr]
        
        result = []
        current = ""
        paren_count = 0
        i = 0
        
        while i < len(expr):
            # Check for operator
            if expr[i:i+len(operator)] == operator and paren_count == 0:
                if current.strip():
                    result.append(current.strip())
                current = ""
                i += len(operator)
                continue
            
            # Track parentheses
            if expr[i] == '(':
                paren_count += 1
            elif expr[i] == ')':
                paren_count -= 1
            
            current += expr[i]
            i += 1
        
        if current.strip():
            result.append(current.strip())
        
        return result

    def arrange_circuit_components(self):
        """Arrange components in a logical layout"""
        # Implement level-based arrangement
        levels = self._get_component_levels()
        
        # Arrange components by level
        level_spacing = 150
        component_spacing = 100
        
        for level_num, level_components in enumerate(levels):
            level_width = len(level_components) * component_spacing
            start_x = (self.width - SIDEBAR_WIDTH - level_width) // 2
            
            for i, component in enumerate(level_components):
                component.rect.centerx = start_x + i * component_spacing
                component.rect.centery = 100 + level_num * level_spacing

    def _get_component_levels(self):
        """Get components arranged in levels based on dependencies"""
        levels = []
        processed = set()
        
        # First level: Input components
        current_level = [c for c in self.components if isinstance(c, Input)]
        levels.append(current_level)
        processed.update(current_level)
        
        while True:
            next_level = []
            for wire in self.wires:
                if wire.start in processed and wire.end not in processed:
                    if all(w.start in processed for w in wire.end.inputs):
                        next_level.append(wire.end)
            
            if not next_level:
                break
            
            levels.append(next_level)
            processed.update(next_level)
        
        return levels

    def show_instructions(self):
        """Show instructions dialog"""
        root = tk.Tk()
        root.title("Logic Gate Simulator - Instructions")
        root.geometry("600x700")
        
        # Center the window
        root.update_idletasks()
        x = (root.winfo_screenwidth() - 600) // 2
        y = (root.winfo_screenheight() - 700) // 2
        root.geometry(f'600x700+{x}+{y}')
        
        # Create main frame with padding
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Instructions content
        sections = [
            ("Basic Controls", [
                "• Left-click and drag to move components",
                "• Right-click on components or wires to delete them",
                "• Click on inputs to toggle their state (ON/OFF)",
                "• Hover over wires to highlight them"
            ]),
            ("Building Circuits", [
                "• Drag components from the right sidebar onto the canvas",
                "• Click output point of one component and drag to input point of another to create wire (press the shift key while you drag to create a straight wire)",
                "• Components automatically update based on input changes",
                "• Only one output component is allowed per circuit",
                "• You can also press ALT + left click to duplicate a component"
            ]),
            ("Expression Builder", [
                "• Click 'Expression → Circuit' to create circuits from logical expressions",
                "• Supported operators: AND, OR, NOT, NAND, NOR, XOR",
                "• Example expressions:",
                "  - A AND B",
                "  - (A AND B) OR (NOT C)",
                "  - (A NAND B) OR (C XOR D)"
            ]),
            ("Saving & Loading", [
                "• Click 'Save' or 'Ctrl + S' to store your circuit locally",
                "• Click 'Load' or 'Ctrl + O' to open a saved circuit",
                "• Files are saved with .lcg extension",
            ]),
            ("Undo & Redo", [
                "• Click undo button (Ctrl + Z) to revert last action",
                "• Click redo button (Ctrl + Shift + Z) to repeat last undone action",
                "• History is maintained for up to 50 actions"
            ]),
            ("Additional Features", [
                "• Click 'Truth Table' or 'Ctrl + T' to see circuit's truth table",
                "• Click 'Get Expression' to see circuit's logical expression",
                "• Use trash button to clear entire canvas",
                "• Grid helps align components precisely"
            ])
        ]
        
        # Add title
        title = ttk.Label(scrollable_frame, text="How to Use the Logic Gate Simulator", 
                         font=("Arial", 14, "bold"))
        title.pack(pady=(0, 20))
        
        # Add sections
        for section_title, items in sections:
            # Section title
            section_label = ttk.Label(scrollable_frame, text=section_title,
                                    font=("Arial", 12, "bold"))
            section_label.pack(anchor="w", pady=(10, 5))
            
            # Section content
            content_frame = ttk.Frame(scrollable_frame)
            content_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            for item in items:
                item_label = ttk.Label(content_frame, text=item, wraplength=500,
                                     font=("Arial", 10))
                item_label.pack(anchor="w", pady=2)
        
        # Pack scrollbar and canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        close_button = ttk.Button(root, text="Close", command=root.destroy)
        close_button.pack(pady=20)
        
        root.mainloop()

    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        window = tk.Tk()
        window.title("Keyboard Shortcuts")
        window.geometry("400x500")

        # Center the window
        window.update_idletasks()
        x = (window.winfo_screenwidth() - 400) // 2
        y = (window.winfo_screenheight() - 500) // 2
        window.geometry(f"400x500+{x}+{y}")

        # Create scrollable frame
        frame = ttk.Frame(window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Add shortcuts list
        shortcuts = [
            ("File Operations", [
                ("Ctrl + S", "Save circuit"),
                ("Ctrl + O", "Open circuit"),
                ("Ctrl + Shift + N", "New circuit")
            ]),
            ("Editing", [
                ("Ctrl + Z", "Undo"),
                ("Ctrl + Shift + Z", "Redo"),
                ("Delete", "Delete selected component"),
                ("Escape", "Cancel current operation")
            ]),
            ("View", [
                ("Ctrl + T", "Show truth table"),
                ("Ctrl + E", "Show logic expression")
            ]),
            ("Input Control", [
                ("1-5", "Toggle input states")
            ]),
            ("Mouse + Keyboard", [
                ("Shift + Left Click", "Draw wires"),
                ("Alt + Left Click", "Duplicate component")
            ])
        ]

        row = 0
        for category, items in shortcuts:
            # Add category header
            ttk.Label(frame, text=category, font=("Arial", 12, "bold")).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=(10, 5))
            row += 1
            
            # Add shortcuts
            for key, description in items:
                ttk.Label(frame, text=key, font=("Courier", 10)).grid(
                    row=row, column=0, sticky="w", padx=(20, 10))
                ttk.Label(frame, text=description).grid(
                    row=row, column=1, sticky="w")
                row += 1

        # Add close button
        ttk.Button(window, text="Close", command=window.destroy).pack(pady=20)

        window.mainloop()

class Circuit:
    def generate_logical_expression(self):
        """Generate logical expression for the circuit"""
        if not self.gates:
            return ""
            
        # Start from output gates (gates with no outgoing connections)
        output_gates = self.find_output_gates()
        
        if not output_gates:
            return ""
            
        # Generate expression starting from each output
        expressions = []
        for output_gate in output_gates:
            expr = self._generate_expression_for_gate(output_gate)
            expressions.append(expr)
            
        return " AND ".join(expressions) if len(expressions) > 1 else expressions[0]
    
    def _generate_expression_for_gate(self, gate):
        """Recursively generate expression for a gate"""
        # Get input connections for this gate
        input_connections = [conn for conn in self.connections 
                           if conn.end_gate == gate]
        
        if not input_connections:
            return str(gate.label)
            
        # Generate expressions for inputs
        input_expressions = []
        for conn in input_connections:
            expr = self._generate_expression_for_gate(conn.start_gate)
            input_expressions.append(expr)
            
        # Combine expressions based on gate type
        if gate.gate_type == "AND":
            return f"({' AND '.join(input_expressions)})"
        elif gate.gate_type == "OR":
            return f"({' OR '.join(input_expressions)})"
        elif gate.gate_type == "NOT":
            return f"NOT({input_expressions[0]})"
        else:
            return f"({' '.join(input_expressions)})"
    
    def find_output_gates(self):
        """Find gates that have no outgoing connections"""
        output_gates = []
        for gate in self.gates:
            is_output = True
            for conn in self.connections:
                if conn.start_gate == gate:
                    is_output = False
                    break
            if is_output:
                output_gates.append(gate)
        return output_gates

if __name__ == "__main__":
    simulator = LogicSimulator()
    simulator.run()