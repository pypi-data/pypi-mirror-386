from typing import Optional, Dict, Tuple
from OpenGL.GL import *
import numpy as np

class ShaderManager:
    _instance: Optional['ShaderManager'] = None

    def __new__(cls) -> 'ShaderManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._init_attempted = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.shader_available = False
        self.program_id: Optional[int] = None
        self._uniform_locations: Dict[str, int] = {}

    def _initialize_shader(self) -> None:
        try:
            version_str = glGetString(GL_VERSION)
            if version_str is None:
                return

            vertex_shader_code = """
            #version 120
            attribute vec2 position;
            attribute vec2 texCoord;
            varying vec2 vTexCoord;
            uniform mat4 transform;

            void main() {
                gl_Position = transform * vec4(position, 0.0, 1.0);
                vTexCoord = texCoord;
            }
            """

            fragment_shader_code = """
            #version 120
            varying vec2 vTexCoord;
            uniform sampler2D texture;
            uniform vec4 backgroundColor;
            uniform vec4 borderColor;
            uniform vec2 texSize;
            uniform vec2 padding;
            uniform float cornerRadius;
            uniform float borderWidth;
            uniform float blurStrength;
            uniform float alpha;

            float roundedBoxSDF(vec2 centerPos, vec2 size, float radius) {
                return length(max(abs(centerPos) - size + radius, 0.0)) - radius;
            }

            vec4 applyGaussianBlur(sampler2D tex, vec2 uv, vec2 texelSize, float sigma) {
                if (sigma <= 0.0) {
                    return texture2D(tex, uv);
                }

                vec4 color = vec4(0.0);
                float totalWeight = 0.0;
                int radius = int(ceil(sigma * 2.0));

                for (int x = -radius; x <= radius; x++) {
                    for (int y = -radius; y <= radius; y++) {
                        vec2 offset = vec2(float(x), float(y)) * texelSize;
                        float dist = length(vec2(float(x), float(y)));
                        float weight = exp(-(dist * dist) / (2.0 * sigma * sigma));
                        color += texture2D(tex, uv + offset) * weight;
                        totalWeight += weight;
                    }
                }

                return color / totalWeight;
            }

            void main() {
                vec2 pixelPos = vTexCoord * texSize;
                vec2 centerPos = pixelPos - texSize * 0.5;
                vec2 halfSize = texSize * 0.5 - vec2(borderWidth * 0.5);

                float dist = roundedBoxSDF(centerPos, halfSize, cornerRadius);

                vec4 texColor = texture2D(texture, vTexCoord);

                if (blurStrength > 0.0) {
                    texColor = applyGaussianBlur(texture, vTexCoord, 1.0 / texSize, blurStrength);
                }

                vec4 finalColor = texColor;

                if (backgroundColor.a > 0.0) {
                    if (dist < 0.0) {
                        finalColor = mix(backgroundColor, texColor, texColor.a);
                    }
                }

                if (borderWidth > 0.0 && borderColor.a > 0.0) {
                    float borderDist = abs(dist);
                    if (borderDist < borderWidth) {
                        float borderAlpha = smoothstep(borderWidth, borderWidth - 1.0, borderDist);
                        finalColor = mix(finalColor, borderColor, borderAlpha * borderColor.a);
                    }
                }

                if (cornerRadius > 0.0) {
                    float edgeDist = dist;
                    if (edgeDist > 0.0) {
                        float edgeAlpha = 1.0 - smoothstep(0.0, 1.0, edgeDist);
                        finalColor.a *= edgeAlpha;
                    }
                }

                finalColor.a *= alpha;
                gl_FragColor = finalColor;
            }
            """

            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_code)
            glCompileShader(vertex_shader)

            if glGetShaderiv(vertex_shader, GL_COMPILE_STATUS) != GL_TRUE:
                glDeleteShader(vertex_shader)
                return

            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_code)
            glCompileShader(fragment_shader)

            if glGetShaderiv(fragment_shader, GL_COMPILE_STATUS) != GL_TRUE:
                glDeleteShader(vertex_shader)
                glDeleteShader(fragment_shader)
                return

            self.program_id = glCreateProgram()
            glAttachShader(self.program_id, vertex_shader)
            glAttachShader(self.program_id, fragment_shader)
            glLinkProgram(self.program_id)

            if glGetProgramiv(self.program_id, GL_LINK_STATUS) != GL_TRUE:
                glDeleteProgram(self.program_id)
                glDeleteShader(vertex_shader)
                glDeleteShader(fragment_shader)
                self.program_id = None
                return

            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)

            self._cache_uniform_locations()
            self.shader_available = True

        except Exception:
            self.shader_available = False
            if self.program_id is not None:
                try:
                    glDeleteProgram(self.program_id)
                except:
                    pass
                self.program_id = None

    def _cache_uniform_locations(self) -> None:
        if self.program_id is None:
            return

        uniform_names = [
            'transform', 'texture', 'backgroundColor', 'borderColor',
            'texSize', 'padding', 'cornerRadius', 'borderWidth',
            'blurStrength', 'alpha'
        ]

        for name in uniform_names:
            loc = glGetUniformLocation(self.program_id, name)
            if loc != -1:
                self._uniform_locations[name] = loc

    def is_shader_available(self) -> bool:
        if not self._init_attempted:
            self._init_attempted = True
            self._initialize_shader()
        return self.shader_available

    def use_shader(self) -> bool:
        if not self.shader_available or self.program_id is None:
            return False
        glUseProgram(self.program_id)
        return True

    def set_uniform_matrix4(self, name: str, matrix: np.ndarray) -> None:
        if name in self._uniform_locations:
            glUniformMatrix4fv(self._uniform_locations[name], 1, GL_FALSE, matrix)

    def set_uniform_int(self, name: str, value: int) -> None:
        if name in self._uniform_locations:
            glUniform1i(self._uniform_locations[name], value)

    def set_uniform_float(self, name: str, value: float) -> None:
        if name in self._uniform_locations:
            glUniform1f(self._uniform_locations[name], value)

    def set_uniform_vec2(self, name: str, x: float, y: float) -> None:
        if name in self._uniform_locations:
            glUniform2f(self._uniform_locations[name], x, y)

    def set_uniform_vec4(self, name: str, x: float, y: float, z: float, w: float) -> None:
        if name in self._uniform_locations:
            glUniform4f(self._uniform_locations[name], x, y, z, w)

    def stop_shader(self) -> None:
        glUseProgram(0)

    def __del__(self) -> None:
        if self.program_id is not None:
            try:
                glDeleteProgram(self.program_id)
            except:
                pass
