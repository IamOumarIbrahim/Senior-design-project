import os
os.environ['SDL_VIDEO_WINDOW_POS']='-3000,-3000'
import pygame
from pygame.locals import *
from OpenGL.GL import *
pygame.init()
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS,1)
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES,8)
pygame.display.set_mode((64,64), DOUBLEBUF|OPENGL|HIDDEN)
print(glGetString(GL_VERSION), glGetString(GL_RENDERER))
fbo=glGenFramebuffers(1); print('fbo',fbo, 'maxsamples', glGetIntegerv(GL_MAX_SAMPLES))
